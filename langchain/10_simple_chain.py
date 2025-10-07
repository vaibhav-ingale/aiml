from model_config import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model
from model_switcher import get_model

from langchain.prompts import ChatPromptTemplate
from utils import print_model_info, print_response

llm = get_configured_model()
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

prompt_for_story_title = ChatPromptTemplate.from_template(
    "suggest 10 story titles based on the following idea: we found aliens on {planet} while we are looking for water there."
)

chain = prompt_for_story_title | llm

# Example usage #1
planet = "mars"
response = chain.invoke({"planet": planet})
print(f"Planet: {planet}")
print("Story Titles:")
print_response(response, PROVIDER)

print("=" * 60)

# Example usage #2
planet = "venus"
response = chain.invoke({"planet": planet})
print(f"Planet: {planet}")
print("Story Titles:")
print_response(response, PROVIDER)
