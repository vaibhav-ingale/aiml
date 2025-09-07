from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama.llms import OllamaLLM
from model_switcher import get_model

model = get_model("ollama", "llama3.2:1b", temperature=0.4, max_tokens=100)


# =============================================================================
# BASIC PROMPT EXAMPLE:
# =============================================================================
print("=" * 60)
print("BASIC PROMPT EXAMPLE:")

prompt_template = PromptTemplate.from_template("Tell me a joke about {topic}")
prompt = prompt_template.format(topic="dogs")
response = model.invoke(prompt)
print(response)


# =============================================================================
# CHAT PROMPT EXAMPLE:
# =============================================================================
input()
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
print(response)
