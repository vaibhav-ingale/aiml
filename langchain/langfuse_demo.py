import os

from langfuse.openai import openai

# Get keys for your project from the project settings page
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-452f6d9f-af89-458c-8be0-22f98b0ac8cc"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-0b1c0e84-c729-430f-876b-990704faa290"
os.environ["LANGFUSE_BASE_URL"] = "http://localhost:3000"


# Drop-in replacement to get full logging by changing only the import
from langfuse.openai import OpenAI

# Configure the OpenAI client to use http://localhost:11434/v1 as base url 
client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)
 
# Define multiple example prompts to test
prompts = [
    "Who was the first person to step on the moon?",
    "Explain how LLMs work in a detailed way with technical examples",
    "What is the capital of France?",
    "How does a transformer architecture work in deep learning?",
    "What are the benefits of using retrieval-augmented generation (RAG)?",
]

# Loop through each prompt and get responses
for i, prompt in enumerate(prompts, 1):
    print(f"\n{'='*80}")
    print(f"Prompt {i}: {prompt}")
    print(f"{'='*80}")

    response = client.chat.completions.create(
        model="llama3.2:latest",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
    )

    print(f"\nResponse:\n{response.choices[0].message.content}")
    print(f"\n{'='*80}\n")