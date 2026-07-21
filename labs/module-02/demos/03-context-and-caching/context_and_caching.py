"""
Context and Caching — Long-Context Handling
Module 2: Prompt Engineering for Applications
Based on: day1/credit_policy_assistant.py

Injects a bundle of Apex Bank reference documents (credit policy manual, loan
processing SOP, sample loan applications, and a terms glossary) into several
questions in a row — first without prompt caching, then with
cache_control: {"type": "ephemeral"} on the reference block — so you can see
the actual usage fields shift: input_tokens stays flat without caching, while
cache_creation_input_tokens (first call) and cache_read_input_tokens (later
calls) appear once caching is turned on.

Why the bundle instead of just the credit policy alone: prompt caching only
activates above a minimum cacheable prefix size, and that minimum is larger
than you might expect (confirmed empirically against the live API — see the
MODEL comment below). The credit policy document alone (~2,300 tokens) was
too small to reliably clear it, so this demo bundles in the other real Apex
Bank reference docs already in shared/data/ plus a short glossary, landing
comfortably over the highest documented per-model minimum. Bundling multiple
reference docs and letting only some of them matter to any given question is
also a realistic "long context" pattern in its own right.

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
# claude-sonnet-4-5, not claude-haiku-4-5: prompt caching silently no-ops below a
# model-specific minimum cacheable prefix (no error, cache_*_tokens just read 0).
# Documented minimums put Sonnet 4.5 at 1024 tokens, but live testing showed the
# credit policy alone (~2,300 tokens) still wasn't enough to trigger caching on
# this account — the effective minimum in practice is evidently higher than the
# cached reference table says. Rather than guess an exact number, this demo
# bundles enough real reference content (below) to comfortably clear the
# highest documented minimum (4096 tokens, Opus/Haiku tier) regardless of model.
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

SHARED_DATA_DIR = Path(__file__).resolve().parents[4] / "shared" / "data"
POLICY_PATH = SHARED_DATA_DIR / "apex_bank_credit_policy.md"
SOP_PATH = SHARED_DATA_DIR / "finance_sop" / "loan_processing_sop.md"
APPLICATIONS_PATH = SHARED_DATA_DIR / "apex_bank_loan_applications.md"

# Genuine reference material (not fabricated policy) sized to push the bundle
# comfortably past the 4096-token ceiling — see the MODEL comment above.
GLOSSARY = """
## Glossary of Terms

Reference definitions for abbreviations used throughout the documents above.

- **CIBIL** — Credit Information Bureau (India) Limited, one of India's four
  RBI-licensed credit bureaus; issues a 3-digit credit score from 300 to 900.
- **Experian** — Another RBI-licensed Indian credit bureau, used as an
  alternative or secondary source for credit scores.
- **ITR** — Income Tax Return, the annual tax filing self-employed applicants
  submit as proof of income.
- **DTI** — Debt-to-Income ratio: (existing EMIs + estimated new EMI) ÷ gross
  monthly income, expressed as a percentage.
- **LTV** — Loan-to-Value ratio: the loan amount as a percentage of the value
  of the asset being financed (property, vehicle, etc.).
- **EMI** — Equated Monthly Installment, the fixed monthly repayment amount
  on a loan.
- **NOC** — No Objection Certificate, issued by a builder or developer
  confirming no legal or financial objection to a property transaction;
  required for under-construction properties.
- **PSU** — Public Sector Undertaking, a government-owned corporation.
- **MNC** — Multinational Corporation.
- **AEL** — Approved Employer List, Apex Bank's internal list of employers
  whose staff qualify under relaxed salaried-applicant criteria.
- **Form CR-07** — The internal Apex Bank form used to request Branch Manager
  approval for a credit-score exception.
- **SLA** — Service Level Agreement, the maximum time allowed to complete a
  defined step of loan processing.
- **LAP** — Loan Against Property, a secured loan using real estate as
  collateral rather than financing the purchase of that property.
- **DPD** — Days Past Due, the count of days a loan repayment is overdue;
  used to classify delinquency severity (e.g. DPD > 90 is a serious default).
- **Credit Committee** — The internal Apex Bank body that reviews
  applications referred for large loan amounts, borderline DTI, or bureau
  unavailability; meets on a fixed weekly schedule and issues written
  decisions within a defined SLA.
- **Branch Manager approval** — Sign-off required from the branch's senior
  officer for defined exception cases (credit-score exceptions, persistent
  bureau failures) that fall outside standard automated processing rules.
