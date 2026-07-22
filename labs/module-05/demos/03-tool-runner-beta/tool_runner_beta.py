"""
Tool Runner (beta) — the higher-level pattern, isolated
Module 5: Tool Use and Function Integration
Based on: day3/invoice_tool_agent_beta.py

Same two-tool scenario as ../02-manual-agentic-loop/, so you can diff the two
demos directly: schema inference from type hints + docstrings, ToolError
instead of an {"error": ...} dict, and client.beta.messages.tool_runner(...)
.until_done() instead of a hand-written while-loop.

Run:
    uv run tool_runner_beta.py
    uv run tool_runner_beta.py --request "Look up vendor VEND-404 and calculate TDS on 50000."
"""

import argparse
import json
import os

import anthropic
from anthropic.lib.tools import ToolError, beta_tool
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise EnvironmentError("ANTHROPIC_API_KEY is not set. Copy .env.example to .env first.")

client = anthropic.Anthropic()
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

VENDOR_DB = {
    "VEND-001": {"name": "SBI Valuers & Associates", "category": "professional_services",
                 "gstin": "27AAACS1234F1Z5", "approved": True},
}
TDS_RATES = {"professional_services": 0.10, "verification_services": 0.02, "goods": 0.01}


@beta_tool
def get_vendor_details(vendor_id: str) -> str:
    """Fetch one vendor's master record by its exact vendor ID.

    Args:
        vendor_id: Exact vendor ID.
    """
    vendor = VENDOR_DB.get(vendor_id)
    if vendor is None:
        raise ToolError(f"No vendor found with ID '{vendor_id}'")
    return json.dumps({"vendor_id": vendor_id, **vendor})


@beta_tool
def calculate_tds(amount_inr: float, category: str) -> str:
    """Calculate TDS and net payable for an invoice amount and vendor category.

    Args:
        amount_inr: Invoice amount in INR.
        category: Vendor's payment category (professional_services, verification_services, goods).
    """
    rate = TDS_RATES.get(category)
    if rate is None:
        raise ToolError(f"Unknown category '{category}'. Valid: {list(TDS_RATES)}")
    tds_amount = round(amount_inr * rate, 2)
    return json.dumps({"tds_rate_pct": rate * 100, "tds_amount_inr": tds_amount,
                        "net_payable_inr": round(amount_inr - tds_amount, 2)})


TOOLS = [get_vendor_details, calculate_tds]

SYSTEM_PROMPT = (
    "You are a vendor-payments assistant. Always call get_vendor_details before assuming a "
    "vendor's category, and always call calculate_tds before stating a TDS amount. If a tool "
    "reports an error, explain it plainly instead of making up a value."
)


def run_agent(user_message: str) -> str:
    result = client.beta.messages.tool_runner(
        model=MODEL, max_tokens=512, system=SYSTEM_PROMPT, tools=TOOLS,
        messages=[{"role": "user", "content": user_message}],
    ).until_done()
    return next((b.text for b in result.content if b.type == "text"), "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request",
        default="Look up vendor VEND-001 and tell me the TDS and net payable on an invoice for 92000.",
        help="The request to send to the agent.",
    )
    args = parser.parse_args()

    print(f"Request: {args.request}")
    print("\n(the tool_runner drives the loop internally — no per-iteration prints here; "
          "compare against ../02-manual-agentic-loop/'s [loop iteration N] trace)")
    answer = run_agent(args.request)
    print(f"\n=== Final answer ===\n{answer}")


if __name__ == "__main__":
    main()
