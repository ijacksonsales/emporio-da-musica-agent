"""Load the store CSVs into typed records and flag known data-quality issues.

See docs/DATA_AUDIT.md for the findings referenced here (F01, F06, ...).
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

# Brands carried by the store, plus model names that identify a brand.
# Used to detect descriptions that talk about a different instrument (F01).
BRANDS = [
    "Music Man", "Fender", "Gibson", "Ibanez", "PRS", "Yamaha", "Pearl", "Tama",
    "Korg", "Roland", "Nord", "Martin", "Taylor", "Takamine", "Crafter",
    "Giannini", "Tagima", "Rozini", "Shelby", "Kala", "Ohana", "Kalani",
]
MODEL_BRANDS = {
    "Jazz Bass": "Fender",
    "Precision": "Fender",
    "Stratocaster": "Fender",
    "Telecaster": "Fender",
    "StingRay": "Music Man",
    "Les Paul": "Gibson",
    "Export": "Pearl",
    "Stage Custom": "Yamaha",
}


def normalize(text: str) -> str:
    """Lowercase and strip accents, for matching user input against names."""
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def digits(text: str) -> str:
    return re.sub(r"\D", "", text or "")


@dataclass
class Product:
    product_id: int
    name: str
    price: float
    category_id: int
    category: str
    description: str
    description_reliable: bool
    stock: int
    status: str  # active | discontinued | coming_soon
    specs: dict
    search_text: str = field(repr=False, default="")

    @property
    def available(self) -> bool:
        return self.status == "active" and self.stock > 0


@dataclass
class Promotion:
    product_id: int
    discount_percent: int
    description: str


@dataclass
class Customer:
    customer_id: int
    name: str
    phone: str
    email: str
    city: str


@dataclass
class OrderItem:
    product_id: int
    quantity: int


@dataclass
class Order:
    order_id: int
    customer_id: int
    order_date: date
    status: str  # pending | confirmed | shipped | delivered | cancelled
    total: float
    payment_method: str
    tracking_code: str | None
    estimated_delivery: date | None
    notes: str | None
    items: list[OrderItem]
    total_mismatch: bool = False


@dataclass
class Store:
    categories: dict[int, str]
    products: dict[int, Product]
    promotions: dict[int, Promotion]  # active promotions only, by product_id
    customers: dict[int, Customer]
    orders: dict[int, Order]


def _brand_of(name: str) -> str | None:
    for brand in BRANDS:
        if re.search(rf"\b{re.escape(brand)}\b", name):
            return brand
    return None


def _brands_mentioned(text: str) -> set[str]:
    found = {b for b in BRANDS if re.search(rf"\b{re.escape(b)}\b", text)}
    found |= {brand for model, brand in MODEL_BRANDS.items() if model in text}
    return found


def description_is_reliable(name: str, description: str, specs: dict) -> bool:
    """False when the description contradicts the product name or specs (F01)."""
    brand = _brand_of(name)
    mentioned = _brands_mentioned(description)
    if brand and mentioned and mentioned != {brand}:
        return False
    for pattern, key in ((r"(\d+)\s*cordas", "strings"), (r"(\d+)\s*teclas", "keys")):
        m = re.search(pattern, description)
        spec = str(specs.get(key, ""))
        if m and spec.isdigit() and m.group(1) != spec:
            return False
    return True


def _opt_str(value) -> str | None:
    return None if pd.isna(value) or value == "" else str(value)


def _opt_date(value) -> date | None:
    return None if pd.isna(value) or value == "" else date.fromisoformat(str(value))


def load_store(data_dir: Path) -> Store:
    read = lambda name: pd.read_csv(data_dir / f"{name}.csv", encoding="utf-8")  # noqa: E731

    categories = {int(r.category_id): r["name"] for _, r in read("categories").iterrows()}

    products: dict[int, Product] = {}
    for _, r in read("products").iterrows():
        specs = json.loads(r.specs) if isinstance(r.specs, str) else {}
        category = categories.get(int(r.category_id), "")
        products[int(r.product_id)] = Product(
            product_id=int(r.product_id),
            name=r["name"],
            price=float(r.price_brl),
            category_id=int(r.category_id),
            category=category,
            description=r.description,
            description_reliable=description_is_reliable(r["name"], r.description, specs),
            stock=int(r.stock_quantity),
            status=r.status,
            specs=specs,
            search_text=normalize(f"{r['name']} {category}"),
        )

    promotions = {
        int(r.product_id): Promotion(int(r.product_id), int(r.discount_percent), r.description)
        for _, r in read("promotions").iterrows()
        if int(r.is_active) == 1
    }

    customers = {
        int(r.customer_id): Customer(
            int(r.customer_id), r["name"], r.phone, r.email.strip().lower(), r.city
        )
        for _, r in read("customers").iterrows()
    }

    items_by_order: dict[int, list[OrderItem]] = {}
    for _, r in read("order_items").iterrows():
        items_by_order.setdefault(int(r.order_id), []).append(
            OrderItem(int(r.product_id), int(r.quantity))
        )

    orders: dict[int, Order] = {}
    for _, r in read("orders").iterrows():
        items = items_by_order.get(int(r.order_id), [])
        items_sum = sum(products[i.product_id].price * i.quantity for i in items)
        orders[int(r.order_id)] = Order(
            order_id=int(r.order_id),
            customer_id=int(r.customer_id),
            order_date=date.fromisoformat(r.order_date),
            status=r.status,
            total=float(r.total_brl),
            payment_method=r.payment_method,
            tracking_code=_opt_str(r.tracking_code),
            estimated_delivery=_opt_date(r.estimated_delivery),
            notes=_opt_str(r.notes),
            items=items,
            total_mismatch=abs(items_sum - float(r.total_brl)) > 0.01,  # F06
        )

    return Store(categories, products, promotions, customers, orders)


@lru_cache(maxsize=1)
def get_store() -> Store:
    from emporio_agent.config import get_settings

    return load_store(get_settings().data_dir)
