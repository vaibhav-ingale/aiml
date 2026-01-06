"""
Quick Model Example
Demonstrates how to use the configured model with one line of code.
Uses model configuration from model_switcher.py
"""

from langchain_core.prompts import ChatPromptTemplate

from mlutils import print_model_info, print_response
from model_switcher import get_model

# Get model from configuration (edit model_switcher.py to change settings)
model = get_model()
print_model_info(model)

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
question = "What is embedings in LLM?"

if model:
    try:
        # Create the chain
        chain = prompt | model
        print("Chain created successfully")

        # Execute the chain
        print(f"\nQuestion: {question}")
        response = chain.invoke({"question": question})

        # Print response using utility function
        print_response(response)

    except Exception as e:
        print(f"Execution error: {e}")
else:
    print("Model not available - check your API keys or model availability")
