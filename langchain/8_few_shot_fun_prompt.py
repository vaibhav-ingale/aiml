# Reference: https://python.langchain.com/docs/modules/chains/popular/chains/few_shot_prompt

from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from model_switcher import get_model

model = get_model("ollama", "gpt-oss:20b", temperature=0.1, max_tokens=100)

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
print(response)
print("-" * 30)
