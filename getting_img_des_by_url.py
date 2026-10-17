import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from image_description_llm import describe_img
import asyncio

def get_img_details(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    image_links = set()

    # 1. <img> tags
    for img in soup.find_all("img"):
        for attr in ("src", "data-src", "data-lazy-src", "data-original", "data-url"):
            src = img.get(attr)
            if src:
                image_links.add(urljoin(url, src))

        for attr in ("srcset", "data-srcset"):
            srcset = img.get(attr)
            if srcset:
                for item in srcset.split(","):
                    image_url = item.strip().split()[0]
                    if image_url:
                        image_links.add(urljoin(url, image_url))

    # 2. <source> tags
    for source in soup.find_all("source"):
        for attr in ("src", "srcset"):
            value = source.get(attr)
            if value:
                for item in value.split(","):
                    image_url = item.strip().split()[0]
                    if image_url:
                        image_links.add(urljoin(url, image_url))

    # 3. Open Graph / Twitter
    for meta in soup.find_all("meta"):
        prop = meta.get("property") or meta.get("name") or ""
        if prop in ("og:image", "og:image:url", "twitter:image", "twitter:image:src"):
            content = meta.get("content")
            if content:
                image_links.add(urljoin(url, content))


    clean_links = []
    for link in sorted(image_links):
        link = link.strip()
    
        if not link.startswith("http"):
            continue
        
    # Skip tiny / icon / logo / sprite images
        lower = link.lower()
        if any(x in lower for x in [
            ".svg", ".gif", ".ico",
            "sprite", "icon", "logo", "pixel", "badge",
            "_ss", "_ac_us", "transparent", "spacer"
        ]):
            continue
            
        # Prefer real product photos (Amazon style)
        if any(x in lower for x in [".jpg", ".jpeg", ".png", ".webp"]):
            # Prefer larger looking images
            if any(size in lower for size in ["_AC_UY", "_AC_SX", "_AC_SL", "_SX", "_SY", "500", "600", "800"]):
                clean_links.append(link)
            elif len(clean_links) < 3:  # still allow a few smaller ones
                clean_links.append(link)

    clean_links = clean_links[:15]
    
    return asyncio.run(describe_img(clean_links))
