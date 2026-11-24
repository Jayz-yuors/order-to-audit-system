from __future__ import annotations

import csv
import io
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text,
    create_engine, func, select,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL is missing. Set it in backend/.env")

SECRET = os.getenv("JWT_SECRET", "local-change-this-secret-before-deployment")
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "8"))
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# -----------------------------------------------------------------------------
# DATABASE MODELS - map to the existing PostgreSQL schema; do not recreate it.
# -----------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    gst: Mapped[Decimal] = mapped_column(Numeric(5, 2))


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    category: Mapped[str] = mapped_column(String(30))
    unit: Mapped[str] = mapped_column(String(20))


class Movement(Base):
    __tablename__ = "movements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    delta: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    source: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    salesman_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    shortage: Mapped[int] = mapped_column(Integer, default=0)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expected: Mapped[int] = mapped_column(Integer, nullable=False)
    actual: Mapped[int] = mapped_column(Integer, nullable=False)
    yield_variance: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    oil_variance: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    run_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    taxable: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cgst: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    sgst: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    igst: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    dispatched: Mapped[bool] = mapped_column(Boolean, default=False)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class Cost(Base):
    __tablename__ = "costs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False)
    labour: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    utilities: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String(160), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(20))


class GSTRate(Base):
    __tablename__ = "gst_rates"
    gst_rate_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(160), nullable=False)
    rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)


class BOMHeader(Base):
    __tablename__ = "bom_headers"
    bom_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(160), nullable=False)
    batch_size_packets: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_output_packets: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class BOMLine(Base):
    __tablename__ = "bom_lines"
    bom_line_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bom_id: Mapped[int] = mapped_column(ForeignKey("bom_headers.bom_id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(160), nullable=False)
    quantity_per_batch: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)


class Purchase(Base):
    __tablename__ = "purchases"
    purchase_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.supplier_id"), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    reference_no: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class ProductionConsumption(Base):
    __tablename__ = "production_consumption"
    consumption_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    planned_qty: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    actual_qty: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    variance_qty: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    variance_percent: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)


