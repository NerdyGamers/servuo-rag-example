"""
coder/code_api.py — FastAPI endpoints for the ServUO AI coding agent.

Run standalone:
    uvicorn coder.code_api:app --host 127.0.0.1 --port 8766

Endpoints:
    POST /code/generate
    POST /code/review
    POST /code/refactor
    GET  /code/health
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from coder.code_agent import generate, review, refactor

app = FastAPI(title="ServUO AI Coding Agent", version="1.0.0")


class ValidationResponse(BaseModel):
    ok: bool
    warnings: list[str]


class GenerateRequest(BaseModel):
    task: str

class GenerateResponse(BaseModel):
    code: str
    sources: list[str]
    validation: ValidationResponse


class ReviewRequest(BaseModel):
    code: str

class ReviewResponse(BaseModel):
    score: int
    issues: list[str]
    suggestions: list[str]
    approved: bool
    sources: list[str]
    validation: ValidationResponse


class RefactorRequest(BaseModel):
    code: str
    instructions: str

class RefactorResponse(BaseModel):
    code: str
    sources: list[str]
    validation: ValidationResponse


@app.get("/code/health")
def health():
    return {"status": "ok", "service": "ServUO AI Coding Agent"}


@app.post("/code/generate", response_model=GenerateResponse)
def generate_endpoint(req: GenerateRequest):
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="task must not be empty")
    return GenerateResponse(**generate(req.task))


@app.post("/code/review", response_model=ReviewResponse)
def review_endpoint(req: ReviewRequest):
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="code must not be empty")
    result = review(req.code)
    return ReviewResponse(
        score=int(result.get("score", 0)),
        issues=list(result.get("issues", [])),
        suggestions=list(result.get("suggestions", [])),
        approved=bool(result.get("approved", False)),
        sources=list(result.get("sources", [])),
        validation=result.get("validation", {"ok": False, "warnings": ["Missing validation result"]}),
    )


@app.post("/code/refactor", response_model=RefactorResponse)
def refactor_endpoint(req: RefactorRequest):
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="code must not be empty")
    return RefactorResponse(**refactor(req.code, req.instructions))
