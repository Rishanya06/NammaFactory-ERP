# NammaFactory — Technical Design Note

## 1. Purpose and scope

NammaFactory is a role-based ERP prototype for a small food manufacturer. Its design connects two operational loops:

- **Order-to-cash:** sales order → approval → GST invoice → dispatch → customer payment → receivables.
- **Purchase-to-production:** supplier purchase → raw-material receipt → BOM-based production → actual consumption and output → finished-goods stock → production cost and variance.

The current implementation is a local Streamlit + SQLAlchemy + SQLite prototype.

## 2. Architecture

```text
Role-based Streamlit UI
        |
        v
Page / workflow functions
        |
        v
Business calculations (Decimal)
        |
        v
SQLAlchemy ORM
        |
        v
SQLite database
        |
        +--> Sales / invoices / payments
        +--> Purchases / production / stock movements
        +--> Audit log
        |
        v
CSV / Excel / PDF reports
```

The UI layer collects inputs and displays workflow results. SQLAlchemy maps application records to relational tables. Reusable calculations such as stock balance aggregation, weighted-average cost and invoice/payment totals are separated into `utils/business_logic.py` so they can be tested independently.

## 3. Data model

The principal entities are:

| Entity | Responsibility |
|---|---|
| User | Login identity, password hash and role |
| Product | Finished-goods SKU, HSN, price and GST rate |
| Customer | Buyer details and state for place-of-supply demonstration |
| Supplier | Supplier identity and contact/tax details |
| RawMaterial | Raw material master, unit and reorder threshold |
| BOM | Product recipe/version and standard batch output |
| BOMItem | Standard material quantity per BOM |
| SalesOrder | Customer order, salesman and approval status |
| SalesOrderItem | Product, quantity and price ordered |
| Invoice | Taxable amount, GST components and total |
| Payment | Receipt linked to an invoice |
| Purchase | Supplier invoice and purchase header |
| PurchaseItem | Material quantity and purchase rate |
| ProductionRun | Planned/actual output, damage, labour and overhead |
| ProductionConsumption | Planned and actual material use and stored unit cost |
| StockMovement | Inventory event and quantity movement |
| AuditLog | User action, entity reference, details and timestamp |

Foreign keys connect the principal records. A production run links to a product and BOM; its consumption rows link to raw materials. An invoice links to a sales order, and a payment links to an invoice.

## 4. Inventory model

Inventory is represented as an append-only sequence of stock movement records rather than a manually edited quantity field.

For an item:

\[
\text{Current balance} =
\sum \text{incoming quantities} -
\sum \text{outgoing quantities}
\]

Incoming movement types include:
- `OPENING`
- `PURCHASE`
- `PRODUCTION_OUTPUT`
- `STOCK_IN`

Outgoing movement types include:
- `PRODUCTION_ISSUE`
- `DISPATCH`
- `STOCK_OUT`

Every movement stores item type, item ID, quantity, unit, movement type, reference type/ID, notes, user and timestamp. The stock ledger reconstructs a running balance from the chronological movement stream.

The dispatch workflow checks available finished stock before posting the outgoing movement. Production checks raw-material availability before recording issues and finished output.

## 5. BOM and production variance

The BOM defines standard material quantities for a planned batch. The production run stores planned output, actual good output, damaged quantity, actual material consumption, labour and overhead.

For each material:

\[
\text{Consumption variance} =
\text{Actual quantity} - \text{Planned quantity}
\]

\[
\text{Consumption variance \%} =
\frac{\text{Actual} - \text{Planned}}{\text{Planned}}\times100
\]

For output:

\[
\text{Yield \%} =
\frac{\text{Good output}}{\text{Planned output}}\times100
\]

\[
\text{Yield variance (percentage points)} =
\text{Yield \%} - 100
\]

Positive material variance indicates over-consumption; negative variance indicates usage below the BOM standard. Damaged output is reported separately from good output.

## 6. Costing approach

The prototype calculates production cost as:

\[
\text{Batch cost} =
\text{Material cost} + \text{Labour} + \text{Overhead}
\]

