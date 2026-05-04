"""
CLI interface for the Local Wikipedia RAG Assistant.
Fallback interface if Streamlit is not available.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieval import retrieve_context, classify_query
from src.generation import generate_answer, LLM_MODEL
from src.vector_store import get_store_stats


def print_header():
    print("=" * 60)
    print("  📚 Local Wikipedia RAG Assistant (CLI)")
    print("=" * 60)
    print(f"  Model: {LLM_MODEL}")

    stats = get_store_stats()
    print(f"  Indexed chunks: {stats.get('total_chunks', 0)}")
    print(f"  Indexed entities: {stats.get('total_entities', 0)}")

    if stats.get("total_chunks", 0) == 0:
        print("\n  ⚠️  Vector store is empty!")
        print("  Run: python scripts/ingest_data.py")

    print("=" * 60)
    print("  Type 'quit' to exit, 'stats' for info, 'clear' to reset")
    print("=" * 60)
    print()


def format_context(retrieval_result: dict) -> str:
    """Format retrieved context for display."""
    chunks = retrieval_result.get("chunks", [])
    if not chunks:
        return "  No relevant context found."

    lines = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadata"]
        distance = chunk.get("distance", "N/A")
        similarity = f"{1 - distance:.3f}" if isinstance(distance, (int, float)) else "N/A"

        lines.append(f"  [{i}] {meta['entity_name']} ({meta['entity_type']})")
        lines.append(f"      Similarity: {similarity} | Chunk {meta['chunk_index']+1}/{meta['total_chunks']}")
        # Show first 200 chars of context
        preview = chunk["text"][:200].replace("\n", " ")
        lines.append(f"      {preview}...")
        lines.append(f"      Source: {meta['source_url']}")
        lines.append("")

    return "\n".join(lines)


def main():
    print_header()

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue

        if query.lower() == "quit":
            print("Goodbye!")
            break

        if query.lower() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            print_header()
            continue

        if query.lower() == "stats":
            stats = get_store_stats()
            print(f"\n  Total chunks: {stats.get('total_chunks', 0)}")
            print(f"  Total entities: {stats.get('total_entities', 0)}")
            print(f"  Person chunks: {stats.get('person_chunks', 0)}")
            print(f"  Place chunks: {stats.get('place_chunks', 0)}")
            if stats.get("entities"):
                print(f"  Entities: {', '.join(stats['entities'])}")
            print()
            continue

        # Classify and retrieve
        query_type = classify_query(query)
        print(f"\n  [Query type: {query_type}]")
        print("  Searching...")

        retrieval_result = retrieve_context(query, n_results=5)
        chunks = retrieval_result.get("chunks", [])

        # Generate answer
        print("  Generating answer...\n")
        answer = generate_answer(query, chunks)

        print(f"Assistant: {answer}\n")

        # Show context option
        show = input("  Show retrieved context? (y/n): ").strip().lower()
        if show == "y":
            print(f"\n  Retrieved Context ({query_type}):")
            print(format_context(retrieval_result))

        print()


if __name__ == "__main__":
    main()
