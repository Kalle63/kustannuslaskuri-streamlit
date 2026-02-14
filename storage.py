from __future__ import annotations

import sqlite3
from pathlib import Path

from models import ProjectCalculation, ProjectQuoteInput, QuoteHistoryRecord

DB_PATH = Path(__file__).resolve().parent / "quotes.db"


def _table_columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(quotes)")}


def _ensure_column(conn: sqlite3.Connection, column_name: str, definition: str) -> None:
    if column_name not in _table_columns(conn):
        conn.execute(f"ALTER TABLE quotes ADD COLUMN {column_name} {definition}")


def init_db(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            customer_name TEXT NOT NULL,
            report_html TEXT NOT NULL,
            input_json TEXT,
            result_json TEXT,
            project_name TEXT,
            total_revenue_net REAL,
            total_revenue_gross REAL,
            variable_cost_total REAL,
            contribution_margin REAL,
            contribution_margin_pct REAL,
            price_excl_vat REAL,
            price_incl_vat REAL,
            profit_amount REAL,
            profitability_pct REAL
        )
        """
    )

    # New schema columns
    _ensure_column(conn, "input_json", "TEXT")
    _ensure_column(conn, "result_json", "TEXT")
    _ensure_column(conn, "project_name", "TEXT")
    _ensure_column(conn, "total_revenue_net", "REAL")
    _ensure_column(conn, "total_revenue_gross", "REAL")
    _ensure_column(conn, "variable_cost_total", "REAL")
    _ensure_column(conn, "contribution_margin", "REAL")
    _ensure_column(conn, "contribution_margin_pct", "REAL")

    # Legacy compatibility columns (may exist from older app versions)
    _ensure_column(conn, "billing_unit", "TEXT")
    _ensure_column(conn, "quantity", "REAL")
    _ensure_column(conn, "unit_rate", "REAL")
    _ensure_column(conn, "work_hours", "REAL")
    _ensure_column(conn, "hourly_rate", "REAL")
    _ensure_column(conn, "materials_cost", "REAL")
    _ensure_column(conn, "overhead_pct", "REAL")
    _ensure_column(conn, "margin_pct", "REAL")
    _ensure_column(conn, "vat_pct", "REAL")
    _ensure_column(conn, "service_cost", "REAL")
    _ensure_column(conn, "price_excl_vat", "REAL")
    _ensure_column(conn, "vat_amount", "REAL")
    _ensure_column(conn, "price_incl_vat", "REAL")
    _ensure_column(conn, "profit_amount", "REAL")
    _ensure_column(conn, "profitability_pct", "REAL")

    conn.commit()
    conn.close()


def save_quote(
    quote: ProjectQuoteInput,
    result: ProjectCalculation,
    report_html: str,
    db_path: Path = DB_PATH,
) -> int:
    conn = sqlite3.connect(db_path)
    table_columns = _table_columns(conn)

    values_by_column = {
        "customer_name": quote.customer_name,
        "project_name": quote.project_name,
        "report_html": report_html,
        "input_json": quote.model_dump_json(),
        "result_json": result.model_dump_json(),
        "total_revenue_net": result.total_revenue_net,
        "total_revenue_gross": result.total_revenue_gross,
        "variable_cost_total": result.variable_cost_total,
        "contribution_margin": result.contribution_margin,
        "contribution_margin_pct": result.contribution_margin_pct,
        # Legacy fields
        "price_excl_vat": result.total_revenue_net,
        "price_incl_vat": result.total_revenue_gross,
        "profit_amount": result.contribution_margin,
        "profitability_pct": result.contribution_margin_pct,
        "billing_unit": "words",
        "quantity": float(result.words_total),
        "unit_rate": result.revenue_per_word,
        "work_hours": float(result.words_total),
        "hourly_rate": result.revenue_per_word,
        "materials_cost": result.other_cost_total,
        "overhead_pct": 0.0,
        "margin_pct": 0.0,
        "vat_pct": 0.0,
        "service_cost": result.total_revenue_net,
        "vat_amount": result.total_revenue_vat,
    }

    insert_columns = [column for column in values_by_column if column in table_columns]
    placeholders = ", ".join("?" for _ in insert_columns)
    sql = f"INSERT INTO quotes ({', '.join(insert_columns)}) VALUES ({placeholders})"
    sql_values = tuple(values_by_column[column] for column in insert_columns)

    cursor = conn.execute(sql, sql_values)
    conn.commit()
    row_id = int(cursor.lastrowid)
    conn.close()
    return row_id


def get_quote_history(db_path: Path = DB_PATH) -> list[QuoteHistoryRecord]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM quotes ORDER BY id DESC").fetchall()
    conn.close()

    return [QuoteHistoryRecord(**dict(row)) for row in rows]
