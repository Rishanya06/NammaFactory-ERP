from decimal import Decimal
from types import SimpleNamespace

import pytest

from utils.business_logic import (
    money, is_intrastate_customer, calculate_stock_balances,
    calculate_weighted_average_cost, calculate_invoice_totals,
)


def movement(item_type, item_id, movement_type, quantity):
    return SimpleNamespace(item_type=item_type, item_id=item_id,
                           movement_type=movement_type, quantity=quantity)


def test_money_rounds_half_up():
    assert money("10.125") == Decimal("10.13")
    assert money("10.124") == Decimal("10.12")


@pytest.mark.parametrize("state", ["Tamil Nadu", "tamilnadu", "TN", " tn "])
def test_tamil_nadu_is_intrastate(state):
    assert is_intrastate_customer(state)


@pytest.mark.parametrize("state", ["Karnataka", "Kerala", "", None])
def test_other_states_are_interstate(state):
    assert not is_intrastate_customer(state)


def test_stock_ledger_benchmark_balances():
    movements = [
        movement("RAW_MATERIAL", 1, "OPENING", "100"),
        movement("RAW_MATERIAL", 1, "PURCHASE", "60"),
        movement("RAW_MATERIAL", 1, "PRODUCTION_ISSUE", "40"),
        movement("RAW_MATERIAL", 2, "OPENING", "30"),
        movement("RAW_MATERIAL", 2, "PRODUCTION_ISSUE", "10.5"),
        movement("PRODUCT", 1, "OPENING", "50"),
        movement("PRODUCT", 1, "PRODUCTION_OUTPUT", "188"),
        movement("PRODUCT", 1, "DISPATCH", "150"),
    ]
    balances = calculate_stock_balances(movements)
    assert balances[("RAW_MATERIAL", 1)] == Decimal("120")
    assert balances[("RAW_MATERIAL", 2)] == Decimal("19.5")
    assert balances[("PRODUCT", 1)] == Decimal("88")


def test_unknown_stock_movement_does_not_change_balance():
    balances = calculate_stock_balances([
        movement("RAW_MATERIAL", 1, "OPENING", "10"),
        movement("RAW_MATERIAL", 1, "UNKNOWN", "5"),
    ])
    assert balances[("RAW_MATERIAL", 1)] == Decimal("10")


def test_weighted_average_flour_cost():
    purchase = SimpleNamespace(quantity="60", unit_price="45")
    assert calculate_weighted_average_cost("RM-FLOUR", [purchase]) == Decimal("43.1250")


def test_weighted_average_opening_oil_cost():
    assert calculate_weighted_average_cost("RM-OIL", []) == Decimal("140.0000")


def test_weighted_average_rejects_negative_purchase_quantity():
    purchase = SimpleNamespace(quantity="-1", unit_price="45")
    with pytest.raises(ValueError):
        calculate_weighted_average_cost("RM-FLOUR", [purchase])


def test_invoice_payment_reconciliation_totals():
    invoice = SimpleNamespace(total_amount="7875", taxable_amount="7500",
                              cgst="187.50", sgst="187.50", igst="0")
    payment = SimpleNamespace(amount="4000")
    totals = calculate_invoice_totals([invoice], [payment])
    assert totals["invoice_total"] == Decimal("7875")
    assert totals["payment_total"] == Decimal("4000")
    assert totals["outstanding"] == Decimal("3875")
    assert totals["taxable_total"] == Decimal("7500")
    assert totals["gst_total"] == Decimal("375")
    assert totals["invoice_count"] == 1


def test_empty_invoice_totals():
    totals = calculate_invoice_totals([], [])
    assert totals["invoice_total"] == Decimal("0")
    assert totals["outstanding"] == Decimal("0")
    assert totals["invoice_count"] == 0
