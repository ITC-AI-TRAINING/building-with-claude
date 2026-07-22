"""
Lab 5 — Invoice Validation Agent (manual tool loop)
Module 5: Tool Use and Function Integration

Reference data: shared/data/apex_bank_vendor_master.md, shared/data/apex_bank_invoices.md
See invoice_tool_agent_beta.py for the same task built with the beta tool_runner() instead.

Run: python invoice_tool_agent.py
"""

import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise EnvironmentError("ANTHROPIC_API_KEY is not set.")

client = anthropic.Anthropic()
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# ── Mock databases (mirrors shared/data/apex_bank_vendor_master.md and
#    apex_bank_invoices.md — read those first) ──────────────────────────────

VENDOR_DB = {
    "VEND-001": {
        "name": "SBI Valuers & Associates",
        "category": "professional_services",
        "gstin": "27AAACS1234F1Z5",
        "approved": True,
        "empanelment_expiry": "2027-03-31",
    },
    "VEND-002": {
        "name": "Metro Legal Associates",
        "category": "professional_services",
        "gstin": "07AABCM5678G1Z2",
        "approved": True,
        "empanelment_expiry": "2026-12-31",
    },
    "VEND-003": {
        "name": "Apex Field Verification Services",
        "category": "verification_services",
        "gstin": "29AACFA9012H1Z8",
        "approved": True,
        "empanelment_expiry": "2026-05-31",
    },
    "VEND-004": {
        "name": "Bharat Stationery Supplies",
        "category": "goods",
        "gstin": "19AADCB3456J1Z1",
        "approved": False,
        "empanelment_expiry": "2027-01-31",
    },
}

INVOICE_DB = {
    "INV-2026-0101": {
        "vendor_id": "VEND-001",
        "invoice_date": "2026-07-05",
        "gstin_on_invoice": "27AAACS1234F1Z5",
        "amount_inr": 185000,
        "po_reference": "PO-4471",
        "description": "Property valuation - home loan HL-20458",
    },
    "INV-2026-0102": {
        "vendor_id": "VEND-002",
        "invoice_date": "2026-07-08",
        "gstin_on_invoice": "07AABCM5678G1Z9",  # mismatch vs. vendor master's ...Z2
        "amount_inr": 92000,
        "po_reference": "PO-4483",
        "description": "Legal opinion - loan agreement review",
    },
    "INV-2026-0103": {
        "vendor_id": "VEND-003",
        "invoice_date": "2026-07-10",  # after VEND-003's 2026-05-31 empanelment expiry
        "gstin_on_invoice": "29AACFA9012H1Z8",
        "amount_inr": 45000,
        "po_reference": "PO-4490",
        "description": "Field verification - 12 applicant addresses",
    },
    "INV-2026-0104": {
        "vendor_id": "VEND-004",  # not empanelled
        "invoice_date": "2026-07-11",
        "gstin_on_invoice": "19AADCB3456J1Z1",
        "amount_inr": 18500,
        "po_reference": "PO-4492",
        "description": "Office stationery - Q3 restock",
    },
    "INV-2026-0105": {
        "vendor_id": "VEND-001",
        "invoice_date": "2026-07-14",
        "gstin_on_invoice": "27AAACS1234F1Z5",
        "amount_inr": 1250000,  # exceeds the INR 10,00,000 sign-off threshold
        "po_reference": "PO-4501",
        "description": "Bulk property valuation - 40 properties, Q3 portfolio",
    },
}

TDS_RATES = {
    "professional_services": 0.10,
    "verification_services": 0.02,
    "goods": 0.01,
}

SIGN_OFF_THRESHOLD_INR = 1_000_000


# ── Tool implementations — one calculator, one search, one database lookup ──

def get_invoice_details(invoice_id: str) -> dict:
    """Database lookup: fetch one invoice record by its exact ID."""
    invoice = INVOICE_DB.get(invoice_id)
    if invoice is None:
        return {"error": f"No invoice found with ID '{invoice_id}'"}
    return {"invoice_id": invoice_id, **invoice}


def get_vendor_details(vendor_id: str) -> dict:
    """Database lookup: fetch one vendor record by its exact ID."""
    vendor = VENDOR_DB.get(vendor_id)
    if vendor is None:
        return {"error": f"No vendor found with ID '{vendor_id}'"}
    return {"vendor_id": vendor_id, **vendor}


def search_invoices(vendor_name: str) -> dict:
    """Search: find invoices by a partial, case-insensitive vendor name match."""
    needle = vendor_name.strip().lower()
    matches = []
    for invoice_id, invoice in INVOICE_DB.items():
        vendor = VENDOR_DB.get(invoice["vendor_id"], {})
        if needle in vendor.get("name", "").lower():
            matches.append({"invoice_id": invoice_id, "vendor_name": vendor.get("name"),
                             "amount_inr": invoice["amount_inr"]})
    if not matches:
        return {"error": f"No invoices found for a vendor matching '{vendor_name}'"}
    return {"matches": matches}


