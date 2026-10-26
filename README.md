# Webby Chat

Webby Chat is a Chrome extension with a FastAPI backend for asking questions about YouTube videos. It retrieves a video's transcript, indexes transcript chunks in Pinecone, and streams answers grounded in the retrieved context.

## How it works

1. The extension sends the active tab URL to the backend.
2. The backend retrieves the YouTube transcript and indexes it.
3. Questions are rewritten for retrieval, matched to transcript chunks, and answered by a Groq-hosted language model.
4. Answers stream into the extension popup. Chat history is saved per video in Chrome storage.

**Scope:** The current backend supports YouTube videos only; ordinary webpages are not supported.

## Setup

Requirements: Python 3.10+, Chrome, and API credentials for Groq and Pinecone. The transcript module also requires an `API_KEY` environment variable.

1. Create a `.env` file in the repository root:

   ```env
   GROQ_API_KEY=your_groq_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   API_KEY=your_transcript_api_key
   ```

2. Install dependencies and start the backend:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   cd backend
   uvicorn main:app --reload
   ```

3. In Chrome, open `chrome://extensions`, enable Developer mode, and choose **Load unpacked**. Select the `front-end` folder.

The extension's API URL is configured in `front-end/popup.js`; update it and the host permission in `front-end/manifest.json` if using a different backend.

## Evaluation

The checked-in RAGAS results contain 10 questions about one YouTube video. Mean scores from that run:

| Metric | Score |
| --- | ---: |
| Answer correctness | 84.3% |
| Faithfulness | 91.8% |
| Answer relevancy | 96.5% |
| Context precision | 84.1% |
| Context recall | 89.3% |

These are evaluation metrics, **not a general accuracy guarantee**. The sample is small and covers only one video. The scores are in `backend/evaluation/ragas_results.csv`; test questions and references are in `backend/evaluation/test.json`. The evaluation script currently calls a disabled `/evaluate/answer` endpoint, so it cannot be rerun against the backend as-is.
