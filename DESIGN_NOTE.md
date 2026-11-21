# NammaFactory – System Design Note

## 1. System Architecture and Data Model

NammaFactory is a role-based ERP application for small food manufacturing businesses. It is built using **Python, Streamlit, SQLAlchemy and SQLite**, with Pandas and OpenPyXL for reporting and ReportLab for invoice PDF generation.

The application follows a modular architecture:
- **Presentation layer:** Streamlit role-specific interfaces for administrators, salesmen, production staff, accountants and owners.
- **Business logic layer:** Handles purchases, BOM-based production, inventory movements, order approval, invoicing, dispatch, payments and costing.
- **Data layer:** SQLAlchemy ORM models backed by an SQLite relational database.

### Core data model

The database contains 17 tables:

| Functional area | Main entities |
|---|---|
| Access and auditing | User, AuditLog |
| Masters | Product, Customer, Supplier, RawMaterial |
| Manufacturing | BOM, BOMItem, ProductionRun, ProductionConsumption |
| Procurement | Purchase, PurchaseItem |
| Sales and finance | SalesOrder, SalesOrderItem, Invoice, Payment |
| Inventory | StockMovement |

### Key relationships

- A Product can have multiple BOM versions.
- A BOM contains multiple BOMItems, each linked to a RawMaterial.
- A ProductionRun references a Product and BOM and records actual material consumption.
- A Purchase contains multiple PurchaseItems and increases raw-material stock.
- A Customer can place multiple SalesOrders.
- A SalesOrder contains SalesOrderItems and can generate an Invoice.
- An Invoice can have multiple Payment records.
- StockMovement records inventory changes, while AuditLog records important user actions.

The design uses primary keys and foreign keys to maintain referential integrity. Stock is derived from recorded movements rather than relying only on manually editable balances.

## 2. Inventory Management and Production Logic

### Stock movement approach

Inventory is maintained through a central **StockMovement ledger**. Each movement records the item type, item ID, movement type, quantity, unit, reference, user and timestamp.

Typical movements include:
- Purchase receipt: increases raw-material stock.
- Production consumption: decreases raw-material stock.
- Production output: increases finished-goods stock.
- Dispatch: decreases finished-goods stock.

The stock balance is calculated by aggregating the relevant movements. Dispatch validation checks available finished stock before allowing a dispatch, preventing negative inventory.

### BOM-based production

A Bill of Materials (BOM) specifies the standard material quantities required to manufacture a defined output quantity.

For the benchmark Murukku 200g batch, the planned BOM output is 200 packets:

| Material | Planned quantity | Actual quantity |
|---|---:|---:|
| Rice flour | 40 kg | 40 kg |
| Cooking oil | 10 L | 10.5 L |
| Spice mix | 1.2 kg | 1.2 kg |
| 200g pouch | 200 | 194 |
| Carton (20 packets) | 10 | 9 |

The production run records planned output, actual good output, damaged quantity, actual consumption and production expenses.

**Yield variance:**

\[
\text{Yield variance} =
\frac{\text{Actual good output}-\text{Planned output}}
{\text{Planned output}}\times100
\]

\[
=\frac{188-200}{200}\times100=-6\%
\]

Oil consumption variance is:

\[
\frac{10.5-10}{10}\times100=5\%
\]

Thus, the batch produced 188 good packets against 200 planned, with a 6% negative yield variance and 5% excess oil consumption.

## 3. Costing and Inventory Valuation

NammaFactory uses **weighted average costing** for raw-material valuation. The weighted average unit cost is calculated using opening inventory and purchases.

For rice flour:

\[
\text{Weighted average cost} =
\frac{(100\times42)+(60\times45)}{100+60}
\]

\[
=₹43.125\text{ per kg}
\]

The 40 kg consumed in production therefore costs ₹1,725.

### Benchmark production cost

| Cost component | Calculation | Cost |
|---|---|---:|
| Rice flour | 40 × ₹43.125 | ₹1,725 |
| Cooking oil | 10.5 × ₹140 | ₹1,470 |
| Spice mix | 1.2 × ₹200 | ₹240 |
| Pouches | 194 × ₹2.50 | ₹485 |
| Cartons | 9 × ₹15 | ₹135 |
| **Total material cost** | | **₹4,055** |
| Labour | | ₹1,200 |
| Gas and power overhead | | ₹600 |
| **Total production cost** | | **₹5,855** |

\[
\text{Cost per good packet} =
\frac{₹5,855}{188}=₹31.14
\]

The unit production cost is calculated using actual good output, not planned output or total units including damaged products.

### Benchmark stock reconciliation

| Item | Opening | Purchase / Production | Consumption / Dispatch | Closing |
|---|---:|---:|---:|---:|
| Rice flour (kg) | 100 | +60 | −40 | 120 |
| Cooking oil (L) | 30 | – | −10.5 | 19.5 |
| Spice mix (kg) | 5 | – | −1.2 | 3.8 |
| Pouches | 500 | – | −194 | 306 |
| Cartons | 30 | – | −9 | 21 |
| Murukku packets | 50 | +188 | −150 | 88 |

The finished-goods balance is 238 packets after production and 88 after dispatching 150 packets to Customer A. A subsequent order for 120 packets is blocked because only 88 packets are available.

## 4. Sales, GST and Financial Tracking

Sales orders are entered by salesmen and remain pending until administrator approval. Approved orders can be invoiced and dispatched after stock validation.

The invoice calculation applies:
- **CGST + SGST** for sales within Tamil Nadu.
- **IGST** for interstate sales, such as a sale to Karnataka.

For the benchmark sale to Customer A, the taxable amount is ₹7,500, CGST is ₹187.50 and SGST is ₹187.50, resulting in an invoice total of ₹7,875. A payment of ₹4,000 leaves ₹3,875 outstanding.

The application also tracks payments, outstanding balances, sales registers, GST summaries and stock reports.

## 5. Assumptions and Limitations

- The benchmark uses the quantities, prices and production expenses specified in the assignment.
- The Murukku BOM is based on the supplied benchmark; other demonstration BOMs use illustrative values.
- Weighted average costing is demonstrated using the available opening stock and purchase data.
- The application is a functional prototype and is not certified for statutory GST filing or production accounting.
- SQLite is suitable for the demonstration but would need migration to PostgreSQL for a larger multi-user deployment.
- Advanced features such as offline synchronisation, batch-wise expiry tracking, FEFO, e-invoicing and e-waybill integration are not implemented.

The design prioritises traceable stock movements, BOM-based production, cost transparency and validation across the purchase-to-production-to-sales workflow.