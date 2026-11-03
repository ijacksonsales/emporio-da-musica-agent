from datetime import date

import pytest

from emporio_agent.tools.handoff import HandoffStore
from emporio_agent.tools.orders import AttemptTracker
from emporio_agent.tools.registry import TOOL_DECLARATIONS, ToolContext, dispatch


@pytest.fixture
def ctx(store, tmp_path):
    return ToolContext(
        store=store,
        today=date(2026, 3, 25),
        session_id="test",
        attempts=AttemptTracker(),
        handoffs=HandoffStore(tmp_path / "test.sqlite3"),
    )


def test_every_declared_tool_dispatches(ctx):
    calls = {
        "search_products": {"category": "ukuleles"},
        "get_product_details": {"product": "Kala KA-15S"},
        "get_order_status": {"order_id": "8", "email_or_phone": "anacarol.ferreira@coldmail.com"},
        "get_store_policy": {"topic": "returns"},
        "escalate_to_human": {"reason": "reclamacao", "summary": "Pedido 8 atrasado", "order_id": "8"},
    }
    assert {d["name"] for d in TOOL_DECLARATIONS} == set(calls)
    for name, args in calls.items():
        assert "erro" not in dispatch(ctx, name, args), name


def test_policy_lookup_returns_section_text(ctx):
    result = dispatch(ctx, "get_store_policy", {"topic": "hours"})
    assert "09:00 às 18:00" in result["politica"]


def test_handoff_returns_protocol(ctx):
    result = dispatch(ctx, "escalate_to_human", {"reason": "reclamacao", "summary": "teste"})
    assert result["protocolo"].startswith("EMP-")


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("drop_database", {}),
        ("get_store_policy", {"topic": "../../.env"}),
        ("get_store_policy", {}),
        ("search_products", {"sql": "SELECT * FROM customers"}),
        ("escalate_to_human", {"reason": "hack", "summary": "x"}),
    ],
)
def test_invalid_calls_return_errors_instead_of_raising(ctx, name, args):
    assert "erro" in dispatch(ctx, name, args)
