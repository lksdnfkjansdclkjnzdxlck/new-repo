# Webby Chat

Webby Chat is a Chrome extension and FastAPI backend for asking questions about the current webpage or YouTube video. The app extracts readable text, splits it into chunks, stores embeddings in ChromaDB, and answers questions using only the content that was indexed for that URL.

## What it does

- Analyzes the active browser tab when the extension is opened.
- Supports normal web pages and YouTube URLs.
- Extracts readable page text with `trafilatura` and transcripts with `youtube-transcript-api`.
- Builds a local vector index in ChromaDB for retrieval-augmented generation.
- Uses a Groq-backed LLM to answer grounded questions from the page/video context.
- Keeps a short chat history per page so follow-up questions feel conversational.
- Shows progress updates while the backend is processing a page.

## Project structure

```text
backend/
  main.py                     FastAPI app and API routes
  function.py                 Retrieval, chunking, indexing, progress updates
  llm.py                     Groq chat model, prompt template, chat history
  get_content.py             Web page extraction helpers
  youtube_transcript.py      YouTube transcript retrieval helpers
  getting_img_des_by_url.py  Image metadata extraction
  image_description_llm.py   Optional image description generation via Gemini
  context_compression.py     Context compression utility for retrieval
  database/                  Local ChromaDB storage
  evaluation/
    evals.py                 Optional evaluation script
    test.json                Sample evaluation dataset
front-end/
  manifest.json              Chrome extension manifest
  popup.html                 Extension popup layout
  popup.css                  Popup styles
  popup.js                   Front-end API logic and UI behavior
README.md
requirements.txt
content.csv
```

## Requirements

- Python 3.10+
- Google Chrome or another Chromium-based browser
- Groq API key
- Google API key for image description support (optional but used by the image-description pipeline)

## Setup

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Add environment variables in a `.env` file at the project root or inside `backend/`:

```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key
```

4. Start the backend:

```powershell
cd backend
uvicorn main:app --reload
```



## Load the extension

1. Open `chrome://extensions`.
2. Turn on Developer mode.
3. Click Load unpacked.
4. Choose the `front-end` folder in this repository.
5. Keep the backend running and then open a normal webpage or a YouTube page and click the extension icon.

The extension will trigger analysis for the active page automatically. Once the indexing finishes, you can ask natural-language questions in the popup.

## API

### POST /analyze

Starts analysis for a page or video URL.

Request body:

```json
{
  "url": "https://example.com"
}
```

Response:

```json
{
  "task_id": "<uuid>"
}
```

### GET /progress/{task_id}

Fetches the current status of the background task.

Example response:

```json
{
  "stage": "complete",
  "progress": 100,
  "message": "Analysis complete!",
  "error": false
}
```

### POST /ask

Asks a question based on the indexed content for a given URL.

Request body:

```json
{
  "url": "https://example.com",
  "question": "What is this page about?"
}
```

Response:

```json
{
  "question": "What is this page about?",
  "answer": "...",
  "context": "..."
}
```

## Local data

The vector store is created in `backend/database`. If you want to reset stored embeddings and page chunks, delete that folder and restart the backend.

## Notes

- The extension is configured to call `https://extension-s-backend-7e95da56.fastapicloud.dev7` by default. If your API is running elsewhere, update `API_BASE` in `front-end/popup.js`.
- CORS is intentionally permissive for local development. Restrict it before exposing the app beyond your machine.
- `backend/evaluation/evals.py` is optional and can be used to benchmark the retrieval pipeline with sample questions.
- The repository includes a local CSV file (`content.csv`) and uses it as part of the indexing workflow.
