"""Persistent per-attempt spending reservations shared by processes and providers."""
from __future__ import annotations

import json
import math
from pathlib import Path
import sqlite3
import time
import uuid

from .config import pricing


class BudgetError(RuntimeError):
    """Stop the run before further requests when spending cannot be bounded."""


class Budget:
    def __init__(self, path: str, limit: float, *, openai_limit: float | None = None):
        self.path, self.limit = Path(path), limit
        if not math.isfinite(limit) or limit <= 0:
            raise ValueError("Budget limit must be finite and positive")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY CHECK(id=1), limit_usd REAL NOT NULL)")
            db.execute("INSERT OR IGNORE INTO budget VALUES(1, ?)", (limit,))
            if db.execute("SELECT limit_usd FROM budget WHERE id=1").fetchone()[0] != limit:
                raise BudgetError("Existing ledger limit differs; cannot reset or expand it implicitly")
            db.execute("CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, kind TEXT NOT NULL, model TEXT, reserved REAL NOT NULL, actual REAL, created REAL NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS service_budgets (service TEXT PRIMARY KEY, limit_usd REAL NOT NULL)")
            if openai_limit is not None:
                if not math.isfinite(openai_limit) or openai_limit <= 0:
                    raise ValueError("OpenAI sublimit must be finite and positive")
                db.execute("INSERT OR IGNORE INTO service_budgets VALUES('openai', ?)", (openai_limit,))
                if db.execute("SELECT limit_usd FROM service_budgets WHERE service='openai'").fetchone()[0] != openai_limit:
                    raise BudgetError("Existing OpenAI sublimit differs; cannot expand or reset it implicitly")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=30)

    def reserve(self, kind: str, identity: dict, body: dict) -> str:
        rates = pricing().get(kind)
        if not isinstance(rates, dict) or rates.get("input") is None or rates.get("output") is None:
            raise BudgetError(f"Known input/output prices required before paid {kind} requests")
        output_tokens = body.get("max_output_tokens", body.get("max_tokens", 0))
        if rates["output"] and (type(output_tokens) is not int or output_tokens <= 0):
            raise BudgetError("Paid output requires an explicit maximum token count")
        # Text-only research requests: UTF-8 bytes bound text tokens; include generous framing overhead.
        # Jev may evaluate each typed question separately, so reserve repeated state conservatively.
        copies = max(1, len(body.get("questions", {}))) if kind == "jev" else 1
        upper_input_tokens = (len(json.dumps(body, ensure_ascii=False).encode()) + 4096) * copies
        reservation = (upper_input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
        call_id = uuid.uuid4().hex
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            used = db.execute("SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM calls").fetchone()[0]
            if used + reservation > self.limit:
                raise BudgetError(f"Experiment budget would exceed ${self.limit:.2f}; paid calls stopped")
            # Generation and LF-Eval judge share the paper's OpenAI account.
            # Read the persisted sublimit even when an older caller omits the option.
            if kind in ("generation", "judge"):
                cap = db.execute("SELECT limit_usd FROM service_budgets WHERE service='openai'").fetchone()
                if cap is not None:
                    openai_used = db.execute("SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM calls WHERE kind IN ('generation','judge')").fetchone()[0]
                    if openai_used + reservation > cap[0]:
                        raise BudgetError(f"OpenAI generation + LF-Eval would exceed ${cap[0]:.2f}; paid calls stopped")
            db.execute("INSERT INTO calls VALUES(?,?,?,?,NULL,?)", (call_id, kind, identity.get("model"), reservation, time.time()))
        return call_id

    def settle(self, call_id: str, actual: float | None):
        # Unknown usage, failures, timeouts and process crashes retain the whole reservation.
        if actual is None:
            return
        if not math.isfinite(actual) or actual < 0:
            raise BudgetError("Invalid actual charge")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT reserved,actual FROM calls WHERE id=?", (call_id,)).fetchone()
            if row is None or row[1] is not None:
                raise BudgetError("Unknown or already-settled request")
            db.execute("UPDATE calls SET actual=? WHERE id=?", (actual, call_id))
        if actual > row[0]:
            raise BudgetError("Observed charge exceeded conservative reservation; stop and reconcile provider billing")

    def summary(self) -> dict:
        with self._connect() as db:
            count, known, pending, accounted = db.execute("SELECT COUNT(*), COALESCE(SUM(actual),0), SUM(actual IS NULL), COALESCE(SUM(COALESCE(actual,reserved)),0) FROM calls").fetchone()
            caps = dict(db.execute("SELECT service,limit_usd FROM service_budgets").fetchall())
            services = {}
            if "openai" in caps:
                service_known, service_used = db.execute("SELECT COALESCE(SUM(actual),0), COALESCE(SUM(COALESCE(actual,reserved)),0) FROM calls WHERE kind IN ('generation','judge')").fetchone()
                services["openai"] = {"limit_usd": caps["openai"], "known_cost_usd": service_known,
                    "accounted_with_reservations_usd": service_used, "remaining_usd": max(0, caps["openai"] - service_used)}
        result = {"limit_usd": self.limit, "attempts": count, "known_cost_usd": known,
                "unsettled_attempts": pending or 0, "accounted_with_reservations_usd": accounted,
                "remaining_usd": max(0, self.limit - accounted)}
        if services:
            result["service_limits"] = services
        return result
