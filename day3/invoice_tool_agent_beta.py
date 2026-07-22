"""
Lab 5 — Invoice Validation Agent (beta tool_runner)
Module 5: Tool Use and Function Integration

Same task as invoice_tool_agent.py, built with the higher-level beta style:
@beta_tool-decorated functions (schema inferred from type hints + docstring) and
client.beta.messages.tool_runner(...).until_done() instead of a manual while-loop.

Reference data: shared/data/apex_bank_vendor_master.md, shared/data/apex_bank_invoices.md

Run: python invoice_tool_agent_beta.py
"""

import json
import os

import anthropic
from anthropic.lib.tools import ToolError, beta_tool
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise EnvironmentError("ANTHROPIC_API_KEY is not set.")

client = anthropic.Anthropic()
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# ── Mock databases — identical data to invoice_tool_agent.py's VENDOR_DB/INVOICE_DB ─

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
        "vendor_id": "VEND-001", "invoice_date": "2026-07-05",
        "gstin_on_invoice": "27AAACS1234F1Z5", "amount_inr": 185000,
        "po_reference": "PO-4471", "description": "Property valuation - home loan HL-20458",
    },
    "INV-2026-0102": {
        "vendor_id": "VEND-002", "invoice_date": "2026-07-08",
        "gstin_on_invoice": "07AABCM5678G1Z9", "amount_inr": 92000,
        "po_reference": "PO-4483", "description": "Legal opinion - loan agreement review",
    },
    "INV-2026-0103": {
        "vendor_id": "VEND-003", "invoice_date": "2026-07-10",
        "gstin_on_invoice": "29AACFA9012H1Z8", "amount_inr": 45000,
        "po_reference": "PO-4490", "description": "Field verification - 12 applicant addresses",
    },
    "INV-2026-0104": {
        "vendor_id": "VEND-004", "invoice_date": "2026-07-11",
        "gstin_on_invoice": "19AADCB3456J1Z1", "amount_inr": 18500,
        "po_reference": "PO-4492", "description": "Office stationery - Q3 restock",
    },
    "INV-2026-0105": {
        "vendor_id": "VEND-001", "invoice_date": "2026-07-14",
        "gstin_on_invoice": "27AAACS1234F1Z5", "amount_inr": 1250000,
        "po_reference": "PO-4501", "description": "Bulk property valuation - 40 properties, Q3 portfolio",
    },
}

TDS_RATES = {"professional_services": 0.10, "verification_services": 0.02, "goods": 0.01}
SIGN_OFF_THRESHOLD_INR = 1_000_000


# ── Tools — a plain function + docstring is enough; @beta_tool infers the JSON
#    schema from the type hints and reads the description from the docstring. ──

@beta_tool
def get_invoice_details(invoice_id: str) -> str:
    """Fetch one invoice's full record by its exact invoice ID, e.g. 'INV-2026-0101'.

    Args:
        invoice_id: Exact invoice ID.
    """
    invoice = INVOICE_DB.get(invoice_id)
    if invoice is None:
        raise ToolError(f"No invoice found with ID '{invoice_id}'")
    return json.dumps({"invoice_id": invoice_id, **invoice})


@beta_tool
def get_vendor_details(vendor_id: str) -> str:
    """Fetch one vendor's master record by its exact vendor ID, e.g. 'VEND-001'.

    Args:
        vendor_id: Exact vendor ID.
    """
    vendor = VENDOR_DB.get(vendor_id)
    if vendor is None:
        raise ToolError(f"No vendor found with ID '{vendor_id}'")
    return json.dumps({"vendor_id": vendor_id, **vendor})


@beta_tool
def search_invoices(vendor_name: str) -> str:
    """Search invoices by a partial, case-insensitive vendor name.

    Args:
        vendor_name: Full or partial vendor name.
    """
    needle = vendor_name.strip().lower()
    matches = []
    for invoice_id, invoice in INVOICE_DB.items():
        vendor = VENDOR_DB.get(invoice["vendor_id"], {})
        if needle in vendor.get("name", "").lower():
            matches.append({"invoice_id": invoice_id, "vendor_name": vendor.get("name"),
                             "amount_inr": invoice["amount_inr"]})
    if not matches:
        raise ToolError(f"No invoices found for a vendor matching '{vendor_name}'")
    return json.dumps({"matches": matches})


@beta_tool
def calculate_tds(amount_inr: float, category: str) -> str:
    """Calculate the TDS amount and net payable for an invoice.

    Args:
        amount_inr: Invoice amount in INR.
        category: Vendor's payment category, from get_vendor_details
            (professional_services, verification_services, or goods).
    """
    rate = TDS_RATES.get(category)
    if rate is None:
        raise ToolError(f"Unknown vendor category '{category}'. Valid categories: {list(TDS_RATES)}")
    tds_amount = round(amount_inr * rate, 2)
    return json.dumps({
        "tds_rate_pct": rate * 100,
        "tds_amount_inr": tds_amount,
        "net_payable_inr": round(amount_inr - tds_amount, 2),
        "requires_signoff": amount_inr > SIGN_OFF_THRESHOLD_INR,
    })


TOOLS = [get_invoice_details, get_vendor_details, search_invoices, calculate_tds]

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
    result = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=[{"role": "user", "content": user_message}],
    ).until_done()

    return next((b.text for b in result.content if b.type == "text"), "")


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
