
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# --------------------------------------------------
# 1. USERS AND ACCESS CONTROL
# --------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# --------------------------------------------------
# 2. MASTER DATA
# --------------------------------------------------

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    hsn_code: Mapped[str] = mapped_column(String(20), default="")
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("5"))
    unit: Mapped[str] = mapped_column(String(20), default="packet")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20), default="")
    gstin: Mapped[str] = mapped_column(String(20), default="")
    state: Mapped[str] = mapped_column(String(50))
    address: Mapped[str] = mapped_column(Text, default="")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20), default="")
    gstin: Mapped[str] = mapped_column(String(20), default="")
    state: Mapped[str] = mapped_column(String(50))


class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    base_unit: Mapped[str] = mapped_column(String(20))
    reorder_level: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# --------------------------------------------------
# 3. BILL OF MATERIALS
# --------------------------------------------------

class BOM(Base):
    __tablename__ = "boms"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    batch_output_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class BOMItem(Base):
    __tablename__ = "bom_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    bom_id: Mapped[int] = mapped_column(ForeignKey("boms.id"))
    raw_material_id: Mapped[int] = mapped_column(
        ForeignKey("raw_materials.id")
    )
    standard_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit: Mapped[str] = mapped_column(String(20))


# --------------------------------------------------
# 4. INVENTORY MOVEMENT LEDGER
# --------------------------------------------------

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_type: Mapped[str] = mapped_column(String(30))
    item_id: Mapped[int] = mapped_column(Integer)
    movement_type: Mapped[str] = mapped_column(String(30))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit: Mapped[str] = mapped_column(String(20))
    reference_type: Mapped[str] = mapped_column(String(40))
    reference_id: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


# --------------------------------------------------
# 5. PURCHASES
# --------------------------------------------------

class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    invoice_number: Mapped[str] = mapped_column(String(50))
    purchase_date: Mapped[datetime] = mapped_column(DateTime)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(30), default="POSTED")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id"))
    raw_material_id: Mapped[int] = mapped_column(
        ForeignKey("raw_materials.id")
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit: Mapped[str] = mapped_column(String(20))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))


# --------------------------------------------------
# 6. PRODUCTION
# --------------------------------------------------

class ProductionRun(Base):
    __tablename__ = "production_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_number: Mapped[str] = mapped_column(String(50), unique=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    bom_id: Mapped[int] = mapped_column(ForeignKey("boms.id"))
    planned_output: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    actual_good_output: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    damaged_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0")
    )
    cartons_used: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0")
    )
    labour_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    overhead_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    status: Mapped[str] = mapped_column(String(30), default="POSTED")
    production_date: Mapped[datetime] = mapped_column(DateTime)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))


class ProductionConsumption(Base):
    __tablename__ = "production_consumptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    production_run_id: Mapped[int] = mapped_column(
        ForeignKey("production_runs.id")
    )
    raw_material_id: Mapped[int] = mapped_column(
        ForeignKey("raw_materials.id")
    )
    planned_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    actual_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit: Mapped[str] = mapped_column(String(20))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4))


# --------------------------------------------------
# 7. SALES AND INVOICING
# --------------------------------------------------

class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    salesman_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    order_date: Mapped[datetime] = mapped_column(DateTime)
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"))
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cgst: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    sgst: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    igst: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(30), default="POSTED")
    invoice_date: Mapped[datetime] = mapped_column(DateTime)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    payment_method: Mapped[str] = mapped_column(String(30))
    reference_number: Mapped[str] = mapped_column(String(100), default="")
    payment_date: Mapped[datetime] = mapped_column(DateTime)


# --------------------------------------------------
# 8. AUDIT TRAIL
# --------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(Integer)
    details: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
