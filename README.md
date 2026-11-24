# FactoryFlow — Order-to-Audit System

**NIT Tiruchirappalli · Centre for Digital Infrastructure · Winter Internship 2026**

A role-based prototype connecting customer orders, approval, GST calculations, dispatch, inventory movements, BOM-based production, purchases, payments, costing and audit exports for a small packaged-snack manufacturer.

> This repository is a prototype, not a production accounting or GST filing system. The acceptance suite uses a disposable SQLite database. The demo PostgreSQL database is kept separate.

## 1. Stack and rationale

- **Backend:** FastAPI + SQLAlchemy. A typed REST API makes transaction rules explicit and provides interactive OpenAPI documentation.
- **Database:** PostgreSQL for the demo deployment. Inventory balances are derived from movement rows rather than manually overwritten quantities.
- **Frontend:** React + Vite. The responsive web interface supports desktop administration and mobile-sized salesman order entry without requiring a native app.
- **Tests:** pytest + FastAPI TestClient against an isolated SQLite database, so acceptance tests never reset the demo PostgreSQL database.

## 2. Roles

| Role | Intended access |
|---|---|
| `salesman` | Create orders; view own orders and own sales CSV |
| `admin` | Purchases, order verification, invoices, dispatch, payments, reports and audit |
| `production` | Production runs and run overheads; read operational data |
| `auditor` | Read-only audit log and receivables; write operations return 403 |

The seeded demo users use `Demo@123` in the supplied CSV seed data. Change demo passwords and the JWT secret before any deployment. Never commit `.env` or credentials.

## 3. Local setup (Windows PowerShell)

### Backend

1. Open PowerShell in `backend`.
2. Create/activate a virtual environment and install dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

3. Create `backend/.env` using `.env.example`. Set `DATABASE_URL` to your PostgreSQL connection string, `JWT_SECRET` to a long random value, and `CORS_ORIGINS=http://localhost:5173`.
4. Ensure the PostgreSQL database has the original tables, then apply `database/migration_full.sql` and load the demo CSV data using the supplied seed/import scripts. For CSV import, copy `database/db_config.py.example` to `database/db_config.py`, set the `PG_*` environment variables (including `PG_PASS`), and run the two import scripts from the `database` directory. Do not use `--reset` on a database containing records you need.
5. Start the API:

```powershell
python -m uvicorn app.main:app --reload
```

API: `http://127.0.0.1:8000` · Swagger: `http://127.0.0.1:8000/docs`.

### Frontend

In a second PowerShell window:

```powershell
cd frontend
npm install
$env:VITE_API_URL="http://127.0.0.1:8000"
npm run dev
```

Open `http://localhost:5173`.

## 4. One-command acceptance test run

The test runner sets `DATABASE_URL` to `sqlite:///./acceptance_test.db`, recreates only that disposable SQLite schema, seeds synthetic users and the benchmark master data, and exercises the API through HTTP. It does **not** connect to or truncate PostgreSQL `DemoDb`.

From the project root in PowerShell, after activating the backend virtual environment:

```powershell
.\backend\.venv\Scripts\Activate.ps1
.\run_final_checks.ps1
```

This runs the backend end-to-end acceptance suite and then installs/builds the React frontend. To run only the API tests, use `backend\run_acceptance_tests.ps1`.

The suite checks purchase posting, BOM production, planned-vs-actual consumption, yield/oil variance, salesman order creation, admin approval, intra-state CGST/SGST, interstate IGST, dispatch, payment/outstanding, production overhead, ledger references, report exports, role restrictions, duplicate dispatch and overpayment rejection.

## 5. Benchmark scenario and results

