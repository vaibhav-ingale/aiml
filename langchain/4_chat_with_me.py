from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model

from mlutils import print_model_info, print_response

model = get_configured_model()
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

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
print("Chat with AI Assistant Maya (type 'exit' or 'quit' to end)")
print("-" * 50)

while True:
    user_input = input("User: ").strip()

    # Validate empty input
    if not user_input:
        print("No input provided. Please type your message or 'exit' to quit.")
        continue

    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat...")
        break

    human_message = HumanMessage(content=user_input)
    chat_history.append(human_message)

    try:
        ai_message = model.invoke(chat_history)
        chat_history.append(ai_message)
        print("AI: ", end="")
        print_response(ai_message, PROVIDER)
    except Exception as e:
        print(f"Error: {e}")

print("History:")
for msg in chat_history:
    print(f"{msg.type}: {msg.content}")
