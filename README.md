# NammaFactory
### An Integrated ERP Platform for Small Food Manufacturing Businesses

NammaFactory is a role-based Enterprise Resource Planning (ERP) application designed to simplify and connect the day-to-day operations of small and medium-sized food manufacturing businesses.

From customer order management and procurement to production planning, inventory tracking, GST invoicing and financial reporting, NammaFactory brings essential business operations together through a unified application and relational database.

The platform focuses on improving operational visibility, maintaining transaction traceability and connecting business activities across departments.

---

## Overview

Food manufacturing businesses often manage sales, raw materials, production, inventory and accounts through disconnected records. This makes it difficult to track stock movements, monitor production costs, manage customer payments and understand overall business performance.

NammaFactory addresses this by providing a connected ERP workflow in which transactions recorded by one department become available to the relevant downstream operations.

The application provides five role-specific workspaces:

- **Administrator** – Business administration, master data, order approvals, procurement and dispatch operations.
- **Salesman** – Customer information and sales order entry.
- **Production Supervisor** – Bills of Materials, production runs, material consumption and production costing.
- **Accountant** – GST invoicing, payment recording, receivables and financial reporting.
- **Factory Owner** – Business dashboards, production intelligence, financial reconciliation and analytics.

## Core Features

### 1. Sales and Customer Management

- Centralised customer and product records.
- Sales order creation through a dedicated salesman interface.
- Administrative order approval and rejection.
- Product-level pricing and GST configuration.
- Order history and status tracking.

### 2. Procurement and Supplier Management

- Supplier master management.
- Purchase entry and supplier invoice references.
- Raw-material receipt and inventory updates.
- Duplicate supplier invoice reference protection.
- Reorder-level configuration for raw materials.

### 3. Production and Manufacturing

- Product-wise Bill of Materials (BOM).
- Planned and actual raw-material consumption tracking.
- Production batch recording.
- Good output and damaged-unit tracking.
- Labour and overhead allocation.
- Production yield and material consumption variance analysis.
- Batch-level production costing and cost per good unit.

### 4. Inventory Management

- Raw-material and finished-goods stock tracking.
- Transaction-based stock movement ledger.
- Running stock balances.
- Purchase receipts and production consumption records.
- Finished-goods output and dispatch deductions.
- Stock availability validation before dispatch.
- Weighted-average material costing.

### 5. GST Invoicing and Financial Management

- GST-aware sales invoice generation.
- Intra-state CGST and SGST calculation.
- Interstate IGST calculation.
- PDF invoice generation.
- Full and partial customer payment recording.
- Outstanding receivables and ageing information.
- GST and financial reconciliation reports.

### 6. Business Intelligence and Reporting

- Factory Owner dashboard.
- Production Intelligence and yield analysis.
- Material consumption and cost indicators.
- Business Analytics and visual reports.
- GST and financial reconciliation.
- Stock, sales, production, purchase and payment reports.
- CSV and Excel exports.

### 7. Audit and System Monitoring

- Audit logging of recorded activities.
- Searchable activity records.
- Audit trail export.
- System-health checks.
- Role-specific navigation and authentication.

---

## Technology Stack

| Technology | Application |
|---|---|
| Python | Core application and business logic |
| Streamlit | Interactive web interface |
| SQLAlchemy | ORM and database management |
| SQLite | Relational database |
| Pandas | Data processing and report preparation |
| Plotly | Business analytics and visualisation |
| ReportLab | PDF invoice generation |
| OpenPyXL | Excel report export |
| Pytest | Automated business-logic testing |

### Why this architecture?

Python provides a common foundation for transaction processing, calculations and reporting. Streamlit enables rapid development of interactive, role-specific interfaces, while SQLAlchemy provides structured database access.

SQLite supports straightforward local deployment without requiring a separate database server. The architecture separates application interfaces, database models, authentication and reusable business calculations.

---

## System Architecture

NammaFactory follows a layered application structure:

