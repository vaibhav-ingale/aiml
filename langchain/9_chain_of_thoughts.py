# Chain of Thought (CoT) prompting example
# CoT helps models break down complex problems into step-by-step reasoning

from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model

from mlutils import print_model_info, print_response

model = get_configured_model()
print_model_info(MODEL_NAME, MODEL_PARAMS, PROVIDER)

# =============================================================================
# EXAMPLE 1: Basic Chain of Thought with Math Problem
# =============================================================================
print("=" * 60)
print("BASIC CHAIN OF THOUGHT - Math Problem:")
print("=" * 60)

cot_prompt = PromptTemplate.from_template(
    """
Question: {question}

Let's think step by step:
"""
)

math_question = "If a store has 23 apples and sells 8 apples in the morning and 6 apples in the afternoon, how many apples are left?"

prompt = cot_prompt.format(question=math_question)
response = model.invoke(prompt)
print_response(response, PROVIDER)

# =============================================================================
# EXAMPLE 2: Few-Shot Chain of Thought
# =============================================================================
print("\n" + "=" * 60)
print("FEW-SHOT CHAIN OF THOUGHT:")
print("=" * 60)

# Examples showing step-by-step reasoning
examples = [
    {
        "question": "Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?",
        "answer": """Let me think step by step:
1. Roger starts with 5 tennis balls
2. He buys 2 cans, each with 3 balls
3. So he gets 2 x 3 = 6 more tennis balls  
4. Total tennis balls = 5 + 6 = 11 tennis balls""",
    },
    {
        "question": "The cafeteria had 23 apples. If they used 20 for lunch and bought 6 more, how many apples do they have?",
        "answer": """Let me think step by step:
1. Started with 23 apples
2. Used 20 apples for lunch, so 23 - 20 = 3 apples left
3. Bought 6 more apples
4. Total apples = 3 + 6 = 9 apples""",
    },
]

example_prompt = PromptTemplate.from_template(
    """
Question: {question}
Answer: {answer}
"""
)

few_shot_prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix="Solve these math problems step by step:\n",
    suffix="\nQuestion: {question}\nAnswer: Let me think step by step:",
    input_variables=["question"],
)

new_question = "A library had 15 books. They gave away 7 books and received 12 new books. How many books do they have now?"
prompt = few_shot_prompt.format(question=new_question)
response = model.invoke(prompt)
print_response(response, PROVIDER)

# =============================================================================
# EXAMPLE 3: Complex Reasoning Chain of Thought
# =============================================================================
print("\n" + "=" * 60)
print("COMPLEX REASONING CHAIN OF THOUGHT:")
print("=" * 60)

complex_cot_prompt = PromptTemplate.from_template(
    """
Question: {question}

To solve this, I need to break it down into steps:

Step 1: Identify what we know
Step 2: Identify what we need to find  
Step 3: Plan the solution approach
Step 4: Execute the solution
Step 5: Verify the answer

Let me work through this systematically:
"""
)

complex_question = "If training a neural network requires 100 epochs, and each epoch takes 2.5 minutes on average, but every 10th epoch takes an extra 30 seconds for validation, how long will the total training take?"

prompt = complex_cot_prompt.format(question=complex_question)
response = model.invoke(prompt)
print_response(response, PROVIDER)
