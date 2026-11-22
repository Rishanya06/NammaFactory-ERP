# NammaFactory — System Design Note

## 1. System Architecture

NammaFactory is a role-based ERP application designed to integrate the operational workflows of small and medium-sized food manufacturing businesses. It is developed using Python, Streamlit, SQLAlchemy and SQLite.

The application follows a modular, layered architecture:

- **Presentation layer:** Streamlit interfaces for Administrator, Salesman, Production Supervisor, Accountant and Factory Owner.
- **Business logic layer:** Handles order processing, purchase transactions, BOM-based production, inventory movements, GST calculations, dispatch validation, payments and costing.
- **Data access layer:** SQLAlchemy ORM manages database operations and entity relationships.
- **Database layer:** SQLite provides relational persistence for business transactions.
- **Reporting layer:** Pandas, Plotly, ReportLab and OpenPyXL support analytics, PDF invoices and spreadsheet exports.

This structure separates user interactions, business operations and persistent data, making the application easier to maintain and extend.

## 2. Database Design

The relational database contains **17 models** organised around the major ERP functions.

| Functional area | Models |
|---|---|
| Access and auditing | User, AuditLog |
| Master data | Product, Customer, Supplier, RawMaterial |
| Manufacturing | BOM, BOMItem, ProductionRun, ProductionConsumption |
| Procurement | Purchase, PurchaseItem |
| Sales and finance | SalesOrder, SalesOrderItem, Invoice, Payment |
| Inventory | StockMovement |

### Key relationships

- Products are associated with their Bills of Materials.
- A BOM contains multiple BOMItems linked to raw materials.
- ProductionRun records the product, BOM, output and actual material consumption.
- Purchases contain multiple PurchaseItems and generate raw-material stock receipts.
- Customers can place multiple SalesOrders, each containing SalesOrderItems.
- Sales orders can be associated with invoices.
- An invoice can have multiple payment records.
- StockMovement records inventory transactions, while AuditLog captures relevant user activities.

Primary keys and foreign keys maintain relational references between entities. The StockMovement ledger provides traceability for inventory changes across business operations.

## 3. Inventory and Production Design

### Stock movement management

NammaFactory uses a central stock movement ledger to record inventory transactions.

| Transaction | Inventory effect |
|---|---|
| Purchase receipt | Increases raw-material stock |
| Production consumption | Decreases raw-material stock |
| Production output | Increases finished-goods stock |
| Customer dispatch | Decreases finished-goods stock |

Stock balances are calculated from recorded movements. Before dispatch, the application validates available finished-goods stock to prevent dispatch quantities from exceeding available inventory.

### BOM-based production

A Bill of Materials defines the standard material requirements for a product. Production records capture planned output, actual good output, damaged quantity, material consumption, labour and overhead.

The benchmark Murukku 200g production run uses the following planned and actual quantities:

| Material | Planned | Actual |
|---|---:|---:|
| Rice flour | 40 kg | 40 kg |
| Cooking oil | 10 L | 10.5 L |
| Spice mix | 1.2 kg | 1.2 kg |
| Pouches | 200 | 194 |
| Cartons | 10 | 9 |

Production yield and consumption variance are calculated as:

\[
\text{Yield}=\frac{\text{Good output}}{\text{Planned output}}\times100
\]

\[
\text{Consumption variance}=
\frac{\text{Actual consumption}-\text{Planned consumption}}
{\text{Planned consumption}}\times100
\]

For the benchmark batch, 188 good packets were produced against 200 planned, resulting in a 94% yield. Oil consumption was 10.5 L against a planned 10 L, representing a 5% increase.

## 4. Production Costing and Inventory Valuation

The application uses weighted-average material costing based on configured opening inventory and recorded purchases.

For rice flour:

\[
\text{Weighted average cost}=
\frac{(100\times42)+(60\times45)}{100+60}
=₹43.125/\text{kg}
\]

The benchmark production cost is calculated by combining material, labour and overhead expenses.

| Cost component | Amount |
|---|---:|
| Rice flour | ₹1,725 |
| Cooking oil | ₹1,470 |
| Spice mix | ₹240 |
| Pouches | ₹485 |
| Cartons | ₹135 |
| **Material cost** | **₹4,055** |
| Labour | ₹1,200 |
| Gas and power overhead | ₹600 |
| **Total production cost** | **₹5,855** |

Cost per good packet:

\[
\frac{₹5,855}{188}=₹31.14
\]

The calculation uses actual good output as the denominator, providing a production cost that accounts for damaged units and recorded manufacturing expenses.

## 5. Sales, GST and Financial Workflow

Salesmen create customer orders, which are reviewed through the administrator approval workflow. Approved orders proceed through invoicing and dispatch operations.

The invoicing module supports:

- CGST and SGST for intra-state transactions.
- IGST for interstate transactions.
- PDF invoice generation.
- Full and partial payment recording.
- Outstanding balance and receivables tracking.

Dispatch validation checks finished-goods availability before stock deduction.

In the benchmark scenario, the Tamil Nadu customer invoice has a taxable value of ₹7,500, with ₹187.50 CGST and ₹187.50 SGST. The Karnataka customer invoice has a taxable value of ₹6,000, with ₹300 IGST. The latter dispatch is blocked because the available stock is insufficient.

These workflows connect sales, inventory and accounting rather than treating them as independent operations.

## 6. Validation, Assumptions and Limitations

The application was validated through automated business-logic tests and manual workflow checks.

- Automated test result: **16 tests passed**.
- Test coverage includes Decimal-based monetary calculations, GST classification, stock movement arithmetic, weighted-average costing and financial aggregation.
- Manual validation covered role-based access, purchases, production posting, invoice generation, payments, dispatch validation, reporting, audit trail and system-health checks.
- Benchmark system health: **7/7 checks passed**.

The implementation is a functional ERP prototype. GST calculations demonstrate basic intra-state and interstate tax treatment and are not a certified statutory filing system. Weighted-average costing uses configured opening rates and recorded purchases; it is not a complete perpetual inventory valuation engine.

SQLite supports local demonstration. A larger deployment would require PostgreSQL or another server database, database migrations, managed backups, concurrency testing and additional security hardening. Offline synchronisation, batch-wise expiry tracking, FEFO dispatch, e-invoicing and e-waybill integration remain future enhancements.

The design prioritises transaction traceability, stock consistency, BOM-driven production, transparent costing and integrated financial workflows across the manufacturing lifecycle.