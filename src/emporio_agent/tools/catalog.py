"""Catalog tools: product search and product details."""

from __future__ import annotations

import difflib

from emporio_agent.data.loader import Product, Store, normalize
from emporio_agent.pricing import quote
from emporio_agent.tools import ToolError

CATEGORY_KEYS = {
    "guitarras": 1,
    "baixos": 2,
    "baterias_percussao": 3,
    "teclados_pianos": 4,
    "violoes": 5,
    "sopros_madeiras": 6,
    "sopros_metais": 7,
    "cordas_orquestrais": 8,
    "ukuleles": 9,
}

STATUS_MESSAGES = {
    "available": "disponível em estoque",
    "out_of_stock": "temporariamente indisponível (sem estoque)",
    "discontinued": "descontinuado: não faz mais parte do catálogo",
    "coming_soon": "em breve: ainda não disponível para venda",
}

MAX_RESULTS = 10
MAX_QUERY_LENGTH = 100


def _status_key(p: Product) -> str:
    if p.status == "discontinued":
        return "discontinued"
    if p.status == "coming_soon":
        return "coming_soon"
    return "available" if p.stock > 0 else "out_of_stock"


def _specs_text(p: Product) -> str:
    return normalize(" ".join(f"{k} {v}" for k, v in p.specs.items()))


def _summary(store: Store, p: Product) -> dict:
    q = quote(p.price, store.promotions.get(p.product_id))
    return {
        "id": p.product_id,
        "nome": p.name,
        "categoria": p.category,
        "situacao": STATUS_MESSAGES[_status_key(p)],
        "estoque": p.stock if p.available else 0,
        "preco": q.to_dict(),
        "especificacoes": p.specs,
    }


def _validate_price(value: float | None, name: str) -> float | None:
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ToolError(f"{name} deve ser um número") from exc
    if value < 0:
        raise ToolError(f"{name} não pode ser negativo")
    return value


def search_products(
    store: Store,
    category: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    string_type: str | None = None,
    electric: bool | None = None,
    query: str | None = None,
    include_unavailable: bool = False,
) -> dict:
    """Filter the catalog. Prices are compared against the final price (promotion applied)."""
    max_price = _validate_price(max_price, "max_price")
    min_price = _validate_price(min_price, "min_price")

    category_id = None
    if category:
        category_id = CATEGORY_KEYS.get(normalize(category))
        if category_id is None:
            raise ToolError(f"categoria inválida; use uma de: {', '.join(CATEGORY_KEYS)}")
        if not any(p.category_id == category_id for p in store.products.values()):
            return {
                "total_encontrado": 0,
                "produtos": [],
                "observacao": (
                    f"A categoria '{store.categories[category_id]}' não tem nenhum produto "
                    "no catálogo no momento."
                ),
            }

    if string_type:
        string_type = {"aco": "steel", "nylon": "nylon"}.get(normalize(string_type))
        if string_type is None:
            raise ToolError("string_type deve ser 'nylon' ou 'aco'")

    tokens: list[str] = []
    if query:
        if len(query) > MAX_QUERY_LENGTH:
            raise ToolError("query muito longa")
        tokens = normalize(query).split()

    results = []
    for p in store.products.values():
        if not include_unavailable and not p.available:
            continue
        if category_id and p.category_id != category_id:
            continue
        if string_type and p.specs.get("strings") != string_type:
            continue
        if electric is not None and (p.specs.get("electronics") == "yes") != electric:
            continue
        haystack = f"{p.search_text} {_specs_text(p)}"
        if tokens and not all(t in haystack for t in tokens):
            continue
        final = float(quote(p.price, store.promotions.get(p.product_id)).final_price)
        if max_price is not None and final > max_price:
            continue
        if min_price is not None and final < min_price:
            continue
        results.append((final, p))

    results.sort(key=lambda item: item[0])
    found = [_summary(store, p) for _, p in results[:MAX_RESULTS]]
    response = {"total_encontrado": len(results), "produtos": found}
    if len(results) > MAX_RESULTS:
        response["observacao"] = f"Mostrando os {MAX_RESULTS} mais baratos; refine a busca."
    if not results:
        response["observacao"] = "Nenhum produto encontrado com esses filtros."
    return response


def find_product(store: Store, product: str) -> Product | list[Product]:
    """Resolve a product by id or (fuzzy) name. Returns a list when ambiguous."""
    text = str(product).strip()
    if not text or len(text) > MAX_QUERY_LENGTH:
        raise ToolError("informe o nome ou o id do produto")
    if text.isdigit():
        p = store.products.get(int(text))
        if p is None:
            raise ToolError(f"produto {text} não encontrado")
        return p

    wanted = normalize(text)
    tokens = wanted.split()

    def score(p: Product) -> float:
        name = normalize(p.name)
        name_tokens = name.split()
        # whole-token matches weigh more than substrings, so "D-28" prefers "D-28" over "D-28E"
        exact = sum(t in name_tokens for t in tokens) / len(tokens)
        partial = sum(t in name for t in tokens) / len(tokens)
        return exact + partial / 2 + difflib.SequenceMatcher(None, wanted, name).ratio() / 2

    ranked = sorted(store.products.values(), key=score, reverse=True)
    best = score(ranked[0])
    if best < 0.9:
        return []
    close = [p for p in ranked if best - score(p) < 0.05]
    return close[0] if len(close) == 1 else close[:5]


def _alternatives(store: Store, p: Product, limit: int = 3) -> list[dict]:
    candidates = [
        c
        for c in store.products.values()
        if c.available
        and c.product_id != p.product_id
        and c.category_id == p.category_id
        and c.specs.get("strings") == p.specs.get("strings")
    ]
    candidates.sort(key=lambda c: abs(c.price - p.price))
    return [_summary(store, c) for c in candidates[:limit]]


def get_product_details(store: Store, product: str) -> dict:
    match = find_product(store, product)
    if isinstance(match, list):
        if not match:
            return {
                "encontrado": False,
                "observacao": "Nenhum produto com esse nome no catálogo.",
            }
        return {
            "encontrado": False,
            "observacao": "Mais de um produto corresponde; confirme com o cliente qual deles.",
            "candidatos": [{"id": p.product_id, "nome": p.name} for p in match],
        }

    details = _summary(store, match)
    details["encontrado"] = True
    if match.description_reliable:
        details["descricao"] = match.description
    else:
        details["descricao"] = None
        details["observacao_interna"] = (
            "A descrição cadastrada deste produto é inconsistente com o nome e as "
            "especificações; use apenas nome e especificações."
        )
    if not match.available:
        details["alternativas"] = _alternatives(store, match)
    return details
