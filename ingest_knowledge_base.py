"""
ingest_knowledge_base.py
One-time (or on-demand) script to build the persistent ChromaDB index from
the documents in /data. Run this whenever you add/change knowledge base
files. The Streamlit app does NOT re-embed on every turn — it only queries
the index built here (see config.py note on performance: "Keep Embeddings
Local").

Usage:
    python ingest_knowledge_base.py            # incremental add
    python ingest_knowledge_base.py --reset     # wipe and rebuild from scratch
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config
from src.rag_pipeline import RAGPipeline


def main():
    parser = argparse.ArgumentParser(description="Ingest knowledge base documents into ChromaDB.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing collection before ingesting (full rebuild).",
    )
    args = parser.parse_args()

    if not config.GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY is not set. Add it to your .env file before running this script.")
        sys.exit(1)

    pipeline = RAGPipeline()

    if args.reset:
        print("Resetting existing collection...")
        pipeline.reset_collection()

    existing_count = pipeline.count()
    print(f"Collection currently has {existing_count} chunks.")
    print(f"Ingesting documents from: {config.DATA_DIR}")

    num_files = pipeline.ingest_directory()

    final_count = pipeline.count()
    print(f"Done. Processed {num_files} files.")
    print(f"Collection now has {final_count} chunks (added {final_count - existing_count}).")


if __name__ == "__main__":
    main()
