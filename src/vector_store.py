"""
Vector store module.
Uses ChromaDB to store and query document embeddings.

Design choice: ONE vector store with metadata filtering.
- Single collection named "wikipedia_rag"
- Each document has metadata: entity_name, entity_type, source_url, chunk_index
- Query filtering by entity_type (person/place) enables targeted retrieval
- This is simpler and more maintainable than two separate stores,
  and allows cross-type queries naturally.
"""

import os
import chromadb
from src.embeddings import get_embedding, get_embeddings_batch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")
COLLECTION_NAME = "wikipedia_rag"


def get_chroma_client() -> chromadb.PersistentClient:
    """Get or create a persistent ChromaDB client."""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def get_collection(client: chromadb.PersistentClient = None):
    """Get or create the Wikipedia RAG collection."""
    if client is None:
        client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Wikipedia RAG embeddings for people and places",
            "hnsw:space": "cosine",  # Use cosine distance for normalized embeddings
        }
    )


def add_chunks_to_store(chunks: list[dict], batch_size: int = 50):
    """
    Add processed chunks to the ChromaDB vector store.
    Generates embeddings and stores them with metadata.
    """
    collection = get_collection()

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]

        ids = []
        documents = []
        metadatas = []

        for chunk in batch:
            # Create a unique ID for each chunk
            safe_name = chunk["entity_name"].lower().replace(" ", "_").replace(".", "")
            chunk_id = f"{safe_name}_chunk_{chunk['chunk_index']}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append({
                "entity_name": chunk["entity_name"],
                "entity_type": chunk["entity_type"],
                "source_url": chunk["source_url"],
                "chunk_index": chunk["chunk_index"],
                "total_chunks": chunk["total_chunks"],
            })

        # Generate embeddings for the batch
        print(f"  Embedding batch {i // batch_size + 1} ({len(batch)} chunks)...")
        embeddings = get_embeddings_batch(documents)

        # Upsert to handle re-runs gracefully
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    return collection.count()


def get_store_stats() -> dict:
    """Get statistics about the vector store."""
    try:
        collection = get_collection()
        count = collection.count()

        # Get unique entity names and types
        if count > 0:
            all_meta = collection.get(include=["metadatas"])
            entity_names = set()
            entity_types = {"person": 0, "place": 0}
            for meta in all_meta["metadatas"]:
                entity_names.add(meta["entity_name"])
                entity_types[meta["entity_type"]] = entity_types.get(meta["entity_type"], 0) + 1

            return {
                "total_chunks": count,
                "total_entities": len(entity_names),
                "person_chunks": entity_types.get("person", 0),
                "place_chunks": entity_types.get("place", 0),
                "entities": sorted(entity_names),
            }
        return {"total_chunks": 0, "total_entities": 0}
    except Exception:
        return {"total_chunks": 0, "total_entities": 0, "error": "Vector store not initialized"}


def reset_store():
    """Delete and recreate the vector store collection."""
    client = get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted collection '{COLLECTION_NAME}'")
    except Exception:
        print(f"Collection '{COLLECTION_NAME}' did not exist")
    get_collection(client)
    print(f"Created fresh collection '{COLLECTION_NAME}'")
