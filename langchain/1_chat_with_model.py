import ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

from utils import print_response

template = """Question: {question}

Answer: Understand like highschool student and answer in a concise manner."""

prompt = ChatPromptTemplate.from_template(template)

models = ollama.list()["models"]
print("Available models:")
for i, model in enumerate(models):
    print(f"{i}: {model.model}")

# Input validation for model selection
while True:
    model_input = input("Select a model by index: ").strip()
    if not model_input:
        print("No input provided. Please enter a valid model index.")
        continue
    try:
        model_index = int(model_input)
        if model_index < 0 or model_index >= len(models):
            print(f"Invalid model index. Please enter a number between 0 and {len(models) - 1}.")
            continue
        break
    except ValueError:
        print("Invalid input. Please enter a valid number.")

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
    print(f"Question : {question}")
    print("Answer:")
    print_response(resp, "ollama")
    print("-" * 40)

print("#" * 40)
