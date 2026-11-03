"""Store policy manual, split by topic (decisions D02/D03).

The sections were curated by hand from data/raw/políticas_da_loja.pdf: automatic PDF
extraction broke words and tables apart, and the manual is small and static, so a
one-time reviewed transcription is more reliable (decision D17).
"""

from __future__ import annotations

from enum import Enum
from importlib import resources


class PolicyTopic(str, Enum):
    ABOUT_CONTACT = "about_contact"
    HOURS = "hours"
    PAYMENT = "payment"
    RETURNS = "returns"
    SHIPPING = "shipping"
    PROMOTIONS = "promotions"
    WARRANTY = "warranty"
    PRIVACY = "privacy"


def load_policy(topic: PolicyTopic) -> str:
    return (resources.files(__package__) / "sections" / f"{topic.value}.md").read_text(
        encoding="utf-8"
    )
