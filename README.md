# ServUO RAG + AI Coding System

A Retrieval-Augmented Generation (RAG) pipeline plus an AI coding agent for ServUO shards.
The RAG grounds every code-generation and review call in your actual ServUO codebase — no hallucinated APIs, no phantom classes.

```
You: "Create a blessed artifact sword with a fire strike special move"
AI:  → FireSword.cs  (grounded in your existing weapon scripts)

You: "Review Scripts/MyItem.cs"
AI:  Score 7/10 · 2 issues · 3 suggestions  (referenced against real ServUO patterns)
```

---

## Architecture

```
data/  (.cs / .txt / .md)         ← your ServUO scripts, lore, docs
  │
ingest.py                         ← chunk → embed → ChromaDB
  │
chroma_db/                        ← local vector store (gitignored)
  │
rag_core.py                       ← retriever + context builder
  │
┌──────────────────────────────┐
│  coder/code_agent.py         │  ← generate | review | refactor
│  coder/validator.py          │  ← post-gen heuristic checks
│  coder/prompts.py            │  ← prompt templates
└──────────────────────────────┘
  │
coder/code_api.py  (port 8766)    ← FastAPI coding endpoints
api_server.py      (port 8765)    ← FastAPI RAG Q&A endpoint
  │
servuo_rag_hook.cs                ← [RAGAsk  in-game Q&A
coder/servuo_coding_hook.cs       ← [AIGenerate / [AIRefactor  in-game
```

---

## Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
```

Drop `.cs`, `.txt`, `.md` files into `data/`, then:

```bash
python ingest.py
```

---

## Coding Agent — CLI

```bash
# Generate a new script
python -m coder.code_agent generate "Create a treasure chest that spawns loot based on player karma" --out Scripts/KarmaChest.cs

# Review an existing script
python -m coder.code_agent review Scripts/MyItem.cs

# Refactor a script
python -m coder.code_agent refactor Scripts/MyItem.cs "Add a daily cooldown using Timer"
```

---

## Coding Agent — API

```bash
uvicorn coder.code_api:app --host 127.0.0.1 --port 8766
```

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/code/generate` | `{"task": "..."}` | `{code, sources, validation}` |
| `POST` | `/code/review` | `{"code": "..."}` | `{score, issues, suggestions, approved, sources, validation}` |
| `POST` | `/code/refactor` | `{"code": "...", "instructions": "..."}` | `{code, sources, validation}` |
| `GET`  | `/code/health` | — | `{status}` |

---

## RAG Q&A API

```bash
uvicorn api_server:app --host 127.0.0.1 --port 8765
# POST /ask  {"question": "..."}
```

---

## In-Game Commands

| Command | Description |
|---|---|
| `[RAGAsk <question>` | Natural-language Q&A about your shard |
| `[AIGenerate <task>` | Generate a new C# script → saved to `AI_Generated/` |
| `[AIRefactor <file.cs> \| <instructions>` | Refactor a script, saved as `_refactored.cs` |

Drop `servuo_rag_hook.cs` and `coder/servuo_coding_hook.cs` into `Scripts/Customs/` and restart.

---

## Validator

Runs automatically on every generate/refactor. Checks for:
- Missing `Serialize` / `Deserialize`
- Missing namespace or class declaration
- `TODO` placeholders
- Blocking `.Result` on async Tasks
- `Console.Write` usage
- Unbalanced braces

```python
from coder.validator import validate
result = validate(open("Scripts/MyItem.cs").read())
print(result.warnings)  # [] = clean
```

---

## Customization

- **Local LLM**: Replace `gpt-4o` in `coder/code_agent.py` with an Ollama-compatible endpoint.
- **Custom checks**: Add patterns to `REQUIRED_PATTERNS` / `FORBIDDEN_PATTERNS` in `coder/validator.py`.
- **Auto-ingest**: Point a `watchdog` file watcher at `data/` to re-run `ingest.py` on save.
- **Filter by type**: Pass `source_type="script"` or `source_type="text"` to `retrieve()` in `rag_core.py`.

---

## License

MIT — use freely in private or public shards.
