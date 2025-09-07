# Reference: https://python.langchain.com/docs/modules/chains/popular/chains/few_shot_prompt

from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from model_switcher import get_model

model = get_model("ollama", "gpt-oss:20b", temperature=0.1, max_tokens=100)


example_prompt = PromptTemplate.from_template("Question: {question}\n{answer}")
examples = [
    {
        "question": "Who was older when they won a Nobel Prize, Albert Einstein or Malala Yousafzai?",
        "answer": """
Are follow up questions needed here: Yes.
Follow up: How old was Albert Einstein when he won the Nobel Prize?
Intermediate answer: Einstein won the Nobel Prize in Physics in 1921, at age 42.
Follow up: How old was Malala Yousafzai when she won the Nobel Prize?
Intermediate answer: Malala won the Nobel Peace Prize in 2014, at age 17.
So the final answer is: Albert Einstein
""",
    },
    {
        "question": "Which country has a larger population, Canada or Australia?",
        "answer": """
Are follow up questions needed here: Yes.
Follow up: What is the population of Canada?
Intermediate answer: About 39 million (as of 2025).
Follow up: What is the population of Australia?
Intermediate answer: About 27 million (as of 2025).
So the final answer is: Canada
""",
    },
    {
        "question": "Was the Wright brothers’ first flight before or after the invention of the light bulb?",
        "answer": """
Are follow up questions needed here: Yes.
Follow up: When did the Wright brothers make their first flight?
Intermediate answer: 1903.
Follow up: When was the light bulb invented?
Intermediate answer: Thomas Edison patented the light bulb in 1879.
So the final answer is: The light bulb was invented before the Wright brothers' first flight.
""",
    },
    {
        "question": "Did Steve Jobs and Bill Gates both drop out of college?",
        "answer": """
Are follow up questions needed here: Yes.
Follow up: Did Steve Jobs drop out of college?
Intermediate answer: Yes, he dropped out of Reed College.
Follow up: Did Bill Gates drop out of college?
Intermediate answer: Yes, he dropped out of Harvard University.
So the final answer is: Yes
""",
    },
]


prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    suffix="Question: {input}",
    input_variables=["input"],
)

chain = prompt | model

response = chain.invoke({"input": "Which company was founded first, Tesla or Amazon?"})
print(f"Question: Which company was founded first, Tesla or Amazon?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Is the capital of Australia farther south than the capital of New Zealand?"})
print(f"Question: Is the capital of Australia farther south than the capital of New Zealand?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Did the US declare war on Germany before or after the US declared war on Japan?"})
print(f"Question: Did the US declare war on Germany before or after the US declared war on Japan?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Did the first president of the USA live to be 80?"})
print(f"Question: Did the first president of the USA live to be 80?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Was the creator of Linux born before 1970?"})
print(f"Question: Was the creator of Linux born before 1970?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Is the tallest mountain in Africa taller than the tallest mountain in Europe?"})
print(f"Question: Is the tallest mountain in Africa taller than the tallest mountain in Europe?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Is the currency of Japan also used in South Korea?"})
print(f"Question: Is the currency of Japan also used in South Korea?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Which city is at a higher elevation, Denver or Mexico City?"})
print(f"Which city is at a higher elevation, Denver or Mexico City?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Was the iPhone released before or after Facebook was founded?"})
print(f"Was the iPhone released before or after Facebook was founded?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Are the birthplaces of Elon Musk and Nelson Mandela in the same country?"})
print(f"Are the birthplaces of Elon Musk and Nelson Mandela in the same country?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Who became president at a younger age, John F. Kennedy or Barack Obama?"})
print(f"Who became president at a younger age, John F. Kennedy or Barack Obama?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Which event happened first, the fall of the Berlin Wall or Nelson Mandela's release from prison?"})
print(f"Which event happened first, the fall of the Berlin Wall or Nelson Mandela's release from prison?")
print(response)
print("-" * 30)
input()

response = chain.invoke({"input": "Did both Marie Curie and Albert Einstein win a Nobel Prize?"})
print(f"Did both Marie Curie and Albert Einstein win a Nobel Prize?")
print(response)
print("-" * 30)
input()
