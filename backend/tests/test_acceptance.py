"""End-to-end acceptance tests. Uses a disposable SQLite database, never production DemoDb."""
import os
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///./acceptance_test.db")
os.environ.setdefault("JWT_SECRET", "test-only-secret-change-me")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import (
    app, Base, engine, SessionLocal, pwd, User, Customer, Product, Item,
    Movement, Supplier, BOMHeader, BOMLine, Invoice, Order, Run, Payment,
    ProductionConsumption, AuditLog,
)

client = TestClient(app)


def reset_and_seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        users = [
            User(username="admin", password_hash=pwd.hash("Demo@123"), role="admin"),
            User(username="sales_a", password_hash=pwd.hash("Demo@123"), role="salesman"),
            User(username="sales_b", password_hash=pwd.hash("Demo@123"), role="salesman"),
            User(username="production", password_hash=pwd.hash("Demo@123"), role="production"),
            User(username="auditor", password_hash=pwd.hash("Demo@123"), role="auditor"),
        ]
        db.add_all(users)
        db.flush()
        db.add_all([
            Customer(id=1, name="Retailer A", state="Tamil Nadu"),
            Customer(id=2, name="Distributor B", state="Karnataka"),
            Product(id=1, name="Murukku 200 g", price=Decimal("50.00"), gst=Decimal("5.00")),
        ])
        items = [
            Item(id=1, name="Flour", category="raw_material", unit="kg"),
            Item(id=2, name="Cooking oil", category="raw_material", unit="litre"),
            Item(id=3, name="Salt and spice mix", category="raw_material", unit="kg"),
            Item(id=4, name="200 g pouch", category="packaging", unit="piece"),
            Item(id=5, name="Carton (20 packets)", category="packaging", unit="piece"),
            Item(id=6, name="Murukku 200 g finished goods", category="finished_goods", unit="packet"),
        ]
        db.add_all(items)
        db.flush()
        opening = [100, 30, 5, 500, 30, 50]
        for item, balance in zip(items, opening):
            db.add(Movement(item_id=item.id, delta=Decimal(str(balance)), source="test opening stock"))
        supplier = Supplier(supplier_id=1, supplier_name="Test Supplier", state="Tamil Nadu", gstin=None)
        db.add(supplier)
        bom = BOMHeader(bom_id=1, product_id=1, product_name="Murukku 200 g", batch_size_packets=1, expected_output_packets=200)
        db.add(bom)
        db.flush()
        bom_lines = [
            (1, "Flour", "40", "kg"), (2, "Cooking oil", "10", "litre"),
            (3, "Salt and spice mix", "1.2", "kg"), (4, "200 g pouch", "200", "piece"),
            (5, "Carton (20 packets)", "10", "piece"),
        ]
        for item_id, name, q, unit in bom_lines:
            db.add(BOMLine(bom_id=1, item_id=item_id, item_name=name, quantity_per_batch=Decimal(q), unit=unit))
        db.commit()
    finally:
        db.close()


