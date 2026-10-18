
import os
import re
import requests
import pandas as pd
from urllib.parse import urlparse, parse_qs

API_KEY = os.environ["API_KEY"]
API_URL = "https://transcriptapi.com/api/v2/youtube/transcript"
CSV_PATH = r"C:\Users\Alvi\Desktop\agentic\incomplete_agent\content.csv"


def load_or_create_df(path: str) -> pd.DataFrame:
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not {"url", "content"}.issubset(df.columns):
            return pd.DataFrame(columns=["url", "content"])
        return df[["url", "content"]]

    return pd.DataFrame(columns=["url", "content"])


df = load_or_create_df(CSV_PATH)


def get_youtube_id(video_url: str) -> str | None:
    parsed = urlparse(video_url)
    host = (parsed.hostname or "").lower()

    if host == "youtu.be":
        return parsed.path.strip("/").split("/")[0] or None

    if host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]

        if parsed.path.startswith(("/embed/", "/v/", "/shorts/")):
            parts = parsed.path.strip("/").split("/")
            return parts[1] if len(parts) > 1 else None

    return None


def get_youtube_transcript(video_url: str) -> str:
    global df

    video_id = get_youtube_id(video_url)
    if not video_id:
        raise ValueError(f"Invalid YouTube URL: {video_url}")

    # Check cache using the original URL
    cached = df.loc[df["url"] == video_url, "content"]
    if not cached.empty and pd.notna(cached.iloc[0]):
        return str(cached.iloc[0])

    try:
        response = requests.get(
            API_URL,
            params={"video_url": video_url, "format": "json"},
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        transcript = data.get("transcript", [])

        if not isinstance(transcript, list):
            raise ValueError("API returned an unexpected transcript format.")

        text_only = "\n".join(
            re.sub(r"\s+", " ", item.get("text", "")).strip()
            for item in transcript
            if isinstance(item, dict)
            and isinstance(item.get("text"), str)
            and item["text"].strip()
        )

        if not text_only:
            raise ValueError("The API returned an empty transcript.")

        # Update the in-memory cache
        df = pd.concat(
            [
                df,
                pd.DataFrame([{"url": video_url, "content": text_only}]),
            ],
            ignore_index=True,
        )

        # Persist the cache to disk
        df.to_csv(CSV_PATH, index=False)

        return text_only

    except (requests.RequestException, ValueError, KeyError) as e:
        raise RuntimeError(f"Failed to retrieve transcript: {e}") from e
