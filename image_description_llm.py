
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import base64
import requests
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    max_retries=3,
    timeout=20,
)
def get_b64_image_content(url: str, mime_type: str = "image/jpeg") -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url,headers=headers)
    response.raise_for_status()
    b64_string = base64.b64encode(response.content).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{b64_string}"}
    }
content_parts = [
    {"type": "text", "text": "Describe each of these images in detail and list their key features."}
]

async def describe_img(image_urls:list[str]) -> str:
    try:
        for url in image_urls:
                    # Adjust mime_type if your images are png, webp, etc.
            content_parts.append(get_b64_image_content(url, mime_type="image/jpeg"))
        message = HumanMessage(content=content_parts)
        response = llm.invoke([message])

        return (response.text)
    except:
        return 'Couldnt read images of this page'