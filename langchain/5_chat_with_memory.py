# Reference : https://python.langchain.com/api_reference/langchain/memory.html
# instead of using chat_history, we will use MessagesPlaceholder
# to manage chat history within the prompt template itself.

from datetime import datetime

from model_switcher import get_model

from langchain.schema import AIMessage, HumanMessage, SystemMessage

model = get_model("ollama", "gpt-oss:20b", temperature=0.1, max_tokens=100)


from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content="You are a helpful assistant. Answer all questions to the best of your ability."
        ),
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
    user_input = input("User: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat...")
        break

    # Add user message to messages list
    messages.append(HumanMessage(content=user_input))

    try:
        # Invoke chain with current messages using MessagesPlaceholder
        ai_response = chain.invoke({"messages": messages})

        # Add AI response to messages list
        messages.append(AIMessage(content=ai_response))

        # Display AI response
        print(f"AI: {ai_response}")

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
