# 8-minute demo walkthrough

**0:00–0:30 — Context**
- State the problem: two connected loops, sales and production, meeting at finished-goods stock.
- Show the role-based login screen and explain the API/database stack.

**0:30–1:30 — Salesman order entry**
- Sign in as `sales_a`.
- Select Retailer A and submit 150 packets.
- Show the salesman sees their own order/status.

**1:30–2:30 — Production / BOM**
- Sign in as production supervisor.
- Show Murukku 200 g BOM: flour 40 kg, oil 10 L, spice 1.2 kg, 200 pouches, 10 cartons.
- Demonstrate a 188-good-packet run, 6 damaged pouches, actual oil 10.5 L and other actual consumption.
- Explain −6% yield and +5% oil variance.

**2:30–3:30 — Inventory**
- Show ledger-derived stock balances after purchase and production: flour 120 kg, oil 19.5 L, pouches 306, cartons 21, finished goods 238 before dispatch.

**3:30–5:00 — Admin verification, GST and dispatch**
- Sign in as admin.
- Verify Retailer A order; show stock sufficiency.
- Generate invoice JSON values: taxable ₹7,500, CGST ₹187.50, SGST ₹187.50, total ₹7,875.
- Dispatch invoice and show finished stock decreases to 88.

**5:00–5:45 — Shortage handling**
- Show Distributor B order for 120 packets; shortage is 32 and it cannot be invoiced while stock is insufficient.

**5:45–6:30 — Collections and overhead**
- Record ₹4,000 payment; show ₹3,875 outstanding.
- Record ₹1,200 labour and ₹600 utilities; explain overhead-only cost limitation.

**6:30–7:30 — Auditor and reports**
- Sign in as auditor; show read-only access, audit log and receivables.
- Download sales, stock and production CSV reports.

**7:30–8:00 — Close**
- Summarize the benchmark results and explicitly mention known gaps: GST PDF/GSTIN/HSN, full material costing, ageing/GST reports and offline sync.
