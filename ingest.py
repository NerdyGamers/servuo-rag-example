"""
ingest.py — ServUO RAG ingestion pipeline

Reads every file in data/, chunks it, embeds it via OpenAI,
and stores the vectors in a local ChromaDB collection.

Usage:
    python ingest.py
"""

import os
import pathlib
from dotenv import load_dotenv
import tiktoken
import chromadb
from openai import OpenAI

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR       = pathlib.Path("data")
CHROMA_PATH    = "chroma_db"
COLLECTION    = "servuo_knowledge"
EMBED_MODEL    = "text-embedding-3-small"
CHUNK_SIZE     = 512   # tokens per chunk
CHUNK_OVERLAP  = 64    # token overlap between consecutive chunks
SUPPORTED_EXT  = {".cs", ".txt", ".md"}

client = OpenAI()
enc    = tiktoken.get_encoding("cl100k_base")


# ── Chunking ──────────────────────────────────────────────────────────────────
def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping token-based chunks."""
    tokens = enc.encode(text)
    chunks = []
    start  = 0
    while start < len(tokens):
        end = min(start + size, len(tokens))
        chunks.append(enc.decode(tokens[start:end]))
        start += size - overlap
    return chunks


# ── Embedding ─────────────────────────────────────────────────────────────────
def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings using OpenAI. Returns a list of float vectors."""
    response = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in response.data]


# ── Main ──────────────────────────────────────────────────────────────────────
def ingest():
    chroma  = chromadb.PersistentClient(path=CHROMA_PATH)
    col     = chroma.get_or_create_collection(COLLECTION)

    existing_ids: set[str] = set(col.get()["ids"])
    added = 0

    for filepath in DATA_DIR.rglob("*"):
        if filepath.suffix.lower() not in SUPPORTED_EXT:
            continue

        source_type = "script" if filepath.suffix == ".cs" else "text"
        text        = filepath.read_text(encoding="utf-8", errors="ignore")
        chunks      = chunk_text(text)

        doc_ids   = []
        doc_texts = []
        doc_metas = []

        for i, chunk in enumerate(chunks):
            doc_id = f"{filepath.stem}__chunk{i}"
            if doc_id in existing_ids:
                continue  # skip already-ingested chunks
            doc_ids.append(doc_id)
            doc_texts.append(chunk)
            doc_metas.append({
                "source":      str(filepath),
                "source_type": source_type,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })

        if not doc_ids:
            print(f"  skip  {filepath.name}  (already ingested)")
            continue

        embeddings = embed_batch(doc_texts)
        col.add(ids=doc_ids, documents=doc_texts, embeddings=embeddings, metadatas=doc_metas)
        added += len(doc_ids)
        print(f"  +{len(doc_ids):>4} chunks  {filepath.name}")

    print(f"\nDone. {added} new chunks added to '{COLLECTION}'.")


if __name__ == "__main__":
    ingest()
