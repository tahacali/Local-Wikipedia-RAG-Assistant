"""
Full ingestion pipeline script.
Fetches Wikipedia articles, chunks them, generates embeddings,
and stores everything in ChromaDB.

Usage:
    python scripts/ingest_data.py
"""

import sys
import os
import time

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.entities import get_all_entities
from src.ingest import ingest_entity
from src.chunking import chunk_article, save_processed_chunks
from src.vector_store import add_chunks_to_store, get_store_stats
from src.embeddings import check_embedding_model


def main():
    print("=" * 60)
    print("  Local Wikipedia RAG - Data Ingestion Pipeline")
    print("=" * 60)

    # Check prerequisites
    print("\n[1/5] Checking prerequisites...")
    if not check_embedding_model():
        print("  [FAIL] Embedding model not found!")
        print("  Run: ollama pull nomic-embed-text")
        print("  Make sure Ollama is running.")
        sys.exit(1)
    print("  [OK] Embedding model available")

    # Get all entities
    entities = get_all_entities()
    print(f"\n[2/5] Ingesting {len(entities)} Wikipedia articles...")
    print(f"  ({sum(1 for e in entities if e['type'] == 'person')} people, "
          f"{sum(1 for e in entities if e['type'] == 'place')} places)")

    # Fetch articles
    articles = []
    failed = []
    for entity in entities:
        result = ingest_entity(entity)
        if result:
            articles.append(result)
        else:
            failed.append(entity["name"])

    print(f"\n  [OK] Successfully ingested: {len(articles)}")
    if failed:
        print(f"  [FAIL] Failed: {len(failed)} - {', '.join(failed)}")

    # Chunk articles
    print(f"\n[3/5] Chunking {len(articles)} articles...")
    all_chunks = []
    for article in articles:
        chunks = chunk_article(article)
        save_processed_chunks(article["name"], chunks)
        all_chunks.extend(chunks)
        print(f"  {article['name']}: {len(chunks)} chunks")

    print(f"\n  Total chunks: {len(all_chunks)}")

    # Store in vector DB
    print(f"\n[4/5] Embedding and storing {len(all_chunks)} chunks in ChromaDB...")
    start_time = time.time()
    total = add_chunks_to_store(all_chunks)
    elapsed = time.time() - start_time
    print(f"  [OK] Stored {total} chunks in {elapsed:.1f}s")

    # Summary
    print(f"\n[5/5] Final statistics:")
    stats = get_store_stats()
    print(f"  Total chunks in store: {stats.get('total_chunks', 0)}")
    print(f"  Total entities: {stats.get('total_entities', 0)}")
    print(f"  Person chunks: {stats.get('person_chunks', 0)}")
    print(f"  Place chunks: {stats.get('place_chunks', 0)}")

    print("\n" + "=" * 60)
    print("  Ingestion complete!")
    print("  Run the app: streamlit run src/app.py")
    print("  Or use CLI: python src/cli.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
