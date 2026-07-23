# Apex Bank — Empanelled Vendor Master

Reference data for Lab 5 (Module 5: Tool Use and Function Integration). Four vendors Apex Bank's
loan-operations team pays for property valuation, legal opinions, field verification, and office
supplies. The `invoice_tool_agent.py` / `invoice_tool_agent_beta.py` reference scripts embed this
same data as `VENDOR_DB` — read it here first so you know what a correct tool lookup should return
before you watch an agent call the tool for you.

| Vendor ID | Name | Category | GSTIN | Empanelled? | Empanelment expiry |
|---|---|---|---|---|---|
| `VEND-001` | SBI Valuers & Associates | `professional_services` | `27AAACS1234F1Z5` | Yes | 2027-03-31 |
| `VEND-002` | Metro Legal Associates | `professional_services` | `07AABCM5678G1Z2` | Yes | 2026-12-31 |
| `VEND-003` | Apex Field Verification Services | `verification_services` | `29AACFA9012H1Z8` | Yes | 2026-05-31 |
| `VEND-004` | Bharat Stationery Supplies | `goods` | `19AADCB3456J1Z1` | **No** — empanelment lapsed, not renewed | 2027-01-31 |

## TDS deduction reference (used by the `calculate_tds` tool)

Tax Deducted at Source is withheld from every vendor payment before disbursal, at a rate that
depends on the vendor's payment category:

| Category | TDS rate |
|---|---|
| `professional_services` | 10% |
| `verification_services` | 2% |
| `goods` | 1% |

## Vendor payment rules (used by the agent's system prompt)

1. A vendor must be **empanelled** (`approved: true`) to be paid at all.
2. The **empanelment expiry date must be on or after the invoice date** — an invoice dated after
   expiry is treated the same as a non-empanelled vendor, even if the vendor was empanelled when
   the underlying work was performed.
3. The **GSTIN on the invoice must exactly match the GSTIN on the vendor master** — a mismatch
   (even a single-character difference) blocks payment until Finance re-verifies the vendor's tax
   registration.
4. Any single invoice for **more than INR 10,00,000 (ten lakh)** requires Finance Controller
   sign-off before payment, regardless of vendor status or GSTIN match.

Note `VEND-003`'s empanelment expired **2026-05-31** — any invoice from Apex Field Verification
Services dated after that (see `apex_bank_invoices.md`) is a deliberate edge case for the lab, the
same way Module 2's Lab 2 used a near-miss question to test the fallback path.
