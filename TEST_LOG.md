# NammaFactory — Test Log and Benchmark Validation

## 1. Automated test execution

Command:

```powershell
python -m pytest tests/ -v
```

Developer-reported local result:

```text
16 passed
```

The suite tests pure business calculations in `utils/business_logic.py`.

## 2. Automated test coverage

| Area | Test coverage |
|---|---|
| Monetary arithmetic | Half-up decimal rounding |
| State classification | Tamil Nadu and interstate classification |
| Stock ledger | Opening, purchase, production issue, output and dispatch arithmetic |
| Movement handling | Unknown movement type does not alter computed balance |
| Weighted-average cost | Flour benchmark and opening oil rate |
| Input validation | Negative purchase quantity rejected by cost helper |
| Financial totals | Invoice, GST, receipts and outstanding aggregation |
| Empty data | Empty invoice/payment aggregate returns zero totals |

## 3. Benchmark expected values

| Benchmark item | Expected |
|---|---:|
| Flour opening stock | 100 kg |
| Flour purchase | 60 kg @ ₹45/kg |
| Flour production issue | 40 kg |
| Flour ending stock | 120 kg |
| Weighted-average flour rate | ₹43.125/kg |
| Oil opening stock | 30 L |
| Oil actual consumption | 10.5 L |
| Oil ending stock | 19.5 L |
| Pouch opening stock | 500 pcs |
| Pouches consumed | 194 pcs |
| Pouch ending stock | 306 pcs |
| Finished stock opening | 50 packets |
| Good production output | 188 packets |
| Finished stock after production | 238 packets |
| Dispatch | 150 packets |
| Finished stock after dispatch | 88 packets |
| Planned production output | 200 packets |
| Production yield | 94% |
| Yield variance | −6 percentage points |
| Oil consumption variance | +5% |
| Total material cost | ₹4,055 |
| Labour | ₹1,200 |
| Overhead | ₹600 |
| Total batch cost | ₹5,855 |
| Cost per good packet | approximately ₹31.14 |

## 4. Sales A GST and payment reconciliation

| Component | Expected |
|---|---:|
| Taxable amount | ₹7,500.00 |
| CGST | ₹187.50 |
| SGST | ₹187.50 |
| IGST | ₹0.00 |
| Invoice total | ₹7,875.00 |
| Payment recorded | ₹4,000.00 |
| Outstanding | ₹3,875.00 |

## 5. Manual workflow checks reported during development

The developer manually verified the following application workflows during iterative development:
- Role-based login and navigation.
- Sales order creation and admin approval.
- GST invoice generation and PDF download.
- Dispatch stock validation (attempt to dispatch 89 against 50 available was blocked).
- Production posting and variance display.
- Production costing display.
- Purchase receipt flow.
- Partial customer payment and receivables.
- CSV/Excel report downloads.
- Owner dashboard.
- Audit trail filters and CSV export.
- Stock ledger and running balances.
- Production intelligence.
- Business analytics.
- GST and financial reconciliation.
- System health diagnostics.

These are development-session manual checks, not a substitute for a repeatable automated end-to-end integration test run.

## 6. Test environment and reproducibility

The project was developed on Windows 11 using Python 3.13 and VS Code. To reproduce:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest tests/ -v
streamlit run app.py
```

For a fresh demo database, initialize demo records with `python seed.py`. Do not rerun the seed script against a database whose transaction history must be retained.

## 7. Notes and limitations

- Benchmark values assume the specified opening balances and transactions only.
- Aggregate dashboards can show larger values if additional test transactions exist.
- Historical test batches created before consumption tracking may show incomplete production variance detail.
- GST summary is an operational report, not a statutory return.
- The weighted-average cost is a periodic approximation using opening rates and received purchase records.
