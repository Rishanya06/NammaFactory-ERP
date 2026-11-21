
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


def seed_database():
    initialize_database()
    db = SessionLocal()

    try:
        # 1. USERS
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
                db.add(User(
                    username=username,
                    password_hash=hash_password(password),
                    full_name=full_name,
                    role=role,
                ))

        db.flush()

        admin = db.scalar(
            select(User).where(User.username == "admin")
        )

        # 2. FINISHED PRODUCTS
        product_data = [
            ("Murukku 200g", "SNK-MUR-200", "210690", "50.00"),
            ("Mixture 200g", "SNK-MIX-200", "210690", "60.00"),
            ("Ribbon Pakoda 200g", "SNK-RIB-200", "210690", "60.00"),
            ("Banana Chips 200g", "SNK-BAN-200", "210690", "80.00"),
            ("Thatta 200g", "SNK-THA-200", "210690", "50.00"),
        ]

        products = {}

        for name, sku, hsn, price in product_data:
            product = db.scalar(
                select(Product).where(Product.sku == sku)
            )

            if product is None:
                product = Product(
                    name=name,
                    sku=sku,
                    hsn_code=hsn,
                    selling_price=Decimal(price),
                    gst_rate=Decimal("5.00"),
                    unit="packet",
                )
                db.add(product)
                db.flush()

            products[sku] = product

        # 3. RAW MATERIALS AND PACKAGING
        material_data = [
            ("Rice Flour", "RM-FLOUR", "kg", "20"),
            ("Cooking Oil", "RM-OIL", "litre", "10"),
            ("Salt and Spice Mix", "RM-SPICE", "kg", "2"),
            ("200g Pouch", "PKG-POUCH", "piece", "100"),
            ("Carton (20 packets)", "PKG-CARTON", "piece", "5"),
            ("Gram Flour", "RM-GRAM", "kg", "10"),
            ("Raw Banana", "RM-BANANA", "kg", "15"),
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

        # 4. CUSTOMERS
        customer_data = [
            ("Retailer A", "9876543210", "Tamil Nadu"),
            ("Distributor B", "9876543211", "Karnataka"),
            ("Chennai Super Stores", "9876543212", "Tamil Nadu"),
            ("Coimbatore Food Mart", "9876543213", "Tamil Nadu"),
            ("Madurai Wholesale Foods", "9876543214", "Tamil Nadu"),
            ("Kochi Snack Distributors", "9876543215", "Kerala"),
            ("Bengaluru Retail Hub", "9876543216", "Karnataka"),
            ("Vijayawada Foods", "9876543217", "Andhra Pradesh"),
        ]

        for name, phone, state in customer_data:
            customer = db.scalar(
                select(Customer).where(Customer.name == name)
            )

            if customer is None:
                db.add(Customer(
                    name=name,
                    phone=phone,
                    state=state,
                    address="Demo business address",
                ))

        # 5. SUPPLIERS
        supplier_data = [
            ("Tamil Nadu Ingredients Supplier", "9876500000", "Tamil Nadu"),
            ("South India Pulses Supplier", "9876500001", "Tamil Nadu"),
            ("Fresh Banana Supplier", "9876500002", "Kerala"),
        ]

        for name, phone, state in supplier_data:
            supplier = db.scalar(
                select(Supplier).where(Supplier.name == name)
            )

            if supplier is None:
                db.add(Supplier(
                    name=name,
                    phone=phone,
                    state=state,
                ))

        db.flush()

        # 6. BILL OF MATERIALS
        # Quantities are illustrative demo recipes.
        # Murukku retains the exact assignment benchmark BOM.

        bom_data = [
            (
                "SNK-MUR-200",
                "200",
                [
                    ("RM-FLOUR", "40", "kg"),
                    ("RM-OIL", "10", "litre"),
                    ("RM-SPICE", "1.2", "kg"),
                    ("PKG-POUCH", "200", "piece"),
                    ("PKG-CARTON", "10", "piece"),
                ],
            ),
            (
                "SNK-MIX-200",
                "100",
                [
                    ("RM-FLOUR", "10", "kg"),
                    ("RM-GRAM", "8", "kg"),
                    ("RM-OIL", "5", "litre"),
                    ("RM-SPICE", "1", "kg"),
                    ("PKG-POUCH", "100", "piece"),
                    ("PKG-CARTON", "5", "piece"),
                ],
            ),
            (
                "SNK-RIB-200",
                "100",
                [
                    ("RM-FLOUR", "12", "kg"),
                    ("RM-GRAM", "6", "kg"),
                    ("RM-OIL", "5", "litre"),
                    ("RM-SPICE", "0.8", "kg"),
                    ("PKG-POUCH", "100", "piece"),
                    ("PKG-CARTON", "5", "piece"),
                ],
            ),
            (
                "SNK-BAN-200",
                "100",
                [
                    ("RM-BANANA", "25", "kg"),
                    ("RM-OIL", "8", "litre"),
                    ("RM-SPICE", "0.5", "kg"),
                    ("PKG-POUCH", "100", "piece"),
                    ("PKG-CARTON", "5", "piece"),
                ],
            ),
            (
                "SNK-THA-200",
                "100",
                [
                    ("RM-FLOUR", "15", "kg"),
                    ("RM-GRAM", "3", "kg"),
                    ("RM-OIL", "4", "litre"),
                    ("RM-SPICE", "0.6", "kg"),
                    ("PKG-POUCH", "100", "piece"),
                    ("PKG-CARTON", "5", "piece"),
                ],
            ),
        ]

        for product_sku, batch_quantity, items in bom_data:
            product = products[product_sku]

            bom = db.scalar(
                select(BOM).where(
                    BOM.product_id == product.id,
                    BOM.is_active == True,
                )
            )

            if bom is None:
                bom = BOM(
                    product_id=product.id,
                    batch_output_quantity=Decimal(batch_quantity),
                    version=1,
                )
                db.add(bom)
                db.flush()

                for material_sku, quantity, unit in items:
                    db.add(BOMItem(
                        bom_id=bom.id,
                        raw_material_id=materials[material_sku].id,
                        standard_quantity=Decimal(quantity),
                        unit=unit,
                    ))

        db.flush()

        # 7. OPENING STOCK
        # Only the original Murukku benchmark receives opening stock.
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
                ("PRODUCT", products["SNK-MUR-200"].id, "50", "packet"),
            ]

            for item_type, item_id, quantity, unit in opening_stock:
                db.add(StockMovement(
                    item_type=item_type,
                    item_id=item_id,
                    movement_type="OPENING",
                    quantity=Decimal(quantity),
                    unit=unit,
                    reference_type="OPENING_BALANCE",
                    reference_id=0,
                    notes="Initial Murukku benchmark opening stock",
                    created_by=admin.id,
                    created_at=datetime.utcnow(),
                ))

        db.commit()

        print("\nNAMMAFACTORY DEMO DATABASE SEEDED SUCCESSFULLY!")
        print("Users: 5")
        print("Finished products: 5")
        print("Customers: 8")
        print("Suppliers: 3")
        print("Raw materials and packaging: 7")
        print("Bills of Material: 5")
        print("Opening stock movements: 6")
        print("Additional products have no opening stock.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
