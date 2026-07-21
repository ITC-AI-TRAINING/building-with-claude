"""
Downstream Summary Integration — What a Validated Summary Buys You
Module 4: Conversation and Context Management
Based on: day2/loan_intake_manager.py

Takes already-produced IntakeSummary instances (the SAME schema
day2/loan_intake_manager.py's final client.messages.parse() call returns) and
reshapes them for three downstream consumers — a CRM follow-up task, a
risk-flagged review queue, and a customer-facing next-step message — with NO
API calls and NO re-validation. Same idea as Module 3's downstream-
integration demo, applied to a conversation's final summary instead of a
single-turn extraction.

Run:
    uv run downstream_summary_integration.py
"""

from typing import Literal

from pydantic import BaseModel


class IntakeSummary(BaseModel):
    applicant_type: Literal["salaried", "self_employed", "unknown"]
    loan_amount_inr: float
    credit_checked: bool
    recommended_action: Literal["proceed", "review", "decline"]


# Four already-completed intake sessions, as if response.parsed_output had
# already run for each (Priya Sharma is the reference script's own demo case).
SESSIONS = [
    ("Priya Sharma", IntakeSummary(applicant_type="salaried", loan_amount_inr=4_000_000,
                                    credit_checked=True, recommended_action="proceed")),
    ("Ananya Desai", IntakeSummary(applicant_type="salaried", loan_amount_inr=6_500_000,
                                    credit_checked=True, recommended_action="review")),
    ("Rahul Verma", IntakeSummary(applicant_type="unknown", loan_amount_inr=250_000,
                                   credit_checked=False, recommended_action="review")),
    ("Meena Iyer", IntakeSummary(applicant_type="self_employed", loan_amount_inr=1_200_000,
                                  credit_checked=True, recommended_action="decline")),
]


def crm_task(name: str, summary: IntakeSummary) -> dict:
    """(a) A follow-up task row for the CRM queue."""
    action_map = {
        "proceed": "Schedule document collection call",
        "review": "Escalate to credit manager for manual review",
        "decline": "Send written decline notice within 2 business days (Section 7.2)",
    }
    return {
        "applicant": name,
        "task": action_map[summary.recommended_action],
        "priority": "high" if summary.recommended_action == "decline" else "normal",
    }


def needs_human_review(summary: IntakeSummary) -> bool:
    """(b) Risk-flagged queue — only sessions that didn't clear automatically."""
    return summary.recommended_action != "proceed"


def customer_message(name: str, summary: IntakeSummary) -> str:
    """(c) A customer-facing next-step message, never inventing a status not in the summary."""
    first_name = name.split()[0]
    if summary.recommended_action == "proceed":
        return (f"Hi {first_name}, thanks for completing your intake — "
                 f"we'll be in touch shortly to collect your documents.")
    if summary.recommended_action == "review":
        return (f"Hi {first_name}, your application is with our credit team for a closer look. "
                 f"We'll update you as soon as a decision is made.")
    return (f"Hi {first_name}, we're unable to proceed with your application at this time. "
            f"A written notice with the reason will follow within 2 business days.")


def main() -> None:
    print("(a) CRM FOLLOW-UP QUEUE")
    print("-" * 70)
    for name, summary in SESSIONS:
        task = crm_task(name, summary)
        print(f"  {task['applicant']:<16} [{task['priority']:<6}] {task['task']}")

    print("\n(b) RISK-FLAGGED REVIEW QUEUE (excludes clean 'proceed' sessions)")
    print("-" * 70)
    flagged = [(n, s) for n, s in SESSIONS if needs_human_review(s)]
    if not flagged:
        print("  (empty — every session cleared automatically)")
    for name, summary in flagged:
        print(f"  {name:<16} action={summary.recommended_action:<8} "
              f"amount={summary.loan_amount_inr:,.0f} credit_checked={summary.credit_checked}")

    print("\n(c) CUSTOMER-FACING NEXT-STEP MESSAGES")
    print("-" * 70)
    for name, summary in SESSIONS:
        print(f"  {name}: {customer_message(name, summary)}")

    print("\nWhat to notice: none of the three functions above call Claude or re-check")
    print("summary.recommended_action's value — it's trusted directly because it can only")
    print("ever be one of the three Literal values Pydantic already validated.")


if __name__ == "__main__":
    main()
