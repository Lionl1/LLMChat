# Chat with Local LLM

FastAPI backend with a lightweight HTML/JS chat UI for local large language models.

## Features
- Chat interface with message history and copyable replies
- Multiple chat management with local storage
- Adjustable model parameters (temperature, max tokens, top_p)
- File parsing via extract-text (DOCX/PPTX/XLSX/RTF/PDF/etc.)
- FastAPI backend with a lightweight HTML/JS UI and explicit error feedback

## Installation

```bash
# Pull submodules
git submodule update --init --recursive

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

Edit the `.env` file and set the API connection details:

```
API_KEY=your_api_key_here
API_URL=http://localhost:8000/v1/chat/completions
MODEL_NAME=local-model
API_TIMEOUT=15
EXTRACT_TEXT_API_URL=http://localhost:7555
EXTRACT_TEXT_TIMEOUT=120
MAX_IMPORTED_CHARS=20000
```

> **Важно:** файл `extract-text` должен быть запущен по адресу `EXTRACT_TEXT_API_URL` (можно через `docker compose` или отдельно из `third_party/extract-text`) — иначе экспорт и импорт файлов будут давать ошибку.

## Usage

Run the application:

```bash
python run.py
```

Open: `http://127.0.0.1:8000`

## Docker

Build and run both the chat app and extract-text service:

```bash
docker compose up --build
```

Chat UI: `http://127.0.0.1:8000`  
Extract-text: `http://127.0.0.1:7555`

## Project Structure

```
chat-with-llm/
├── src/
│   ├── config/
│   │   └── app_config.py
│   ├── utils/
│   │   ├── extract_text_client.py
│   │   └── llm_client.py
│   └── server.py
├── web/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── docs/
│   └── architecture.md
├── docker/
│   └── extract-text.Dockerfile
├── third_party/
│   └── extract-text/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitmodules
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

## License

MIT
