# NammaFactory — Order-to-Audit ERP for Small Food Manufacturers

NammaFactory is a role-based, production-oriented ERP prototype designed around the operating workflow of a small food manufacturer. It connects sales orders, GST invoicing, dispatch, inventory movements, purchases, production, costing, payments, reconciliation and management reporting.

## Project status

This is an internship project prototype. The core Streamlit application and business-calculation test suite have been implemented. The automated business-logic suite was run locally by the developer with **16/16 tests passing**.

> Important: This prototype is not a certified accounting package, statutory GST filing system, or production-hardened multi-user ERP. Review the assumptions and limitations below before using real business data.

## Core workflows

### Sales-to-cash
1. Salesman creates a customer order.
2. Factory administrator approves or rejects the order.
3. Accountant generates a GST invoice.
4. Dispatch validates finished-goods availability and records stock deduction.
5. Accountant records full or partial customer payments.
6. Receivables, invoice reconciliation and ageing reports show outstanding balances.

### Purchase-to-production
1. Administrator records a supplier purchase and receives raw materials.
2. Purchase receipt creates stock movement records.
3. Production supervisor selects a product BOM and records actual consumption, good output, damaged units, labour and overhead.
4. Production posting records material issues and finished-goods output.
5. Production intelligence compares planned and actual consumption, yield and batch cost.

## Roles

| Role | Main responsibilities |
|---|---|
| Salesman | Create customer sales orders |
| Factory administrator | Manage order approvals, purchases, dispatch and operational administration |
| Production supervisor | Record production runs and material consumption |
| Accountant | GST invoices, payments, financial reports and reconciliation |
| Owner | Business dashboard, production intelligence, business analytics and oversight |

The application includes role-based navigation and password authentication. Use the demo accounts below only in a local demonstration environment.

## Features implemented

- Password authentication with PBKDF2 password hashing.
- Role-specific workspaces.
- Product, customer, supplier, raw-material and BOM master data.
- Sales order entry and administrator approval/rejection.
- GST invoice calculation and PDF generation.
- Intrastate CGST/SGST and interstate IGST treatment.
- Dispatch stock validation and stock deduction.
- Supplier purchase receipt and raw-material stock update.
- Production run posting, BOM comparison and actual consumption capture.
- Production costing including material, labour and overhead.
- Customer payment recording, partial-payment support and receivables ageing.
- Stock summary, stock movement ledger and running balances.
- CSV and Excel operational reports.
- Owner dashboard, business analytics and production intelligence.
- GST and financial reconciliation.
- Read-only audit trail and system-health diagnostics.
- Automated tests for core business calculations.

## Technology stack

| Technology | Purpose |
|---|---|
| Python | Application and business logic |
| Streamlit | Web user interface |
| SQLAlchemy | ORM and database access |
| SQLite | Local prototype database |
| Pandas | Report preparation and tabular exports |
| Plotly / Streamlit charts | Visual reporting where used |
| ReportLab | GST invoice PDF generation |
| openpyxl | Excel workbook export |
| pytest | Automated business-logic tests |

The prototype uses SQLite to keep local setup simple and avoid infrastructure requirements. A production deployment should use a server database such as PostgreSQL, managed backups, stronger authorization controls and concurrency testing.

## Project structure

```text
NammaFactory/
├── app.py
├── database.py
├── models.py
├── seed.py
├── requirements.txt
├── modules/
│   ├── __init__.py
│   └── authentication.py
├── utils/
│   ├── __init__.py
│   └── business_logic.py
├── tests/
│   ├── __init__.py
│   └── test_business_logic.py
├── assets/
└── README.md
```

The SQLite database is generated locally by the application/initialization process. Do not commit a live business database or credentials to a public repository.

## Local setup

### 1. Requirements
- Python 3.10 or later (the project was developed and tested using Python 3.13).
- Git.
- Windows, macOS or Linux.

### 2. Clone the repository

```bash
git clone https://github.com/Rishanya06/NammaFactory-ERP.git
cd NammaFactory-ERP
```

### 3. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize demo data

```bash
python seed.py
```

Run the seed script only for a fresh demo database or when intentionally resetting/recreating demo data. Do not run it against a database containing transactions you need to preserve.

### 6. Start the application

```bash
streamlit run app.py
```

Streamlit prints the local URL in the terminal, usually `http://localhost:8501`.

## Demo accounts

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Admin@123` |
| Salesman | `salesman` | `Sales@123` |
| Production supervisor | `production` | `Prod@123` |
| Accountant | `accountant` | `Accounts@123` |
| Owner | `owner` | `Owner@123` |

These are demonstration credentials. Change them before any deployment beyond a local demonstration. Do not reuse these passwords for real accounts.

## Automated tests

Run:

```bash
python -m pytest tests/ -v
```

The business-logic test suite contains 16 tests covering:
- Monetary rounding with `Decimal` and half-up rounding.
- Tamil Nadu intrastate classification.
- Interstate classification.
- Stock ledger movement arithmetic.
- Unknown movement handling.
- Weighted-average flour and oil cost calculations.
- Rejection of negative purchase quantities.
- Invoice, GST, payment and outstanding aggregation.
- Empty financial datasets.

Developer-reported local result: **16 passed**. See `TEST_LOG.md` for the benchmark figures and scope.

## Benchmark scenario

The benchmark used in development is documented in `DESIGN_NOTE.md` and `TEST_LOG.md`. Important expected results include:
- Flour weighted-average rate after a 60 kg purchase: ₹43.125/kg.
- Production planned output: 200 packets.
- Good output: 188 packets (94% yield).
- Oil consumption: 10.5 L against 10 L standard (+5%).
- Sales A invoice: ₹7,875 including ₹187.50 CGST and ₹187.50 SGST.
- Payment received: ₹4,000.
- Outstanding on Sales A: ₹3,875.
- Finished goods: 88 packets after production and dispatch of 150 packets, assuming opening finished stock of 50 and production output of 188.

## Important assumptions and limitations

1. The factory is assumed to be in Tamil Nadu. The current state comparison recognizes common Tamil Nadu spellings and `TN`.
2. The GST logic is a simplified place-of-supply demonstration. It is not a complete GST compliance engine and does not validate GSTINs, exemptions, reverse charge, e-invoicing, e-way bills or statutory return formats.
3. The weighted-average material-cost calculation is a periodic calculation based on configured opening stock rates and received purchase records. It is not a perpetual moving-average valuation engine with full cost-layer depletion.
4. The prototype uses SQLite. Concurrent multi-user production usage, backup/restore, migrations and operational monitoring need further engineering.
5. The application includes audit logging and read-only audit/health pages, but it is not tamper-proof or independently certified.
6. Historical/test transactions should not be deleted to make reports appear clean. Corrections should be implemented through traceable reversals or adjustment transactions.
7. Offline synchronization, FEFO batch/expiry tracking, barcode support, supplier payment workflows, statutory GST filing, advanced authorization and production deployment hardening are not claimed as complete unless separately demonstrated.

## Git repository

https://github.com/Rishanya06/NammaFactory-ERP

## Suggested demo flow

1. Log in as Salesman and create an order.
2. Log in as Admin and approve it.
3. Log in as Accountant and generate the GST invoice PDF.
4. Record a customer payment and show outstanding reconciliation.
5. Show a purchase receipt and its stock movement.
6. Log in as Production and post a production run.
7. Show production variance, stock ledger and costing.
8. Log in as Owner and show the dashboard, Business Analytics and System Health.
9. Run the automated test suite from the terminal.

