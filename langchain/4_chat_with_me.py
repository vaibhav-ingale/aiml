from datetime import datetime

from langchain_ollama.llms import OllamaLLM
from model_switcher import get_model

from langchain.schema import AIMessage, HumanMessage, SystemMessage

model = get_model("ollama", "gpt-oss:20b", temperature=0.1, max_tokens=100)


chat_history = []

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
system_message = SystemMessage(
    content=f"Today's date and time is: {now}. \
Always use this value if the user asks for the current date or time. \
You are a helpful AI assistant and youe name is Maya. \
Answer the user's questions to the best of your ability. \
Always refer to the conversation history for context. \
Strictly provide answers to the user's questions without any additional information."
)

chat_history.append(system_message)
while True:
    user_input = input("User: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat...")
        break

    human_message = HumanMessage(content=user_input)
    chat_history.append(human_message)

    try:
        response = model.invoke(chat_history)
        ai_message = AIMessage(content=response)
        chat_history.append(ai_message)
        print(f"AI: {response}")
    except Exception as e:
        print(f"Error: {e}")

print("History:")
for msg in chat_history:
    print(f"{msg.type}: {msg.content}")
