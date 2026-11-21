"""Pure business calculations used by NammaFactory and its automated tests."""
from decimal import Decimal, ROUND_HALF_UP

OPENING_STOCK_RATES = {
    "RM-FLOUR": (Decimal("100"), Decimal("42.00")),
    "RM-OIL": (Decimal("30"), Decimal("140.00")),
    "RM-SPICE": (Decimal("5"), Decimal("200.00")),
    "PKG-POUCH": (Decimal("500"), Decimal("2.50")),
    "PKG-CARTON": (Decimal("30"), Decimal("15.00")),
}
BENCHMARK_UNIT_COSTS = {
    "RM-FLOUR": Decimal("43.125"),
    "RM-OIL": Decimal("140.00"),
    "RM-SPICE": Decimal("200.00"),
    "PKG-POUCH": Decimal("2.50"),
    "PKG-CARTON": Decimal("15.00"),
}
INCOMING_MOVEMENTS = {"OPENING", "PURCHASE", "PRODUCTION_OUTPUT", "STOCK_IN"}
OUTGOING_MOVEMENTS = {"PRODUCTION_ISSUE", "DISPATCH", "STOCK_OUT"}


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def is_intrastate_customer(customer_state):
    normalized = (customer_state or "").strip().lower()
    return normalized in {"tamil nadu", "tamilnadu", "tn"}


def calculate_stock_balances(movements):
    balances = {}
    for movement in movements:
        key = (movement.item_type, movement.item_id)
        balances.setdefault(key, Decimal("0"))
        movement_type = str(movement.movement_type or "").upper()
        quantity = Decimal(str(movement.quantity or 0))
        if movement_type in INCOMING_MOVEMENTS:
            balances[key] += quantity
        elif movement_type in OUTGOING_MOVEMENTS:
            balances[key] -= quantity
    return balances


def calculate_weighted_average_cost(sku, received_items):
    opening_qty, opening_rate = OPENING_STOCK_RATES.get(
        sku, (Decimal("0"), Decimal("0"))
    )
    total_qty = opening_qty
    total_value = opening_qty * opening_rate
    for item in received_items:
        qty = Decimal(str(item.quantity or 0))
        rate = Decimal(str(item.unit_price or 0))
        if qty < 0 or rate < 0:
            raise ValueError("Purchase quantity and unit price cannot be negative.")
        total_qty += qty
        total_value += qty * rate
    if total_qty <= 0:
        return BENCHMARK_UNIT_COSTS.get(sku, Decimal("0.00"))
    return (total_value / total_qty).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )


def calculate_invoice_totals(invoices, payments):
    invoice_total = sum((Decimal(str(row.total_amount or 0)) for row in invoices), Decimal("0"))
    payment_total = sum((Decimal(str(row.amount or 0)) for row in payments), Decimal("0"))
    taxable_total = sum((Decimal(str(row.taxable_amount or 0)) for row in invoices), Decimal("0"))
    gst_total = sum((
        Decimal(str(row.cgst or 0)) + Decimal(str(row.sgst or 0)) + Decimal(str(row.igst or 0))
        for row in invoices
    ), Decimal("0"))
    return {
        "invoice_total": invoice_total,
        "payment_total": payment_total,
        "outstanding": invoice_total - payment_total,
        "taxable_total": taxable_total,
        "gst_total": gst_total,
        "invoice_count": len(invoices),
    }
