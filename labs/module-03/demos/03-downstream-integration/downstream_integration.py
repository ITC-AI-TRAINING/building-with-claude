"""
Downstream Integration — What a Validated Record Buys You
Module 3: Structured Outputs and Validation
Based on: day2/loan_application_extractor.py

Takes already-validated LoanApplicationRecord instances (the SAME five
applicants day2/loan_application_extractor.py extracts) and reshapes them for
three downstream consumers — a core-banking CSV row, a credit-committee
referral queue, and a rough risk bucket — with NO API calls and NO
re-validation. This is deliberately offline: the point of Module 3 is that
once you have response.parsed_output, you never need to re-parse or
defensively re-check it again.

Run:
    uv run downstream_integration.py
"""

import csv
import io
from typing import Literal, Optional

from pydantic import BaseModel, field_validator

# Same schema as day2/loan_application_extractor.py — no anthropic/API import
# needed here, because this demo starts from records that are already valid.


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


# The same five applicants as day2/loan_application_extractor.py's RAW_APPLICATIONS,
# already extracted (as if response.parsed_output had already run for each).
RECORDS = [
    LoanApplicationRecord(applicant_name="Rajesh Kumar", loan_type="home_loan",
                          loan_amount_inr=4_500_000, monthly_income_inr=85_000,
                          tenure_years=20, credit_score=742),
    LoanApplicationRecord(applicant_name="Sunita Rao", loan_type="personal_loan",
                          loan_amount_inr=300_000, monthly_income_inr=45_000,
                          tenure_years=3, credit_score=None),
    LoanApplicationRecord(applicant_name="Arun Mehta", loan_type="business_loan",
                          loan_amount_inr=2_500_000, monthly_income_inr=220_000,
                          tenure_years=5, credit_score=710),
    LoanApplicationRecord(applicant_name="Deepika Joshi", loan_type="vehicle_loan",
                          loan_amount_inr=850_000, monthly_income_inr=55_000,
                          tenure_years=4, credit_score=780),
    LoanApplicationRecord(applicant_name="Venkatesh Iyer", loan_type="home_loan",
                          loan_amount_inr=7_000_000, monthly_income_inr=150_000,
                          tenure_years=25, credit_score=760),
]

# From the credit policy's Section 2.2 (see day2/starter.py's SYSTEM_PROMPT /
# shared/data/apex_bank_credit_policy.md): loans above this need committee review.
COMMITTEE_REVIEW_THRESHOLD_INR = 5_000_000


def to_csv_row(record: LoanApplicationRecord) -> dict:
    """(a) Core-banking system row — flat, no nested objects, ready for csv.DictWriter."""
    return {
        "applicant_name": record.applicant_name,
        "loan_type": record.loan_type,
        "loan_amount_inr": f"{record.loan_amount_inr:.2f}",
        "monthly_income_inr": f"{record.monthly_income_inr:.2f}",
        "tenure_years": record.tenure_years,
        "credit_score": record.credit_score if record.credit_score is not None else "",
    }


def committee_review_reason(record: LoanApplicationRecord) -> Optional[str]:
    """(b) Credit-committee referral queue — only records that need a human look."""
    if record.loan_amount_inr > COMMITTEE_REVIEW_THRESHOLD_INR:
        return f"loan_amount_inr {record.loan_amount_inr:,.0f} exceeds INR {COMMITTEE_REVIEW_THRESHOLD_INR:,} (Section 2.2)"
    if record.credit_score is None:
        return "credit_score unavailable — bureau not checked yet (Section 4.1: refer, never decline)"
    return None


def risk_bucket(record: LoanApplicationRecord) -> str:
    """(c) A rough affordability proxy, NOT the bank's real DTI formula (Section 2.1) —
    that needs existing_emi_inr, which this schema doesn't capture. Illustrative only.
    """
    annual_income = record.monthly_income_inr * 12
    ratio = record.loan_amount_inr / annual_income
    if ratio < 3:
        return "low"
    if ratio < 6:
        return "medium"
    return "high"


def main() -> None:
    print("(a) CORE-BANKING CSV EXPORT")
    print("-" * 70)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(to_csv_row(RECORDS[0]).keys()))
    writer.writeheader()
    for record in RECORDS:
        writer.writerow(to_csv_row(record))
    print(buffer.getvalue())

    print("(b) CREDIT-COMMITTEE REFERRAL QUEUE")
    print("-" * 70)
    queued = [(r, committee_review_reason(r)) for r in RECORDS]
    queued = [(r, reason) for r, reason in queued if reason]
    if not queued:
        print("  (empty — nothing needs committee review)")
    for record, reason in queued:
        print(f"  {record.applicant_name:<16} -> {reason}")

    print(f"\n(c) RISK BUCKETS (illustrative loan-to-annual-income proxy)")
    print("-" * 70)
    for record in RECORDS:
        print(f"  {record.applicant_name:<16} {risk_bucket(record):<8} "
              f"(loan={record.loan_amount_inr:,.0f}, annual_income={record.monthly_income_inr*12:,.0f})")

    print("\nWhat to notice: none of the three functions above call Claude, parse JSON, or")
    print("re-check a field's type. record.loan_amount_inr is trusted directly because")
    print("Pydantic already guaranteed it's a float > 0 the moment extraction succeeded.")


if __name__ == "__main__":
    main()
