import os, requests
import pandas as pd
from urllib.parse import urlparse,parse_qs
API_KEY = os.environ['API_KEY'] 
url = 'https://transcriptapi.com/api/v2/youtube/transcript'
def load_or_create_df(path) -> pd.DataFrame:
   
    if os.path.exists(path):
        df = pd.read_csv(path)
        # ensure expected columns exist
        if not set(["url", "content"]).issubset(df.columns):
            df = pd.DataFrame(columns=["url", "content"])
    else:
        df = pd.DataFrame(columns=["url", "content"])
    return df

# Load once at module/script level
df = load_or_create_df(r"C:\Users\Alvi\Desktop\agentic\incomplete_agent\content.csv"  ) # Load the CSV file into a DataFrame


def get_youtube_id(url):
    if url in df['url']:
        return df[df['url']==url][content]
    parsed_url = urlparse(url)
    
    # Handle youtu.be short URLs
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
        
    # Handle standard youtube.com watch URLs
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        # Handle embed or v URLs (e.g., ://youtube.com)
        if parsed_url.path.startswith(('/embed/', '/v/')):
            return parsed_url.path.split('/')[2]
            
    return None
def get_youtube_transcript(url:str) -> str:
    video_id = get_youtube_id(url)

    try:
        params = {'video_url': video_id, 'format': 'json'}
        r = requests.get(url, params=params, headers={'Authorization': 'Bearer ' + API_KEY}, timeout=30)
        r.raise_for_status()
        text_only = "\n".join(item["text"] for item in transcript)
        return text_only
    except Exception as e:
    # FIX: Wrap the error message string inside an Exception class
        raise RuntimeError(f"An error occurred: {e}") from e
