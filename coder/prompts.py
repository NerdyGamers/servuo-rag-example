"""
coder/prompts.py — System and user prompt templates for the ServUO coding agent.
"""

CODING_SYSTEM_PROMPT = """\
You are an expert ServUO / Ultima Online C# script developer.
You write clean, complete, production-ready ServUO scripts.

Rules:
- Use only the ServUO API patterns shown in the context chunks below.
- Always include proper using directives, namespace, class, Constructable, Serialize/Deserialize.
- Never leave TODOs or placeholder comments — every method must be implemented.
- If the task requires a mechanic not shown in context, implement it using standard ServUO patterns.
- Output ONLY the raw C# code block. No prose. No markdown fences unless explicitly asked.
- Add a brief file-header comment (// filename.cs / purpose / author: ServUO RAG Coder).
"""

CODE_REVIEW_SYSTEM_PROMPT = """\
You are a senior ServUO C# code reviewer.
Review the provided script against ServUO best practices and the reference context.

Return a JSON object with:
  {
    "score": 0-10,
    "issues": ["..."],
    "suggestions": ["..."],
    "approved": true | false
  }
"""

REFACTOR_SYSTEM_PROMPT = """\
You are an expert ServUO C# refactoring assistant.
Refactor the provided script to match ServUO best practices.
Output ONLY the improved C# code. No prose.
"""


def build_coding_prompt(task: str, context: str) -> list[dict]:
    return [
        {"role": "system", "content": CODING_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Reference context from the ServUO codebase:\n"
                f"{context}\n\n"
                f"Task: {task}"
            ),
        },
    ]


def build_review_prompt(code: str, context: str) -> list[dict]:
    return [
        {"role": "system", "content": CODE_REVIEW_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Reference context:\n{context}\n\n"
                f"Script to review:\n{code}"
            ),
        },
    ]


def build_refactor_prompt(code: str, instructions: str, context: str) -> list[dict]:
    return [
        {"role": "system", "content": REFACTOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Reference context:\n{context}\n\n"
                f"Refactor instructions: {instructions}\n\n"
                f"Original script:\n{code}"
            ),
        },
    ]
