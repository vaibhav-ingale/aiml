# Reference: https://python.langchain.com/docs/modules/chains/popular/chains/few_shot_prompt

from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model

from mlutils import print_model_info, print_response

model = get_configured_model()
print_model_info(MODEL_NAME, MODEL_PARAMS, PROVIDER)


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

questions = [
    "Which company was founded first, Tesla or Amazon?",
    "Is the capital of Australia farther south than the capital of New Zealand?",
    "Did the US declare war on Germany before or after the US declared war on Japan?",
    "Did the first president of the USA live to be 80?",
    "Was the creator of Linux born before 1970?",
    "Is the tallest mountain in Africa taller than the tallest mountain in Europe?",
    "Is the currency of Japan also used in South Korea?",
    "Which city is at a higher elevation, Denver or Mexico City?",
    "Was the iPhone released before or after Facebook was founded?",
    "Are the birthplaces of Elon Musk and Nelson Mandela in the same country?",
    "Who became president at a younger age, John F. Kennedy or Barack Obama?",
    "Which event happened first, the fall of the Berlin Wall or Nelson Mandela's release from prison?",
    "Did both Marie Curie and Albert Einstein win a Nobel Prize?",
]

for question in questions:
    response = chain.invoke({"input": question})
    print(f"Question: {question}")
    print("Answer:")
    print_response(response, PROVIDER)
    print("-" * 30)
    user_input = input("Press Enter to continue...").strip()
