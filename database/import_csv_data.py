"""
Import the schema-compatible NIT Order-to-Audit CSV files into PostgreSQL.

Expected folder:
NIT_datasets/
    schema_compatible/
        users.csv, customers.csv, products.csv, items.csv, movements.csv,
        orders.csv, runs.csv, invoices.csv, payments.csv, costs.csv

Keep db_config.py in the same directory as this script. It must expose:
    create_connection()

Usage:
    python import_csv_data.py
    python import_csv_data.py --reset

Default mode refuses to import if any target table already contains rows.
--reset TRUNCATES the ten target tables (and dependent rows) before importing.
"""

import argparse
import csv
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql

from db_config import create_connection


# Edit this path if your schema_compatible folder is somewhere else.
CSV_DIR = Path(__file__).resolve().parent / "seed_data" / "NIT_Order_Audit_Dummy_CSV_Data" / "schema_compatible"

# Order matters because of foreign-key dependencies.
IMPORT_PLAN = [
    ("users", ["id", "username", "password_hash", "role"]),
    ("customers", ["id", "name", "state"]),
    ("products", ["id", "name", "price", "gst"]),
    ("items", ["id", "name", "category", "unit"]),
    ("movements", ["id", "item_id", "delta", "source"]),
    ("orders", ["id", "customer_id", "salesman_id", "qty", "status", "shortage"]),
    ("runs", ["id", "expected", "actual", "yield_variance", "oil_variance"]),
    ("invoices", [
        "id", "order_id", "taxable", "cgst", "sgst", "igst",
        "total", "paid", "dispatched"
    ]),
    ("payments", ["id", "invoice_id", "amount"]),
    ("costs", ["id", "run_id", "labour", "utilities"]),
]


def read_csv_rows(csv_path: Path, expected_columns: list[str]) -> list[dict]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"Missing CSV file: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(f"{csv_path.name} is empty or has no header.")

        actual = [name.strip() for name in reader.fieldnames]
        if actual != expected_columns:
            raise ValueError(
                f"Header mismatch in {csv_path.name}\n"
                f"Expected: {expected_columns}\n"
                f"Found:    {actual}"
            )

        rows = []
        for line_number, row in enumerate(reader, start=2):
            cleaned = {
                key: (value.strip() if value is not None else None)
                for key, value in row.items()
            }

            if all(value in (None, "") for value in cleaned.values()):
                continue

            # The supplied dummy dataset may contain a placeholder hash if bcrypt
            # was unavailable when the CSV bundle was generated. Replace it here
            # with a real bcrypt hash for the documented demo password.
            if csv_path.name == "users.csv":
                password_hash = cleaned.get("password_hash", "")
                if not password_hash or password_hash.startswith("REPLACE_WITH_"):
                    try:
                        import bcrypt
                    except ImportError as exc:
                        raise RuntimeError(
                            "bcrypt is required to generate demo password hashes. "
                            "Install it with: pip install bcrypt"
                        ) from exc

                    # All dummy accounts use this local-only password.
                    demo_password = b"Demo@123"
                    cleaned["password_hash"] = bcrypt.hashpw(
                        demo_password, bcrypt.gensalt(rounds=12)
                    ).decode("utf-8")

            rows.append(cleaned)

    return rows


def table_row_count(cursor, table_name: str) -> int:
    cursor.execute(
        sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name))
    )
    return cursor.fetchone()[0]


def insert_rows(cursor, table_name: str, columns: list[str], rows: list[dict]) -> int:
    if not rows:
        print(f"  {table_name}: 0 rows (empty CSV)")
        return 0

    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )

    values = [
        tuple(row[column] if row[column] != "" else None for column in columns)
        for row in rows
    ]

    cursor.executemany(query, values)
    print(f"  {table_name}: imported {len(values)} rows")
    return len(values)


def reset_serial_sequence(cursor, table_name: str) -> None:
    # Explicit CSV IDs do not automatically advance SERIAL sequences.
    cursor.execute(
        """
        SELECT setval(
            pg_get_serial_sequence(%s, 'id'),
            GREATEST(COALESCE((SELECT MAX(id) FROM """ + table_name + """), 1), 1),
            COALESCE((SELECT MAX(id) FROM """ + table_name + """), 0) > 0
        )
        """,
        (table_name,),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Import NIT benchmark CSV data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="TRUNCATE all ten target tables before import. This deletes existing rows.",
    )
    args = parser.parse_args()

    if not CSV_DIR.is_dir():
        print(f"CSV folder not found:\n{CSV_DIR}")
        print("Edit CSV_DIR near the top of this script to point to schema_compatible.")
        return 1

    # Read and validate every CSV before opening a database transaction.
    prepared = []
    try:
        for table_name, columns in IMPORT_PLAN:
            rows = read_csv_rows(CSV_DIR / f"{table_name}.csv", columns)
            prepared.append((table_name, columns, rows))
    except Exception as error:
        print(f"CSV validation failed: {error}")
        return 1

    connection = None
    try:
        connection = create_connection()
        connection.autocommit = False

        with connection.cursor() as cursor:
            target_tables = [table for table, _ in IMPORT_PLAN]

            # Confirm all expected tables exist.
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = ANY(%s)
                """,
                (target_tables,),
            )
            existing = {row[0] for row in cursor.fetchall()}
            missing = sorted(set(target_tables) - existing)
            if missing:
                raise RuntimeError(
                    "Missing database tables: " + ", ".join(missing)
                    + ". Run schema.sql first."
                )

            if args.reset:
                print("WARNING: --reset will delete all rows in the ten target tables.")
                cursor.execute(
                    sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                        sql.SQL(", ").join(map(sql.Identifier, target_tables))
                    )
                )
            else:
                populated = {
                    table: table_row_count(cursor, table)
                    for table in target_tables
                }
                populated = {table: count for table, count in populated.items() if count}
                if populated:
                    details = ", ".join(
                        f"{table}={count}" for table, count in populated.items()
                    )
                    raise RuntimeError(
                        "Import stopped because target tables already contain data: "
                        + details
                        + ". Back up first; rerun with --reset only if you intend "
                          "to replace those rows."
                    )

            print("\nImporting schema-compatible CSV files:")
            total = 0
            for table_name, columns, rows in prepared:
                total += insert_rows(cursor, table_name, columns, rows)

            for table_name, _ in IMPORT_PLAN:
                reset_serial_sequence(cursor, table_name)

        connection.commit()
        print(f"\nSUCCESS: imported {total} rows into {len(IMPORT_PLAN)} tables.")
        print("CSV import transaction committed.")
        return 0

    except Exception as error:
        if connection is not None:
            connection.rollback()
        print(f"\nIMPORT FAILED. All changes were rolled back.\nReason: {error}")
        return 1

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    sys.exit(main())
