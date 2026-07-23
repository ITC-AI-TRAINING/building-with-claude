# Apex Bank — Vendor Invoice Batch

Five invoices for Lab 5's invoice-validation exercise, cross-referencing
[`apex_bank_vendor_master.md`](apex_bank_vendor_master.md). One is clean, one exceeds the
Finance Controller sign-off threshold, and three are deliberate failure cases — a GSTIN
mismatch, an expired empanelment, and an unapproved vendor — so the agent's tool calls have to
actually catch something, not just confirm a happy path.

| Invoice ID | Vendor ID | Invoice date | GSTIN on invoice | Amount (INR) | PO reference | Description |
|---|---|---|---|---|---|---|
| `INV-2026-0101` | `VEND-001` | 2026-07-05 | `27AAACS1234F1Z5` | 185,000 | `PO-4471` | Property valuation — home loan HL-20458 |
| `INV-2026-0102` | `VEND-002` | 2026-07-08 | `07AABCM5678G1Z9` | 92,000 | `PO-4483` | Legal opinion — loan agreement review |
| `INV-2026-0103` | `VEND-003` | 2026-07-10 | `29AACFA9012H1Z8` | 45,000 | `PO-4490` | Field verification — 12 applicant addresses |
| `INV-2026-0104` | `VEND-004` | 2026-07-11 | `19AADCB3456J1Z1` | 18,500 | `PO-4492` | Office stationery — Q3 restock |
| `INV-2026-0105` | `VEND-001` | 2026-07-14 | `27AAACS1234F1Z5` | 1,250,000 | `PO-4501` | Bulk property valuation — 40 properties, Q3 portfolio |

## What each invoice should resolve to

Work these out by hand against `apex_bank_vendor_master.md`'s rules before running the script —
the point of Lab 5 is recognising when the agent's tool-driven answer matches your own:

| Invoice | Expected outcome | Why |
|---|---|---|
| `INV-2026-0101` | **Approve** | Vendor empanelled, GSTIN matches, amount under the sign-off threshold |
| `INV-2026-0102` | **Hold — GSTIN mismatch** | Invoice GSTIN ends `...Z9`; vendor master has `...Z2` |
| `INV-2026-0103` | **Hold — empanelment expired** | Vendor's empanelment lapsed 2026-05-31, before this invoice's 2026-07-10 date |
| `INV-2026-0104` | **Hold — vendor not empanelled** | `VEND-004` is `approved: false` in the vendor master |
| `INV-2026-0105` | **Hold — requires Finance Controller sign-off** | Amount (INR 12,50,000) exceeds the INR 10,00,000 threshold |
