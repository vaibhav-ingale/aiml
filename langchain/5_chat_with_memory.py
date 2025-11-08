from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model

from mlutils import print_model_info, print_response

model = get_configured_model()
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content="You are a helpful assistant. Answer all questions to the best of your ability."),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = prompt | model

# Initialize messages list for MessagesPlaceholder
messages = []

print("Chat with Assistant (type 'exit' or 'quit' to end)")
print("-" * 45)

# Main chat loop
while True:
    user_input = input("User: ").strip()

    # Validate empty input
    if not user_input:
        print("No input provided. Please type your message or 'exit' to quit.")
        continue

    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat...")
        break

    # Add user message to messages list
    messages.append(HumanMessage(content=user_input))

    try:
        # Invoke chain with current messages using MessagesPlaceholder
        ai_response = chain.invoke({"messages": messages})

        # llama.cpp responses may come back as raw strings; normalize to AIMessage
        assistant_message = ai_response if isinstance(ai_response, AIMessage) else AIMessage(content=str(ai_response))

        messages.append(assistant_message)

        # Display AI response
        print("AI: ", end="")
        print_response(assistant_message, PROVIDER)

    except Exception as e:
        print(f"Error: {e}")

# Print conversation history at the end
print("\nConversation History:")
print("=" * 50)
for i, msg in enumerate(messages, 1):
    role = "User" if isinstance(msg, HumanMessage) else "AI"
    print(f"{i}. {role}: {msg.content}")

print(f"\nTotal messages: {len(messages)}")
print(f"Conversation turns: {len(messages) // 2}")
