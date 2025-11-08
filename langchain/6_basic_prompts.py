from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama.llms import OllamaLLM
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model
from model_switcher import get_model

from mlutils import print_model_info, print_response

model = get_configured_model()
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)


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
print_response(response, PROVIDER)
