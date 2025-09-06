import ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """Question: {question}

Answer: Understand like highschool student"""

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

# Crete series of questions
questions = [
    "What is the capital of France?",
    "What is the largest mammal?",
    "What is the speed of light?",
    "What is the meaning of life?",
    "What is the Fibonacci sequence?",
]
for question in questions:
    resp = chain.invoke({"question": question})
    print(f"Question: {question}\nAnswer: {resp}\n")
# Example usage
print("Generating a specific question response:")

print(resp)
