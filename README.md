# NammaFactory — Order-to-Audit ERP for Small Food Manufacturers

NammaFactory is a role-based ERP prototype designed for small food manufacturers. It connects sales orders, GST invoicing, dispatch, inventory movements, purchases, BOM-based production, costing, payments, reconciliation and management reporting.

## Project status

This internship project prototype is built using Python, Streamlit, SQLAlchemy and SQLite.

- Five user roles with role-specific workspaces.
- Purchase-to-production and sales-to-cash workflows.
- Stock movement ledger and production costing.
- GST invoice PDF generation and financial reports.
- **Automated business-logic tests: 16 passed locally.**

> **Important:** This is a functional prototype, not a certified accounting package, statutory GST filing system or production-hardened multi-user ERP. See the assumptions and limitations below.

## Core workflows

### Sales-to-cash

1. Salesman creates a customer sales order.
2. Administrator approves or rejects the order.
3. Accountant generates the GST invoice.
4. Dispatch checks finished-goods availability and records stock deduction.
5. Accountant records full or partial customer payments.
6. Receivables, reconciliation and ageing reports show outstanding balances.

### Purchase-to-production

1. Administrator records a supplier purchase.
2. Purchase receipt increases raw-material stock through stock movements.
3. Production supervisor selects a product BOM and records actual material consumption, good output, damaged units, labour and overhead.
4. Production posting records raw-material issues and finished-goods output.
5. Production intelligence compares planned and actual consumption, yield and batch cost.

## User roles

| Role | Main responsibilities |
|---|---|
| Salesman | Create customer sales orders |
| Factory administrator | Manage approvals, purchases, dispatch and administration |
| Production supervisor | Record production runs and material consumption |
| Accountant | Generate invoices, record payments and review financial reports |
| Owner | View business dashboard, production intelligence and analytics |

The application uses password authentication with PBKDF2 password hashing and role-specific navigation.

## Features against assignment scope

### Must Have

| Assignment requirement | Implementation |
|---|---|
| Login with at least three roles | Implemented: salesman, admin, production, accountant and owner |
| Product, customer, raw-material and BOM masters | Implemented |
| Mobile-friendly order entry and admin approval | Implemented using responsive Streamlit interfaces |
| GST invoice as PDF | Implemented |
| Production updates raw-material and finished-goods stock | Implemented through stock movements |
| Planned vs actual consumption and yield variance | Implemented |
| Stock summary and stock ledger | Implemented with running balances |
| Sales register and stock report in Excel/CSV | Implemented |

### Should Have

| Assignment requirement | Implementation |
|---|---|
| Purchases and supplier records | Implemented |
| Payments, outstanding and ageing | Implemented, including partial payments |
| Cost per packet with overheads | Implemented using material, labour and overhead costs |
| GST summary report | Implemented |
| Variance alerts | Implemented through production variance analysis |
| Owner dashboard | Implemented |

### Stretch goals

| Stretch goal | Status |
|---|---|
| Offline order capture with synchronisation | Not implemented |
| Batch and expiry tracking with FEFO dispatch | Not implemented |
| Reorder levels and low-stock alerts | Reorder thresholds are stored; a complete automated replenishment workflow is not claimed |
| Production planning from pending orders | Not implemented |
| Salesman route or GPS visit log | Not implemented |
| Tally-compatible export | Not implemented |
| e-Invoice / e-Way Bill integration | Not implemented |
| Tamil language interface | Not implemented |

The implementation prioritises the benchmark and core operational workflows before stretch functionality.

## Technology stack

| Technology | Purpose |
|---|---|
| Python | Application and business logic |
| Streamlit | Web user interface |
| SQLAlchemy | ORM and database access |
| SQLite | Relational database for local prototype |
| Pandas | Report preparation and tabular exports |
| Plotly / Streamlit charts | Visual reporting where used |
| ReportLab | GST invoice PDF generation |
| openpyxl | Excel workbook export |
| pytest | Automated business-logic tests |

**Why this stack?** Python provides a common language for the business logic, calculations and reporting. Streamlit enables rapid development of role-specific, responsive interfaces, while SQLAlchemy and SQLite provide a straightforward relational data model without requiring a separate database server for the demonstration.

For production deployment, SQLite should be replaced with a server database such as PostgreSQL, with managed backups, migrations, concurrency testing and stronger operational security.

## Architecture and project structure

The application separates the user interface, database models, authentication and reusable business calculations.

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

The relational schema includes users, products, customers, suppliers, raw materials, BOMs, purchases, production runs, consumption records, sales orders, invoices, payments, stock movements and audit logs.

Inventory balances are derived from stock movements rather than being maintained only as manually editable quantities. Movement records include item details, movement type, source reference, user and timestamp.

The SQLite database is created locally. A live transaction database is not included in the public repository.

## Local setup

### Requirements

- Python 3.10 or later (developed and tested using Python 3.13).
- Git.
- Windows, macOS or Linux.

### 1. Clone the repository

```bash
git clone https://github.com/Rishanya06/NammaFactory-ERP.git
cd NammaFactory-ERP
```

### 2. Create and activate a virtual environment

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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialise demo data

```bash
python seed.py
```

Run the seed script only when creating a fresh demo database or intentionally recreating demo data. Do not run it against a database containing transactions that must be preserved.

### 5. Start the application

```bash
streamlit run app.py
```

The terminal displays the local application URL, usually:

`http://localhost:8501`

