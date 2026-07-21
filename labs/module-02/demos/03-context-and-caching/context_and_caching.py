"""
Context and Caching — Long-Context Handling
Module 2: Prompt Engineering for Applications
Based on: day1/credit_policy_assistant.py

Injects the same ~200-line policy document into several questions in a row,
first without prompt caching and then with cache_control: {"type": "ephemeral"}
on the document block, so you can see the actual usage fields shift:
input_tokens stays flat without caching, while cache_creation_input_tokens
(first call) and cache_read_input_tokens (later calls) appear once caching
is turned on.

Run:
    uv run context_and_caching.py
    uv run context_and_caching.py --questions 2
    uv run context_and_caching.py --no-cache   # baseline only, skip the caching half
"""

import argparse
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise EnvironmentError(
        "ANTHROPIC_API_KEY is not set.\n"
        "Copy .env.example to .env in this folder and add your key, e.g.:\n"
        "    cp .env.example .env"
    )

client = anthropic.Anthropic()
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")

POLICY_PATH = Path(__file__).resolve().parents[4] / "shared" / "data" / "apex_bank_credit_policy.md"

SYSTEM_PROMPT = """
You are a credit-policy assistant for Apex Bank.
Answer ONLY from the policy document provided, citing the section number.
Keep answers under 100 words.
"""

QUESTIONS = [
    "What is the maximum debt-to-income ratio for a home loan?",
    "How long does it take to get a personal loan disbursed?",
    "What documents does a self-employed applicant need to submit?",
]


def usage_line(response) -> str:
    u = response.usage
    creation = getattr(u, "cache_creation_input_tokens", None) or 0
    read = getattr(u, "cache_read_input_tokens", None) or 0
    return (
        f"input={u.input_tokens:>5}  output={u.output_tokens:>4}  "
        f"cache_creation={creation:>5}  cache_read={read:>5}"
    )


def run_without_cache(policy_text: str, questions: list[str]) -> None:
    print(f"\n{'='*70}\nBASELINE — no cache_control, document resent every call\n{'='*70}")
    for i, q in enumerate(questions, 1):
        messages = [
            {
                "role": "user",
                "content": f"[Policy Document]\n{policy_text}\n\n[Question]\n{q}",
            }
        ]
        response = client.messages.create(
            model=MODEL, max_tokens=200, system=SYSTEM_PROMPT, messages=messages,
        )
        print(f"\nCall {i}: {q}")
        print(f"  {usage_line(response)}")


def run_with_cache(policy_text: str, questions: list[str]) -> None:
    print(f"\n{'='*70}\nCACHED — cache_control: ephemeral on the document block\n{'='*70}")
    for i, q in enumerate(questions, 1):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"[Policy Document]\n{policy_text}",
                        "cache_control": {"type": "ephemeral"},
                    },
                    {"type": "text", "text": f"[Question]\n{q}"},
                ],
            }
        ]
        response = client.messages.create(
            model=MODEL, max_tokens=200, system=SYSTEM_PROMPT, messages=messages,
        )
        print(f"\nCall {i}: {q}")
        print(f"  {usage_line(response)}")
        if i == 1:
            print("  ^ first call: pays to WRITE the cache (cache_creation_input_tokens)")
        else:
            print("  ^ later call: READS the cache instead of reprocessing the document")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=int, default=len(QUESTIONS),
                         help=f"How many questions to run (max {len(QUESTIONS)}).")
    parser.add_argument("--no-cache", action="store_true",
                         help="Only run the baseline (no caching) half.")
    args = parser.parse_args()

    if not POLICY_PATH.exists():
        raise SystemExit(f"ERROR: policy document not found at {POLICY_PATH}")
    policy_text = POLICY_PATH.read_text()
    questions = QUESTIONS[: max(1, min(args.questions, len(QUESTIONS)))]

    count = client.messages.count_tokens(
        model=MODEL,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"[Policy Document]\n{policy_text}\n\n[Question]\n{questions[0]}"}],
    )
    print(f"Pre-flight estimate (count_tokens, no inference, free): "
          f"{count.input_tokens} input tokens for call 1")

    run_without_cache(policy_text, questions)
    if not args.no_cache:
        run_with_cache(policy_text, questions)

    print(f"\n{'='*70}")
    print("What to notice: in the BASELINE section every call's input_tokens is")
    print("roughly the same (the whole document, resent). In the CACHED section,")
    print("call 1 shows cache_creation_input_tokens > 0 (writing the cache), and")
    print("calls 2+ show cache_read_input_tokens > 0 instead — a much cheaper")
    print("re-read of the same document. Caching changes COST, never correctness:")
    print("the answers themselves don't change.")
    print("(Any dollar figures you compute from these counts are illustrative —")
    print(" check current per-model rates at platform.claude.com/docs.)")


if __name__ == "__main__":
    main()
