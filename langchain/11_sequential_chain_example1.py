from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from mlutils import print_model_info, print_response
from model_switcher import get_model

# Get model from configuration (edit model_switcher.py to change settings)
llm = get_model()
print_model_info(llm)

prompt_for_story_title = ChatPromptTemplate.from_template(
    "suggest 10 story titles based on the following idea: we found aliens on {planet} while we are looking for water there."
)

# First prompt template
first_prompt = ChatPromptTemplate.from_template("What is the best name to describe a company that makes {product}?")

# Second prompt template
second_prompt = ChatPromptTemplate.from_template("Write a 100 words description for the following company: {company_name}")

# REF: https://blog.langchain.com/langchain-expression-language/, https://www.geeksforgeeks.org/artificial-intelligence/langchain/
# Create chains using LCEL syntax 
chain_one = first_prompt | llm | StrOutputParser()

# Create second chain
chain_two = second_prompt | llm | StrOutputParser()


# Sequential processing function
def sequential_chain(inputs):
    company_name = chain_one.invoke({"product": inputs["product"]})
    description = chain_two.invoke({"company_name": company_name})
    return {"company_name": company_name, "description": description}


# Test with first product
product = "AI powered cars"
print(f"Product: {product}")
response = sequential_chain({"product": product})
print(f"Company Name:")
print_response(response["company_name"])
print(f"\nDescription:")
print_response(response["description"])
print()

print("=" * 60)

# Test with second product
product = "AI in healthcare"
print(f"Product: {product}")
response = sequential_chain({"product": product})
print(f"Company Name:")
print_response(response["company_name"])
print(f"\nDescription:")
print_response(response["description"])
print()
