"""
Faithfulness Judge — LLM-as-judge scoring an answer against its cited context
Module 7: Evaluation and Output Quality
Based on: day4/eval_rag_assistant.py (faithfulness_judge)

Faithfulness asks one narrow question: does every factual claim in the ANSWER actually appear in
the CONTEXT it cites? A plausible-sounding number is not the same thing as a supported one — this
demo runs the judge on one faithful answer and one hallucinated-but-plausible answer to the same
real Apex Bank question, so you can see the judge catch the difference.

Run:
    uv run faithfulness_judge.py
    uv run faithfulness_judge.py --answer unfaithful
"""

import argparse
import json
import os
import re

import anthropic
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise EnvironmentError("ANTHROPIC_API_KEY is not set. Copy .env.example to .env first.")

client = anthropic.Anthropic()
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

QUESTION = "What is the maximum loan-to-value ratio for home loans?"

# Same real snippet used across the Module 6 demos.
CONTEXT = (
    "[policy-0] (Credit Policy)\n"
    "Maximum loan-to-value ratio for home loans is 90% up to INR 30 lakhs, "
    "80% between 30 and 75 lakhs, and 75% above 75 lakhs."
)

ANSWERS = {
    "faithful": (
        "Apex Bank's maximum LTV for home loans is 90% up to INR 30 lakhs, 80% between 30 "
        "and 75 lakhs, and 75% above 75 lakhs [policy-0]."
    ),
    "unfaithful": (
        "Apex Bank's maximum LTV for home loans is 95% regardless of loan amount [policy-0]."
    ),
}

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```")
_BARE_RE = re.compile(r"\{[\s\S]*\}")


def parse_judge_json(raw: str) -> dict:
    fence_match = _FENCE_RE.search(raw)
    candidate = fence_match.group(1) if fence_match else raw
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    bare_match = _BARE_RE.search(raw)
    if bare_match:
        try:
            return json.loads(bare_match.group(0))
        except json.JSONDecodeError:
            pass
    return {"score": 0, "reasoning": f"parse error: could not parse judge output: {raw[:200]}"}


def faithfulness_judge(question: str, context: str, answer: str) -> dict:
    judge_prompt = f"""You are a strict faithfulness judge for a RAG assistant. Given CONTEXT
and an ANSWER that claims to be grounded in it, decide whether every factual claim in the ANSWER
is actually supported by the CONTEXT — not just plausible, actually stated.

CONTEXT:
{context}

QUESTION: {question}

ANSWER: {answer}

Respond with ONLY a JSON object, no other text:
{{"score": 0 or 1, "unsupported_claims": ["..."], "reasoning": "one sentence"}}"""
    response = client.messages.create(
        model=MODEL, max_tokens=400, messages=[{"role": "user", "content": judge_prompt}]
    )
    raw = next((b.text for b in response.content if b.type == "text"), "")
    return parse_judge_json(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--answer", choices=["faithful", "unfaithful", "both"], default="both",
        help="Which candidate answer to judge (default: both, for comparison).",
    )
    args = parser.parse_args()

    kinds = ["faithful", "unfaithful"] if args.answer == "both" else [args.answer]

    try:
        print(f"Question: {QUESTION}\n")
        print(f"Context:\n{CONTEXT}\n")
        for kind in kinds:
            answer = ANSWERS[kind]
            print(f"--- {kind} answer ---")
            print(f"Answer: {answer}")
            verdict = faithfulness_judge(QUESTION, CONTEXT, answer)
            print(f"Judge verdict: score={verdict.get('score')} — {verdict.get('reasoning')}")
            if verdict.get("unsupported_claims"):
                print(f"Unsupported claims: {verdict['unsupported_claims']}")
            print()

        print("What to log in a real app: question, context id(s), answer, judge score, "
              "judge reasoning, and the raw judge response for audit — see day4/eval_log.jsonl.")
    except anthropic.AuthenticationError:
        print("ERROR: Invalid API key — check ANTHROPIC_API_KEY in your .env file.")
        raise SystemExit(1)
    except anthropic.RateLimitError as e:
        retry_after = int(e.response.headers.get("retry-after", "60"))
        print(f"ERROR: Rate limited — retry after {retry_after} seconds.")
        raise SystemExit(1)
    except anthropic.APIConnectionError:
        print("ERROR: Cannot reach the API — check your network connection.")
        raise SystemExit(1)
    except anthropic.APIStatusError as e:
        print(f"ERROR: API returned status {e.status_code}: {e.message}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
