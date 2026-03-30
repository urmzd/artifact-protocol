#!/usr/bin/env python3
"""
Simple LLM streaming via ollama.

Usage: uv run --project python ag-stream [output-path] [model]
"""
import sys

import ollama


PROMPT = """Create a self-contained HTML page with CSS animations.
Output raw HTML only, no markdown fences."""


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/artifact.html"
    model = sys.argv[2] if len(sys.argv) > 2 else "llama3.2"

    with open(path, "w") as f:
        for chunk in ollama.generate(model=model, prompt=PROMPT, stream=True):
            token = chunk.get("response", "")
            if token:
                f.write(token)
                f.flush()


if __name__ == "__main__":
    main()