| Benchmark check | Expected | Seeded demo result |
|---|---:|---:|
| Flour closing | 120 kg | 120 kg |
| Cooking oil closing | 19.5 L | 19.5 L |
| Spice closing | 3.8 kg | 3.8 kg |
| Pouches closing | 306 | 306 |
| Cartons closing | 21 | 21 |
| Finished goods after production | 238 packets | 238 packets before dispatch |
| Finished goods after 150 dispatch | 88 packets | 88 packets |
| Yield variance | −6% | −6% |
| Oil consumption variance | +5% | +5% |
| Retailer A taxable | ₹7,500 | ₹7,500 |
| CGST / SGST | ₹187.50 / ₹187.50 | ₹187.50 / ₹187.50 |
| Invoice total | ₹7,875 | ₹7,875 |
| Payment | ₹4,000 | ₹4,000 |
| Outstanding | ₹3,875 | ₹3,875 |
| Distributor B shortage | 32 packets | 32 packets |

The backend production calculation compares actual material usage with the full BOM batch standard. A run is one complete 200-packet BOM batch; actual output is recorded separately. Thus oil planned = 10 L and actual = 10.5 L, producing +5% consumption variance.

## 6. Inventory and costing design

For each inventory item:

`Closing balance = SUM(all movement deltas for that item)`

Receipts are positive movements; production issues and dispatches are negative movements; production output is a positive finished-goods movement. Every movement created by the current API records `reference_type` and `reference_id` to its source purchase, production run or dispatch. Earlier imported opening/benchmark movements may have null structured references; their source description remains in the ledger. These legacy rows should be backfilled if the dataset is migrated for production use.

Production planned quantities are read from the BOM; actual quantities are entered by the production user. Variance quantity = actual − planned; variance percentage = variance / planned × 100. Yield variance = (good packets − expected packets) / expected packets × 100.

The current costing endpoint records labour and utilities and returns overhead per good packet. It does **not yet** calculate a complete material-plus-overhead unit cost using FIFO or weighted-average valuation. Do not represent the overhead-only number as fully absorbed product cost.

## 7. Implemented scope and known gaps

### Implemented in this prototype
- Authentication and role gates for admin, salesman, production and auditor.
- Customer/product/BOM reads and mobile-responsive order submission UI.
- Admin stock verification, invoice tax split calculation and dispatch posting.
- Purchase receipt and ledger update.
- BOM-driven production with actual consumption, yield and oil variance.
- Payment collection and outstanding balance.
- Labour/utilities overhead capture.
- Stock ledger, audit log, receivables endpoint, sales/stock/production CSV exports.
- Automated acceptance test suite in an isolated test database.

### Known gaps to disclose
- The current invoice API returns invoice values as JSON; a downloadable GST invoice PDF, seller/customer GSTIN fields, HSN code and FY-based invoice numbering are not implemented.
- GST calculations are demonstrated for the benchmark states/rate; this is not a validated GST compliance engine.
- Full material valuation (FIFO/weighted average), fully absorbed cost per packet and margin are not implemented; current per-packet costing is overhead-only.
- Monthly GST summary, purchase register, collections/ageing, PDF reports and owner dashboard are not complete.
- Offline order capture/synchronization, returns, partial dispatch, batch/expiry tracking and invoice credit-note workflow are not implemented.
- Imported benchmark opening movements may lack structured reference IDs; newly posted purchase, production and dispatch movements use them.
- The UI uses a supplier ID field because the current API does not expose a supplier-master listing endpoint.

## 8. Submission checklist

- [ ] Push this project to a public GitHub/GitLab repository with incremental commits.
- [ ] Run `backend/run_acceptance_tests.ps1` and include the real test output in the submission.
- [ ] Capture screenshots of salesman, admin, production and auditor screens.
- [ ] Record an unlisted demo video (maximum 8 minutes) following `docs/demo_script.md`.
- [ ] Add the video and live/local run links to the repository README.
- [ ] Review and explain every known gap above before the interview.

## 9. Security notes

Keep `.env`, JWT secrets, database credentials and real access tokens out of Git. Rotate any database password that has been shared outside your local environment. The included data is synthetic only.
