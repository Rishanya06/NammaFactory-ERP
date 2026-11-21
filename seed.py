
from datetime import datetime
from decimal import Decimal
import hashlib
import secrets

from sqlalchemy import select, func

from database import SessionLocal, initialize_database
from models import (
    User,
    Product,
    Customer,
    Supplier,
    RawMaterial,
    BOM,
    BOMItem,
    StockMovement,
)


# --------------------------------------------------
# PASSWORD HASHING
# --------------------------------------------------

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 310000

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()

    return f"pbkdf2_sha256${iterations}${salt}${password_hash}"


# --------------------------------------------------
# INITIALISE DATABASE
# --------------------------------------------------

def seed_database():
    initialize_database()

    db = SessionLocal()

    try:
        # 1. CREATE DEMO USERS
        user_data = [
            ("admin", "Admin@123", "Factory Administrator", "admin"),
            ("salesman", "Sales@123", "Sales Executive A", "salesman"),
            ("production", "Prod@123", "Production Supervisor", "production"),
            ("accountant", "Accounts@123", "Factory Accountant", "accountant"),
            ("owner", "Owner@123", "Factory Owner", "owner"),
        ]

        for username, password, full_name, role in user_data:
            user = db.scalar(
                select(User).where(User.username == username)
            )

            if user is None:
                db.add(
                    User(
                        username=username,
                        password_hash=hash_password(password),
                        full_name=full_name,
                        role=role,
                    )
                )

        db.flush()

        admin = db.scalar(
            select(User).where(User.username == "admin")
        )

        # 2. CREATE FINISHED PRODUCT
        product = db.scalar(
            select(Product).where(Product.sku == "SNK-MUR-200")
        )

        if product is None:
            product = Product(
                name="Murukku 200g",
                sku="SNK-MUR-200",
                hsn_code="210690",
                selling_price=Decimal("50.00"),
                gst_rate=Decimal("5.00"),
                unit="packet",
            )
            db.add(product)
            db.flush()

        # 3. CREATE RAW MATERIALS AND PACKAGING
        material_data = [
            ("Rice Flour", "RM-FLOUR", "kg", "20"),
            ("Cooking Oil", "RM-OIL", "litre", "10"),
            ("Salt and Spice Mix", "RM-SPICE", "kg", "2"),
            ("200g Pouch", "PKG-POUCH", "piece", "100"),
            ("Carton (20 packets)", "PKG-CARTON", "piece", "5"),
        ]

        materials = {}

        for name, sku, unit, reorder_level in material_data:
            material = db.scalar(
                select(RawMaterial).where(RawMaterial.sku == sku)
            )

            if material is None:
                material = RawMaterial(
                    name=name,
                    sku=sku,
                    base_unit=unit,
                    reorder_level=Decimal(reorder_level),
                )
                db.add(material)
                db.flush()

            materials[sku] = material

        # 4. CREATE CUSTOMERS
        customer_data = [
            ("Retailer A", "9876543210", "Tamil Nadu"),
            ("Distributor B", "9876543211", "Karnataka"),
        ]

        for name, phone, state in customer_data:
            customer = db.scalar(
                select(Customer).where(Customer.name == name)
            )

            if customer is None:
                db.add(
                    Customer(
                        name=name,
                        phone=phone,
                        state=state,
                        address="Demo address",
                    )
                )

        # 5. CREATE SUPPLIER
        supplier = db.scalar(
            select(Supplier).where(
                Supplier.name == "Tamil Nadu Ingredients Supplier"
            )
        )

        if supplier is None:
            db.add(
                Supplier(
                    name="Tamil Nadu Ingredients Supplier",
                    phone="9876500000",
                    state="Tamil Nadu",
                )
            )

        db.flush()

        # 6. CREATE BILL OF MATERIALS
        bom = db.scalar(
            select(BOM).where(
                BOM.product_id == product.id,
                BOM.is_active == True,
            )
        )

        if bom is None:
            bom = BOM(
                product_id=product.id,
                batch_output_quantity=Decimal("200"),
                version=1,
            )
            db.add(bom)
            db.flush()

            bom_items = [
                ("RM-FLOUR", "40", "kg"),
                ("RM-OIL", "10", "litre"),
                ("RM-SPICE", "1.2", "kg"),
                ("PKG-POUCH", "200", "piece"),
                ("PKG-CARTON", "10", "piece"),
            ]

            for sku, quantity, unit in bom_items:
                db.add(
                    BOMItem(
                        bom_id=bom.id,
                        raw_material_id=materials[sku].id,
                        standard_quantity=Decimal(quantity),
                        unit=unit,
                    )
                )

        db.flush()

        # 7. CREATE OPENING STOCK MOVEMENTS ONLY ONCE
        opening_count = db.scalar(
            select(func.count(StockMovement.id)).where(
                StockMovement.reference_type == "OPENING_BALANCE"
            )
        )

        if opening_count == 0:
            opening_stock = [
                ("RAW_MATERIAL", materials["RM-FLOUR"].id, "100", "kg"),
                ("RAW_MATERIAL", materials["RM-OIL"].id, "30", "litre"),
                ("RAW_MATERIAL", materials["RM-SPICE"].id, "5", "kg"),
                ("RAW_MATERIAL", materials["PKG-POUCH"].id, "500", "piece"),
                ("RAW_MATERIAL", materials["PKG-CARTON"].id, "30", "piece"),
                ("PRODUCT", product.id, "50", "packet"),
            ]

            for item_type, item_id, quantity, unit in opening_stock:
                db.add(
                    StockMovement(
                        item_type=item_type,
                        item_id=item_id,
                        movement_type="OPENING",
                        quantity=Decimal(quantity),
                        unit=unit,
                        reference_type="OPENING_BALANCE",
                        reference_id=0,
                        notes="Initial benchmark opening stock",
                        created_by=admin.id,
                        created_at=datetime.utcnow(),
                    )
                )

        db.commit()

        print("NAMMAFACTORY SEED DATA CREATED SUCCESSFULLY!")
        print("Demo users: 5")
        print("Finished products: 1")
        print("Raw materials and packaging: 5")
        print("Customers: 2")
        print("BOM: Murukku 200g")
        print("Opening stock movements: 6")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
