"""
Quick Model Switching Examples
Demonstrates how to switch between different LLM providers with one line of code.
"""

from langchain_core.prompts import ChatPromptTemplate
from model_switcher import get_model

print("=" * 60)
print("QUICK MODEL SWITCHING EXAMPLES")
print("=" * 60)

# =============================================================================
# MODEL SELECTION BLOCK
# =============================================================================
print("\nMODEL SELECTION:")
print("-" * 30)

# Select your model by uncommenting one line:
model = get_model("ollama", "llama3.2:1b", temperature=0.1, max_tokens=100)
# model = get_model("openai", "gpt-4", temperature=0.1, max_tokens=100)
# model = get_model("anthropic", "claude-3-sonnet-20240229", temperature=0.1, max_tokens=100)
# model = get_model("mistral", "mistral-small-latest", temperature=0.1, max_tokens=100)
# model = get_model(
#     "google", "gemini-2.5-flash-lite", temperature=0.1, max_output_tokens=100
# )

print(f"Selected model: {type(model).__name__ if model else 'None'}")

# =============================================================================
# MODEL CHAINING AND EXECUTION BLOCK
# =============================================================================
print("\nCHAINING AND EXECUTION:")
print("-" * 30)

# Define the prompt template
template = """Question: {question}

Answer: Understand like highschool student and answer in a concise manner."""

prompt = ChatPromptTemplate.from_template(template)

# Test question
question = "What is machine learning?"

if model:
    try:
        # Create the chain
        chain = prompt | model
        print("Chain created successfully")

        # Execute the chain
        print(f"Question: {question}")
        response = chain.invoke({"question": question})
        print(f"Response: {response}")

    except Exception as e:
        print(f"Execution error: {e}")
else:
    print("Model not available - check your API keys or model availability")
