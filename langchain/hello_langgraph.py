# Step 1: Define tools and model
import json
from typing import Any, Dict, List

from langchain_community.llms import Ollama

from langchain.tools import tool

# Initialize Ollama model
# Make sure Ollama is running locally with: ollama run gptoss:20b
model = Ollama(model="gpt-oss:20b", temperature=0, base_url="http://localhost:11434")  # Default Ollama URL


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.
    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.
    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.
    Args:
        a: First int
        b: Second int
    """
    return a / b


# Create tools list and dictionary
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}

import operator

# Step 2: Define state
from typing import Annotated, Optional, TypedDict


class MessagesState(TypedDict):
    messages: Annotated[List[Dict[str, Any]], operator.add]
    llm_calls: int


# Step 3: Define custom tool calling logic for Ollama
def format_tools_for_prompt(tools: List) -> str:
    """Format tools for the system prompt"""
    tool_descriptions = []
    for tool in tools:
        tool_descriptions.append(
            f"""
- {tool.name}: {tool.description}
  Parameters: {tool.args}"""
        )
    return "\n".join(tool_descriptions)


def parse_tool_calls(response: str) -> List[Dict[str, Any]]:
    """Parse tool calls from the LLM response"""
    tool_calls = []

    # Look for JSON-formatted tool calls in the response
    import re

    # Pattern to find tool calls in format: {"tool": "name", "args": {...}}
    pattern = r'\{[^}]*"tool"[^}]*\}'
    matches = re.findall(pattern, response)

    for match in matches:
        try:
            call_data = json.loads(match)
            if "tool" in call_data and "args" in call_data:
                tool_calls.append({"id": f"call_{len(tool_calls)}", "name": call_data["tool"], "args": call_data["args"]})
        except json.JSONDecodeError:
            continue

    return tool_calls


# Step 4: Define model node with Ollama
def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    # Format the conversation history
    conversation = ""
    for msg in state.get("messages", []):
        if msg.get("role") == "user":
            conversation += f"User: {msg.get('content', '')}\n"
        elif msg.get("role") == "assistant":
            conversation += f"Assistant: {msg.get('content', '')}\n"
        elif msg.get("role") == "tool":
            conversation += f"Tool Result: {msg.get('content', '')}\n"

    # Create the prompt with tool descriptions
    prompt = f"""You are a helpful assistant tasked with performing arithmetic on a set of inputs.

Available tools:
{format_tools_for_prompt(tools)}

To use a tool, respond with a JSON object in this format:
{{"tool": "tool_name", "args": {{"param1": value1, "param2": value2}}}}

After using a tool, wait for the result before proceeding.
If no tool is needed, provide a direct answer.

Conversation:
{conversation}
Current request: """

    # Get the response from Ollama
    response = model.invoke(prompt)

    # Parse tool calls from response
    tool_calls = parse_tool_calls(response)

    # Create message with tool calls
    message = {"role": "assistant", "content": response, "tool_calls": tool_calls}

    return {"messages": [message], "llm_calls": state.get("llm_calls", 0) + 1}


# Step 5: Define tool node
def tool_node(state: dict):
    """Performs the tool call"""
    result = []
    last_message = state["messages"][-1]

    for tool_call in last_message.get("tool_calls", []):
        tool = tools_by_name.get(tool_call["name"])
        if tool:
            try:
                observation = tool.invoke(tool_call["args"])
                result.append({"role": "tool", "content": f"Tool '{tool_call['name']}' returned: {observation}", "tool_call_id": tool_call["id"]})
            except Exception as e:
                result.append({"role": "tool", "content": f"Error calling tool '{tool_call['name']}': {str(e)}", "tool_call_id": tool_call["id"]})

    return {"messages": result}


# Step 6: Define logic to determine whether to end
from typing import Literal

from langgraph.graph import END, START, StateGraph


def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.get("tool_calls"):
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


# Step 7: Build agent
# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

# Optional: Visualize the graph (requires graphviz)
try:
    from IPython.display import Image, display

    display(Image(agent.get_graph(xray=True).draw_mermaid_png()))
except:
    print("Graph visualization not available")


# Step 8: Test the agent
def test_agent():
    """Test the agent with a simple arithmetic task"""

    # Create initial message
    messages = [{"role": "user", "content": "Add 3 and 4, then multiply the result by 2."}]

    # Invoke the agent
    result = agent.invoke({"messages": messages, "llm_calls": 0})

    # Print the conversation
    print("\n=== Agent Execution ===")
    for i, msg in enumerate(result["messages"]):
        print(f"\nMessage {i + 1}:")
        print(f"Role: {msg.get('role', 'unknown')}")
        print(f"Content: {msg.get('content', '')}")
        if msg.get("tool_calls"):
            print(f"Tool Calls: {msg['tool_calls']}")

    print(f"\nTotal LLM calls: {result['llm_calls']}")

    return result


# Alternative simpler usage without visualization
def run_simple_query(query: str):
    """Run a simple query through the agent"""
    messages = [{"role": "user", "content": query}]
    result = agent.invoke({"messages": messages, "llm_calls": 0})

    # Get the final answer
    for msg in reversed(result["messages"]):
        if msg.get("role") == "assistant" and not msg.get("tool_calls"):
            return msg.get("content", "No answer found")

    return "No final answer provided"


if __name__ == "__main__":
    print("Testing Ollama LangGraph Agent with gptoss:20b model")
    print("=" * 50)

    from IPython.display import Image, display

    # Show the agent
    display(Image(agent.get_graph(xray=True).draw_mermaid_png()))

    # Make sure Ollama is running
    print("\nNote: Make sure Ollama is running locally with:")
    print("  ollama run gptoss:20b")
    print("\nOr pull the model first if you haven't:")
    print("  ollama pull gptoss:20b")
    print("=" * 50)

    # Test the agent
    test_agent()

    # Additional test queries
    print("\n\n=== Additional Tests ===")
    queries = ["What is 10 divided by 2?", "Calculate 15 plus 25", "Multiply 7 by 8"]

    for query in queries:
        print(f"\nQuery: {query}")
        answer = run_simple_query(query)
        print(f"Answer: {answer}")
