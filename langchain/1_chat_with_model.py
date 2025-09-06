import ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """Question: {question}

Answer: Understand like highschool student and answer in a concise manner."""

prompt = ChatPromptTemplate.from_template(template)


models = ollama.list()["models"]
print("Available models:")
for i, model in enumerate(models):
    print(f"{i}: {model.model}")
model_index = int(input("Select a model by index: "))
if model_index < 0 or model_index >= len(models):
    raise ValueError("Invalid model index selected.")

model_name = models[model_index].model
model = OllamaLLM(model=model_name, temperature=0.1, max_tokens=100)
chain = prompt | model

# Crete series of questions
questions = [
    "What is the capital of France?",
    "What is the largest mammal?",
    "What is the speed of light?",
    "What is the Fibonacci sequence?",
]
print("=" * 40)
# include qustion number as well
for i, question in enumerate(questions, 1):
    question = f"{i}. {question}"
    resp = chain.invoke({"question": question})
    print(f"Question : {question}\nAnswer: {resp}\n")
    print("-" * 40)

print("#" * 40)
