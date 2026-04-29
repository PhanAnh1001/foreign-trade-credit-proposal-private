"""Load and cache LC rules from YAML knowledge base."""
from __future__ import annotations
from pathlib import Path
from functools import lru_cache
import yaml

_RULES_DIR = Path(__file__).parent / "rules"


@lru_cache(maxsize=None)
def load_ucp600_rules() -> dict:
    with open(_RULES_DIR / "ucp600_rules.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=None)
def load_isbp821_rules() -> dict:
    with open(_RULES_DIR / "isbp821_rules.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=None)
def load_incoterms_rules() -> dict:
    with open(_RULES_DIR / "incoterms_rules.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_required_documents_for_incoterms(incoterms_term: str) -> dict:
    """Return document requirements dict for a given Incoterms term."""
    rules = load_incoterms_rules()
    term = incoterms_term.upper()
    terms = rules.get("terms", {})
    return terms.get(term, terms.get("DEFAULT", {}))


def get_presentation_period_default() -> int:
    """UCP600 Article 14(c): 21 calendar days after the date of shipment."""
    rules = load_ucp600_rules()
    return rules.get("article_14c", {}).get("presentation_period_days", 21)
