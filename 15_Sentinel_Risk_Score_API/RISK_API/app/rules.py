"""Rule-based risk scoring for SENTINEL (no model call).

Each rule mirrors a feature-engineering rule from the requirement document (FE-01..FE-06,
FE-10) and maps to one reason code. The score is the sum of the weights of the rules that
fire, plus a bonus when several signals occur together, capped at 1.0. Bands and decisions
follow the initial decision policy (section 10.4).

Thresholds live in DEFAULT_CONFIG and can be overridden without a code change by pointing
SENTINEL_RULES_CONFIG at a JSON file with any subset of the same keys (FR-RE-01).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.features import amount_ratio

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict = {
    # rule thresholds
    "odd_hour_start": 0,          # FE-04: midnight-5 AM is night (start inclusive, end exclusive)
    "odd_hour_end": 5,
    "failed_attempts_min": 3,     # FE-05: has_recent_failures (>= 3)
    "new_account_days": 30,       # FE-06: is_new_account (< 30 days)
    "geo_distance_km": 500,       # FE-03: far from merchant (matches stored reason codes)
    "amount_spike_ratio": 5.0,    # FE-01: amount / avg_90d (matches stored reason codes)
    # weight each reason code adds to the score
    "weights": {
        "R01_NEW_DEVICE": 0.25,
        "R02_GEO_MISMATCH": 0.15,
        "R03_ODD_HOUR": 0.10,
        "R04_FAILED_ATTEMPTS": 0.25,
        "R05_AMOUNT_SPIKE": 0.20,
        "R06_NEW_ACCOUNT": 0.15,
    },
    # FE-10: risk compounds - bonus per fired rule beyond the second
    "combo_bonus_per_flag": 0.05,
    # section 10.4: lower bound of each band -> (risk_level, decision)
    "bands": [
        [0.85, "CRITICAL", "BLOCK"],
        [0.60, "HIGH", "REVIEW"],
        [0.30, "MEDIUM", "ALLOW"],
        [0.00, "LOW", "ALLOW"],
    ],
}

REASON_TEXT = {
    "R01_NEW_DEVICE": "First use of this device",
    "R03_ODD_HOUR": "in the {hour:02d}h IST hour (unusual time)",
    "R04_FAILED_ATTEMPTS": "after {failed_attempts} failed attempts",
    "R05_AMOUNT_SPIKE": "amount is {ratio:.0f}x the customer's 90-day average",
    "R06_NEW_ACCOUNT": "account only {account_age_days} days old",
}


def load_config(path: Optional[str] = None) -> Dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    path = path or os.getenv("SENTINEL_RULES_CONFIG")
    if path:
        override = json.loads(Path(path).read_text(encoding="utf-8"))
        cfg["weights"].update(override.pop("weights", {}))
        cfg.update(override)
        logger.info("Loaded rules config overrides from %s: %s", path, sorted(override))
    return cfg


def fired_reasons(t: Dict, cfg: Dict) -> List[str]:
    """Reason codes whose rule fires, in code order. Unknown (None) inputs never fire."""
    ratio = amount_ratio(t)
    far = t.get("distance_km") is not None and t["distance_km"] >= cfg["geo_distance_km"]
    start, end = cfg["odd_hour_start"], cfg["odd_hour_end"]
    odd = start <= t["hour"] < end if start <= end else (t["hour"] >= start or t["hour"] < end)
    checks = {
        "R01_NEW_DEVICE": t.get("is_new_device") is True,
        # FE-03: far from the merchant, or in a city not seen in the last 90 days
        "R02_GEO_MISMATCH": far or t.get("is_new_city") is True,
        "R03_ODD_HOUR": odd,
        "R04_FAILED_ATTEMPTS": t["failed_attempts"] >= cfg["failed_attempts_min"],
        # no 90-day history: a first transaction cannot be a spike against it
        "R05_AMOUNT_SPIKE": ratio is not None and ratio >= cfg["amount_spike_ratio"],
        "R06_NEW_ACCOUNT": (t.get("account_age_days") is not None
                            and t["account_age_days"] < cfg["new_account_days"]),
    }
    return [code for code, hit in checks.items() if hit]


def risk_score(reasons: List[str], cfg: Dict) -> float:
    score = sum(cfg["weights"][r] for r in reasons)
    score += cfg["combo_bonus_per_flag"] * max(0, len(reasons) - 2)
    return round(min(score, 1.0), 4)


def band(score: float, cfg: Dict) -> Tuple[str, str]:
    for lower, level, decision in cfg["bands"]:
        if score >= lower:
            return level, decision
    return cfg["bands"][-1][1], cfg["bands"][-1][2]


def explain(t: Dict, reasons: List[str]) -> str:
    if not reasons:
        return "No risk signals fired."
    ctx = {**t, "ratio": amount_ratio(t) or 0.0}
    parts = [geo_text(t) if r == "R02_GEO_MISMATCH" else REASON_TEXT[r].format(**ctx) for r in reasons]
    return ", ".join(parts) + "."


def geo_text(t: Dict) -> str:
    parts = []
    if t.get("distance_km") is not None:
        parts.append(f"{t['distance_km']:,.0f} km from the merchant")
    if t.get("is_new_city"):
        parts.append("in a city not seen in the last 90 days")
    return " ".join(parts)


def score_transaction(t: Dict, cfg: Dict) -> Dict:
    reasons = fired_reasons(t, cfg)
    score = risk_score(reasons, cfg)
    level, decision = band(score, cfg)
    return {
        "risk_score": score,
        "risk_level": level,
        "decision": decision,
        "reason_codes": reasons,
        "explanation": explain(t, reasons),
    }