def token(username):
    r = client.post("/api/login", json={"username": username, "password": "Demo@123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def headers(username):
    return {"Authorization": f"Bearer {token(username)}"}


def test_full_acceptance_flow():
    reset_and_seed()
    admin = headers("admin")
    salesman = headers("sales_a")
    production = headers("production")
    auditor = headers("auditor")

    # Health, login and role identity.
    assert client.get("/api/health").json() == {"status": "ok", "database": "connected"}
    assert client.get("/api/me", headers=auditor).json()["role"] == "auditor"

    # Salesman cannot create a purchase; auditor is read-only.
    purchase_body = {"supplier_id": 1, "item_id": 1, "quantity": 60, "unit_rate": 45, "reference_no": "TEST-PUR-001"}
    assert client.post("/api/purchases", headers=auditor, json=purchase_body).status_code == 403
    assert client.post("/api/purchases", headers=salesman, json=purchase_body).status_code == 403

    # Purchase -> flour 160 kg.
    p = client.post("/api/purchases", headers=admin, json=purchase_body)
    assert p.status_code == 200, p.text
    assert p.json()["new_balance"] == 160.0
    assert p.json()["line_total"] == 2700.0
    duplicate_purchase = client.post("/api/purchases", headers=admin, json=purchase_body)
    assert duplicate_purchase.status_code == 409
    assert client.get("/api/inventory", headers=admin).json()[0]["balance"] == 160.0

    # An insufficient-material production attempt must roll back completely.
    invalid_run = {"bom_id": 1, "good_packets": 188, "damaged_pouches": 6,
                   "actual_consumption": {"1": 999, "2": 10.5, "3": 1.2, "4": 194, "5": 9}}
    assert client.post("/api/production/execute", headers=production, json=invalid_run).status_code == 409
    assert client.get("/api/production/history", headers=admin).json() == []

    # Production: actual materials, good output and damaged pouches.
    run_body = {"bom_id": 1, "good_packets": 188, "damaged_pouches": 6,
                "actual_consumption": {"1": 40, "2": 10.5, "3": 1.2, "4": 194, "5": 9}}
    run = client.post("/api/production/execute", headers=production, json=run_body)
    assert run.status_code == 200, run.text
    run_data = run.json()
    assert run_data["expected_output"] == 200
    assert run_data["good_output"] == 188
    assert run_data["yield_variance_percent"] == -6.0
    assert run_data["oil_variance_percent"] == 5.0
    oil_row = next(x for x in run_data["consumption"] if x["item"] == "Cooking oil")
    assert oil_row["planned"] == 10.0 and oil_row["actual"] == 10.5
    assert run_data["finished_goods_balance"] == 238.0

    # Order A -> approval -> GST invoice -> dispatch -> payment.
    order_a = client.post("/api/orders", headers=salesman, json={"customer_id": 1, "quantity": 150, "product_id": 1})
    assert order_a.status_code == 200, order_a.text
    order_a_id = order_a.json()["id"]
    assert [x["id"] for x in client.get("/api/orders", headers=salesman).json()] == [order_a_id]
    approve_a = client.post(f"/api/orders/{order_a_id}/approve", headers=admin)
    assert approve_a.status_code == 200 and approve_a.json()["status"] == "approved"
    invoice = client.post(f"/api/orders/{order_a_id}/invoice", headers=admin)
    assert invoice.status_code == 200, invoice.text
    inv = invoice.json()
    assert (inv["taxable"], inv["cgst"], inv["sgst"], inv["igst"], inv["total"]) == (7500.0, 187.5, 187.5, 0.0, 7875.0)
    dispatch = client.post(f"/api/invoices/{inv['invoice_id']}/dispatch", headers=admin)
    assert dispatch.status_code == 200 and dispatch.json()["remaining_finished_stock"] == 88.0
    payment = client.post("/api/payments", headers=admin, json={"invoice_id": inv["invoice_id"], "amount": 4000})
    assert payment.status_code == 200, payment.text
    assert payment.json()["outstanding"] == 3875.0

    # Order B -> shortage of 32; cannot invoice while short.
    order_b = client.post("/api/orders", headers=headers("sales_b"), json={"customer_id": 2, "quantity": 120, "product_id": 1})
    assert order_b.status_code == 200, order_b.text
    order_b_id = order_b.json()["id"]
    approve_b = client.post(f"/api/orders/{order_b_id}/approve", headers=admin)
    assert approve_b.status_code == 200
    assert approve_b.json()["status"] == "stock_shortage"
    assert approve_b.json()["shortage"] == 32
    assert client.post(f"/api/orders/{order_b_id}/invoice", headers=admin).status_code == 400

    # A smaller interstate order can be approved and should use IGST.
    order_c = client.post("/api/orders", headers=headers("sales_b"), json={"customer_id": 2, "quantity": 10, "product_id": 1})
    assert order_c.status_code == 200, order_c.text
    order_c_id = order_c.json()["id"]
    assert client.post(f"/api/orders/{order_c_id}/approve", headers=admin).json()["status"] == "approved"
    interstate_invoice = client.post(f"/api/orders/{order_c_id}/invoice", headers=admin)
    assert interstate_invoice.status_code == 200, interstate_invoice.text
    assert interstate_invoice.json()["igst"] == 25.0
    assert interstate_invoice.json()["cgst"] == 0.0 and interstate_invoice.json()["sgst"] == 0.0

    # Cost entry and expected overhead per good packet.
    cost = client.post("/api/production/cost", headers=production,
                       json={"run_id": run_data["run_id"], "labour": 1200, "utilities": 600})
    assert cost.status_code == 200, cost.text
    assert cost.json()["overheads"] == 1800.0
    assert cost.json()["overhead_per_good_packet"] == round(1800 / 188, 2)

    # Verify final inventory balances from ledger.
    stock = {x["name"]: x["balance"] for x in client.get("/api/inventory", headers=admin).json()}
    assert stock["Flour"] == 120.0
    assert stock["Cooking oil"] == 19.5
    assert stock["Salt and spice mix"] == 3.8
    assert stock["200 g pouch"] == 306.0
    assert stock["Carton (20 packets)"] == 21.0
    assert stock["Murukku 200 g finished goods"] == 88.0

    # Every transaction-created movement must be traceable to a source record.
    ledger = client.get("/api/inventory/ledger", headers=admin).json()
    tx_movements = [x for x in ledger if x["source"] != "test opening stock"]
    assert tx_movements and all(x["reference_type"] and x["reference_id"] for x in tx_movements)

    # Auditor can read reports/audit but cannot mutate.
    assert client.get("/api/audit-log", headers=auditor).status_code == 200
    assert client.get("/api/reports/receivables", headers=auditor).json()[0]["outstanding"] == 3875.0
    assert client.post("/api/payments", headers=auditor, json={"invoice_id": inv["invoice_id"], "amount": 1}).status_code == 403
    assert client.post(f"/api/orders/{order_a_id}/approve", headers=salesman).status_code == 403
    assert client.post("/api/purchases", headers=production, json=purchase_body).status_code == 403

    # Reports respond and contain benchmark rows.
    assert "120.000" in client.get("/api/reports/stock.csv", headers=admin).text
    assert "-6.000" in client.get("/api/reports/production.csv", headers=admin).text
    assert "pending_stock_shortage" not in client.get("/api/reports/sales.csv", headers=headers("sales_a")).text
    assert "dispatched" in client.get("/api/reports/sales.csv", headers=salesman).text

    # Reject overpayment and duplicate dispatch.
    assert client.post("/api/payments", headers=admin,
                       json={"invoice_id": inv["invoice_id"], "amount": 99999}).status_code == 400
    assert client.post(f"/api/invoices/{inv['invoice_id']}/dispatch", headers=admin).status_code == 409
