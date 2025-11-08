from langchain_core.output_parsers import StrOutputParser
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model
from model_switcher import get_model

from langchain.prompts import ChatPromptTemplate
from mlutils import print_model_info, print_response

llm = get_configured_model()
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

# prompt template 1: translate to english
first_prompt = ChatPromptTemplate.from_template("Translate the following review to english:" "\n\n{Review}")
# chain 1: input= Review and output= English_Review
chain_one = first_prompt | llm | StrOutputParser()


# prompt template 2: summarize the english review
second_prompt = ChatPromptTemplate.from_template("Can you summarize the following review in 1 sentence:" "\n\n{English_Review}")
# chain 2: input= English_Review and output= summary
chain_two = second_prompt | llm | StrOutputParser()


# prompt template 3: translate to english
third_prompt = ChatPromptTemplate.from_template("What language is the following review:\n\n{Review}")
# chain 3: input= Review and output= Language
chain_three = third_prompt | llm | StrOutputParser()

# prompt template 4: follow up response
fourth_prompt = ChatPromptTemplate.from_template(
    "Write a follow up response to the following " "summary in the specified language:" "\n\nSummary: {summary}\n\nLanguage: {language}"
)
# chain 4: input= summary and language and output= follow up response
chain_four = fourth_prompt | llm | StrOutputParser()


# Sequential processing function
def sequential_chain(inputs):
    # Invoke the first chain to get the English review
    english_review = chain_one.invoke({"Review": inputs["Review"]})
    # Invoke the second chain to summarize the English review
    summary = chain_two.invoke({"English_Review": english_review})
    # Invoke the third chain to detect the language of the original review
    language = chain_three.invoke({"Review": inputs["Review"]})
    # Invoke the fourth chain to generate a follow-up response
    followup_message = chain_four.invoke({"summary": summary, "language": language})
    return {
        "English_Review": english_review,
        "summary": summary,
        "followup_message": followup_message,
    }


# Test with first product
review = "Je trouve le goût médiocre. La mousse ne tient pas, c'est bizarre. J'achète les mêmes dans le commerce et le goût est bien meilleur... Vieux lot ou contrefaçon !?"
reponse = sequential_chain({"Review": review})
print(f"Original Review: {review}")
print(f"\nEnglish Review:")
print_response(reponse["English_Review"], PROVIDER)
print(f"\nSummary:")
print_response(reponse["summary"], PROVIDER)
print(f"\nFollow-up Response:")
print_response(reponse["followup_message"], PROVIDER)
print("=" * 60)


review = "Das Produkt ist von schlechter Qualität. Es riecht komisch und funktioniert nicht richtig."
reponse = sequential_chain({"Review": review})
print(f"Original Review: {review}")
print(f"\nEnglish Review:")
print_response(reponse["English_Review"], PROVIDER)
print(f"\nSummary:")
print_response(reponse["summary"], PROVIDER)
print(f"\nFollow-up Response:")
print_response(reponse["followup_message"], PROVIDER)
print("=" * 60)


# in Hindi
review = "यह उत्पाद बहुत अच्छा है। मुझे इसकी गुणवत्ता और प्रदर्शन पसंद आया।"
reponse = sequential_chain({"Review": review})
print(f"Original Review: {review}")
print(f"\nEnglish Review:")
print_response(reponse["English_Review"], PROVIDER)
print(f"\nSummary:")
print_response(reponse["summary"], PROVIDER)
print(f"\nFollow-up Response:")
print_response(reponse["followup_message"], PROVIDER)
print("=" * 60)
