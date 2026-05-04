"""
Reset script — clears the vector store and optionally the cached data.

Usage:
    python scripts/reset_store.py            # Reset vector store only
    python scripts/reset_store.py --all      # Reset vector store + cached data
"""

import sys
import os
import shutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vector_store import reset_store

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    reset_all = "--all" in sys.argv

    print("=" * 50)
    print("  Local Wikipedia RAG - Reset")
    print("=" * 50)

    # Reset vector store
    print("\n[1] Resetting vector store...")
    reset_store()
    print("  [OK] Vector store reset")

    if reset_all:
        # Remove raw data
        raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")
        if os.path.exists(raw_dir):
            shutil.rmtree(raw_dir)
            os.makedirs(raw_dir, exist_ok=True)
            print("\n[2] Cleared raw data")

        # Remove processed data
        processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")
        if os.path.exists(processed_dir):
            shutil.rmtree(processed_dir)
            os.makedirs(processed_dir, exist_ok=True)
            print("[3] Cleared processed data")

        print("\n  [OK] Full reset complete")
    else:
        print("\n  Use --all to also clear cached Wikipedia data")

    print("\n  To re-ingest: python scripts/ingest_data.py")


if __name__ == "__main__":
    main()
