"""
query.py — interactive RAG query loop for ServUO knowledge base

Usage:
    python query.py
    python query.py --type script    # restrict to .cs files only
    python query.py --type text      # restrict to .txt / .md files only
"""

import argparse
from rag_core import ask


def main():
    parser = argparse.ArgumentParser(description="ServUO RAG Query")
    parser.add_argument("--type", choices=["script", "text"], default=None,
                        help="Filter retrieval to 'script' (.cs) or 'text' (.txt/.md)")
    args = parser.parse_args()

    print("ServUO RAG — ask anything about your shard.")
    print(f"  Source filter : {args.type or 'all'}")
    print("  Type 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit", "q"):
            break

        result = ask(question, source_type=args.type)

        print(f"\nRAG: {result['answer']}")
        if result["sources"]:
            print("\nSources:")
            for s in result["sources"]:
                print(f"  • {s}")
        print()


if __name__ == "__main__":
    main()