def calculate_tds(amount_inr: float, category: str) -> dict:
    """Calculator: apply the TDS rate for a vendor category to an invoice amount."""
    rate = TDS_RATES.get(category)
    if rate is None:
        return {"error": f"Unknown vendor category '{category}'. "
                          f"Valid categories: {list(TDS_RATES)}"}
    tds_amount = round(amount_inr * rate, 2)
    return {
        "tds_rate_pct": rate * 100,
        "tds_amount_inr": tds_amount,
        "net_payable_inr": round(amount_inr - tds_amount, 2),
        "requires_signoff": amount_inr > SIGN_OFF_THRESHOLD_INR,
    }


TOOL_FUNCTIONS = {
    "get_invoice_details": get_invoice_details,
    "get_vendor_details": get_vendor_details,
    "search_invoices": search_invoices,
    "calculate_tds": calculate_tds,
}

TOOLS = [
    {
        "name": "get_invoice_details",
        "description": "Fetch one invoice's full record (vendor ID, date, amount, GSTIN, PO "
                        "reference) by its exact invoice ID, e.g. 'INV-2026-0101'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "description": "Exact invoice ID"},
            },
            "required": ["invoice_id"],
        },
    },
    {
        "name": "get_vendor_details",
        "description": "Fetch one vendor's master record (name, category, GSTIN, empanelment "
                        "status, empanelment expiry) by its exact vendor ID, e.g. 'VEND-001'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "string", "description": "Exact vendor ID"},
            },
            "required": ["vendor_id"],
        },
    },
    {
        "name": "search_invoices",
        "description": "Search invoices by a partial, case-insensitive vendor name — use this "
                        "when you have a vendor name but not an invoice ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_name": {"type": "string", "description": "Full or partial vendor name"},
            },
            "required": ["vendor_name"],
        },
    },
    {
        "name": "calculate_tds",
        "description": "Calculate the Tax Deducted at Source (TDS) amount and net payable for "
                        "an invoice, given its amount and the vendor's payment category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount_inr": {"type": "number", "description": "Invoice amount in INR"},
                "category": {
                    "type": "string",
                    "enum": list(TDS_RATES),
                    "description": "Vendor's payment category, from get_vendor_details",
                },
            },
            "required": ["amount_inr", "category"],
        },
    },
]

SYSTEM_PROMPT = """
You are the invoice-validation agent for Apex Bank's vendor-payments desk.
Your role: decide whether an invoice is ready for payment, using tool calls to look up the
invoice and vendor records rather than guessing at their contents.

CONSTRAINTS:
- Always call get_invoice_details (or search_invoices, if you only have a vendor name) before
  reasoning about an invoice — never assume its amount, date, or GSTIN.
- Always call get_vendor_details for the invoice's vendor before deciding — never assume a
  vendor's empanelment status, GSTIN, or category.
- Always call calculate_tds before approving an invoice — never compute TDS yourself.
- A vendor must have approved = true to be paid at all.
- The vendor's empanelment_expiry must be on or after the invoice's invoice_date.
- The invoice's gstin_on_invoice must exactly match the vendor's gstin (any difference is a
  mismatch, however small).
- If calculate_tds reports requires_signoff = true, the invoice needs Finance Controller
  sign-off regardless of any other check.

FORMAT:
End every invoice review with a line of the exact form:
  DECISION: APPROVE | HOLD - <short reason>
followed by one line giving the net payable amount if approved, or the specific rule that
was violated if held.
"""


def run_agent(user_message: str) -> str:
    messages: list[dict] = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Always append the FULL content list, not content[0].text — dropping the
        # tool_use blocks here silently breaks the next turn's tool_result pairing.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Loop until end_turn — never break out early on stop_reason == "tool_use".
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            func = TOOL_FUNCTIONS[block.name]
            result = func(**block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
                "is_error": "error" in result,
            })
        messages.append({"role": "user", "content": tool_results})

    return next((b.text for b in response.content if b.type == "text"), "")


def main():
    requests = [
        "Validate invoice INV-2026-0101 for payment.",
        "Validate invoice INV-2026-0102 for payment.",
        "Validate invoice INV-2026-0103 for payment.",
        "Validate invoice INV-2026-0104 for payment.",
        "Validate invoice INV-2026-0105 for payment.",
        "I don't have the invoice ID, only that the vendor is 'Metro Legal' — find and "
        "validate their most recent invoice.",
    ]

    for i, request in enumerate(requests, 1):
        print(f"\n{'=' * 70}\n[{i}] {request}\n{'=' * 70}")
        try:
            print(run_agent(request))
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
