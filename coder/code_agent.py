"""
coder/code_agent.py — RAG-grounded ServUO AI coding agent.

Three operations:
  generate(task)               -> new C# script from natural-language task
  review(code)                 -> score + critique against your codebase
  refactor(code, instructions) -> rewrite grounded in retrieved patterns

CLI:
    python -m coder.code_agent generate "Blessed artifact sword with fire strike" --out Scripts/FireSword.cs
    python -m coder.code_agent review Scripts/MyItem.cs
    python -m coder.code_agent refactor Scripts/MyItem.cs "Add daily cooldown via Timer"
"""

import argparse
import json
import pathlib

from openai import OpenAI
from dotenv import load_dotenv

from rag_core import retrieve, build_context
from coder.prompts import build_coding_prompt, build_review_prompt, build_refactor_prompt
from coder.validator import validate

load_dotenv()

CHAT_MODEL   = "gpt-4o"   # swap to gpt-4o-mini to cut cost
TOP_K_CODE   = 6
TOP_K_REVIEW = 4

_client = OpenAI()


def _clean_code_block(text: str) -> str:
    """Strip markdown fences the LLM sometimes wraps around code."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def generate(task: str) -> dict:
    """Generate a new ServUO C# script grounded in retrieved codebase context."""
    chunks   = retrieve(task, top_k=TOP_K_CODE, source_type="script")
    context  = build_context(chunks)
    messages = build_coding_prompt(task, context)
    response = _client.chat.completions.create(
        model=CHAT_MODEL, messages=messages, temperature=0.15, max_tokens=4096
    )
    code       = _clean_code_block(response.choices[0].message.content or "")
    validation = validate(code).to_dict()
    sources    = list({c["source"] for c in chunks})
    return {"code": code, "sources": sources, "validation": validation}


def review(code: str) -> dict:
    """Score and critique a C# script against ServUO patterns."""
    chunks   = retrieve(code[:1000], top_k=TOP_K_REVIEW, source_type="script")
    context  = build_context(chunks)
    messages = build_review_prompt(code, context)
    response = _client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content or "{}")
    result["sources"]    = list({c["source"] for c in chunks})
    result["validation"] = validate(code).to_dict()
    return result


def refactor(code: str, instructions: str) -> dict:
    """Rewrite a C# script following instructions, grounded in codebase context."""
    chunks   = retrieve(instructions + "\n" + code[:500], top_k=TOP_K_CODE, source_type="script")
    context  = build_context(chunks)
    messages = build_refactor_prompt(code, instructions, context)
    response = _client.chat.completions.create(
        model=CHAT_MODEL, messages=messages, temperature=0.15, max_tokens=4096
    )
    refactored = _clean_code_block(response.choices[0].message.content or "")
    validation = validate(refactored).to_dict()
    sources    = list({c["source"] for c in chunks})
    return {"code": refactored, "sources": sources, "validation": validation}


def _print_result(result: dict, operation: str):
    print(f"\n{'='*60}")
    print(f"  ServUO RAG Coder — {operation}")
    print(f"{'='*60}\n")
    if "code" in result:
        print(result["code"])
    else:
        print(f"Score     : {result.get('score')}/10")
        print(f"Approved  : {result.get('approved')}")
        for section in ("issues", "suggestions"):
            vals = result.get(section, [])
            if vals:
                print(f"\n{section.title()}:")
                for v in vals:
                    print(f"  • {v}")
    validation = result.get("validation") or {}
    warns = validation.get("warnings", [])
    if warns:
        print("\nValidation warnings:")
        for w in warns:
            print(f"  • {w}")
    sources = result.get("sources", [])
    if sources:
        print("\nContext sources:")
        for s in sources:
            print(f"  • {s}")


def main():
    parser = argparse.ArgumentParser(description="ServUO RAG Coding Agent")
    sub    = parser.add_subparsers(dest="op", required=True)

    gen_p = sub.add_parser("generate")
    gen_p.add_argument("task")
    gen_p.add_argument("--out")

    rev_p = sub.add_parser("review")
    rev_p.add_argument("file")

    ref_p = sub.add_parser("refactor")
    ref_p.add_argument("file")
    ref_p.add_argument("instructions")
    ref_p.add_argument("--out")

    args = parser.parse_args()

    if args.op == "generate":
        result = generate(args.task)
        _print_result(result, "GENERATE")
        if args.out:
            pathlib.Path(args.out).write_text(result["code"], encoding="utf-8")
            print(f"\nWritten to {args.out}")
    elif args.op == "review":
        result = review(pathlib.Path(args.file).read_text(encoding="utf-8"))
        _print_result(result, "REVIEW")
    else:
        code   = pathlib.Path(args.file).read_text(encoding="utf-8")
        result = refactor(code, args.instructions)
        _print_result(result, "REFACTOR")
        out    = args.out or args.file
        pathlib.Path(out).write_text(result["code"], encoding="utf-8")
        print(f"\nWritten to {out}")


if __name__ == "__main__":
    main()