class Dispatch(Base):
    __tablename__ = "dispatches"
    dispatch_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    dispatch_date: Mapped[date] = mapped_column(Date, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity_dispatched: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"
    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    performed_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    details: Mapped[Optional[str]] = mapped_column(Text)


# NOTE: No Base.metadata.create_all() here. The PostgreSQL schema was migrated
# and seeded separately. This API maps to that schema and must not mutate it.

# -----------------------------------------------------------------------------
# APP / AUTH / DB HELPERS
# -----------------------------------------------------------------------------
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth = OAuth2PasswordBearer(tokenUrl="/api/login")
app = FastAPI(title="NIT Trichy Order-to-Audit System", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def cash(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def qty(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def get_user(token: str = Depends(oauth), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        user_id = int(payload.get("sub", ""))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    current = db.get(User, user_id)
    if not current:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return current


def allow(*roles: str):
    def checker(current: User = Depends(get_user)) -> User:
        if current.role not in roles:
            raise HTTPException(status_code=403, detail="Role not permitted")
        return current
    return checker


def item_balance(db: Session, item_id: int) -> Decimal:
    total = db.scalar(select(func.coalesce(func.sum(Movement.delta), 0)).where(Movement.item_id == item_id))
    return Decimal(str(total or 0))


def add_movement(db: Session, item_id: int, delta: Decimal, source: str,
                 reference_type: str, reference_id: int) -> None:
    db.add(Movement(
        item_id=item_id,
        delta=qty(delta),
        source=source[:100],
        created_at=datetime.utcnow(),
        reference_type=reference_type,
        reference_id=reference_id,
    ))


def add_audit(db: Session, current: User, entity_type: str, entity_id: int,
              action: str, details: str) -> None:
    db.add(AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        performed_by_user_id=current.id,
        event_time=datetime.utcnow(),
        details=details,
    ))


def finished_item(db: Session) -> Item:
    # Match actual imported master data, not the old starter's category='finished'.
    result = db.scalar(select(Item).where(Item.category == "finished_goods").order_by(Item.id))
    if result is None:
        raise HTTPException(status_code=500, detail="No item with category 'finished_goods' exists")
    return result


# -----------------------------------------------------------------------------
# REQUEST SCHEMAS
# -----------------------------------------------------------------------------
class LoginInput(BaseModel):
    username: str
    password: str


class OrderInput(BaseModel):
    customer_id: int
    quantity: int = Field(gt=0)
    product_id: int = 1


class PurchaseInput(BaseModel):
    supplier_id: int
    item_id: int
    quantity: Decimal = Field(gt=0)
    unit_rate: Decimal = Field(gt=0)
    reference_no: str = Field(min_length=2, max_length=80)


class ProductionRunInput(BaseModel):
    bom_id: int
    good_packets: int = Field(gt=0)
    damaged_pouches: int = Field(default=0, ge=0)
    # Keys are item IDs as strings in JSON, values are actual material quantities.
    actual_consumption: dict[int, Decimal]


class PaymentInput(BaseModel):
    invoice_id: int
    amount: Decimal = Field(gt=0)


class CostInput(BaseModel):
    run_id: int
    labour: Decimal = Field(ge=0)
    utilities: Decimal = Field(ge=0)


# -----------------------------------------------------------------------------
# HEALTH / AUTH
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "NIT Trichy Order-to-Audit System API", "status": "running", "documentation": "/docs", "schema": "/openapi.json"}


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database connection failed")


@app.post("/api/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    current = db.scalar(select(User).where(User.username == data.username))
    if not current or not pwd.verify(data.password, current.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = jwt.encode(
        {"sub": str(current.id), "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)},
        SECRET,
        algorithm="HS256",
    )
    return {"access_token": token, "token_type": "bearer", "user": {"id": current.id, "username": current.username, "role": current.role}}


@app.get("/api/me")
def me(current: User = Depends(get_user)):
    return {"id": current.id, "username": current.username, "role": current.role}


# -----------------------------------------------------------------------------
# MASTER DATA / INVENTORY READS
# -----------------------------------------------------------------------------
@app.get("/api/customers")
def customers(db: Session = Depends(get_db), current: User = Depends(get_user)):
    return [{"id": c.id, "name": c.name, "state": c.state} for c in db.scalars(select(Customer).order_by(Customer.id))]


@app.get("/api/products")
def products(db: Session = Depends(get_db), current: User = Depends(get_user)):
    return [{"id": p.id, "name": p.name, "price": float(p.price), "gst": float(p.gst)} for p in db.scalars(select(Product).order_by(Product.id))]


@app.get("/api/inventory")
def inventory(db: Session = Depends(get_db), current: User = Depends(get_user)):
    result = []
    for item in db.scalars(select(Item).order_by(Item.id)):
        result.append({"item_id": item.id, "name": item.name, "category": item.category, "unit": item.unit, "balance": float(item_balance(db, item.id))})
    return result


@app.get("/api/inventory/ledger")
def inventory_ledger(db: Session = Depends(get_db), current: User = Depends(get_user)):
    rows = db.execute(
        select(Movement, Item).join(Item, Item.id == Movement.item_id).order_by(Movement.id)
    ).all()
    return [{
        "movement_id": movement.id, "item_id": item.id, "item": item.name,
        "delta": float(movement.delta), "source": movement.source,
        "reference_type": movement.reference_type, "reference_id": movement.reference_id,
        "created_at": movement.created_at.isoformat() if movement.created_at else None,
    } for movement, item in rows]


@app.get("/api/bom")
def list_boms(db: Session = Depends(get_db), current: User = Depends(get_user)):
    output = []
    for bom in db.scalars(select(BOMHeader).order_by(BOMHeader.bom_id)):
        lines = db.scalars(select(BOMLine).where(BOMLine.bom_id == bom.bom_id).order_by(BOMLine.bom_line_id)).all()
        output.append({
            "bom_id": bom.bom_id, "product_id": bom.product_id,
            "product_name": bom.product_name,
            "batch_size_packets": bom.batch_size_packets,
            "expected_output_packets": bom.expected_output_packets,
            "materials": [{"item_id": line.item_id, "item_name": line.item_name,
                           "quantity_per_batch": float(line.quantity_per_batch), "unit": line.unit}
                          for line in lines],
        })
    return output


# -----------------------------------------------------------------------------
# PURCHASES - purchase record + stock ledger entry are atomic
# -----------------------------------------------------------------------------
@app.post("/api/purchases")
def create_purchase(data: PurchaseInput, db: Session = Depends(get_db), current: User = Depends(allow("admin"))):
    try:
        supplier = db.get(Supplier, data.supplier_id)
        item = db.get(Item, data.item_id)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        if item is None:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        if db.scalar(select(Purchase).where(Purchase.reference_no == data.reference_no)):
            raise HTTPException(status_code=409, detail="Purchase reference already exists")
        quantity_value = qty(data.quantity)
        rate = cash(data.unit_rate)
        purchase = Purchase(
            supplier_id=supplier.supplier_id, purchase_date=date.today(),
            reference_no=data.reference_no, item_id=item.id,
            quantity=quantity_value, unit=item.unit, unit_rate=rate,
            line_total=cash(quantity_value * rate),
        )
        db.add(purchase)
        db.flush()
        add_movement(db, item.id, quantity_value, f"purchase:{purchase.purchase_id}", "purchase", purchase.purchase_id)
        add_audit(db, current, "purchase", purchase.purchase_id, "received", f"Received {quantity_value} {item.unit} of {item.name}")
        db.commit()
        return {"purchase_id": purchase.purchase_id, "reference_no": purchase.reference_no,
                "item": item.name, "quantity_received": float(quantity_value),
                "line_total": float(purchase.line_total), "new_balance": float(item_balance(db, item.id))}
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Purchase could not be saved: {str(exc.orig)}")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Purchase transaction failed")


@app.get("/api/purchases")
def get_purchases(db: Session = Depends(get_db), current: User = Depends(get_user)):
    rows = db.execute(select(Purchase, Supplier, Item).join(Supplier).join(Item)).all()
    return [{"purchase_id": p.purchase_id, "reference_no": p.reference_no,
             "supplier": s.supplier_name, "item": i.name, "quantity": float(p.quantity),
             "unit": p.unit, "unit_rate": float(p.unit_rate), "line_total": float(p.line_total),
             "purchase_date": p.purchase_date.isoformat()} for p, s, i in rows]


# -----------------------------------------------------------------------------
# SALES ORDER / APPROVAL / GST INVOICE / DISPATCH
# -----------------------------------------------------------------------------
@app.post("/api/orders")
def create_order(data: OrderInput, db: Session = Depends(get_db), current: User = Depends(allow("salesman", "admin"))):
    customer = db.get(Customer, data.customer_id)
    product = db.get(Product, data.product_id)
    if not customer or not product:
        raise HTTPException(status_code=404, detail="Customer or product not found")
    order = Order(customer_id=customer.id, salesman_id=current.id, qty=data.quantity,
                  status="submitted", shortage=0, product_id=product.id)
    db.add(order)
    db.flush()
    add_audit(db, current, "order", order.id, "submitted", f"Order quantity {order.qty}")
    db.commit()
    return {"id": order.id, "status": order.status, "quantity": order.qty}


@app.get("/api/orders")
def get_orders(db: Session = Depends(get_db), current: User = Depends(get_user)):
    query = select(Order).order_by(Order.id.desc())
    if current.role == "salesman":
        query = query.where(Order.salesman_id == current.id)
    return [{"id": o.id, "customer_id": o.customer_id, "product_id": o.product_id,
             "salesman_id": o.salesman_id, "quantity": o.qty, "status": o.status,
             "shortage": o.shortage} for o in db.scalars(query)]


@app.post("/api/orders/{order_id}/approve")
def approve_order(order_id: int, db: Session = Depends(get_db), current: User = Depends(allow("admin"))):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in ("submitted", "stock_shortage"):
        raise HTTPException(status_code=409, detail=f"Cannot approve order in status {order.status}")
    product = db.get(Product, order.product_id)
    finished = finished_item(db)
    available = int(item_balance(db, finished.id))
    order.shortage = max(0, order.qty - available)
    order.status = "stock_shortage" if order.shortage else "approved"
    add_audit(db, current, "order", order.id, "approved" if not order.shortage else "shortage_detected",
              f"Available {available}; requested {order.qty}; shortage {order.shortage}")
    db.commit()
    return {"status": order.status, "shortage": order.shortage, "available_finished_stock": available}


@app.post("/api/orders/{order_id}/invoice")
def create_invoice(order_id: int, db: Session = Depends(get_db), current: User = Depends(allow("admin"))):
    order = db.get(Order, order_id)
    if order is None or order.status != "approved":
        raise HTTPException(status_code=400, detail="Order must be approved before invoicing")
    if db.scalar(select(Invoice).where(Invoice.order_id == order.id)):
        raise HTTPException(status_code=409, detail="Invoice already exists for this order")
    customer = db.get(Customer, order.customer_id)
    product = db.get(Product, order.product_id)
    taxable = cash(Decimal(order.qty) * Decimal(str(product.price)))
    gst_total = cash(taxable * Decimal(str(product.gst)) / Decimal("100"))
    # Benchmark seller location is Tamil Nadu. Intra-state = CGST+SGST; inter-state = IGST.
    if customer.state.strip().lower() == "tamil nadu":
        cgst, sgst, igst = cash(gst_total / 2), cash(gst_total - cash(gst_total / 2)), Decimal("0.00")
    else:
        cgst, sgst, igst = Decimal("0.00"), Decimal("0.00"), gst_total
    invoice = Invoice(order_id=order.id, taxable=taxable, cgst=cgst, sgst=sgst,
                      igst=igst, total=cash(taxable + gst_total), paid=Decimal("0.00"), dispatched=False)
    db.add(invoice)
    order.status = "invoiced"
    db.flush()
    add_audit(db, current, "invoice", invoice.id, "created", f"Invoice total {invoice.total}")
    db.commit()
    return {"invoice_id": invoice.id, "taxable": float(taxable), "cgst": float(cgst),
            "sgst": float(sgst), "igst": float(igst), "total": float(invoice.total)}


@app.post("/api/invoices/{invoice_id}/dispatch")
def dispatch_invoice(invoice_id: int, db: Session = Depends(get_db), current: User = Depends(allow("admin"))):
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).with_for_update().first()
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice.dispatched:
            raise HTTPException(status_code=409, detail="Invoice has already been dispatched")
        order = db.get(Order, invoice.order_id)
        finished = db.query(Item).filter(Item.category == "finished_goods").with_for_update().first()
        if finished is None:
            raise HTTPException(status_code=500, detail="Finished goods item is not configured")
        available = item_balance(db, finished.id)
        if available < Decimal(order.qty):
            raise HTTPException(status_code=409, detail=f"Insufficient finished stock: {available} available")
        dispatch = Dispatch(invoice_id=invoice.id, dispatch_date=date.today(), product_id=order.product_id,
                            quantity_dispatched=order.qty, status="dispatched")
        db.add(dispatch)
        db.flush()
        add_movement(db, finished.id, Decimal(-order.qty), f"dispatch:{dispatch.dispatch_id}", "dispatch", dispatch.dispatch_id)
        invoice.dispatched = True
        order.status = "dispatched"
        add_audit(db, current, "dispatch", dispatch.dispatch_id, "dispatched", f"Dispatched {order.qty} packets")
        db.commit()
        return {"dispatch_id": dispatch.dispatch_id, "status": "dispatched",
                "remaining_finished_stock": float(item_balance(db, finished.id))}
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Dispatch transaction failed")


# -----------------------------------------------------------------------------
# PRODUCTION: BOM-DRIVEN, ACTUAL CONSUMPTION, STOCK LEDGER, AUDIT LOG
# -----------------------------------------------------------------------------
@app.post("/api/production/execute")
def execute_production(data: ProductionRunInput, db: Session = Depends(get_db), current: User = Depends(allow("production", "admin"))):
    try:
        bom = db.query(BOMHeader).filter(BOMHeader.bom_id == data.bom_id).with_for_update().first()
        if bom is None:
            raise HTTPException(status_code=404, detail="BOM not found")
        if data.good_packets + data.damaged_pouches <= 0:
            raise HTTPException(status_code=400, detail="Total produced quantity must be positive")
        if data.good_packets > bom.expected_output_packets:
            raise HTTPException(status_code=400, detail="Good output cannot exceed BOM batch output")
        lines = db.scalars(select(BOMLine).where(BOMLine.bom_id == bom.bom_id).order_by(BOMLine.item_id)).all()
        if not lines:
            raise HTTPException(status_code=400, detail="BOM has no material lines")
        line_item_ids = {line.item_id for line in lines}
        supplied_ids = set(data.actual_consumption.keys())
        if line_item_ids != supplied_ids:
            missing = sorted(line_item_ids - supplied_ids)
            extra = sorted(supplied_ids - line_item_ids)
            raise HTTPException(status_code=422, detail={"message": "actual_consumption must include exactly the BOM item IDs", "missing_item_ids": missing, "extra_item_ids": extra})

        # Lock item rows in ascending order to serialize stock checks and avoid deadlocks.
        locked_items = {}
        for item_id in sorted(line_item_ids):
            item = db.query(Item).filter(Item.id == item_id).with_for_update().first()
            if item is None:
                raise HTTPException(status_code=404, detail=f"BOM item {item_id} not found")
            locked_items[item_id] = item

        # One submitted run represents one complete BOM batch. Planned material
        # quantities therefore remain the BOM quantities even when yield is low.
        # Actual consumption is compared against the full-batch standard.
        scale = Decimal("1")
        consumption = []
        for line in lines:
            item = locked_items[line.item_id]
            planned = qty(Decimal(str(line.quantity_per_batch)) * scale)
            actual = qty(data.actual_consumption[line.item_id])
            if actual < 0:
                raise HTTPException(status_code=422, detail=f"Negative consumption is invalid for {item.name}")
            available = item_balance(db, item.id)
            if available < actual:
                raise HTTPException(status_code=409, detail=f"Insufficient {item.name}: available {available} {item.unit}; requested {actual}")
            variance = qty(actual - planned)
            variance_percent = Decimal("0.000") if planned == 0 else (variance / planned * 100).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            consumption.append((line, item, planned, actual, variance, variance_percent))

        finished = db.query(Item).filter(Item.category == "finished_goods").with_for_update().first()
        if finished is None:
            raise HTTPException(status_code=500, detail="Finished goods item category 'finished_goods' not found")

        expected = bom.expected_output_packets
        yield_variance = ((Decimal(data.good_packets) - Decimal(expected)) / Decimal(expected) * 100).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        oil_variance = next((row[5] for row in consumption if row[1].name.strip().lower() == "cooking oil"), Decimal("0.000"))
        run = Run(product_id=bom.product_id, expected=expected, actual=data.good_packets,
                  yield_variance=yield_variance, oil_variance=oil_variance, run_date=date.today())
        db.add(run)
        db.flush()

        for line, item, planned, actual, variance, variance_percent in consumption:
            db.add(ProductionConsumption(run_id=run.id, item_id=item.id, planned_qty=planned,
                                          actual_qty=actual, unit=item.unit,
                                          variance_qty=variance, variance_percent=variance_percent))
            add_movement(db, item.id, -actual, f"production-consumption:{run.id}", "production_run", run.id)

        add_movement(db, finished.id, Decimal(data.good_packets), f"production-output:{run.id}", "production_run", run.id)
        add_audit(db, current, "production_run", run.id, "completed",
                  f"Good packets={data.good_packets}; damaged pouches={data.damaged_pouches}; BOM={bom.bom_id}")
        db.commit()
        return {
            "run_id": run.id, "product": bom.product_name,
            "expected_output": expected, "good_output": data.good_packets,
            "damaged_pouches": data.damaged_pouches,
            "yield_variance_percent": float(yield_variance),
            "oil_variance_percent": float(oil_variance),
            "consumption": [{"item": item.name, "planned": float(planned), "actual": float(actual),
                             "variance": float(variance), "variance_percent": float(variance_percent), "unit": item.unit}
                            for _, item, planned, actual, variance, variance_percent in consumption],
            "finished_goods_balance": float(item_balance(db, finished.id)),
        }
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Production data conflict: {str(exc.orig)}")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Production transaction failed; all changes rolled back")


@app.get("/api/production/history")
def production_history(db: Session = Depends(get_db), current: User = Depends(get_user)):
    runs = db.scalars(select(Run).order_by(Run.id.desc())).all()
    return [{"run_id": r.id, "product_id": r.product_id, "expected": r.expected,
             "actual": r.actual, "yield_variance_percent": float(r.yield_variance or 0),
             "oil_variance_percent": float(r.oil_variance or 0),
             "run_date": r.run_date.isoformat() if r.run_date else None} for r in runs]


# -----------------------------------------------------------------------------
# PAYMENTS / COSTING
# -----------------------------------------------------------------------------
@app.post("/api/payments")
def record_payment(data: PaymentInput, db: Session = Depends(get_db), current: User = Depends(allow("admin"))):
    try:
        invoice = db.query(Invoice).filter(Invoice.id == data.invoice_id).with_for_update().first()
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        new_paid = cash(Decimal(str(invoice.paid)) + data.amount)
        if new_paid > Decimal(str(invoice.total)):
            raise HTTPException(status_code=400, detail="Payment exceeds invoice outstanding balance")
        payment = Payment(invoice_id=invoice.id, amount=cash(data.amount))
        db.add(payment)
        invoice.paid = new_paid
        db.flush()
        add_audit(db, current, "payment", payment.id, "received", f"Received {payment.amount} against invoice {invoice.id}")
        db.commit()
        return {"payment_id": payment.id, "paid": float(invoice.paid), "outstanding": float(cash(Decimal(str(invoice.total)) - new_paid))}
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Payment transaction failed")


@app.post("/api/production/cost")
def record_cost(data: CostInput, db: Session = Depends(get_db), current: User = Depends(allow("admin", "production"))):
    run = db.get(Run, data.run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Production run not found")
    cost = Cost(run_id=run.id, labour=cash(data.labour), utilities=cash(data.utilities))
    db.add(cost)
    db.flush()
    overhead = cash(cost.labour + cost.utilities)
    per_packet = cash(overhead / Decimal(run.actual)) if run.actual else Decimal("0.00")
    add_audit(db, current, "production_cost", cost.id, "recorded", f"Overhead={overhead}; per good packet={per_packet}")
    db.commit()
    return {"cost_id": cost.id, "overheads": float(overhead), "overhead_per_good_packet": float(per_packet)}


# -----------------------------------------------------------------------------
# REPORTS / AUDIT
# -----------------------------------------------------------------------------
@app.get("/api/reports/sales.csv")
def sales_csv(db: Session = Depends(get_db), current: User = Depends(get_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["order_id", "customer_id", "product_id", "salesman_id", "quantity", "status", "shortage"])
    query = select(Order).order_by(Order.id)
    if current.role == "salesman":
        query = query.where(Order.salesman_id == current.id)
    for order in db.scalars(query):
        writer.writerow([order.id, order.customer_id, order.product_id, order.salesman_id, order.qty, order.status, order.shortage])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=sales.csv"})


@app.get("/api/reports/stock.csv")
def stock_csv(db: Session = Depends(get_db), current: User = Depends(get_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["item_id", "item_name", "category", "unit", "closing_balance"])
    for item in db.scalars(select(Item).order_by(Item.id)):
        writer.writerow([item.id, item.name, item.category, item.unit, item_balance(db, item.id)])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=stock.csv"})


@app.get("/api/audit-log")
def audit_log(db: Session = Depends(get_db), current: User = Depends(allow("admin", "auditor"))):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.audit_id.desc()).limit(500)).all()
    return [{"audit_id": x.audit_id, "entity_type": x.entity_type, "entity_id": x.entity_id,
             "action": x.action, "performed_by_user_id": x.performed_by_user_id,
             "event_time": x.event_time.isoformat() if x.event_time else None, "details": x.details} for x in rows]


@app.get("/api/reports/receivables")
def receivables(db: Session = Depends(get_db), current: User = Depends(allow("admin", "auditor"))):
    rows = db.execute(select(Invoice, Order, Customer).join(Order, Invoice.order_id == Order.id).join(Customer, Order.customer_id == Customer.id)).all()
    return [{"invoice_id": inv.id, "order_id": order.id, "customer": customer.name,
             "total": float(inv.total), "paid": float(inv.paid),
             "outstanding": float(cash(Decimal(str(inv.total)) - Decimal(str(inv.paid)))),
             "dispatched": inv.dispatched} for inv, order, customer in rows]


@app.get("/api/reports/production.csv")
def production_csv(db: Session = Depends(get_db), current: User = Depends(get_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["run_id", "product_id", "expected", "actual", "yield_variance_percent", "oil_variance_percent", "run_date"])
    for run in db.scalars(select(Run).order_by(Run.id)):
        writer.writerow([run.id, run.product_id, run.expected, run.actual, run.yield_variance, run.oil_variance, run.run_date])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=production.csv"})
