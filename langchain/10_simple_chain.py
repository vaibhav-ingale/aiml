from langchain_core.prompts import ChatPromptTemplate
from mlutils import print_model_info, print_response
from model_switcher import get_model

# Get model from configuration (edit model_switcher.py to change settings)
llm = get_model()
print_model_info(llm)
prompt_for_story_title = ChatPromptTemplate.from_template(
    "suggest 10 story titles based on the following idea: we found aliens on {planet} while we are looking for water there."
)

chain = prompt_for_story_title | llm

# Example usage #1
planet = "mars"
response = chain.invoke({"planet": planet})
print(f"Planet: {planet}")
print("Story Titles:")
print_response(response)

print("=" * 60)

# Example usage #2
planet = "venus"
response = chain.invoke({"planet": planet})
print(f"Planet: {planet}")
print("Story Titles:")
print_response(response)