## Demo accounts

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Admin@123` |
| Salesman | `salesman` | `Sales@123` |
| Production supervisor | `production` | `Prod@123` |
| Accountant | `accountant` | `Accounts@123` |
| Owner | `owner` | `Owner@123` |

These are demonstration credentials for local evaluation only. Change them before any deployment beyond a local demonstration. Do not use them for real business accounts.

## Automated tests

Run the test suite:

```bash
python -m pytest tests/ -v
```

The current business-logic suite contains 16 tests covering:

- Monetary rounding using `Decimal` and half-up rounding.
- Tamil Nadu intrastate and interstate classification.
- Stock ledger movement arithmetic.
- Handling of unknown movement types.
- Weighted-average flour and oil cost calculations.
- Rejection of negative purchase quantities by the cost helper.
- Invoice, GST, payment and outstanding aggregation.
- Empty financial datasets.

**Developer-reported local result: 16 passed.**

See `TEST_LOG.md` for the test scope and benchmark validation notes.

## Benchmark scenario and results

The following results are from the benchmark transactions executed in the local demo database. The benchmark uses an opening finished-goods balance of 50 Murukku packets.

### Purchase and production

| Operation | Benchmark result |
|---|---:|
| Opening flour stock | 100 kg @ ₹42/kg |
| Flour purchase | 60 kg @ ₹45/kg |
| Weighted-average flour cost | ₹43.125/kg |
| Planned production | 200 packets |
| Actual good output | 188 packets |
| Damaged units | 6 |
| Actual flour consumption | 40 kg |
| Actual oil consumption | 10.5 L |
| Actual spice consumption | 1.2 kg |
| Pouches used | 194 |
| Cartons used | 9 |

### Production variance and costing

- Yield: 188 / 200 = **94%**.
- Yield variance: **−6%**.
- Oil consumption variance: **+5%** (10.5 L actual against 10 L planned).

| Cost component | Amount |
|---|---:|
| Flour: 40 × ₹43.125 | ₹1,725 |
| Oil: 10.5 × ₹140 | ₹1,470 |
| Spice: 1.2 × ₹200 | ₹240 |
| Pouches: 194 × ₹2.50 | ₹485 |
| Cartons: 9 × ₹15 | ₹135 |
| **Total material cost** | **₹4,055** |
| Labour | ₹1,200 |
| Gas and power overhead | ₹600 |
| **Total production cost** | **₹5,855** |
| **Cost per good packet: ₹5,855 / 188** | **₹31.14** |

The cost per packet uses actual good output as the denominator and includes the recorded labour and overhead expenses.

### Inventory reconciliation

| Item | Expected closing balance |
|---|---:|
| Flour | 120 kg |
| Oil | 19.5 L |
| Spice | 3.8 kg |
| Pouches | 306 |
| Cartons | 21 |
| Murukku after production | 238 packets |
| Murukku after dispatch to Customer A | 88 packets |

### Sales and invoice results

**Customer A — Tamil Nadu**

| Item | Amount |
|---|---:|
| Quantity | 150 packets |
| Taxable amount | ₹7,500 |
| CGST | ₹187.50 |
| SGST | ₹187.50 |
| Invoice total | ₹7,875 |
| Payment received | ₹4,000 |
| Outstanding | ₹3,875 |

**Customer B — Karnataka**

- Order quantity: 120 packets.
- Interstate GST treatment: IGST.
- Invoice generated: ₹6,300, including ₹300 IGST.
- Dispatch validation: blocked because only 88 packets were available.
- Shortage reported: **32 packets**.

The Customer B invoice remains outstanding for ₹6,300 because no payment was recorded in the benchmark.

**Combined financial reconciliation**

| Metric | Result |
|---|---:|
| Number of invoices | 2 |
| Total invoice value | ₹14,175 |
| Total GST | ₹675 |
| Payment received | ₹4,000 |
| Total outstanding | ₹10,175 |

These figures describe the completed benchmark transactions in the demo database. Additional transactions or a fresh seed database will produce different aggregate reports.

## Assumptions and limitations

1. The demonstration factory is assumed to be located in Tamil Nadu. State comparison recognises common Tamil Nadu spellings and `TN`.
2. GST calculation is a simplified place-of-supply demonstration. It does not cover all statutory GST cases, GSTIN validation, exemptions, reverse charge, e-invoicing, e-way bills or statutory return formats.
3. Weighted-average material cost is calculated from configured opening stock rates and received purchase records. This is not a complete perpetual moving-average inventory valuation engine with full cost-layer depletion.
4. The application uses SQLite for local demonstration. Multi-user concurrency, backup and restore, migrations and production monitoring need further engineering.
5. Audit logging and read-only audit/system-health pages are implemented, but the audit trail is not tamper-proof or independently certified.
6. Posted invoice cancellation through formal credit-note workflows is not implemented.
7. Offline synchronisation, batch-wise expiry tracking, FEFO, barcode support, Tally export, e-invoice/e-waybill integration and statutory GST filing are not implemented.
8. The prototype should be evaluated using dummy data, not real customer or financial records.

## Repository and supporting documents

**GitHub:** https://github.com/Rishanya06/NammaFactory-ERP

- `DESIGN_NOTE.md` — architecture, data model, stock/BOM logic and costing method.
- `TEST_LOG.md` — automated test execution and benchmark validation.
- `seed.py` — demo master data initialisation.

## Suggested demonstration flow

1. Log in as Salesman and create Customer A's order.
2. Log in as Administrator and approve the order.
3. Generate the GST invoice PDF.
4. Dispatch the order and record the ₹4,000 payment.
5. Show the purchase receipt and raw-material stock update.
6. Show the production run, actual consumption, yield variance and costing.
7. Log in as Salesman and create Customer B's interstate order.
8. Show the IGST invoice and the dispatch block caused by the 32-packet shortage.
9. Log in as Owner and show the dashboard, Business Analytics, GST reconciliation, Stock Ledger and System Health.
10. Run the automated test suite from the terminal.