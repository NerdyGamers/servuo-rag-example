# ServUO RAG Example

A **Retrieval-Augmented Generation (RAG)** pipeline designed for ServUO shards. Ask natural-language questions about your scripts, systems, quests, lore, and get grounded, cited answers backed by your actual codebase and documentation.

```
You: "What level does the Fire Elemental start spawning in Shame?"
RAG: "According to ShameSpawner.cs line 42, Fire Elementals begin spawning at level 3 (Shame dungeon)."
```

---

## Architecture

```
 docs/ scripts/ lore/          ← Your ServUO content (text, .cs files)
       │
  ingest.py                    ← Chunk → Embed → Store in ChromaDB
       │
   chroma_db/                  ← Local vector store (persisted)
       │
  query.py                     ← User question → Embed → Retrieve → LLM → Answer
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your OpenAI API key

```bash
export OPENAI_API_KEY="sk-..."
```

Or create a `.env` file:
```
OPENAI_API_KEY=sk-...
```

### 3. Add your content

Drop `.cs` scripts, `.txt` lore files, or `.md` documentation into the `data/` folder. The ingester handles all three.

### 4. Ingest (embed your data)

```bash
python ingest.py
```

This chunks each file, generates embeddings via `text-embedding-3-small`, and stores them in a local ChromaDB collection.

### 5. Query

```bash
python query.py
```

You'll get an interactive prompt. Type any question about your shard. Type `exit` to quit.

---

## Files

| File | Purpose |
|---|---|
| `ingest.py` | Reads `data/`, chunks, embeds, stores in ChromaDB |
| `query.py` | Interactive RAG query loop |
| `rag_core.py` | Shared retriever + prompt builder |
| `servuo_rag_hook.cs` | Optional C# bridge to call RAG from in-game |
| `data/` | Drop your `.cs`, `.txt`, `.md` files here |
| `chroma_db/` | Auto-created vector store (gitignored) |

---

## Customization

- **Swap the LLM**: Replace `gpt-4o-mini` in `query.py` with any OpenAI model, or swap `openai` for `ollama` / `llama-cpp-python` for fully local inference.
- **Change chunk size**: Edit `CHUNK_SIZE` and `CHUNK_OVERLAP` in `ingest.py`.
- **Filter by type**: Pass `where={"source_type": "script"}` to `collection.query()` in `rag_core.py` to restrict retrieval to C# scripts only.
- **In-game integration**: See `servuo_rag_hook.cs` — it opens a local HTTP connection to a thin FastAPI wrapper around `rag_core.py`.

---

## Example Data

See `data/example_lore.txt` and `data/ExampleSpawner.cs` for sample content that demonstrates how the pipeline ingests both narrative text and actual C# source.

---

## License

MIT — use freely in private or public shards.
