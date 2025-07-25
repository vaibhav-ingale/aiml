import ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """Question: {question}

Answer: Let's think step by step to understand like highschool student."""

prompt = ChatPromptTemplate.from_template(template)


models = ollama.list()["models"]
print("Available models:")
for i, model in enumerate(models):
    print(f"{i}: {model.model}")
model_index = int(input("Select a model by index: "))
if model_index < 0 or model_index >= len(models):
    raise ValueError("Invalid model index selected.")

model_name = models[model_index].model
model = OllamaLLM(model=model_name, temperature=0.1, max_tokens=1000)
chain = prompt | model

resp = chain.invoke({"question": "What is Bias and Variance?"})

print(resp)
