"""
Embeddings module.
Generates embeddings locally using Ollama's nomic-embed-text model.
No external API calls - everything runs on localhost.

IMPORTANT: nomic-embed-text requires task-specific prefixes:
  - "search_document: " for document chunks (at indexing time)
  - "search_query: " for user queries (at query time)
This ensures documents and queries are mapped into the correct embedding space.
"""

import ollama

EMBEDDING_MODEL = "nomic-embed-text"


def get_embedding(text: str, prefix: str = "search_query") -> list[float]:
    """
    Generate an embedding vector for the given text.
    
    Args:
        text: The text to embed
        prefix: Task prefix for nomic-embed-text.
                Use "search_query" for queries, "search_document" for documents.
    """
    prefixed_text = f"{prefix}: {text}"
    try:
        response = ollama.embed(model=EMBEDDING_MODEL, input=prefixed_text)
        return response["embeddings"][0]
    except Exception as e:
        raise RuntimeError(
            f"Failed to generate embedding. Is Ollama running with '{EMBEDDING_MODEL}' pulled?\n"
            f"Run: ollama pull {EMBEDDING_MODEL}\n"
            f"Error: {e}"
        )


def get_embeddings_batch(texts: list[str], prefix: str = "search_document") -> list[list[float]]:
    """
    Generate embeddings for a batch of texts.
    
    Args:
        texts: List of texts to embed
        prefix: Task prefix. Default "search_document" for indexing.
    """
    prefixed_texts = [f"{prefix}: {t}" for t in texts]
    try:
        response = ollama.embed(model=EMBEDDING_MODEL, input=prefixed_texts)
        return response["embeddings"]
    except Exception as e:
        raise RuntimeError(
            f"Failed to generate batch embeddings. Is Ollama running with '{EMBEDDING_MODEL}' pulled?\n"
            f"Run: ollama pull {EMBEDDING_MODEL}\n"
            f"Error: {e}"
        )


def check_embedding_model() -> bool:
    """Check if the embedding model is available in Ollama."""
    try:
        models = ollama.list()
        model_names = [m.model for m in models.models]
        return any(EMBEDDING_MODEL in name for name in model_names)
    except Exception:
        return False
