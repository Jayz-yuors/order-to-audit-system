
# FactoryFlow — Order-to-Audit System

**NIT Tiruchirappalli | Centre for Digital Infrastructure | Winter Internship 2026**

A role-based web application prototype connecting customer orders, admin approval, GST calculations, dispatch, inventory movements, BOM-based production, purchases, payments, costing and audit reporting for a small packaged-snack manufacturer.

---

## Project Author

**Jay Keluskar**

- **Degree:** B.Tech — Computer Engineering Third Year
- **Institute:** Vidyalankar Institute of Technology
- **University:** Mumbai University
- **GitHub:** [Jayz-yuors](https://github.com/Jayz-yuors)
- **LinkedIn:** [Jay Keluskar](https://www.linkedin.com/in/jay-keluskar-b17601358/)

**Project:** FactoryFlow — Order-to-Audit System  
**Organization:** Centre for Digital Infrastructure, NIT Tiruchirappalli  
**Program:** Winter Internship 2026

---

## 1. Project Overview

Small-scale food manufacturers often manage sales, production, inventory, invoicing and accounts using disconnected spreadsheets, notebooks and applications. This results in duplicate data entry, stock discrepancies, unnoticed production wastage and time-consuming monthly audits.

FactoryFlow addresses this problem through a centralized application that connects business transactions across sales, production, inventory and accounts.

### Sales Workflow

Salesman Order → Admin Verification → GST Calculation → Invoice → Dispatch → Finished Goods Deduction → Receivables

### Production Workflow

Purchase → Raw Material Inventory → BOM-Based Production → Actual Consumption → Finished Goods Addition → Variance Analysis → Costing

Both workflows contribute to inventory tracking and audit-oriented reporting.

> **Note:** FactoryFlow is an academic internship prototype, not a production accounting application or a government-validated GST filing system. The acceptance test suite uses a disposable SQLite database, separate from the PostgreSQL demonstration database.

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React, Vite, CSS | Responsive role-based interface |
| Backend | Python, FastAPI | REST APIs and business logic |
| ORM | SQLAlchemy | Database operations |
| Database | PostgreSQL | Persistent application data |
| Testing | pytest, FastAPI TestClient | Automated acceptance testing |
| Test Database | SQLite | Isolated test execution |
| API Documentation | Swagger / OpenAPI | Interactive API exploration |
| Version Control | Git, GitHub | Source code management |

### Technology Rationale

FastAPI provides a structured REST API with interactive documentation, while SQLAlchemy supports database operations and transaction management. PostgreSQL provides persistent relational storage, and React with Vite provides a responsive interface for desktop administration and mobile-sized salesman workflows.

Inventory is represented through stock movement records rather than relying solely on manually overwritten quantities.

---

## 3. Application Roles

| Role | Responsibilities |
|---|---|
| Salesman | Submit customer orders and access relevant sales information |
| Admin | Verify orders, manage purchases, invoices, dispatches, payments and reports |
| Production | Record production runs, material consumption and overheads |
| Auditor | Read-only access to audit-oriented information and receivables |

Role-based authorization is implemented at the API level. The auditor role is restricted from write operations, with unauthorized write requests returning HTTP 403.

### Demo Credentials

The supplied synthetic seed data uses the following demo password:

`Demo@123`

Use the seeded usernames for the respective roles. These credentials are intended only for local demonstration. Change demo passwords and the JWT secret before deployment.

Never commit local environment files or real credentials.

---

## 4. Implemented Features

### 4.1 Sales and Order Management

- Role-based authentication and authorization.
- Customer and product selection.
- Salesman order submission through the web interface.
- Admin-side order verification and approval.
- Finished-goods availability checks.
- Order status and dispatch tracking.
- Customer-specific order information.

### 4.2 GST Billing and Dispatch

- Taxable value calculation.
- Intra-state CGST and SGST calculation.
- Interstate IGST calculation.
- Invoice records associated with customer orders.
- Dispatch processing with corresponding finished-goods stock deduction.
- Backend validation against duplicate dispatch operations.

### 4.3 BOM-Based Production

- Product-specific Bill of Materials.
- Expected production output based on BOM batch quantities.
- Recording actual raw-material consumption.
- Recording actual good output and wastage.
- Automatic raw-material deduction and finished-goods addition.
- Planned-versus-actual material consumption comparison.
- Yield and material consumption variance calculations.
- Variance alerts for production deviations.

### 4.4 Inventory Management

Separate inventory tracking for:

- Raw materials such as flour, oil and spices.
- Packaging materials such as pouches and cartons.
- Finished goods by product and pack size.

Inventory movements include purchase receipts, production issues, production output and dispatch deductions.

### 4.5 Purchases and Supplier Records

- Purchase recording.
- Supplier-related records.
- Raw-material receipt processing.
- Inventory updates from purchase transactions.

### 4.6 Payments and Receivables

- Recording customer payments.
- Payment association with invoices.
- Outstanding balance calculation.
- Receivables reporting.

### 4.7 Production Costing

- Labour overhead recording.
- Utilities and power overhead recording.
- Overhead allocation per good packet.

### 4.8 Audit and Reports

- Inventory ledger.
- Audit log.
- Sales register export.
- Stock report export.
- Production report export.
- Receivables reporting.
- Role-restricted audit access.

CSV exports are available for the implemented report endpoints.

---

## 5. Mandatory Benchmark Scenario

The application includes the benchmark master data and expected results specified in the NIT Tiruchirappalli problem statement.

### Benchmark Production Configuration

**Product:** Murukku 200 g  
**Expected Batch Output:** 200 packets

| Material | Standard Quantity | Actual Quantity |
|---|---:|---:|
| Flour | 40 kg | 40 kg |
| Cooking Oil | 10 L | 10.5 L |
| Salt and Spice Mix | 1.2 kg | 1.2 kg |
| 200 g Pouches | 200 pieces | 194 pieces consumed, including 6 damaged |
| Cartons | 10 pieces | 9 pieces |

### Verified Benchmark Results

| Benchmark Check | Expected Result | Seeded Demo Result |
|---|---:|---:|
| Flour closing balance | 120 kg | 120 kg |
| Cooking oil closing balance | 19.5 L | 19.5 L |
| Spice closing balance | 3.8 kg | 3.8 kg |
| Pouches closing balance | 306 | 306 |
| Cartons closing balance | 21 | 21 |
| Finished goods after production | 238 packets | 238 packets |
| Finished goods after Retailer A dispatch | 88 packets | 88 packets |
| Yield variance | -6% | -6% |
| Oil consumption variance | +5% | +5% |
| Retailer A taxable value | ₹7,500 | ₹7,500 |
| CGST | ₹187.50 | ₹187.50 |
| SGST | ₹187.50 | ₹187.50 |
| Invoice total | ₹7,875 | ₹7,875 |
| Payment received | ₹4,000 | ₹4,000 |
| Outstanding balance | ₹3,875 | ₹3,875 |
| Distributor B shortage | 32 packets | 32 packets |

### Production Variance Calculation

- Yield variance = (188 - 200) / 200 × 100 = **-6%**
- Oil consumption variance = (10.5 - 10) / 10 × 100 = **+5%**

The production calculation compares actual consumption against the full BOM batch standard. Actual good output is recorded separately from expected output.

The figures above describe the seeded demonstration data and verified API results. They should not be interpreted as a claim that every benchmark step was successfully demonstrated in the recorded video.

---

## 6. Inventory and Data Design

Inventory is represented through stock movement records.

**Closing Balance = Sum of all movement deltas for an inventory item**

- Purchase receipts create positive movements.
- Production material issues create negative movements.
- Production output creates positive finished-goods movements.
- Dispatch creates negative finished-goods movements.

Each movement created by the current transaction APIs records a source reference through `reference_type` and `reference_id`, linking it to the relevant purchase, production run or dispatch.

Some previously imported opening and benchmark movements have null structured references. Their source descriptions remain available in the ledger. These legacy records should be backfilled for complete traceability.

### Production Variance Calculations

Material variance quantity:

`Actual Consumption - Planned Consumption`

Material variance percentage:

`(Actual - Planned) / Planned × 100`

Yield variance:

`(Actual Good Output - Expected Output) / Expected Output × 100`

### Costing Approach

The current implementation records labour and utility overheads and calculates overhead per good packet.

A complete material valuation model using FIFO or weighted-average costing has not yet been implemented. Therefore, the overhead-only result should not be interpreted as the fully absorbed manufacturing cost per packet.

---

## 7. Testing and Verification

The project includes an automated backend acceptance suite using pytest and FastAPI TestClient.

The acceptance environment uses an isolated SQLite database and does not reset the PostgreSQL demonstration database.

The suite covers:

- Purchase posting and stock updates.
- BOM-based production.
- Planned-versus-actual material consumption.
- Yield and oil consumption variance.
- Salesman order creation.
- Admin approval.
- CGST, SGST and IGST calculations.
- Dispatch and finished-goods stock deduction.
- Payment and outstanding calculations.
- Production overhead recording.
- Ledger source references.
- Report exports.
- Role restrictions.
- Duplicate dispatch prevention.
- Overpayment rejection.

### Latest Recorded Automated Checks

| Check | Result |
|---|---|
| Backend end-to-end acceptance test | PASS |
| Frontend dependency installation | PASS |
| React/Vite production build | PASS |

The backend acceptance test completed with **1 passed**. The frontend production build also completed successfully.

These checks establish automated test and build results; they do not imply that every possible live PostgreSQL workflow or every frontend interaction has been manually verified.

---

## 8. Local Installation and Setup Guide

### Prerequisites

Install the following:

- Python 3.12
- PostgreSQL
- Node.js and npm
- Git

### Step 1 — Clone the Repository

```powershell
git clone https://github.com/Jayz-yuors/order-to-audit-system.git
cd order-to-audit-system
```

Replace the repository URL if you choose a different repository name.

### Step 2 — Configure the Backend Environment

From the project root:

```powershell
cd backend

py -3.12 -m venv .venv

Set-ExecutionPolicy -Scope Process Bypass

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install -r requirements.txt
```

### Step 3 — Configure Environment Variables

Create a local `backend/.env` using the supplied `backend/.env.example`.

Configure:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/DemoDb
JWT_SECRET=YOUR_LONG_RANDOM_SECRET
CORS_ORIGINS=http://localhost:5173
```

Use your own PostgreSQL credentials and a securely generated JWT secret. Do not commit this file.

### Step 4 — Initialize and Seed PostgreSQL

Ensure PostgreSQL is running and the required database exists.

Apply the database migration:

```powershell
cd ..

psql -U postgres -d DemoDb -f database/migration_full.sql
```

Configure the database import environment using the supplied example:

```powershell
Copy-Item database/db_config.py.example database/db_config.py
```

Set the required PostgreSQL environment variables, including `PG_PASS`, using your local database credentials.

Run the supplied import scripts from the database directory:

```powershell
cd database

python import_csv_data.py

python import_extended_csv_data.py
```

**Important:** Review the migration and import scripts before running them against any database containing records you need. Do not use reset options on an existing database without a backup.

### Step 5 — Start the Backend

From the project root:

```powershell
cd backend

.\.venv\Scripts\Activate.ps1

python -m uvicorn app.main:app --reload
```

Backend:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

### Step 6 — Start the Frontend

Open a second VS Code terminal:

```powershell
cd frontend

npm install

$env:VITE_API_URL="http://127.0.0.1:8000"

npm run dev
```

Open:

`http://localhost:5173`

---

## 9. Automated Acceptance Test

From the project root, activate the backend virtual environment:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

Run the complete verification script:

```powershell
.\run_final_checks.ps1
```

This runs the backend acceptance suite and the frontend production build.

The acceptance test suite uses a disposable SQLite database. It is designed to avoid resetting or modifying the PostgreSQL demonstration database.

To run the backend tests separately:

```powershell
cd backend

python -m pytest tests/test_acceptance.py -v
```

---

## 10. Room for Further Improvement

The current prototype covers the central sales and production workflows. The following areas provide opportunities for further development:

1. **Extended GST Documentation and Reporting:** Add downloadable GST invoice PDFs with GSTIN, HSN and financial-year-based invoice numbering, alongside more comprehensive monthly GST and purchase reports.

2. **Advanced Manufacturing Costing and Traceability:** Implement FIFO or weighted-average material valuation for fully absorbed product costing, and backfill structured source references for legacy inventory movements.

---

## 11. Demonstration Video

The following video demonstrates the FactoryFlow frontend and its major application modules.

**Project Demonstration:**

[Watch the FactoryFlow Demonstration Video](https://drive.google.com/file/d/1wVNhME4Ev9gz6m6I1MseISQ4-TQdg0u5/view?usp=sharing)

---

## 12. Submission Checklist

- [x] Backend implementation and automated acceptance test suite.
- [x] React frontend and successful production build.
- [x] Role-based application access.
- [x] Benchmark master data and seeded results.
- [x] Database migration and seed/import scripts.
- [x] Project README and design documentation.
- [x] Frontend demonstration video.
- [x] Publish the source code in a public GitHub repository.
- [ ] Verify clean-machine setup and add the final repository URL.
- [ ] Complete remaining submission-specific checks.

---

## 13. Security and Data Disclaimer

- The supplied benchmark and demo records are synthetic.
- Never commit `.env` files, database passwords, JWT secrets or access tokens.
- Rotate credentials if they have been exposed outside the local development environment.
- Do not use this prototype as a production accounting, statutory GST filing or financial reporting system without further validation.

---

**FactoryFlow — Connecting Sales, Production, Inventory and Audit.**

Developed as an individual project for the **Centre for Digital Infrastructure, NIT Tiruchirappalli — Winter Internship 2026**.
