# Intelligent Document Processing

Streamlit-based Intelligent Document Processing app for document summary, structured extraction, and document Q&A over uploaded files.

## Features

- Executive summaries powered by Gemini
- Structured JSON extraction for business documents
- Retrieval-based Q&A over processed content
- Support for `pdf`, `png`, `jpg`, `jpeg`, `docx`, `ppt`, and `pptx`

## Project Structure

```text
Intern_Project/
|-- app/
|   |-- config/      # environment-driven settings
|   |-- core/        # document loading, chunking, embeddings
|   |-- services/    # summary, JSON extraction, RAG services
|   |-- ui/          # Streamlit screens and components
|   `-- utils/       # cache, file, and text helpers
|-- .streamlit/
|-- Dockerfile
|-- Procfile
|-- main.py          # root Streamlit entrypoint
|-- requirements.txt
`-- README.md
```

## Local Setup

1. Create a virtual environment and activate it.
2. Copy `.env.example` to `.env`.
3. Set `GEMINI_API_KEY`.
4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Start the app:

```bash
streamlit run main.py
```

## Environment Variables

Common runtime settings live in `.env`:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `EMBEDDING_MODEL`


## Deployment

### Docker

```bash
docker build -t idp-app .
docker run --env-file .env -p 8501:8501 idp-app
```

### Procfile Platforms

Use the included `Procfile` on platforms that expect a `web` process definition.

## Notes

- Runtime caches are created under `.cache/` and can be deleted safely.
- `TESSERACT_CMD` is optional, but recommended for image OCR on local machines.
- If `GEMINI_API_KEY` is missing, the app still loads with limited AI functionality.
