from emporio_agent.config import PROJECT_ROOT
from emporio_agent.data.loader import load_store

store = load_store(PROJECT_ROOT / "data" / "raw")


def test_loads_all_tables():
    assert len(store.products) == 65
    assert len(store.customers) == 50
    assert len(store.orders) == 20
    assert set(store.promotions) == {90, 94, 121, 127}


def test_flags_contradictory_descriptions():
    unreliable = {p.product_id for p in store.products.values() if not p.description_reliable}
    assert unreliable == {135, 136, 137, 139, 140, 142, 144}


def test_flags_orders_whose_total_does_not_match_items():
    mismatched = {o.order_id for o in store.orders.values() if o.total_mismatch}
    assert mismatched == {3, 20}


def test_availability_considers_status_and_stock():
    assert not store.products[96].available  # active, zero stock
    assert not store.products[113].available  # discontinued
    assert not store.products[130].available  # coming soon
    assert store.products[95].available
