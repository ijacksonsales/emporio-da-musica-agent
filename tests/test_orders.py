from datetime import date

import pytest

from emporio_agent.tools import ToolError
from emporio_agent.tools.orders import AttemptTracker, get_order_status

TODAY = date(2026, 3, 25)


def lookup(store, order_id, contact, tracker=None, session="s1"):
    return get_order_status(store, order_id, contact, TODAY, tracker or AttemptTracker(), session)


def test_verified_by_email(store):
    result = lookup(store, 8, "anacarol.ferreira@coldmail.com")
    assert result["verificado"]
    assert result["cliente_primeiro_nome"] == "Ana"


@pytest.mark.parametrize("phone", ["(67) 99654-7821", "67996547821", "+55 67 99654-7821", "996547821"])
def test_verified_by_phone_in_any_format(store, phone):
    assert lookup(store, 8, phone)["verificado"]


def test_delayed_shipment_is_detected(store):
    result = lookup(store, 8, "anacarol.ferreira@coldmail.com")
    assert result["atrasado"] is True
    assert result["dias_de_atraso"] == 25


def test_return_windows_for_delivered_order(store):
    # Order 7 delivered (estimated) on 2026-02-17: regret window closed on 2026-02-24
    result = lookup(store, 7, "leticia.rocha@jmail.com")
    windows = result["prazos"]
    assert windows["arrependimento_7_dias_apos_recebimento"]["dentro_do_prazo"] is False
    assert windows["garantia_legal_90_dias_apos_recebimento"]["dentro_do_prazo"] is True


def test_shared_email_does_not_open_other_customers_order(store):
    # Customers 11 and 43 share an e-mail; order 10 belongs to 11, phone of 43 must fail
    assert lookup(store, 10, "bruno.martins@jmail.com")["verificado"]
    assert not lookup(store, 10, "(67) 99456-3456")["verificado"]


def test_total_mismatch_is_flagged_internally(store):
    result = lookup(store, 3, "isabela.moreira@jmail.com")
    assert "observacao_interna" in result


def test_no_personal_data_in_response(store):
    text = str(lookup(store, 8, "anacarol.ferreira@coldmail.com"))
    assert "@" not in text and "99654" not in text


def test_wrong_contact_and_missing_order_look_identical(store):
    wrong_contact = lookup(store, 8, "someone@else.com")
    missing_order = lookup(store, 999, "someone@else.com")
    assert wrong_contact["observacao"] == missing_order["observacao"]


def test_locks_after_three_failed_attempts(store):
    tracker = AttemptTracker()
    for order_id in (1, 2, 3):
        assert not lookup(store, order_id, "attacker@x.com", tracker)["verificado"]
    locked = lookup(store, 8, "anacarol.ferreira@coldmail.com", tracker)
    assert locked.get("bloqueado") is True
    # other conversations are not affected
    assert lookup(store, 8, "anacarol.ferreira@coldmail.com", tracker, session="s2")["verificado"]


@pytest.mark.parametrize("bad_id", ["1 OR 1=1", "8; DROP TABLE orders", "abc", "", "9" * 20])
def test_rejects_non_numeric_order_ids(store, bad_id):
    with pytest.raises(ToolError):
        lookup(store, bad_id, "anacarol.ferreira@coldmail.com")
