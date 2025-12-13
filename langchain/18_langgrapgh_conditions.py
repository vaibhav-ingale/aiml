from typing import TypedDict, Literal

from langgraph.graph import END, StateGraph


# Define the state structure using TypedDict
class GraphState(TypedDict):
    messages: list[str]
    user_input: str
    score: int
    path_taken: str


# Define the nodes (functions)
def start_node(state: GraphState) -> GraphState:
    """Starting node that initializes the workflow."""
    return {
        "messages": state["messages"] + ["Starting workflow..."],
        "user_input": state.get("user_input", ""),
        "score": state.get("score", 0),
        "path_taken": "start",
    }


def analyze_input(state: GraphState) -> GraphState:
    """Analyzes the user input and assigns a score."""
    user_input = state["user_input"].lower()

    # Simple scoring logic based on input
    score = len(user_input)

    if "urgent" in user_input or "important" in user_input:
        score += 10
    if "help" in user_input:
        score += 5

    return {
        "messages": state["messages"] + [f"Analyzed input: '{user_input}' (Score: {score})"],
        "user_input": state["user_input"],
        "score": score,
        "path_taken": state["path_taken"],
    }


def high_priority_handler(state: GraphState) -> GraphState:
    """Handles high priority requests."""
    return {
        "messages": state["messages"] + ["HIGH PRIORITY: Processing immediately!"],
        "user_input": state["user_input"],
        "score": state["score"],
        "path_taken": state["path_taken"] + " -> high_priority",
    }


def medium_priority_handler(state: GraphState) -> GraphState:
    """Handles medium priority requests."""
    return {
        "messages": state["messages"] + ["MEDIUM PRIORITY: Processing in normal queue."],
        "user_input": state["user_input"],
        "score": state["score"],
        "path_taken": state["path_taken"] + " -> medium_priority",
    }


def low_priority_handler(state: GraphState) -> GraphState:
    """Handles low priority requests."""
    return {
        "messages": state["messages"] + ["LOW PRIORITY: Will process when resources available."],
        "user_input": state["user_input"],
        "score": state["score"],
        "path_taken": state["path_taken"] + " -> low_priority",
    }


def validation_node(state: GraphState) -> GraphState:
    """Validates the processing."""
    return {
        "messages": state["messages"] + ["Validation complete."],
        "user_input": state["user_input"],
        "score": state["score"],
        "path_taken": state["path_taken"] + " -> validation",
    }


def escalation_node(state: GraphState) -> GraphState:
    """Escalates high priority items for additional processing."""
    return {
        "messages": state["messages"] + ["Escalating to senior team..."],
        "user_input": state["user_input"],
        "score": state["score"],
        "path_taken": state["path_taken"] + " -> escalation",
    }


def final_processing(state: GraphState) -> GraphState:
    """Final processing before completion."""
    return {
        "messages": state["messages"] + ["Final processing complete."],
        "user_input": state["user_input"],
        "score": state["score"],
        "path_taken": state["path_taken"] + " -> final",
    }


# Conditional routing function
def route_by_priority(state: GraphState) -> Literal["high_priority", "medium_priority", "low_priority"]:
    """Routes based on the score (priority level)."""
    score = state["score"]

    if score >= 20:
        return "high_priority"
    elif score >= 10:
        return "medium_priority"
    else:
        return "low_priority"


def route_after_high_priority(state: GraphState) -> Literal["escalation", "validation"]:
    """Decides whether to escalate high priority items."""
    score = state["score"]

    # Escalate if score is very high (>= 25)
    if score >= 25:
        return "escalation"
    else:
        return "validation"


def route_to_end(state: GraphState) -> Literal["final", "end"]:
    """Decides whether additional final processing is needed."""
    # If the path included escalation, skip final processing
    if "escalation" in state["path_taken"]:
        return "end"
    else:
        return "final"


# Create a new StateGraph with the defined state structure
workflow = StateGraph(GraphState)

# Add all nodes to the graph
workflow.add_node("start", start_node)
workflow.add_node("analyze", analyze_input)
workflow.add_node("high_priority", high_priority_handler)
workflow.add_node("medium_priority", medium_priority_handler)
workflow.add_node("low_priority", low_priority_handler)
workflow.add_node("validation", validation_node)
workflow.add_node("escalation", escalation_node)
workflow.add_node("final", final_processing)

# Set the entry point
workflow.set_entry_point("start")

# Add sequential edges
workflow.add_edge("start", "analyze")

# Add conditional edge from analyze to priority handlers
workflow.add_conditional_edges(
    "analyze",
    route_by_priority,
    {
        "high_priority": "high_priority",
        "medium_priority": "medium_priority",
        "low_priority": "low_priority",
    }
)

# Add conditional edge from high_priority
workflow.add_conditional_edges(
    "high_priority",
    route_after_high_priority,
    {
        "escalation": "escalation",
        "validation": "validation",
    }
)

# Medium and low priority go directly to validation
workflow.add_edge("medium_priority", "validation")
workflow.add_edge("low_priority", "validation")

# Escalation goes to validation
workflow.add_edge("escalation", "validation")

# Add conditional edge from validation
workflow.add_conditional_edges(
    "validation",
    route_to_end,
    {
        "final": "final",
        "end": END,
    }
)

# Final goes to END
workflow.add_edge("final", END)

# Compile the graph into a runnable workflow
app = workflow.compile()


def run_workflow(user_input: str):
    """Run the workflow with a given user input."""
    print(f"\n{'=' * 80}")
    print(f"Processing: '{user_input}'")
    print(f"{'=' * 80}")

    # Invoke the workflow with an initial state
    initial_state = {
        "messages": [],
        "user_input": user_input,
        "score": 0,
        "path_taken": "",
    }
    result = app.invoke(initial_state)

    # Print the results
    print(f"\nScore: {result['score']}")
    print(f"Path Taken: {result['path_taken']}")

    print("\nWorkflow Messages:")
    print("-" * 80)
    for i, msg in enumerate(result["messages"], 1):
        print(f"{i}. {msg}")
    print("-" * 80)

    return result


# Generate PNG visualization of the graph
def generate_graph_visualization():
    """Generate and save a PNG visualization of the workflow graph."""
    try:
        # Generate the PNG
        png_data = app.get_graph().draw_mermaid_png()

        # Save to file
        output_file = "18_workflow_graph.png"
        with open(output_file, "wb") as f:
            f.write(png_data)

        print(f"\n{'=' * 80}")
        print(f"Graph visualization saved to: {output_file}")
        print(f"{'=' * 80}\n")

        return output_file
    except Exception as e:
        print(f"\nNote: Could not generate PNG visualization: {e}")
        print("You may need to install: pip install pygraphviz or pip install graphviz")
        return None


# Test the workflow with different inputs
if __name__ == "__main__":
    # Generate graph visualization first
    generate_graph_visualization()

    # Test 1: Low priority
    run_workflow("hello")

    # Test 2: Medium priority
    run_workflow("I need some help with this")

    # Test 3: High priority (no escalation)
    run_workflow("This is urgent help needed")

    # Test 4: Very high priority (with escalation)
    run_workflow("URGENT AND IMPORTANT: Critical issue needs immediate help!")