- **Regional Credit Manager** — The officer who reviews customer appeals
  against a declined loan decision.
- **Zonal Credit Manager** — The escalation point for borderline cases that
  branch staff believe the automated decision misjudged.

## Document Index

This reference bundle concatenates four Apex Bank documents in order:
1. The Credit Policy Manual — eligibility, DTI, LTV, documentation, and
   decline-condition sections, each with a numbered section reference.
2. The Loan Processing Standard Operating Procedure — the day-to-day
   processing rules that implement the policy manual, including bureau
   unavailability handling, SLAs, and the appeals process.
3. Five raw loan application submissions, included as sample source text
   from real applicant intake (not policy — no section numbers apply here).
4. This glossary, defining the abbreviations used across the first three
   documents so an unfamiliar reader can follow the terminology without
   looking it up elsewhere.
"""

SYSTEM_PROMPT = """
You are a credit-policy assistant for Apex Bank.
Answer ONLY from the reference documents provided, citing the section number
when one applies.
Keep answers under 100 words.
"""

QUESTIONS = [
    "What is the maximum debt-to-income ratio for a home loan?",
    "How long does it take to get a personal loan disbursed?",
    "What documents does a self-employed applicant need to submit?",
]


def load_reference_text() -> str:
    for path in (POLICY_PATH, SOP_PATH, APPLICATIONS_PATH):
        if not path.exists():
            raise SystemExit(f"ERROR: reference document not found at {path}")
    return "\n\n---\n\n".join(
        [POLICY_PATH.read_text(), SOP_PATH.read_text(), APPLICATIONS_PATH.read_text(), GLOSSARY]
    )


def usage_line(response) -> str:
    u = response.usage
    creation = getattr(u, "cache_creation_input_tokens", None) or 0
    read = getattr(u, "cache_read_input_tokens", None) or 0
    return (
        f"input={u.input_tokens:>5}  output={u.output_tokens:>4}  "
        f"cache_creation={creation:>5}  cache_read={read:>5}"
    )


def run_without_cache(reference_text: str, questions: list[str]) -> None:
    print(f"\n{'='*70}\nBASELINE — no cache_control, documents resent every call\n{'='*70}")
    for i, q in enumerate(questions, 1):
        messages = [
            {
                "role": "user",
                "content": f"[Reference Documents]\n{reference_text}\n\n[Question]\n{q}",
            }
        ]
        response = client.messages.create(
            model=MODEL, max_tokens=200, system=SYSTEM_PROMPT, messages=messages,
        )
        print(f"\nCall {i}: {q}")
        print(f"  {usage_line(response)}")


def run_with_cache(reference_text: str, questions: list[str]) -> None:
    print(f"\n{'='*70}\nCACHED — cache_control: ephemeral on the reference block\n{'='*70}")
    for i, q in enumerate(questions, 1):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"[Reference Documents]\n{reference_text}",
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
            print("  ^ later call: READS the cache instead of reprocessing the documents")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=int, default=len(QUESTIONS),
                         help=f"How many questions to run (max {len(QUESTIONS)}).")
    parser.add_argument("--no-cache", action="store_true",
                         help="Only run the baseline (no caching) half.")
    args = parser.parse_args()

    reference_text = load_reference_text()
    questions = QUESTIONS[: max(1, min(args.questions, len(QUESTIONS)))]

    count = client.messages.count_tokens(
        model=MODEL,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"[Reference Documents]\n{reference_text}\n\n[Question]\n{questions[0]}"}],
    )
    print(f"Pre-flight estimate (count_tokens, no inference, free): "
          f"{count.input_tokens} input tokens for call 1")

    run_without_cache(reference_text, questions)
    if not args.no_cache:
        run_with_cache(reference_text, questions)

    print(f"\n{'='*70}")
    print("What to notice: in the BASELINE section every call's input_tokens is")
    print("roughly the same (the whole reference bundle, resent). In the CACHED")
    print("section, call 1 shows cache_creation_input_tokens > 0 (writing the")
    print("cache), and calls 2+ show cache_read_input_tokens > 0 instead — a much")
    print("cheaper re-read of the same content. Caching changes COST, never")
    print("correctness: the answers themselves don't change.")
    print("(Any dollar figures you compute from these counts are illustrative —")
    print(" check current per-model rates at platform.claude.com/docs.)")


if __name__ == "__main__":
    main()
