"""
rag_core.py — shared retriever and prompt builder

Import this in query.py or your FastAPI server.
"""

import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

load_dotenv()

CHROMA_PATH = "chroma_db"
COLLECTION  = "servuo_knowledge"
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL  = "gpt-4o-mini"
TOP_K       = 5

_client = OpenAI()
_chroma = chromadb.PersistentClient(path=CHROMA_PATH)
_col    = _chroma.get_or_create_collection(COLLECTION)


SYSTEM_PROMPT = """\
You are an expert ServUO / Ultima Online shard assistant.
Answer questions using ONLY the provided context chunks.
If the answer isn't in the context, say so clearly.
Cite the source filename when referencing specific code or lore.
"""


def retrieve(question: str, top_k: int = TOP_K, source_type: str | None = None) -> list[dict]:
    """Embed the question and return the top-k matching chunks."""
    vec = _client.embeddings.create(model=EMBED_MODEL, input=[question]).data[0].embedding

    where = {"source_type": source_type} if source_type else None
    results = _col.query(
        query_embeddings=[vec],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({"text": doc, "source": meta["source"], "distance": dist})
    return chunks


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"--- Chunk {i} | Source: {c['source']} ---\n{c['text']}")
    return "\n\n".join(parts)


def ask(question: str, source_type: str | None = None) -> dict:
    """
    Full RAG round-trip.
    Returns {"answer": str, "sources": list[str], "chunks": list[dict]}
    """
    chunks  = retrieve(question, source_type=source_type)
    context = build_context(chunks)

    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]

    response = _client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.2,
    )

    answer  = response.choices[0].message.content
    sources = list({c["source"] for c in chunks})
    return {"answer": answer, "sources": sources, "chunks": chunks}
