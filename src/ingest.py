"""
Wikipedia ingestion module.
Fetches Wikipedia article text using requests + BeautifulSoup.
Saves raw article text to data/raw/ as JSON files.
"""

import json
import os
import time
import requests
from bs4 import BeautifulSoup

# Directories relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")


def ensure_dirs():
    """Create data directories if they don't exist."""
    os.makedirs(RAW_DIR, exist_ok=True)


def fetch_wikipedia_article(url: str) -> str:
    """
    Fetch a Wikipedia article and extract its main text content.
    Returns the cleaned article text.
    """
    headers = {
        "User-Agent": "LocalWikipediaRAG/1.0 (Educational project)"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unwanted elements
    for tag in soup.find_all(["script", "style", "sup", "table", "figure"]):
        tag.decompose()

    # Remove reference sections, navigation boxes, etc.
    for div in soup.find_all("div", class_=["reflist", "navbox", "sidebar",
                                             "mw-references-wrap", "toc",
                                             "catlinks", "mw-indicators"]):
        div.decompose()

    # Extract text from the main content area
    content_div = soup.find("div", {"id": "mw-content-text"})
    if not content_div:
        content_div = soup.find("div", {"id": "bodyContent"})

    if not content_div:
        raise ValueError(f"Could not find main content in {url}")

    # Get text from paragraphs and headings
    text_parts = []
    for element in content_div.find_all(["p", "h2", "h3", "h4", "li"]):
        text = element.get_text(strip=True)
        if text and len(text) > 10:  # Skip very short fragments
            # Add section markers for headings
            if element.name in ["h2", "h3", "h4"]:
                # Remove [edit] links that Wikipedia adds
                text = text.replace("[edit]", "").strip()
                text = f"\n\n== {text} ==\n"
            text_parts.append(text)

    article_text = "\n".join(text_parts)

    # Clean up excessive whitespace
    while "\n\n\n" in article_text:
        article_text = article_text.replace("\n\n\n", "\n\n")

    return article_text.strip()


def save_raw_article(entity_name: str, entity_type: str, url: str, text: str):
    """Save raw article data as a JSON file."""
    ensure_dirs()

    # Create a safe filename
    safe_name = entity_name.lower().replace(" ", "_").replace(".", "")
    filename = f"{safe_name}.json"
    filepath = os.path.join(RAW_DIR, filename)

    data = {
        "name": entity_name,
        "type": entity_type,
        "url": url,
        "text": text,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath


def load_raw_article(entity_name: str) -> dict:
    """Load a previously saved raw article."""
    safe_name = entity_name.lower().replace(" ", "_").replace(".", "")
    filename = f"{safe_name}.json"
    filepath = os.path.join(RAW_DIR, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No raw data found for '{entity_name}' at {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_raw_articles() -> list:
    """Load all saved raw articles from the data/raw/ directory."""
    ensure_dirs()
    articles = []

    for filename in sorted(os.listdir(RAW_DIR)):
        if filename.endswith(".json"):
            filepath = os.path.join(RAW_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                articles.append(json.load(f))

    return articles


def ingest_entity(entity: dict) -> dict:
    """
    Ingest a single entity: fetch from Wikipedia and save locally.
    Returns the saved article data, or None on failure.
    """
    name = entity["name"]
    url = entity["url"]
    entity_type = entity["type"]

    # Check if already ingested
    safe_name = name.lower().replace(" ", "_").replace(".", "")
    filepath = os.path.join(RAW_DIR, f"{safe_name}.json")
    if os.path.exists(filepath):
        print(f"  [SKIP] {name} - already ingested")
        return load_raw_article(name)

    print(f"  [FETCH] {name} from {url}")
    try:
        text = fetch_wikipedia_article(url)
        save_raw_article(name, entity_type, url, text)
        print(f"  [OK]   {name} - {len(text)} characters")
        # Be polite to Wikipedia servers
        time.sleep(1)
        return {"name": name, "type": entity_type, "url": url, "text": text}
    except requests.RequestException as e:
        print(f"  [FAIL] {name} - network error: {e}")
        return None
    except Exception as e:
        print(f"  [FAIL] {name} - error: {e}")
        return None
