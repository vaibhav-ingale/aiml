from model_switcher import get_model

from langchain.prompts import ChatPromptTemplate

llm = get_model("ollama", "gpt-oss:20b", temperature=0.1, max_tokens=500)

prompt_for_story_title = ChatPromptTemplate.from_template(
    "suggest 10 story titles based on the following idea: we found aliens on {planet} while we are looking for water there."
)

chain = prompt_for_story_title | llm

# Example usage #1
planet = "mars"
response = chain.invoke({"planet": planet})
print(response)

print("=" * 60)

# Example usage #2
planet = "venus"
response = chain.invoke({"planet": planet})
print(response)
