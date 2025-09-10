import json
import re

from langchain_core.output_parsers import StrOutputParser
from model_switcher import get_model

from langchain.prompts import ChatPromptTemplate

llm = get_model("ollama", "gemma3:4b", temperature=0.1, max_tokens=500)


# Subject-specific templates
templates = {
    "physics": """You are a very smart physics professor. You are great at answering questions about physics in a concise and easy to understand manner. When you don't know the answer to a question you admit that you don't know.

Here is a question: {input}""",
    "math": """You are a very good mathematician. You are great at answering math questions. You are so good because you are able to break down hard problems into their component parts, answer the component parts, and then put them together to answer the broader question.

Here is a question: {input}""",
    "history": """You are a very good historian. You have an excellent knowledge of and understanding of people, events and contexts from a range of historical periods. You have the ability to think, reflect, debate, discuss and evaluate the past. You have a respect for historical evidence and the ability to make use of it to support your explanations and judgements.

Here is a question: {input}""",
    "computer science": """You are a successful computer scientist. You have a passion for creativity, collaboration, forward-thinking, confidence, strong problem-solving capabilities, understanding of theories and algorithms, and excellent communication skills. You are great at answering coding questions. You are so good because you know how to solve a problem by describing the solution in imperative steps that a machine can easily interpret and you know how to choose a solution that has a good balance between time complexity and space complexity.

Here is a question: {input}""",
    "biology": """You are a very good biologist. You have an excellent knowledge of and understanding of living organisms, their life processes, and their interactions with each other and their environments. You have the ability to think, reflect, debate, discuss and evaluate biological concepts and phenomena. You have a respect for scientific evidence and the ability to make use of it to support your explanations and judgements.

Here is a question: {input}""",
}

# Create chains for each subject
chains = {}
for name, template in templates.items():
    prompt = ChatPromptTemplate.from_template(template)
    chains[name] = prompt | llm | StrOutputParser()

# Default chain
default_chain = ChatPromptTemplate.from_template("{input}") | llm | StrOutputParser()

# Router prompt with better classification
router_prompt = ChatPromptTemplate.from_template(
    """
You are an expert at classifying questions into subject areas. Analyze the question and determine which subject area it belongs to.

Subject areas and their descriptions:
- physics: Questions about physical phenomena, forces, energy, radiation, thermodynamics, quantum mechanics, etc.
- math: Questions about calculations, equations, mathematical concepts, algebra, geometry, statistics, etc.
- history: Questions about historical events, people, periods, civilizations, wars, politics from the past, etc.
- computer science: Questions about programming, algorithms, data structures, software development, coding, etc.
- biology: Questions about living organisms, life processes, ecosystems, genetics, cellular functions, etc.
- DEFAULT: Questions that don't clearly fit into the above categories

Question: {input}

Think about the question and classify it. Consider keywords and concepts. No not explain your reasoning.

Examples:
- "What is black body radiation?" -> physics (radiation is a physics concept)
- "What is 2 + 2?" -> math (basic arithmetic)
- "Who was Napoleon?" -> history (historical figure)
- "How do I sort an array?" -> computer science (programming concept)
- "What is photosynthesis?" -> biology (biological process)

Now classify this question and respond with ONLY the subject name: physics, math, history, computer science, or DEFAULT.

Summarize the output text in exactly two lines. Be concise and capture the main points.
"""
)

router_chain = router_prompt | llm | StrOutputParser()


def route_question(question):
    """Route question to appropriate subject expert"""
    # Get routing decision
    route_response = router_chain.invoke({"input": question}).strip().lower()

    # Extract the subject from the response (in case LLM adds extra text)
    route = "DEFAULT"
    for subject in chains.keys():
        if subject in route_response:
            route = subject
            break

    print(f"Question: '{question}'")
    print(f"Router response: '{route_response}'")
    print(f"Routing to: ===>[[ {route} ]]<===")
    print("-" * 50)

    # Route to appropriate chain
    if route in chains:
        return chains[route].invoke({"input": question})
    else:
        return default_chain.invoke({"input": question})


# Test questions
questions = [
    "What is black body radiation?",
    "what is (2*2)^4",
    "Why does every cell in our body contain DNA?",
    "How does glycogen generate energy?",
    "What is the Pythagorean theorem?",
    "Explain the theory of relativity.",
    "What is the capital of France?",
    "How do I write a for loop in Python?",
    # "What is the significance of the Battle of Hastings?",
    # "What is the time complexity of quicksort?",
    # "What is the derivative of x^2?",
    # "Who was the first president of the United States?",
    # "What is the difference between a virus and bacteria?",
    # "How does photosynthesis work?",
    # "What is the Fibonacci sequence?",
    # "What is the purpose of the mitochondria in a cell?",
    # "What is the difference between a compiler and an interpreter?",
]

for question in questions:
    print(f"Question: {question}")
    response = route_question(question)
    print(f"Answer: {response}")
    print("=" * 60)
    print(f"Answer: {response}")
    print("=" * 60)
