# NammaFactory — Test Log and Benchmark Validation

## 1. Automated Test Execution

**Command:**

```powershell
python -m pytest tests/ -v
```

**Verified local result:**

```text
16 passed in 0.46s
```

The automated test suite covers reusable business calculations implemented in `utils/business_logic.py`.

## 2. Automated Test Coverage

| Area | Test coverage |
|---|---|
| Monetary arithmetic | Decimal calculations and half-up rounding |
| State classification | Tamil Nadu intrastate and interstate classification |
| Stock ledger | Opening, purchase, production issue, output and dispatch arithmetic |
| Movement handling | Unknown movement type does not alter computed balance |
| Weighted-average cost | Flour benchmark and opening oil rate |
| Input validation | Negative purchase quantity rejected by cost helper |
| Financial totals | Invoice, GST, receipts and outstanding aggregation |
| Empty data | Empty invoice/payment aggregate returns zero totals |

## 3. Purchase and Production Benchmark

### Purchase

| Parameter | Recorded value |
|---|---:|
| Purchase reference | PUR-BENCH-001 |
| Material | Rice flour |
| Quantity purchased | 60 kg |
| Purchase rate | ₹45/kg |
| Purchase value | ₹2,700 |

### Production

| Parameter | Planned | Actual |
|---|---:|---:|
| Production output | 200 packets | 188 good packets |
| Rice flour | 40 kg | 40 kg |
| Cooking oil | 10 L | 10.5 L |
| Spice mix | 1.2 kg | 1.2 kg |
| Pouches | 200 | 194 |
| Cartons | 10 | 9 |

Additional production records:
- Damaged quantity: 6 units.
- Labour cost: ₹1,200.
- Gas and power overhead: ₹600.

## 4. Production Variance and Costing

### Production performance

| Metric | Verified result |
|---|---:|
| Planned output | 200 packets |
| Actual good output | 188 packets |
| Production yield | 94% |
| Yield variance | −6% |
| Standard oil consumption | 10 L |
| Actual oil consumption | 10.5 L |
| Oil consumption variance | +5% |

### Weighted-average flour valuation

Opening flour inventory was 100 kg at ₹42/kg, followed by a purchase of 60 kg at ₹45/kg.

\[
\text{Weighted average cost}
=
\frac{(100\times42)+(60\times45)}{160}
=₹43.125/\text{kg}
\]

### Production cost calculation

| Cost component | Calculation | Amount |
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
\text{Cost per good packet}
=
\frac{5855}{188}
\approx ₹31.14
\]

## 5. Inventory Reconciliation

| Inventory item | Opening | Inward / Output | Consumption / Dispatch | Closing |
|---|---:|---:|---:|---:|
| Rice flour (kg) | 100 | +60 | −40 | 120 |
| Cooking oil (L) | 30 | – | −10.5 | 19.5 |
| Spice mix (kg) | 5 | – | −1.2 | 3.8 |
| Pouches | 500 | – | −194 | 306 |
| Cartons | 30 | – | −9 | 21 |
| Murukku packets | 50 | +188 | −150 | 88 |

Finished-goods reconciliation:

- Opening finished stock: 50 packets.
- Good production output: 188 packets.
- Stock after production: 238 packets.
- Customer A dispatch: 150 packets.
- Remaining finished stock: 88 packets.

## 6. Sales and GST Reconciliation

### Customer A — Tamil Nadu

| Component | Verified result |
|---|---:|
| Quantity ordered | 150 packets |
| Taxable amount | ₹7,500 |
| CGST | ₹187.50 |
| SGST | ₹187.50 |
| IGST | ₹0 |
| Invoice total | ₹7,875 |
| Payment received | ₹4,000 |
| Outstanding | ₹3,875 |

The invoice was generated and the dispatch of 150 packets was completed.

### Customer B — Karnataka

| Component | Verified result |
|---|---:|
| Quantity ordered | 120 packets |
| Taxable amount | ₹6,000 |
| IGST | ₹300 |
| Invoice total | ₹6,300 |
| Available finished stock | 88 packets |
| Dispatch shortage | 32 packets |
| Dispatch status | Blocked |
| Payment received | ₹0 |
| Outstanding | ₹6,300 |

The application generated the interstate invoice with IGST and prevented dispatch because available stock was insufficient.

### Combined financial reconciliation

| Metric | Verified result |
|---|---:|
| Number of invoices | 2 |
| Total taxable value | ₹13,500 |
| Total GST | ₹675 |
| Total invoice value | ₹14,175 |
| Payments received | ₹4,000 |
| Total outstanding | ₹10,175 |

## 7. Manual Application Validation

The following application workflows were manually exercised during development and benchmark execution:

- Role-based login and navigation.
- Sales order creation and administrator approval.
- GST invoice generation and PDF download.
- Purchase receipt and raw-material stock update.
- Production run posting and actual consumption capture.
- Production yield and material variance display.
- Production costing display.
- Customer payment recording and outstanding reconciliation.
- Dispatch stock validation.
- CSV and Excel report downloads.
- Owner dashboard and business analytics.
- Production intelligence.
- GST and financial reconciliation.
- Stock ledger and running balances.
- Audit trail filters and CSV export.
- System-health diagnostics.

### System health verification

| Diagnostic result | Verified count |
|---|---:|
| Total checks | 7 |
| Passed | 7 |
| Warnings | 0 |
| Errors | 0 |

The audit trail displayed 22 events during the completed benchmark validation.

These manual checks are application-level verification, not a substitute for automated end-to-end integration tests.

## 8. Test Environment and Reproducibility

**Development environment:**
- Operating system: Windows 11.
- Python: 3.13.
- IDE: Visual Studio Code.
- Database: SQLite.
- Application: Streamlit.

To reproduce the local test environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest tests/ -v
streamlit run app.py
```

For a fresh demo database:

```powershell
python seed.py
```

Do not rerun the seed script against a database whose transaction history must be preserved.

## 9. Notes and Limitations

- Benchmark figures assume the specified opening balances and transactions.
- Additional transactions can change aggregate dashboard and report values.
- The benchmark costing uses weighted-average material valuation based on opening rates and purchase records.
- Historical development transactions created before consumption tracking may show incomplete production variance details.
- GST calculations are an operational demonstration, not a statutory GST filing engine.
- The automated test suite focuses on reusable business calculations; full automated UI and database integration testing remains future work.
- The application is a prototype and requires additional engineering for production deployment, multi-user concurrency, database migrations and operational security.