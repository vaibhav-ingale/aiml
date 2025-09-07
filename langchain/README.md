# LangChain Examples

This folder contains examples and tutorials for working with LangChain.

## File Index

| File                                           | Description                                                                                                                                                        |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [model_switcher.py](./model_switcher.py) | Universal model switcher supporting multiple LLM providers with one-line switching |
| [1_chat_with_model.py](./1_chat_with_model.py) | Interactive chat application with universal model switching (Ollama, OpenAI, Anthropic, etc.) |
| [2_quick_model_example.py](./2_quick_model_example.py) | Examples demonstrating quick model switching between different providers |
| [3_conversation.py](./3_conversation.py) | Comprehensive examples of SystemMessage, HumanMessage, and AIMessage usage patterns |
| [.env.example](./.env.example) | Template for environment variables and API keys |

### Quick Usage

```python
from model_switcher import get_model

# Switch between any provider with one line
model = get_model('ollama', 'llama2')
model = get_model('openai', 'gpt-3.5-turbo')
model = get_model('anthropic', 'claude-3-sonnet-20240229')
model = get_model('mistral', 'mistral-large-latest')
```

### Installation for specific providers

```bash
# For OpenAI
pip install langchain-openai

# For Anthropic  
pip install langchain-anthropic

# For Mistral
pip install langchain-mistralai

# For HuggingFace
pip install langchain-huggingface

# For Google
pip install langchain-google-genai

# For Ollama (local)
pip install langchain-ollama
```

## Usage

1. Make sure Ollama is running with some models installed
2. Run the example:
   ```bash
   python <file>.py
   ```
3. Select a model from the available options
4. The script will ask "What is Bias and Variance?" and display the response
