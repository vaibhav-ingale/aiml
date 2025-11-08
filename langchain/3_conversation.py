"""
LangChain Messages - Comprehensive Examples
Demonstrates proper usage of SystemMessage, HumanMessage, and AIMessage for various use cases.
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from mlutils import print_model_info, print_response
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model

# Get model from global configuration (edit model_config.py to change)
model = get_configured_model()
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

print("LangChain Messages - Use Case Examples")
print("=" * 50)

# =============================================================================
# USE CASE 1: BASIC CONVERSATION WITH SYSTEM PROMPT
# =============================================================================
user_input = input("Press Enter to continue to USE CASE 1...").strip()
print("\nUSE CASE 1: Math Tutor with System Prompt")
print("-" * 40)

messages = [
    SystemMessage(content="You are a helpful math tutor. Explain your reasoning step by step with maths concepts used and keep answers concise."),
    HumanMessage(content="What is 256 divided by 7?"),
]

result = model.invoke(messages)
print(f"Question: What is 256 divided by 7?")
print("AI Response:")
print_response(result, PROVIDER)

# =============================================================================
# USE CASE 2: CONVERSATION WITH CONTEXT (MULTI-TURN)
# =============================================================================
user_input = input("Press Enter to continue to USE CASE 2...").strip()
print("\nUSE CASE 2: Multi-turn Conversation with Context")
print("-" * 40)

conversation = [
    SystemMessage(content="You are a cooking assistant. Give brief, practical cooking advice."),
    HumanMessage(content="How do I make pasta?"),
    AIMessage(content="1. Boil salted water 2. Add pasta 3. Cook 8-12 minutes 4. Drain 5. Add sauce"),
    HumanMessage(content="What if I want to make it healthier?"),
]

result = model.invoke(conversation)
print("Previous exchange:")
print("Human: How do I make pasta?")
print("AI: 1. Boil salted water 2. Add pasta 3. Cook 8-12 minutes 4. Drain 5. Add sauce")
print(f"\nHuman: What if I want to make it healthier?")
print("AI Response:")
print_response(result, PROVIDER)

# =============================================================================
# USE CASE 3: ROLE-BASED CONVERSATION
# =============================================================================
input("Press Enter to continue...")
print("\nUSE CASE 3: Role-based Conversation (Code Review)")
print("-" * 40)

code_review = [
    SystemMessage(content="You are a senior Python developer reviewing code. Focus on best practices and improvements."),
    HumanMessage(
        content="""
def calculate_area(length, width):
    return length * width

result = calculate_area(5, 10)
print(result)
"""
    ),
]

result = model.invoke(code_review)
print("Code to review:")
print("def calculate_area(length, width):")
print("    return length * width")
print("result = calculate_area(5, 10)")
print("print(result)")
print("\nCode Review:")
print_response(result, PROVIDER)

# =============================================================================
# USE CASE 4: TASK-SPECIFIC WITH EXAMPLES (FEW-SHOT)
# =============================================================================
user_input = input("Press Enter to continue to USE CASE 4...").strip()
print("\nUSE CASE 4: Few-shot Learning (Sentiment Analysis)")
print("-" * 40)

sentiment_task = [
    SystemMessage(content="Classify the sentiment of text as: POSITIVE, NEGATIVE, or NEUTRAL. Be concise. and provide only the single label."),
    HumanMessage(content="I love this product! It works perfectly."),
    AIMessage(content="POSITIVE"),
    HumanMessage(content="This is okay, nothing special."),
    AIMessage(content="NEUTRAL"),
    HumanMessage(content="I hate about the new features coming next month!"),
]

result = model.invoke(sentiment_task)
print("Examples provided:")
print("'I love this product! It works perfectly.' → POSITIVE")
print("'This is okay, nothing special.' → NEUTRAL")
print(f"\nNew text: 'I hate about the new features coming next month!'")
print("AI Classification:")
print_response(result, PROVIDER)

# =============================================================================
# USE CASE 5: CREATIVE WRITING WITH CONSTRAINTS
# =============================================================================
user_input = input("Press Enter to continue to USE CASE 5...").strip()
print("\nUSE CASE 5: Creative Writing with Constraints")
print("-" * 40)

creative_writing = [
    SystemMessage(content="You are a creative writer. Write exactly 2 sentences. Be imaginative but concise."),
    HumanMessage(content="Write a short story about a robot learning to paint"),
]

result = model.invoke(creative_writing)
print("Prompt: Write a short story about a robot learning to paint")
print("AI Story:")
print_response(result, PROVIDER)

# =============================================================================
# USE CASE 6: DYNAMIC CONVERSATION BUILDING
# =============================================================================
user_input = input("Press Enter to continue to USE CASE 6...").strip()
print("\nUSE CASE 6: Building Conversation Dynamically")
print("-" * 40)


def build_conversation(system_prompt, qa_pairs):
    """Helper function to build conversation from Q&A pairs."""
    messages = [SystemMessage(content=system_prompt)]

    for question, answer in qa_pairs:
        messages.append(HumanMessage(content=question))
        if answer:  # If we have an answer, add it
            messages.append(AIMessage(content=answer))

    return messages


# Build a conversation about plants
plant_conversation = build_conversation(
    system_prompt="You are a plant expert. Give practical gardening advice.",
    qa_pairs=[
        (
            "How often should I water my houseplants?",
            "Check soil moisture. Most houseplants need water when top inch is dry, usually 1-2 times per week.",
        ),
        (
            "My plant leaves are turning yellow. What should I do?",
            None,
        ),  # No answer yet - this is what we want to ask
    ],
)

result = model.invoke(plant_conversation)
print("Conversation history:")
print("Q: How often should I water my houseplants?")
print("A: Check soil moisture. Most houseplants need water when top inch is dry, usually 1-2 times per week.")
print(f"\nQ: My plant leaves are turning yellow. What should I do?")
print("A:")
print_response(result, PROVIDER)

print("\n" + "=" * 50)
