"""
Import the 8 extended benchmark CSVs into PostgreSQL.

Place this script beside db_config.py and keep the dataset at:
    NIT_datasets/extended_for_full_requirements/

Run:
    python import_extended_csv_data.py

The script validates CSV headers against the actual PostgreSQL table columns,
checks foreign-key references through PostgreSQL, and commits all inserts in
one transaction. It refuses to duplicate existing rows.
"""

import argparse
import csv
import sys
from pathlib import Path

from psycopg2 import sql
from db_config import create_connection

CSV_DIR = Path(__file__).resolve().parent / "seed_data" / "NIT_Order_Audit_Dummy_CSV_Data" / "extended_for_full_requirements"

# Parent tables first; child tables afterwards.
IMPORT_PLAN = [
    ("suppliers", [
        "supplier_id", "supplier_name", "state", "gstin"
    ], "supplier_id"),
    ("gst_rates", [
        "gst_rate_id", "description", "rate_percent", "effective_from"
    ], "gst_rate_id"),
    ("bom_headers", [
        "bom_id", "product_id", "product_name",
        "batch_size_packets", "expected_output_packets"
    ], "bom_id"),
    ("bom_lines", [
        "bom_line_id", "bom_id", "item_id", "item_name",
        "quantity_per_batch", "unit"
    ], "bom_line_id"),
    ("purchases", [
        "purchase_id", "supplier_id", "purchase_date", "reference_no",
        "item_id", "quantity", "unit", "unit_rate", "line_total"
    ], "purchase_id"),
    ("production_consumption", [
        "consumption_id", "run_id", "item_id", "planned_qty",
        "actual_qty", "unit", "variance_qty", "variance_percent"
    ], "consumption_id"),
    ("dispatches", [
        "dispatch_id", "invoice_id", "dispatch_date",
        "product_id", "quantity_dispatched", "status"
    ], "dispatch_id"),
    ("audit_log", [
        "audit_id", "entity_type", "entity_id", "action",
        "performed_by_user_id", "event_time", "details"
    ], "audit_id"),
]


def load_csv(table, expected_columns):
    path = CSV_DIR / f"{table}.csv"
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        actual = [c.strip() for c in (reader.fieldnames or [])]
        if actual != expected_columns:
            raise ValueError(
                f"{path.name} header mismatch.\n"
                f"Expected: {expected_columns}\nFound: {actual}"
            )

        rows = []
        for row in reader:
            clean = {
                key: (value.strip() if value is not None else None)
                for key, value in row.items()
            }
            if any(v not in ("", None) for v in clean.values()):
                rows.append(clean)
        return rows


def get_table_columns(cur, table):
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    return [r[0] for r in cur.fetchall()]


def count_rows(cur, table):
    cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
    return cur.fetchone()[0]


def insert_rows(cur, table, columns, rows):
    if not rows:
        print(f"  {table}: 0 rows")
        return 0

    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in columns),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )
    values = [
        tuple(row[c] if row[c] != "" else None for c in columns)
        for row in rows
    ]
    cur.executemany(query, values)
    print(f"  {table}: imported {len(values)} rows")
    return len(values)


def reset_sequence(cur, table, id_column):
    cur.execute(
        "SELECT setval(pg_get_serial_sequence(%s, %s), "
        "GREATEST(COALESCE((SELECT MAX(" + id_column + ") FROM " + table + "), 1), 1), "
        "COALESCE((SELECT MAX(" + id_column + ") FROM " + table + "), 0) > 0)",
        (table, id_column),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset", action="store_true",
        help="Delete existing rows in these 8 extended tables before importing."
    )
    args = parser.parse_args()

    if not CSV_DIR.is_dir():
        print(f"CSV folder not found: {CSV_DIR}")
        return 1

    # Validate all CSVs before connecting.
    try:
        prepared = [
            (table, columns, id_col, load_csv(table, columns))
            for table, columns, id_col in IMPORT_PLAN
        ]
    except Exception as exc:
        print(f"CSV validation failed: {exc}")
        return 1

    conn = None
    try:
        conn = create_connection()
        conn.autocommit = False

        with conn.cursor() as cur:
            for table, expected, _, _ in prepared:
                actual = get_table_columns(cur, table)
                if not actual:
                    raise RuntimeError(f"Table public.{table} does not exist.")
                missing = [c for c in expected if c not in actual]
                if missing:
                    raise RuntimeError(
                        f"Table {table} is missing columns: {missing}. "
                        f"Actual columns: {actual}"
                    )

            populated = {
                table: count_rows(cur, table)
                for table, _, _, _ in prepared
            }
            populated = {t: n for t, n in populated.items() if n}

            if args.reset:
                print("WARNING: resetting only the eight extended tables.")
                cur.execute(
                    sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                        sql.SQL(", ").join(
                            sql.Identifier(table)
                            for table, _, _, _ in prepared
                        )
                    )
                )
            elif populated:
                detail = ", ".join(f"{t}={n}" for t, n in populated.items())
                raise RuntimeError(
                    "Extended tables already contain data: " + detail +
                    ". No changes made. Use --reset only if you intend to replace it."
                )

            print("Importing extended benchmark CSV files:")
            total = 0
            for table, columns, id_col, rows in prepared:
                total += insert_rows(cur, table, columns, rows)

            for table, _, id_col, _ in prepared:
                reset_sequence(cur, table, id_col)

        conn.commit()
        print(f"\nSUCCESS: imported {total} rows into 8 extended tables.")
        print("All inserts committed in one transaction.")
        return 0

    except Exception as exc:
        if conn is not None:
            conn.rollback()
        print(f"\nIMPORT FAILED. All changes rolled back.\nReason: {exc}")
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
