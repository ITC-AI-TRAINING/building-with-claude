"""
Schema vs. Freeform — JSON Generation & Parsing
Module 3: Structured Outputs and Validation
Based on: day2/loan_application_extractor.py

Sends the SAME raw loan application text through two extraction approaches:
  (a) the naive way — ask nicely for JSON in the prompt, then json.loads()
      the raw text yourself
  (b) the schema-driven way — client.messages.parse(output_format=Model)

(a) usually "works" but is fragile: a leading sentence or a markdown fence
around the JSON breaks a blind json.loads(). (b) never has that failure mode
because there's no raw-text parsing step at all.

Run:
    uv run schema_vs_freeform.py
    uv run schema_vs_freeform.py --applicant 2
"""

import argparse
import json
import os
import re
from typing import Literal, Optional

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise EnvironmentError(
        "ANTHROPIC_API_KEY is not set.\n"
        "Copy .env.example to .env in this folder and add your key, e.g.:\n"
        "    cp .env.example .env"
    )

client = anthropic.Anthropic()
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Same five applicants as day2/loan_application_extractor.py
RAW_APPLICATIONS = [
    "Rajesh Kumar, home loan INR 45L over 20 yrs, monthly income INR 85K, credit score 742.",
    "Sunita Rao, personal loan INR 3L, repay over 3 years, income INR 45K/month.",
    "Arun Mehta, business loan INR 25L, 5-year term, monthly business income INR 2.2L, CIBIL 710.",
    "Deepika Joshi, vehicle loan INR 8.5L, 4 years, income INR 55K/month, credit score 780.",
    "Venkatesh Iyer, home loan INR 70L, 25-year term, household income INR 1.5L/month, score 760.",
]

FENCE_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```")


class LoanApplicationRecord(BaseModel):
    applicant_name: str
    loan_type: Literal["home_loan", "personal_loan", "business_loan", "vehicle_loan"]
    loan_amount_inr: float
    monthly_income_inr: float
    tenure_years: int
    credit_score: Optional[int] = None

    @field_validator("loan_amount_inr")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("loan_amount_inr must be positive")
        return v


NAIVE_SYSTEM_PROMPT = """
Extract the loan application fields as a JSON object with keys:
applicant_name, loan_type, loan_amount_inr, monthly_income_inr, tenure_years,
credit_score (null if unknown). Return ONLY the JSON object.
"""


def naive_extract(raw_text: str) -> None:
    print("\n--- (a) Naive: create() + json.loads() ---")
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=NAIVE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": raw_text}],
    )
    raw_output = next((b.text for b in response.content if b.type == "text"), "")
    print(f"Raw model output:\n{raw_output}")

    try:
        data = json.loads(raw_output)
        print(f"json.loads() succeeded on the raw text: {data}")
        return
    except json.JSONDecodeError as e:
        print(f"json.loads() FAILED on the raw text: {e}")

    fence_match = FENCE_RE.search(raw_output)
    if fence_match:
        data = json.loads(fence_match.group(1))
        print(f"Recovered by stripping a markdown fence by hand: {data}")
    else:
        print("No fence found either — this input would need a human to look at it.")


def schema_extract(raw_text: str) -> None:
    print("\n--- (b) Schema-driven: messages.parse(output_format=...) ---")
    response = client.messages.parse(
        model=MODEL,
        max_tokens=300,
        temperature=0,
        messages=[{"role": "user", "content": f"Extract the loan application fields from: '{raw_text}'"}],
        output_format=LoanApplicationRecord,
    )
    record = response.parsed_output
    print(f"response.parsed_output is already a {type(record).__name__}: {record}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--applicant", type=int, default=1,
                         help=f"Which applicant to test, 1-{len(RAW_APPLICATIONS)} (default 1).")
    args = parser.parse_args()
    idx = max(1, min(args.applicant, len(RAW_APPLICATIONS))) - 1
    raw_text = RAW_APPLICATIONS[idx]

    print(f"Applicant {idx + 1}: {raw_text}")
    naive_extract(raw_text)
    schema_extract(raw_text)

    print("\nWhat to notice: (a) may succeed most of the time, but every success depends on")
    print("Claude happening not to add a fence or a sentence — a behavior you don't control.")
    print("(b) has no raw-text parsing step, so that entire failure mode doesn't exist.")


if __name__ == "__main__":
    main()
