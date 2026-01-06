from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama.llms import OllamaLLM

from mlutils import print_model_info, print_response
from model_switcher import get_model

# Get model from configuration (edit model_switcher.py to change settings)
model = get_model()
print_model_info(model)

# =============================================================================
# BASIC PROMPT EXAMPLE:
# =============================================================================
print("=" * 60)
print("BASIC PROMPT EXAMPLE:")

prompt_template = PromptTemplate.from_template("Tell me a joke about {topic}")
prompt = prompt_template.format(topic="dogs")
response = model.invoke(prompt)
print_response(response, "ollama")


# =============================================================================
# CHAT PROMPT EXAMPLE:
# =============================================================================
user_input = input("Press Enter to continue to CHAT PROMPT EXAMPLE...").strip()
print("=" * 60)
print("BASIC CHAT PROMPT EXAMPLE:")

prompt_template = ChatPromptTemplate(
    [
        ("system", "You are a helpful assistant that tells jokes"),
        ("user", "Tell me a joke about {topic}"),
    ]
)

prompt = prompt_template.invoke({"topic": "cats and dogs"})
response = model.invoke(prompt)
print_response(response)
