from langchain_core.output_parsers import StrOutputParser
from model_config import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model
from model_switcher import get_model

from langchain.prompts import ChatPromptTemplate
from utils import print_model_info, print_response

llm = get_configured_model()
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

# First prompt template
first_prompt = ChatPromptTemplate.from_template("What is the best name to describe a company that makes {product}?")

# Second prompt template
second_prompt = ChatPromptTemplate.from_template("Write a 100 words description for the following company: {company_name}")

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
print_response(response["company_name"], PROVIDER)
print(f"\nDescription:")
print_response(response["description"], PROVIDER)
print()

print("=" * 60)

# Test with second product
product = "AI in healthcare"
print(f"Product: {product}")
response = sequential_chain({"product": product})
print(f"Company Name:")
print_response(response["company_name"], PROVIDER)
print(f"\nDescription:")
print_response(response["description"], PROVIDER)
print()
