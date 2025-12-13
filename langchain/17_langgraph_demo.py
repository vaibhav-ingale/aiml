from typing import TypedDict

from langgraph.graph import END, StateGraph


# Define the state structure using TypedDict
class GraphState(TypedDict):
    messages: list[str]


# Define the nodes (functions)
def node1(state: GraphState) -> GraphState:
    """Processes the input and adds a message from Node 1."""
    return {"messages": state["messages"] + ["I reached Node 1."]}


def node2(state: GraphState) -> GraphState:
    """Processes the input and adds a message from Node 2."""
    return {"messages": state["messages"] + ["And now at Node 2."]}


# Create a new StateGraph with the defined state structure
workflow = StateGraph(GraphState)

# Add the nodes to the graph
workflow.add_node("first_node", node1)
workflow.add_node("second_node", node2)

# Set the entry point (where the graph starts)
workflow.set_entry_point("first_node")

# Add an edge from the first node to the second node
workflow.add_edge("first_node", "second_node")

# Add edge from second node to END to finish the workflow
workflow.add_edge("second_node", END)

# Compile the graph into a runnable workflow
app = workflow.compile()

# Invoke the workflow with an initial state
initial_state = {"messages": ["Starting the workflow."]}
result = app.invoke(initial_state)

# Print the final state
print("\nFinal State:")
print("=" * 50)
print(result)
print("=" * 50)

# Print messages one by one for better readability
print("\nWorkflow Messages:")
print("-" * 50)
for i, msg in enumerate(result["messages"], 1):
    print(f"{i}. {msg}")
print("-" * 50)