1. **Presentation Layer:** Streamlit interfaces and role-specific workspaces.
2. **Application and Business Logic Layer:** Authentication, transaction workflows, GST calculations, inventory processing and production costing.
3. **Data Access Layer:** SQLAlchemy ORM and database operations.
4. **Database Layer:** SQLite relational storage.
5. **Reporting Layer:** Pandas, Plotly, ReportLab and OpenPyXL.

### Database Design

The relational data model includes the following entities:

- User
- Product
- Customer
- Supplier
- RawMaterial
- BOM and BOMItem
- StockMovement
- Purchase and PurchaseItem
- ProductionRun and ProductionConsumption
- SalesOrder and SalesOrderItem
- Invoice
- Payment
- AuditLog

Inventory changes are recorded through stock movement transactions, allowing purchases, production consumption, finished-goods output and dispatch operations to be traced.

---

## Project Structure

```text
NammaFactory/
│
├── app.py
├── database.py
├── models.py
├── seed.py
├── requirements.txt
├── README.md
├── TEST_LOG.md
│
├── modules/
│   ├── __init__.py
│   └── authentication.py
│
├── utils/
│   ├── __init__.py
│   └── business_logic.py
│
├── tests/
│   ├── __init__.py
│   └── test_business_logic.py
│
└── assets/
```

---

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- Git
- Windows, macOS or Linux

### 1. Clone the repository

```bash
git clone https://github.com/Rishanya06/NammaFactory-ERP.git
cd NammaFactory-ERP
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialise the database

```bash
python seed.py
```

Run the seed script only when creating a fresh demo database or intentionally recreating demo data. Do not run it against a database containing transactions that must be preserved.

### 5. Launch the application

```bash
streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

---

## Demo Access

The application includes five demonstration accounts:

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Admin@123` |
| Salesman | `salesman` | `Sales@123` |
| Production Supervisor | `production` | `Prod@123` |
| Accountant | `accountant` | `Accounts@123` |
| Factory Owner | `owner` | `Owner@123` |

These credentials are intended only for local demonstration and evaluation. They must be changed before any deployment beyond a local prototype.

---

## Testing and Validation

NammaFactory includes automated tests for important business calculations and transaction logic.

Run the test suite using:

```bash
python -m pytest tests/ -v
```

The existing business-logic test suite covers:

- Monetary calculations and rounding using Python Decimal.
- Intra-state and interstate GST classification.
- Stock movement arithmetic.
- Invalid stock movement handling.
- Weighted-average material cost calculations.
- Purchase quantity validation in cost calculations.
- Invoice, GST, payment and outstanding aggregation.
- Empty financial dataset handling.

**Recorded local test result: 16 tests passed.**

Refer to `TEST_LOG.md` for test execution details and benchmark validation.

---

## Engineering Considerations and Limitations

NammaFactory is a functional ERP prototype intended for demonstration and further development.

The following considerations apply:

- GST calculations demonstrate basic intra-state and interstate tax treatment; the application is not a certified statutory GST filing system.
- Weighted-average costing uses configured opening stock rates and recorded purchases; it is not a complete perpetual inventory valuation engine.
- SQLite is intended for local demonstration. Production deployment would require a server database such as PostgreSQL, database migrations, managed backups and concurrency testing.
- Audit records support operational traceability but are not tamper-proof or independently certified.
- Offline synchronisation, batch-wise expiry tracking, FEFO dispatch, Tally integration, e-invoicing and e-waybill functionality are not implemented.
- Production deployment would require additional security hardening, monitoring and operational controls.

---

## Future Development

Potential areas for further development include:

- PostgreSQL-based multi-user deployment.
- Batch-wise traceability and expiry management.
- FEFO-based inventory dispatch.
- Automated low-stock and replenishment alerts.
- Production planning based on pending sales orders.
- Offline order capture and synchronisation.
- Tally-compatible accounting exports.
- E-invoice and e-waybill integration.
- Enhanced business intelligence and forecasting.

---

## Repository

**GitHub:** https://github.com/Rishanya06/NammaFactory-ERP

NammaFactory aims to provide small food manufacturers with a connected, traceable and data-driven approach to managing their business operations—from customer orders and manufacturing to inventory, accounts and management decisions.