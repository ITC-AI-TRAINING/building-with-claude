"""
Manual Agentic Loop — the while-loop pattern, isolated
Module 5: Tool Use and Function Integration
Based on: day3/invoice_tool_agent.py

Trims the full invoice agent down to TWO tools (get_vendor_details,
calculate_tds) and two requests — one clean, one that fails a tool lookup —
so the shape of the manual `while` loop is the only thing left to watch.
Every print() traces one loop iteration.

Run:
    uv run manual_agentic_loop.py
    uv run manual_agentic_loop.py --request "Look up vendor VEND-404 and calculate TDS on 50000."
"""

import argparse
import json
import os

import anthropic
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


def get_vendor_details(vendor_id: str) -> dict:
    vendor = VENDOR_DB.get(vendor_id)
    if vendor is None:
        return {"error": f"No vendor found with ID '{vendor_id}'"}
    return {"vendor_id": vendor_id, **vendor}


def calculate_tds(amount_inr: float, category: str) -> dict:
    rate = TDS_RATES.get(category)
    if rate is None:
        return {"error": f"Unknown category '{category}'. Valid: {list(TDS_RATES)}"}
    tds_amount = round(amount_inr * rate, 2)
    return {"tds_rate_pct": rate * 100, "tds_amount_inr": tds_amount,
             "net_payable_inr": round(amount_inr - tds_amount, 2)}


TOOL_FUNCTIONS = {"get_vendor_details": get_vendor_details, "calculate_tds": calculate_tds}

TOOLS = [
    {
        "name": "get_vendor_details",
        "description": "Fetch one vendor's master record by its exact vendor ID.",
        "input_schema": {
            "type": "object",
            "properties": {"vendor_id": {"type": "string"}},
            "required": ["vendor_id"],
        },
    },
    {
        "name": "calculate_tds",
        "description": "Calculate TDS and net payable for an invoice amount and vendor category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount_inr": {"type": "number"},
                "category": {"type": "string", "enum": list(TDS_RATES)},
            },
            "required": ["amount_inr", "category"],
        },
    },
]

SYSTEM_PROMPT = (
    "You are a vendor-payments assistant. Always call get_vendor_details before assuming a "
    "vendor's category, and always call calculate_tds before stating a TDS amount. If a tool "
    "reports an error, explain it plainly instead of making up a value."
)


def run_agent(user_message: str) -> str:
    messages: list[dict] = [{"role": "user", "content": user_message}]
    turn = 0

    while True:
        turn += 1
        print(f"\n[loop iteration {turn}] sending {len(messages)} message(s) to Claude...")

        response = client.messages.create(
            model=MODEL, max_tokens=512, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages,
        )
        print(f"[loop iteration {turn}] stop_reason = {response.stop_reason!r}")

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"[loop iteration {turn}] tool_use: {block.name}({block.input})")
            result = TOOL_FUNCTIONS[block.name](**block.input)
            print(f"[loop iteration {turn}] tool_result: {result}")
            tool_results.append({
                "type": "tool_result", "tool_use_id": block.id,
                "content": json.dumps(result), "is_error": "error" in result,
            })
        messages.append({"role": "user", "content": tool_results})

    return next((b.text for b in response.content if b.type == "text"), "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request",
        default="Look up vendor VEND-001 and tell me the TDS and net payable on an invoice for 92000.",
        help="The request to send to the agent.",
    )
    args = parser.parse_args()

    print(f"Request: {args.request}")
    answer = run_agent(args.request)
    print(f"\n=== Final answer ===\n{answer}")


if __name__ == "__main__":
    main()
