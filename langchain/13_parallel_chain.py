from langchain_core.output_parsers import StrOutputParser
from langchain_ollama.llms import OllamaLLM
from model_config import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model
from model_switcher import get_model

from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableLambda, RunnableParallel
from utils import print_model_info, print_response

llm = get_configured_model()
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)


# Define prompt template
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an expert product reviewer."),
        ("human", "List the main features of the product {product_name}."),
    ]
)


# Define pros analysis step
def analyze_pros(features):
    pros_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert product reviewer."),
            (
                "human",
                "Given these features: {features}, list the pros of these features.",
            ),
        ]
    )
    return pros_template.format_prompt(features=features)


# Define cons analysis step
def analyze_cons(features):
    cons_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert product reviewer."),
            (
                "human",
                "Given these features: {features}, list the cons of these features.",
            ),
        ]
    )
    return cons_template.format_prompt(features=features)


# Combine pros and cons into a final review
def combine_pros_cons(pros, cons):
    return f"Pros:\n{pros}\n\nCons:\n{cons}"


# Simplify branches with LCEL
pros_branch_chain = RunnableLambda(lambda x: analyze_pros(x)) | llm | StrOutputParser()

cons_branch_chain = RunnableLambda(lambda x: analyze_cons(x)) | llm | StrOutputParser()

# Create the combined chain using LangChain Expression Language (LCEL)
chain = (
    prompt_template
    | llm
    | StrOutputParser()
    | RunnableParallel(branches={"pros": pros_branch_chain, "cons": cons_branch_chain})
    | RunnableLambda(lambda x: combine_pros_cons(x["branches"]["pros"], x["branches"]["cons"]))
)

# Run the chain
result = chain.invoke({"product_name": "MacBook Pro"})

# Output
print("Product Review for MacBook Pro:")
print_response(result, PROVIDER)