\[
\text{Cost per good packet} =
\frac{\text{Batch cost}}{\text{Good output}}
\]

Material cost uses actual consumed quantity multiplied by the stored unit cost for the production consumption row.

For the benchmark flour purchase, periodic weighted-average cost is:

\[
\frac{(100 \times ₹42)+(60 \times ₹45)}{100+60}
= ₹43.125/\text{kg}
\]

This is a simplified periodic weighted-average calculation based on opening balances and received purchases. It does not implement a full perpetual inventory valuation engine or cost-layer depletion.

## 7. GST and receivables

The prototype assumes the factory is in Tamil Nadu.

- A Tamil Nadu customer is treated as intrastate: CGST + SGST.
- A customer in another state is treated as interstate: IGST.

For the Sales A benchmark:

| Component | Amount |
|---|---:|
| Taxable value | ₹7,500.00 |
| CGST | ₹187.50 |
| SGST | ₹187.50 |
| IGST | ₹0.00 |
| Invoice total | ₹7,875.00 |
| Receipt | ₹4,000.00 |
| Outstanding | ₹3,875.00 |

Outstanding is calculated as invoice total less receipts allocated to that invoice. The reconciliation report classifies invoices as unpaid, partially paid, fully paid or overpaid. Ageing uses the invoice date and current date.

This is an operational demonstration only, not a statutory GST engine or tax filing system.

## 8. Benchmark scenario and expected results

Opening inventory:
- Flour 100 kg; oil 30 L; spice 5 kg; pouches 500; cartons 30; finished Murukku 50 packets.

Purchase:
- Flour 60 kg at ₹45/kg.

Production:
- BOM plan: 200 packets; flour 40 kg; oil 10 L; spice 1.2 kg; pouches 200; cartons 10.
- Actual consumption: flour 40 kg; oil 10.5 L; spice 1.2 kg; 194 pouches; 9 cartons.
- Good output 188 packets; damaged pouches 6.

Expected inventory balances for the benchmark flow:
- Flour: 100 + 60 − 40 = 120 kg.
- Oil: 30 − 10.5 = 19.5 L.
- Pouches: 500 − 194 = 306 pieces.
- Finished Murukku after production: 50 + 188 = 238 packets.
- Finished Murukku after dispatch of 150: 88 packets.

Yield = 188/200 = 94%; yield variance = −6 percentage points. Oil consumption variance = (10.5−10)/10 = +5%.

The assignment's costing assumptions produce:
- Flour: 40 × ₹43.125 = ₹1,725.
- Oil: 10.5 × ₹140 = ₹1,470.
- Spice: 1.2 × ₹200 = ₹240.
- Pouches: 194 × ₹2.50 = ₹485.
- Cartons: 9 × ₹15 = ₹135.
- Material total = ₹4,055.
- Labour = ₹1,200; overhead = ₹600.
- Total batch cost = ₹5,855.
- Cost per good packet = ₹5,855/188 ≈ ₹31.14.

The figures above are benchmark expectations. Actual reports depend on the transactions present in the local demo database. If extra test batches or dispatches were posted, balances and aggregate dashboard totals will differ.

## 9. Integrity, audit and testing

The application records audit events for key workflows and provides read-only audit trail and system-health pages. System health checks include negative stock, stock movement references/quantities, duplicate invoices per order, invoice arithmetic/GST consistency, payment allocations, production consumption completeness and invoice-to-order references.

The reusable pure calculation functions are tested with pytest. The current business-logic suite contains 16 tests. The developer reported that all 16 passed locally.

## 10. Known limitations and next engineering steps

- Replace SQLite with PostgreSQL for multi-user production deployment.
- Add database migrations, backup/restore procedures and concurrency testing.
- Strengthen server-side authorization and session controls.
- Add tamper-evident audit protection and formal reversal/credit-note workflows.
- Implement full moving-average inventory valuation with issue valuation.
- Add batch/lot, expiry and FEFO traceability.
- Extend GST logic for statutory edge cases, GSTIN validation, e-invoice and e-way bill integrations.
- Add automated integration tests against a disposable test database.
- Add deployment configuration, secrets management, monitoring and operational logging.

