"""Lightweight SQLite persistence for occupancy history and analytics."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class AnalyticsStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS occupancy_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    total_slots INTEGER NOT NULL,
                    occupied_slots INTEGER NOT NULL,
                    available_slots INTEGER NOT NULL,
                    occupancy_rate REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS slot_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    slot_id TEXT NOT NULL,
                    zone_id TEXT NOT NULL,
                    occupied INTEGER NOT NULL,
                    source TEXT NOT NULL
                )
                """
            )

    def record_snapshot(
        self, total_slots: int, occupied_slots: int, available_slots: int, occupancy_rate: float
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO occupancy_snapshots
                    (recorded_at, total_slots, occupied_slots, available_slots, occupancy_rate)
                VALUES (?, ?, ?, ?, ?)
                """,
                (now, total_slots, occupied_slots, available_slots, round(occupancy_rate, 4)),
            )

    def record_slot_events(self, events: list[tuple[str, str, bool, str]]) -> None:
        if not events:
            return
        now = datetime.now(UTC).isoformat()
        rows = [(now, slot_id, zone_id, int(occ), source) for slot_id, zone_id, occ, source in events]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO slot_events (recorded_at, slot_id, zone_id, occupied, source)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )

    def get_recent_snapshots(self, limit: int = 60) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT recorded_at, total_slots, occupied_slots, available_slots, occupancy_rate
                FROM occupancy_snapshots
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT recorded_at, slot_id, zone_id, occupied, source
                FROM slot_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
