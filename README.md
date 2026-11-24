
<div align="center">

# ⚙️ FactoryFlow
### Order-to-Audit Management System

**From Salesman Order to Production, Inventory & Audit — One Connected System.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org/)
[![Vite](https://img.shields.io/badge/Vite-Build-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![pytest](https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)

**NIT Tiruchirappalli · Centre for Digital Infrastructure · Winter Internship 2026**

[🎥 Demo Video](https://drive.google.com/file/d/1wVNhME4Ev9gz6m6I1MseISQ4-TQdg0u5/view?usp=sharing) · [GitHub](https://github.com/Jayz-yuors) · [LinkedIn](https://www.linkedin.com/in/jay-keluskar-b17601358/)

</div>

---

## 👨‍💻 Project Author

**Jay Keluskar**  
B.Tech Computer Engineering · Third Year  
**Vidyalankar Institute of Technology, Mumbai University**

[![GitHub](https://img.shields.io/badge/GitHub-Jayz--yuors-181717?logo=github)](https://github.com/Jayz-yuors)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Jay_Keluskar-0A66C2?logo=linkedin)](https://www.linkedin.com/in/jay-keluskar-b17601358/)

---

## 🎯 About the Project

Small food manufacturers often manage sales, production, inventory, billing and accounts using disconnected spreadsheets and manual records. This creates stock discrepancies, unnoticed wastage, duplicate entries and complicated month-end audits.

**FactoryFlow** is a role-based web application prototype designed to connect these operations through a centralized workflow.

It brings together two interconnected business processes:

```text
       SALES WORKFLOW
       ──────────────
  Salesman Order
        ↓
  Admin Verification
        ↓
  GST Invoice
        ↓
     Dispatch
        ↓
  Finished Stock Deduction
        ↓
  Payments & Receivables


      PRODUCTION WORKFLOW
      ───────────────────
       Raw Material Purchase
                ↓
          Inventory Receipt
                ↓
          BOM-Based Production
                ↓
       Planned vs Actual Usage
                ↓
          Finished Goods
                ↓
       Yield & Cost Analysis
```

**Core objective:** Record business transactions once and make their impact visible across inventory, production, sales and audit reporting.

---

## ✨ Key Features

| Module | Capabilities |
|:---|:---|
| 🔐 Authentication | Role-based login and access control |
| 🛒 Sales | Customer selection, order submission and tracking |
| ✅ Order Management | Admin verification, approval and stock checks |
| 🧾 GST Billing | Taxable value, CGST, SGST and IGST calculations |
| 🚚 Dispatch | Finished-goods stock deduction |
| 🏭 Production | BOM-based production and actual consumption |
| 📦 Inventory | Raw materials, packaging and finished goods |
| 📥 Purchases | Supplier-related purchase recording and stock receipts |
| 💰 Accounts | Payment recording and outstanding balances |
| 📊 Costing | Labour and utilities overhead per good packet |
| 🔍 Audit | Inventory ledger, audit log and report exports |

### 👥 Role-Based Access

| Role | Access |
|:---|:---|
| Salesman | Order creation and relevant sales information |
| Admin | Orders, purchases, invoices, dispatch, payments and reports |
| Production | Production runs, material consumption and overheads |
| Auditor | Read-only audit-oriented information and receivables |

Auditor write operations are restricted at the API level and return HTTP `403`.

---

## 🧠 Technology Architecture

<div align="center">

| Frontend | Backend | Database |
|:---:|:---:|:---:|
| React + Vite | FastAPI + Python | PostgreSQL |
| Responsive UI | REST APIs | SQLAlchemy ORM |

**Testing:** pytest · FastAPI TestClient · SQLite

</div>

- **React + Vite:** Responsive interface for desktop administration and mobile-sized salesman workflows.
- **FastAPI:** REST API, business logic and interactive OpenAPI documentation.
- **SQLAlchemy:** Database models and transaction operations.
- **PostgreSQL:** Persistent application data.
- **SQLite:** Isolated database for automated acceptance tests.

**Design principle:** Inventory is represented through stock movements rather than relying solely on manually overwritten stock quantities.

---

## 📈 Benchmark Results — NIT Trichy

The application includes the prescribed Murukku 200 g benchmark scenario.

**Production configuration**

| Material | BOM Standard | Actual |
|:---|---:|---:|
| Flour | 40 kg | 40 kg |
| Cooking Oil | 10 L | 10.5 L |
| Spice Mix | 1.2 kg | 1.2 kg |
| Pouches | 200 | 194 consumed, including 6 damaged |
| Cartons | 10 | 9 |

### Verified Benchmark Output

| Evaluation Metric | Expected | Seeded Result |
|:---|---:|---:|
| Flour closing stock | 120 kg | 120 kg |
| Oil closing stock | 19.5 L | 19.5 L |
| Spice closing stock | 3.8 kg | 3.8 kg |
| Pouches closing stock | 306 | 306 |
| Cartons closing stock | 21 | 21 |
| Finished stock after production | 238 | 238 |
| Finished stock after dispatch | 88 | 88 |
| Yield variance | -6% | -6% |
| Oil variance | +5% | +5% |
| Taxable invoice value | ₹7,500 | ₹7,500 |
| CGST + SGST | ₹375 | ₹375 |
| Invoice total | ₹7,875 | ₹7,875 |
| Payment received | ₹4,000 | ₹4,000 |
| Outstanding | ₹3,875 | ₹3,875 |
| Distributor B shortage | 32 packets | 32 packets |

<details>
<summary><b>🔬 View calculation methodology</b></summary>

**Yield variance**

`(188 - 200) / 200 × 100 = -6%`

**Oil consumption variance**

`(10.5 - 10) / 10 × 100 = +5%`

**Inventory calculation**

`Closing Stock = Sum of all movement deltas`

- Purchase receipts: positive movement.
- Production issues: negative movement.
- Production output: positive movement.
- Dispatch: negative movement.

The production calculation compares actual material usage against the full BOM batch standard.

The figures above represent seeded demonstration data and verified API results, not a claim that every benchmark step was successfully demonstrated in the recorded video.

</details>

---

## 🧪 Testing & Verification

The project includes an automated end-to-end acceptance suite using pytest and FastAPI TestClient.

<details>
<summary><b>View acceptance test coverage</b></summary>

- Purchase posting and inventory updates.
- BOM-based production.
- Planned vs actual material consumption.
- Yield and oil variance.
- Salesman order creation.
- Admin approval.
- CGST, SGST and IGST calculations.
- Dispatch and finished-goods deduction.
- Payment and outstanding calculations.
- Production overhead recording.
- Ledger source references.
- Report exports.
- Role restrictions.
- Duplicate dispatch prevention.
- Overpayment rejection.

</details>

| Verification | Result |
|:---|:---:|
| Backend acceptance test | ✅ PASS |
| Frontend dependency installation | ✅ PASS |
| React/Vite production build | ✅ PASS |

**Latest recorded backend test:** `1 passed`

The acceptance suite uses a disposable SQLite database and does not reset the PostgreSQL demonstration database.

---

## 🚀 Getting Started

### Prerequisites

`Python 3.12` · `PostgreSQL` · `Node.js & npm` · `Git`

### 1. Clone the repository

```powershell
git clone https://github.com/Jayz-yuors/order-to-audit-system.git
cd order-to-audit-system
```

### 2. Backend setup

```powershell
cd backend

py -3.12 -m venv .venv

Set-ExecutionPolicy -Scope Process Bypass

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install -r requirements.txt
```

### 3. Configure environment variables

Create `backend/.env` using `backend/.env.example`.

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/DemoDb
JWT_SECRET=YOUR_LONG_RANDOM_SECRET
CORS_ORIGINS=http://localhost:5173
```

Use your own PostgreSQL credentials and a secure JWT secret. Never commit `.env` files.

### 4. Database migration and seeding

Ensure PostgreSQL is running and the required database exists.

From the project root:

```powershell
psql -U postgres -d DemoDb -f database/migration_full.sql

Copy-Item database/db_config.py.example database/db_config.py
```

Configure the required PostgreSQL environment variables, including `PG_PASS`.

Then run:

```powershell
cd database

python import_csv_data.py
python import_extended_csv_data.py
```

> ⚠️ Review migration and import scripts before running them against an existing database. Do not use reset options on data you need to preserve.

### 5. Start the backend

From the project root:

```powershell
cd backend

.\.venv\Scripts\Activate.ps1

python -m uvicorn app.main:app --reload
```

Backend: `http://127.0.0.1:8000`  
Swagger: `http://127.0.0.1:8000/docs`

### 6. Start the frontend

Open a second terminal:

```powershell
cd frontend

npm install

$env:VITE_API_URL="http://127.0.0.1:8000"

npm run dev
```

Frontend: `http://localhost:5173`

---

## 🧰 Run Automated Checks

From the project root:

```powershell
.\backend\.venv\Scripts\Activate.ps1

.\run_final_checks.ps1
```

This runs the backend acceptance suite and frontend production build.

To run only backend tests:

```powershell
cd backend

python -m pytest tests/test_acceptance.py -v
```

---

## 🎥 Project Demonstration

<div align="center">

### FactoryFlow — Frontend Walkthrough

[![Watch Demo](https://img.shields.io/badge/▶-Watch_Project_Demo-red?style=for-the-badge&logo=google-drive)](https://drive.google.com/file/d/1wVNhME4Ev9gz6m6I1MseISQ4-TQdg0u5/view?usp=sharing)

**[Open Demonstration Video](https://drive.google.com/file/d/1wVNhME4Ev9gz6m6I1MseISQ4-TQdg0u5/view?usp=sharing)**

</div>

---

## 🛠️ Future Improvements

1. **Extended GST Reporting:** Downloadable GST invoice PDFs with GSTIN, HSN and financial-year-based invoice numbering, plus more comprehensive monthly GST and purchase reports.
2. **Advanced Costing & Traceability:** FIFO/weighted-average material valuation for fully absorbed product costing and structured references for legacy inventory movements.

---

## 📁 Project Structure

```text
FactoryFlow/
│
├── backend/
│   ├── app/
│   │   └── main.py
│   ├── tests/
│   │   └── test_acceptance.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── database/
│   ├── migration_full.sql
│   ├── schema.sql
│   ├── seed.sql
│   └── seed_data/
│
├── docs/
│   ├── design_note.md
│   └── demo_script.md
│
├── run_final_checks.ps1
└── README.md
```

---

## ⚠️ Scope & Important Notes

- FactoryFlow is an academic prototype, not a production accounting or GST filing system.
- The current invoice API returns JSON; downloadable GST invoice PDFs, GSTIN/HSN fields and FY-based invoice numbering are not implemented.
- Current costing covers labour and utility overhead per good packet, not complete material-plus-overhead valuation.
- Some imported opening and benchmark ledger movements have null structured source references; their descriptions remain available.
- The benchmark results describe seeded data and API verification. The recorded video is a frontend walkthrough, not a complete clean execution of every benchmark step.
- Demo credentials are synthetic. Change passwords and JWT secrets before deployment.

---

<div align="center">

### Built with 💻 for NIT Tiruchirappalli

**FactoryFlow — Connecting Sales, Production, Inventory & Audit.**

*Individual project · Winter Internship 2026*

[GitHub](https://github.com/Jayz-yuors) · [LinkedIn](https://www.linkedin.com/in/jay-keluskar-b17601358/)

</div>
