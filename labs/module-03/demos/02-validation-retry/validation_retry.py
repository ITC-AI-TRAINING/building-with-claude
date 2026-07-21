"""
Validation Retry — Retries, and Their Limits
Module 3: Structured Outputs and Validation
Based on: day2/loan_application_extractor.py

Runs the same bounded validation-retry loop from the reference script against
three inputs: a normal application (should succeed on attempt 1), an
ambiguous one (may need a retry to settle on a valid loan_type / a single
tenure value), and a genuinely incomplete one with no loan amount stated at
all anywhere in the text (should FAIL even after retries — because retries
fix a model mistake, never a gap in the source data).

Run:
    uv run validation_retry.py
"""

import os
from typing import Literal, Optional

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, field_validator

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise EnvironmentError(
        "ANTHROPIC_API_KEY is not set.\n"
        "Copy .env.example to .env in this folder and add your key, e.g.:\n"
        "    cp .env.example .env"
    )

client = anthropic.Anthropic()
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_RETRIES = 2


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


TEST_CASES = [
    {
        "id": "APP-NORMAL",
        "label": "normal — should succeed on attempt 1",
        "text": "Rajesh Kumar, home loan INR 45L over 20 yrs, monthly income INR 85K, credit score 742.",
    },
    {
        "id": "APP-AMBIGUOUS",
        "label": "ambiguous phrasing — may need a retry to settle on one value",
        "text": (
            "I need money to expand my shop, around 12 lakhs, my shop earns about "
            "60 thousand a month, want to pay back in 4-5 years."
        ),
    },
    {
        "id": "APP-INCOMPLETE",
        "label": "genuinely incomplete — no loan amount anywhere, should FAIL",
        "text": (
            "My name is Kavita Nair. I want to apply for a loan but haven't decided "
            "the amount yet — I'll confirm once I know what the property costs. "
            "My monthly income is INR 60,000 and I'd like around a 15-year term."
        ),
    },
]


def extract_record(raw_text: str) -> tuple[Optional[LoanApplicationRecord], int, Optional[str]]:
    """Returns (record_or_None, retries_used, final_error_or_None)."""
    messages = [{"role": "user", "content": f"Extract the loan application fields from: '{raw_text}'"}]

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.messages.parse(
                model=MODEL, max_tokens=512, temperature=0,
                messages=messages, output_format=LoanApplicationRecord,
            )
            return response.parsed_output, attempt, None
        except ValidationError as e:
            if attempt == MAX_RETRIES:
                return None, attempt, str(e)
            # NOTE: client.messages.parse() raises ValidationError from INSIDE the call
            # itself (while building the parsed response), so `response` is never bound
            # here — there is no raw assistant text available to echo back. Feed the
            # error alone; it already names the offending field and value.
            print(f"    attempt {attempt + 1} failed validation, retrying: {e}")
            messages.append({
                "role": "user",
                "content": (
                    f"Your previous output failed schema validation:\n{e}\n\n"
                    "Please return a corrected JSON object that matches the schema exactly."
                ),
            })
    return None, MAX_RETRIES, "unreachable"


def main() -> None:
    ledger = []
    for case in TEST_CASES:
        print(f"\n{'='*70}\n{case['id']}: {case['label']}\n{'-'*70}")
        record, retries, error = extract_record(case["text"])
        ledger.append((case["id"], record, retries, error))
        if record:
            print(f"  -> OK after {retries} retr{'y' if retries == 1 else 'ies'}: {record}")
        else:
            print(f"  -> FAILED after {retries} retries: {error}")

    print(f"\n{'='*70}\nRETRY LEDGER\n{'='*70}")
    print(f"{'ID':<16} {'Status':<8} {'Retries':<8} Note")
    print("-" * 70)
    for case_id, record, retries, error in ledger:
        status = "OK" if record else "FAILED"
        note = "" if record else "no fabricated amount — correctly reported as failed"
        print(f"{case_id:<16} {status:<8} {retries:<8} {note}")


if __name__ == "__main__":
    main()
