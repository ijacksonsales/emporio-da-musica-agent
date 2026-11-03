import pytest

from emporio_agent.tools import ToolError
from emporio_agent.tools.catalog import get_product_details, search_products


def ids(result):
    return [p["id"] for p in result["produtos"]]


def test_guitars_up_to_1000_exclude_unavailable(store):
    result = search_products(store, category="violoes", max_price=1000)
    assert 96 not in ids(result)  # zero stock
    assert 113 not in ids(result)  # discontinued
    assert all(float(p["preco"]["preco_final"][3:].replace(".", "").replace(",", ".")) <= 1000
               for p in result["produtos"])


def test_price_filter_uses_promotional_price(store):
    # Product 90 lists at R$ 2,399 but costs R$ 1,967.18 with the active promotion
    result = search_products(store, category="violoes", min_price=1900, max_price=2000)
    assert 90 in ids(result)


def test_choro_scenario_seven_string_nylon_within_budget(store):
    result = search_products(store, query="7 cordas", string_type="nylon", max_price=1500)
    assert set(ids(result)) == {109, 110}


def test_empty_category_is_reported(store):
    result = search_products(store, category="sopros_madeiras")
    assert result["total_encontrado"] == 0
    assert "não tem nenhum produto" in result["observacao"]


def test_invalid_inputs_raise_tool_error(store):
    with pytest.raises(ToolError):
        search_products(store, category="acessorios")
    with pytest.raises(ToolError):
        search_products(store, max_price="mil reais")
    with pytest.raises(ToolError):
        search_products(store, max_price=-1)


def test_details_by_fuzzy_name(store):
    details = get_product_details(store, "takamine gd20")
    assert details["id"] == 95
    assert details["preco"]["promocao_ativa"] is None  # its 12% promotion is expired


def test_unreliable_description_is_hidden(store):
    details = get_product_details(store, "Music Man Bass 1X")
    assert details["descricao"] is None
    assert "observacao_interna" in details


def test_unavailable_product_suggests_alternatives(store):
    details = get_product_details(store, "113")
    assert "descontinuado" in details["situacao"]
    assert details["alternativas"]
    assert all(a["especificacoes"]["strings"] == "nylon" for a in details["alternativas"])


def test_unknown_product(store):
    assert get_product_details(store, "saxofone yamaha yas-280")["encontrado"] is False
