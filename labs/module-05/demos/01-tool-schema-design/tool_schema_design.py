"""
Tool Schema Design — Database, Search, and Calculator Patterns
Module 5: Tool Use and Function Integration
Based on: day3/invoice_tool_agent.py

Shows the anatomy of a tool definition and what happens on each side of a
tool_use / tool_result exchange — WITHOUT calling Claude at all. A fixed list
of simulated tool_use blocks (the shape Claude's API response would contain)
is dispatched by hand, including one that's missing a required argument, so
you can see schema validation catch a bad call before your code ever runs it.

Run:
    uv run tool_schema_design.py                       # walk all 5 scenarios
    uv run tool_schema_design.py --tool calculate_tds --args '{"amount_inr": 92000, "category": "professional_services"}'
"""

import argparse
import json

# ── Mock data — the same shape as day3/invoice_tool_agent.py's VENDOR_DB/INVOICE_DB ─

VENDOR_DB = {
    "VEND-001": {"name": "SBI Valuers & Associates", "category": "professional_services",
                 "gstin": "27AAACS1234F1Z5", "approved": True},
    "VEND-002": {"name": "Metro Legal Associates", "category": "professional_services",
                 "gstin": "07AABCM5678G1Z2", "approved": True},
}
TDS_RATES = {"professional_services": 0.10, "verification_services": 0.02, "goods": 0.01}


# ── Tool implementations — one of each pattern from the course design ──────

def get_vendor_details(vendor_id: str) -> dict:
    """Database pattern: exact-key lookup."""
    vendor = VENDOR_DB.get(vendor_id)
    if vendor is None:
        return {"error": f"No vendor found with ID '{vendor_id}'"}
    return {"vendor_id": vendor_id, **vendor}


def search_vendors(name_contains: str) -> dict:
    """Search pattern: partial, case-insensitive match, zero-to-many results."""
    needle = name_contains.strip().lower()
    matches = [{"vendor_id": vid, **v} for vid, v in VENDOR_DB.items()
               if needle in v["name"].lower()]
    return {"matches": matches} if matches else {"error": f"No vendor matches '{name_contains}'"}


def calculate_tds(amount_inr: float, category: str) -> dict:
    """Calculator pattern: pure computation, no lookup."""
    rate = TDS_RATES.get(category)
    if rate is None:
        return {"error": f"Unknown category '{category}'. Valid: {list(TDS_RATES)}"}
    tds_amount = round(amount_inr * rate, 2)
    return {"tds_rate_pct": rate * 100, "tds_amount_inr": tds_amount,
             "net_payable_inr": round(amount_inr - tds_amount, 2)}


TOOL_FUNCTIONS = {
    "get_vendor_details": get_vendor_details,
    "search_vendors": search_vendors,
    "calculate_tds": calculate_tds,
}

# The three input_schema dicts, exactly as they'd appear in a real `tools=[...]`
# parameter — see day3/invoice_tool_agent.py for the full TOOLS list this is drawn from.
TOOL_SCHEMAS = {
    "get_vendor_details": {
        "pattern": "database",
        "description": "Fetch one vendor's master record by its exact vendor ID.",
        "input_schema": {
            "type": "object",
            "properties": {"vendor_id": {"type": "string"}},
            "required": ["vendor_id"],
        },
    },
    "search_vendors": {
        "pattern": "search",
        "description": "Find vendors by a partial, case-insensitive name match.",
        "input_schema": {
            "type": "object",
            "properties": {"name_contains": {"type": "string"}},
            "required": ["name_contains"],
        },
    },
    "calculate_tds": {
        "pattern": "calculator",
        "description": "Calculate TDS and net payable for an invoice amount and category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount_inr": {"type": "number"},
                "category": {"type": "string", "enum": list(TDS_RATES)},
            },
            "required": ["amount_inr", "category"],
        },
    },
}


def validate_against_schema(tool_name: str, args: dict) -> str | None:
    """A deliberately minimal required-field + type check — real validation is
    the API's job, but this is enough to show WHY a schema exists at all."""
    schema = TOOL_SCHEMAS[tool_name]["input_schema"]
    for field in schema["required"]:
        if field not in args:
            return f"missing required field '{field}'"
    for field, value in args.items():
        expected = schema["properties"].get(field, {}).get("type")
        if expected == "string" and not isinstance(value, str):
            return f"field '{field}' must be a string, got {type(value).__name__}"
        if expected == "number" and not isinstance(value, (int, float)):
            return f"field '{field}' must be a number, got {type(value).__name__}"
    return None


def dispatch(tool_name: str, args: dict) -> None:
    """Simulate one tool_use block → tool_result round trip, printed step by step."""
    schema = TOOL_SCHEMAS[tool_name]
    print(f"\n--- Simulated tool_use: {tool_name} ({schema['pattern']} pattern) ---")
    print(f"description : {schema['description']}")
    print(f"input       : {json.dumps(args)}")

    error = validate_against_schema(tool_name, args)
    if error:
        result = {"error": f"Schema validation failed — {error}"}
        is_error = True
    else:
        result = TOOL_FUNCTIONS[tool_name](**args)
        is_error = "error" in result

    tool_result = {"type": "tool_result", "tool_use_id": "toolu_demo01",
                    "content": json.dumps(result), "is_error": is_error}
    print(f"tool_result : {json.dumps(tool_result, indent=2)}")


SCENARIOS = [
    ("get_vendor_details", {"vendor_id": "VEND-001"}),                       # database — hit
    ("get_vendor_details", {"vendor_id": "VEND-999"}),                       # database — miss
    ("search_vendors", {"name_contains": "Legal"}),                          # search — one match
    ("calculate_tds", {"amount_inr": 185000, "category": "professional_services"}),  # calculator
    ("calculate_tds", {"category": "professional_services"}),                # missing required field
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=list(TOOL_SCHEMAS), help="Run one tool with --args instead of the scripted scenarios")
    parser.add_argument("--args", help="JSON object of arguments, e.g. '{\"vendor_id\": \"VEND-001\"}'")
    parsed = parser.parse_args()

    if parsed.tool:
        args = json.loads(parsed.args) if parsed.args else {}
        dispatch(parsed.tool, args)
        return

    print("Walking all 5 scripted scenarios (one per pattern, plus one schema violation):")
    for tool_name, args in SCENARIOS:
        dispatch(tool_name, args)


if __name__ == "__main__":
    main()
