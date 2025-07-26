# Chat with Local LLM

A Streamlit-based chat interface for interacting with local large language models.

## Features
- ß
- Chat interface with message history
- Multiple chat management
- Bilingual support (English/Russian)
- Adjustable model parameters
- Error handling and rate limiting
- Chat export/import functionality

## Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
```

## Configuration

Edit the `.env` file and add your API key:

```
API_KEY=your_api_key_here
```

## Usage

Run the application:

```bash
streamlit run src/main.py
```

## Project Structure

```
chat-with-llm/
├── src/
│   ├── config/
│   │   └── app_config.py
│   ├── utils/
│   │   ├── api_client.py
│   │   ├── chat_manager.py
│   │   └── message_handler.py
│   └── main.py
├── tests/
│   └── test_chat.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Development

```bash
# Run tests
pytest

# Format code
black .

# Check code style
flake8
```

## License

MIT
