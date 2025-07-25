# LangChain Examples

This folder contains examples and tutorials for working with LangChain.

## File Index

| File                                           | Description                                                                                                                                                        |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [1_chat_with_model.py](./1_chat_with_model.py) | Interactive chat application using Ollama models with LangChain, allows model selection and prompts with step-by-step reasoning for high school level explanations |

## Prerequisites

- Python 3.8+
- Ollama installed and running
- Required packages:
  ```bash
  pip install langchain-core langchain-ollama ollama
  ```

## Usage

1. Make sure Ollama is running with some models installed
2. Run the example:
   ```bash
   python <file>.py
   ```
3. Select a model from the available options
4. The script will ask "What is Bias and Variance?" and display the response
