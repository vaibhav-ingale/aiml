"""
Quick Model Switching Examples
Demonstrates how to switch between different LLM providers with one line of code.
Now uses global model configuration from model_config.py
"""

from langchain_core.prompts import ChatPromptTemplate
from mlutils import print_model_info, print_response
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model

# Get model from global configuration (edit model_config.py to change)
model = get_configured_model()
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

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
        print_response(response, PROVIDER)

    except Exception as e:
        print(f"Execution error: {e}")
else:
    print("Model not available - check your API keys or model availability")
