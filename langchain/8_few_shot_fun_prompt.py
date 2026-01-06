# Reference: https://python.langchain.com/docs/modules/chains/popular/chains/few_shot_prompt

from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

from mlutils import print_model_info, print_response
from model_switcher import get_model

# Get model from configuration (edit model_switcher.py to change settings)
model = get_model()
print_model_info(model)

# 😂 is ^ in this context
example_prompt = PromptTemplate.from_template("Question: {question}\n{answer}")
examples = [
    {
        "question": "2 😂 3",
        "answer": "8",
    },
    {
        "question": "2 😂 5",
        "answer": "32",
    },
    {
        "question": "3 😂 4",
        "answer": "81",
    },
]


prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    suffix="Question: {input}",
    input_variables=["input"],
)

chain = prompt | model

response = chain.invoke({"input": "25 😂 4"})
print(f"Question: 25 😂 4")
print("Answer:")
print_response(response)
print("-" * 30)
