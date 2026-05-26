"""
api_server.py — thin FastAPI wrapper around rag_core

Exposes a single POST /ask endpoint so ServUO (or any HTTP client)
can query the RAG pipeline over a local socket.

Usage:
    uvicorn api_server:app --host 127.0.0.1 --port 8765
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_core import ask

app = FastAPI(title="ServUO RAG API", version="1.0.0")


class QueryRequest(BaseModel):
    question: str
    source_type: str | None = None  # "script" | "text" | None


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]


@app.post("/ask", response_model=QueryResponse)
def ask_endpoint(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")
    result = ask(req.question, source_type=req.source_type)
    return QueryResponse(answer=result["answer"], sources=result["sources"])


@app.get("/health")
def health():
    return {"status": "ok"}
