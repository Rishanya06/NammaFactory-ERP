
import streamlit as st
import pandas as pd
import secrets
from datetime import datetime
from io import BytesIO

from sqlalchemy import select, func
from decimal import Decimal, ROUND_HALF_UP

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from database import SessionLocal
from models import (
    User,
    Product,
    RawMaterial,
    Customer,
    Supplier,
    Purchase,
    PurchaseItem,
    StockMovement,
    SalesOrder,
    SalesOrderItem,
    AuditLog,
    ProductionRun,
    BOM,
    BOMItem,
    ProductionConsumption,
    Invoice,
    Payment,
)

from modules.authentication import authenticate_user, logout

from utils.business_logic import (
    money,
    is_intrastate_customer,
    calculate_stock_balances,
    calculate_weighted_average_cost,
    calculate_invoice_totals,
)


# ============================================================
# 1. APPLICATION CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NammaFactory | Manufacturing ERP",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. ROLE-SPECIFIC THEMES
# ============================================================

THEMES = {
    "admin": {
        "name": "Factory Control",
        "background": "#F1F5F0",
        "sidebar": "#123D2B",
        "primary": "#16845B",
        "text": "#18372A",
        "sidebar_text": "#FFFFFF",
        "card": "#FFFFFF",
        "accent": "#D8EBDD",
        "emoji": "🏭",
    },

    "salesman": {
        "name": "Sales Studio",
        "background": "#FFF3E6",
        "sidebar": "#542B16",
        "primary": "#E87932",
        "text": "#59351F",
        "sidebar_text": "#FFFFFF",
        "card": "#FFFFFF",
        "accent": "#FCE4CB",
        "emoji": "🛍️",
    },

    "production": {
        "name": "Production Hub",
        "background": "#E9EEF5",
        "sidebar": "#17263E",
        "primary": "#3478B9",
        "text": "#1B3048",
        "sidebar_text": "#FFFFFF",
        "card": "#FFFFFF",
        "accent": "#D8E7F8",
        "emoji": "⚙️",
    },

    "accountant": {
        "name": "Finance Desk",
        "background": "#E9F5F3",
        "sidebar": "#073D40",
        "primary": "#168C91",
        "text": "#183D40",
        "sidebar_text": "#FFFFFF",
        "card": "#FFFFFF",
        "accent": "#D4EEEE",
        "emoji": "💰",
    },

    "owner": {
        "name": "Executive Suite",
        "background": "#F7F2E9",
        "sidebar": "#29213D",
        "primary": "#C4A15A",
        "text": "#40351E",
        "sidebar_text": "#FFFFFF",
        "card": "#FFFFFF",
        "accent": "#F1E7C9",
        "emoji": "👑",
    },
}

# Assignment benchmark valuation rates. These are transparent demo assumptions;
# the purchase-receipt workflow will replace them with live weighted-average rates.
BENCHMARK_UNIT_COSTS = {
    "RM-FLOUR": Decimal("43.125"),   # (100 kg x ₹42 + 60 kg x ₹45) / 160 kg
    "RM-OIL": Decimal("140.00"),
    "RM-SPICE": Decimal("200.00"),
    "PKG-POUCH": Decimal("2.50"),
    "PKG-CARTON": Decimal("15.00"),
}


def apply_role_theme(role):

    theme = THEMES.get(role, THEMES["admin"])

    st.markdown(
        f"""
        <style>
        /* =====================================================
           NAMMAFACTORY ACCESSIBLE LIGHT INTERFACE
           Rule: light surfaces = dark text; dark surfaces = light text
           ===================================================== */

        :root {{
            color-scheme: light;
        }}

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        section[data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {{
            background-color: {theme['background']} !important;
            color: #202A35 !important;
        }}

        /* Main content typography */
        .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp h5, .stApp h6,
        .stApp p, .stApp li, .stApp label,
        .stApp legend,
        .stApp [data-testid="stMarkdownContainer"],
        .stApp [data-testid="stCaptionContainer"],
        .stApp [data-testid="stText"],
        .stApp [data-testid="stWidgetLabel"] {{
            color: #202A35 !important;
        }}

        .main-title {{
            color: #202A35 !important;
            font-size: 34px;
            font-weight: 800;
        }}

        .subtitle {{
            color: #465466 !important;
            opacity: 1 !important;
        }}

        /* Sidebar is intentionally dark: use light text throughout */
        [data-testid="stSidebar"] {{
            background-color: {theme['sidebar']} !important;
            color: #FFFFFF !important;
        }}

        [data-testid="stSidebar"] *,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
            color: #FFFFFF !important;
        }}

        [data-testid="stSidebar"] button {{
            border-color: #FFFFFF66 !important;
        }}

        /* Cards and containers */
        div[data-testid="stMetric"],
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: #FFFFFF !important;
            color: #202A35 !important;
            border-color: #D4DCE5 !important;
        }}

        div[data-testid="stMetric"] {{
            border: 1px solid {theme['primary']}55 !important;
            border-radius: 16px !important;
            padding: 20px !important;
            box-shadow: 0 3px 12px rgba(0,0,0,0.05);
        }}

        div[data-testid="stMetric"] *,
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricDelta"] {{
            color: #202A35 !important;
            opacity: 1 !important;
        }}

        /* ALL main-page form fields: white surface + dark readable text */
        .stApp input,
        .stApp textarea,
        .stApp [data-baseweb="input"],
        .stApp [data-baseweb="input"] > div,
        .stApp [data-baseweb="textarea"],
        .stApp [data-baseweb="textarea"] > div,
        .stApp [data-baseweb="select"] > div,
        .stApp [data-testid="stNumberInput"] > div,
        .stApp [data-testid="stDateInput"] > div,
        .stApp [data-testid="stTimeInput"] > div,
        .stApp [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            color: #202A35 !important;
            border-color: #AAB6C4 !important;
        }}

        .stApp input,
        .stApp textarea,
        .stApp [data-baseweb="select"] *,
        .stApp [data-baseweb="input"] *,
        .stApp [data-baseweb="textarea"] *,
        .stApp [data-testid="stNumberInput"] *,
        .stApp [data-testid="stDateInput"] *,
        .stApp [data-testid="stTimeInput"] *,
        .stApp [data-testid="stMultiSelect"] * {{
            color: #202A35 !important;
            -webkit-text-fill-color: #202A35 !important;
            opacity: 1 !important;
        }}

        .stApp input::placeholder,
        .stApp textarea::placeholder {{
            color: #687586 !important;
            -webkit-text-fill-color: #687586 !important;
            opacity: 1 !important;
        }}

        /* Number input +/- controls */
        .stApp [data-testid="stNumberInput"] button {{
            background-color: #EEF2F6 !important;
            color: #202A35 !important;
            border-color: #C7D0DA !important;
        }}
        .stApp [data-testid="stNumberInput"] button svg {{
            fill: #202A35 !important;
            color: #202A35 !important;
        }}

        /* Dropdown menus and options */
        [data-baseweb="popover"],
        [data-baseweb="menu"],
        [role="listbox"],
        [role="option"] {{
            background-color: #FFFFFF !important;
            color: #202A35 !important;
        }}
        [role="option"] *,
        [data-baseweb="popover"] * {{
            color: #202A35 !important;
        }}

        /* Dataframes: request a light grid with dark text */
        .stApp [data-testid="stDataFrame"],
        .stApp [data-testid="stTable"] {{
            background-color: #FFFFFF !important;
            color: #202A35 !important;
            --gdg-bg-cell: #FFFFFF;
            --gdg-bg-cell-medium: #F4F7FA;
            --gdg-bg-header: #E8EEF4;
            --gdg-bg-header-hover: #DCE5EE;
            --gdg-text-dark: #202A35;
            --gdg-text-medium: #344255;
            --gdg-text-light: #526174;
            --gdg-border-color: #D3DCE6;
            --gdg-header-font-style: 600 13px;
            --gdg-cell-font-style: 13px;
        }}

        /* Captions and help text */
        .stApp small,
        .stApp [data-testid="stCaptionContainer"],
        .stApp [data-testid="stHelp"] {{
            color: #526174 !important;
            opacity: 1 !important;
        }}

        /* Alerts: pale surfaces with strong readable text */
        .stApp [data-testid="stAlert"] {{
            background-color: #F3F6FA !important;
            border: 1px solid #D6DFE9 !important;
        }}
        .stApp [data-testid="stAlert"] p,
        .stApp [data-testid="stAlert"] span,
        .stApp [data-testid="stAlert"] div {{
            color: #202A35 !important;
        }}
        .stApp [data-testid="stAlert"][data-baseweb="notification"] {{
            color: #202A35 !important;
        }}

        /* Streamlit status containers */
        .stApp [data-testid="stNotificationContentSuccess"],
        .stApp [data-testid="stNotificationContentInfo"],
        .stApp [data-testid="stNotificationContentWarning"],
        .stApp [data-testid="stNotificationContentError"] {{
            color: #202A35 !important;
        }}

        /* Buttons retain role colour; text stays white on primary buttons */
        .stApp button[kind="primary"],
        .stApp button[kind="primary"] *,
        .stApp [data-testid="stFormSubmitButton"] button,
        .stApp [data-testid="stFormSubmitButton"] button * {{
            background-color: {theme['primary']} !important;
            border-color: {theme['primary']} !important;
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }}

        .stApp button[kind="secondary"],
        .stApp button[kind="secondary"] * {{
            background-color: #FFFFFF !important;
            color: #202A35 !important;
            -webkit-text-fill-color: #202A35 !important;
            border-color: #AAB6C4 !important;
        }}

        /* Progress indicators and links */
        div[data-testid="stProgress"] > div > div {{
            background-color: {theme['primary']} !important;
        }}

        .stApp a {{
            color: {theme['primary']} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 3. DATABASE HELPERS
# ============================================================

def get_count(db, model):

    return db.scalar(
        select(func.count()).select_from(model)
    ) or 0


def get_user_orders(db, user_id):

    return db.scalars(
        select(SalesOrder).where(
            SalesOrder.salesman_id == user_id
        ).order_by(SalesOrder.id.desc())
    ).all()


def get_stock_balances(db):
    movements = db.scalars(select(StockMovement)).all()
    return calculate_stock_balances(movements)


def get_invoice_totals(db):
    invoices = db.scalars(select(Invoice)).all()
    payments = db.scalars(select(Payment)).all()
    return calculate_invoice_totals(invoices, payments)


def format_currency(value):

    return f"₹{Decimal(str(value)):,.2f}"


def get_weighted_average_unit_cost(db, material):
    """Calculate periodic weighted-average cost from opening stock and received purchases."""
    received_items = db.scalars(
        select(PurchaseItem)
        .join(Purchase, PurchaseItem.purchase_id == Purchase.id)
        .where(
            PurchaseItem.raw_material_id == material.id,
            Purchase.status == "RECEIVED",
        )
    ).all()
    return calculate_weighted_average_cost(material.sku, received_items)


# ============================================================
# 4. SHARED UI COMPONENTS
# ============================================================

def page_header(title, description):

    st.markdown(
        f'<div class="main-title">{title}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="subtitle">{description}</div>',
        unsafe_allow_html=True,
    )

    st.divider()


def section_heading(title, description=None):

    st.subheader(title)

    if description:
        st.caption(description)


def show_empty_state(message):

    st.info(message)


# ============================================================
# 5. ADMIN DASHBOARD
# ============================================================

def admin_dashboard(db):

    page_header(
        "Factory Administration",
        "Your central control centre for factory operations.",
    )

    total_orders = get_count(db, SalesOrder)
    total_products = get_count(db, Product)
    total_customers = get_count(db, Customer)
    total_materials = get_count(db, RawMaterial)

    pending_orders = db.scalar(
        select(func.count(SalesOrder.id)).where(
            SalesOrder.status == "PENDING"
        )
    ) or 0

    total_runs = get_count(db, ProductionRun)

    st.subheader("Factory Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Orders", total_orders)
    c2.metric("Pending Approvals", pending_orders)
    c3.metric("Products", total_products)
    c4.metric("Customers", total_customers)

    st.divider()

    left, right = st.columns(2)

    with left:

        section_heading(
            "🏭 Production Overview",
            "Manufacturing activity across the factory.",
        )

        st.metric("Production Batches", total_runs)
        st.metric("Raw Material Categories", total_materials)

    with right:

        section_heading(
            "📦 Master Data",
            "Registered factory records.",
        )

        st.metric("Finished Products", total_products)
        st.metric("Registered Customers", total_customers)

    st.divider()

    section_heading("Administrative Priorities")

    st.markdown(
        """
        - Review orders awaiting approval.
        - Monitor raw material availability.
        - Coordinate production operations.
        - Monitor finished goods before dispatch.
        - Review stock and transaction reports.
        """
    )


# ============================================================
# 6. SALESMAN DASHBOARD
# ============================================================

def salesman_dashboard(db, user):

    page_header(
        "My Sales Workspace",
        f"Welcome back, {user['full_name']}. Manage your customers and orders.",
    )

    orders = get_user_orders(db, user["id"])

    total_orders = len(orders)

    pending = sum(
        o.status == "PENDING" for o in orders
    )

    approved = sum(
        o.status == "APPROVED" for o in orders
    )

    dispatched = sum(
        o.status == "DISPATCHED" for o in orders
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("My Orders", total_orders)
    c2.metric("Pending", pending)
    c3.metric("Approved", approved)
    c4.metric("Dispatched", dispatched)

    st.divider()

    section_heading(
        "📋 Recent Orders",
        "Track your submitted customer orders.",
    )

    if orders:

        order_data = [
            {
                "Order Number": o.order_number,
                "Date": o.order_date.strftime("%d-%m-%Y"),
                "Status": o.status,
            }
            for o in orders
        ]

        st.dataframe(
            pd.DataFrame(order_data),
            use_container_width=True,
            hide_index=True,
        )

    else:

        show_empty_state(
            "You haven't submitted any orders yet. "
            "Create your first order using New Order."
        )

    st.divider()

    section_heading("🎯 Sales Workspace")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### Customer Management")
        st.write("Access customer records.")
        st.write("Select customers for new orders.")

    with col2:

        st.markdown("### Order Management")
        st.write("Submit customer orders.")
        st.write("Track approval and dispatch status.")


# ============================================================
# 7. PRODUCTION DASHBOARD
# ============================================================

def production_dashboard(db):

    page_header(
        "Production Control Centre",
        "Monitor manufacturing batches, output and material consumption.",
    )

    runs = db.scalars(
        select(ProductionRun)
    ).all()

    total_batches = len(runs)

    planned_output = sum(
        (Decimal(str(r.planned_output)) for r in runs),
        Decimal("0"),
    )

    actual_output = sum(
        (Decimal(str(r.actual_good_output)) for r in runs),
        Decimal("0"),
    )

    damaged = sum(
        (Decimal(str(r.damaged_quantity)) for r in runs),
        Decimal("0"),
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Production Batches", total_batches)
    c2.metric("Planned Output", f"{planned_output:,.0f}")
    c3.metric("Good Output", f"{actual_output:,.0f}")
    c4.metric("Damaged Units", f"{damaged:,.0f}")

    st.divider()

    section_heading("📊 Production Yield")

    if planned_output > 0:

        yield_percentage = (
            actual_output / planned_output
        ) * 100

        st.metric(
            "Production Yield",
            f"{yield_percentage:.2f}%",
        )

        st.progress(
            min(float(yield_percentage / 100), 1.0)
        )

    else:

        show_empty_state(
            "No production batches have been recorded yet."
        )

    st.divider()

    section_heading("⚙️ Production Workflow")

    st.markdown(
        """
        1. Review the Bill of Materials.
        2. Check raw material availability.
        3. Record material issued to production.
        4. Enter good output and damaged quantities.
        5. Review planned-versus-actual consumption.
        6. Analyse production yield and wastage.
        """)


# ============================================================
# 8. ACCOUNTANT DASHBOARD
# ============================================================

def accountant_dashboard(db):

    page_header(
        "Finance & Accounts",
        "Manage GST invoices, payments and customer receivables.",
    )

    totals = get_invoice_totals(db)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Invoices",
        totals["invoice_count"],
    )

    c2.metric(
        "Invoice Value",
        format_currency(totals["invoice_total"]),
    )

    c3.metric(
        "Payments Received",
        format_currency(totals["payment_total"]),
    )

    c4.metric(
        "Outstanding",
        format_currency(totals["outstanding"]),
    )

    st.divider()

    section_heading("🧾 GST and Financial Summary")

    left, right = st.columns(2)

    with left:

        st.metric(
            "Taxable Sales",
            format_currency(totals["taxable_total"]),
        )

    with right:

        st.metric(
            "GST Recorded",
            format_currency(totals["gst_total"]),
        )

    st.divider()

    section_heading("Finance Operations")

    st.markdown(
        """
        - Maintain the sales invoice register.
        - Review CGST, SGST and IGST.
        - Record customer payments.
        - Monitor outstanding balances.
        - Generate monthly financial reports.
        """)


# ============================================================
# 9. OWNER DASHBOARD
# ============================================================

def owner_dashboard(db):
    """Owner-facing summary of finance, production, inventory and recent activity."""

    page_header(
        "Owner Dashboard",
        "A live overview of sales, cash collection, manufacturing efficiency and inventory health.",
    )

    # -------------------------
    # Pull current business data
    # -------------------------
    totals = get_invoice_totals(db)

    invoices = db.scalars(
        select(Invoice).order_by(Invoice.invoice_date.desc())
    ).all()

    runs = db.scalars(
        select(ProductionRun).order_by(ProductionRun.production_date.desc())
    ).all()

    purchases = db.scalars(
        select(Purchase).order_by(Purchase.purchase_date.desc())
    ).all()

    materials = db.scalars(
        select(RawMaterial).where(RawMaterial.is_active == True)
    ).all()

    products = db.scalars(
        select(Product).where(Product.is_active == True)
    ).all()

    balances = get_stock_balances(db)

    production_output = sum(
        (Decimal(str(run.actual_good_output or 0)) for run in runs),
        Decimal("0"),
    )
    planned_output = sum(
        (Decimal(str(run.planned_output or 0)) for run in runs),
        Decimal("0"),
    )
    damaged_units = sum(
        (Decimal(str(run.damaged_quantity or 0)) for run in runs),
        Decimal("0"),
    )
    production_yield = (
        production_output / planned_output * Decimal("100")
        if planned_output > 0 else Decimal("0")
    )

    purchase_spend = sum(
        (
            Decimal(str(p.total_amount or 0))
            for p in purchases
            if str(p.status).upper() in {"RECEIVED", "POSTED", "COMPLETED"}
        ),
        Decimal("0"),
    )

    # -------------------------
    # KPI row
    # -------------------------
    st.subheader("Business at a glance")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Taxable Revenue", format_currency(totals["taxable_total"]))
    k2.metric("Customer Collections", format_currency(totals["payment_total"]))
    k3.metric("Outstanding Receivables", format_currency(totals["outstanding"]))
    k4.metric("Purchase Spend", format_currency(purchase_spend))

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Production Batches", f"{len(runs):,}")
    k6.metric("Good Units Produced", f"{production_output:,.0f}")
    k7.metric("Average Production Yield", f"{production_yield:.2f}%")
    k8.metric("Damaged Units", f"{damaged_units:,.0f}")

    st.divider()

    # -------------------------
    # Sales trend
    # -------------------------
    left, right = st.columns(2)

    with left:
        section_heading("📈 Monthly Sales")
        monthly_sales = {}
        for invoice in invoices:
            invoice_date = invoice.invoice_date
            if invoice_date:
                month_key = invoice_date.strftime("%Y-%m")
                monthly_sales[month_key] = monthly_sales.get(month_key, Decimal("0")) + Decimal(
                    str(invoice.taxable_amount or 0)
                )

        if monthly_sales:
            sales_frame = pd.DataFrame(
                [{"Month": month, "Taxable sales (₹)": float(value)}
                 for month, value in sorted(monthly_sales.items())]
            ).set_index("Month")
            st.bar_chart(sales_frame, use_container_width=True)
        else:
            st.info("No invoices have been generated yet. Monthly sales will appear here.")

    with right:
        section_heading("🏭 Production Output")
        if runs:
            production_rows = []
            for run in reversed(runs[:12]):
                label = run.batch_number
                production_rows.append({
                    "Batch": label,
                    "Good output": float(Decimal(str(run.actual_good_output or 0))),
                    "Planned output": float(Decimal(str(run.planned_output or 0))),
                })
            production_frame = pd.DataFrame(production_rows).set_index("Batch")
            st.bar_chart(production_frame, use_container_width=True)
        else:
            st.info("No production runs have been recorded yet.")

    st.divider()

    # -------------------------
    # Inventory health
    # -------------------------
    section_heading("📦 Inventory Health")

    low_stock_rows = []
    inventory_rows = []

    for material in materials:
        quantity = balances.get(("RAW_MATERIAL", material.id), Decimal("0"))
        reorder = Decimal(str(material.reorder_level or 0))
        inventory_rows.append({
            "Material": material.name,
            "Available": float(quantity),
            "Unit": material.base_unit,
            "Reorder level": float(reorder),
            "Status": "REORDER" if quantity <= reorder else "OK",
        })
        if quantity <= reorder:
            low_stock_rows.append({
                "Item": material.name,
                "Available": f"{quantity:,.3f} {material.base_unit}",
                "Reorder level": f"{reorder:,.3f} {material.base_unit}",
            })

    for product in products:
        quantity = balances.get(("PRODUCT", product.id), Decimal("0"))
        inventory_rows.append({
            "Material": product.name,
            "Available": float(quantity),
            "Unit": product.unit,
            "Reorder level": None,
            "Status": "CHECK STOCK" if quantity <= 0 else "OK",
        })

    inv_left, inv_right = st.columns([1, 1.4])
    with inv_left:
        if low_stock_rows:
            st.warning(f"{len(low_stock_rows)} raw material(s) at or below reorder level.")
            st.dataframe(pd.DataFrame(low_stock_rows), use_container_width=True, hide_index=True)
        else:
            st.success("All active raw materials are above their reorder levels.")

    with inv_right:
        if inventory_rows:
            inventory_frame = pd.DataFrame(inventory_rows)
            st.dataframe(inventory_frame, use_container_width=True, hide_index=True)
        else:
            st.info("No inventory master records are available.")

    st.divider()

    # -------------------------
    # Production costing
    # -------------------------
    section_heading("🧾 Production Cost Snapshot")

    cost_rows = []
    total_batch_cost = Decimal("0")
    total_costed_output = Decimal("0")

    for run in runs:
        consumptions = db.scalars(
            select(ProductionConsumption).where(
                ProductionConsumption.production_run_id == run.id
            )
        ).all()

        material_cost = sum(
            (
                Decimal(str(item.actual_quantity or 0))
                * Decimal(str(item.unit_cost or 0))
                for item in consumptions
            ),
            Decimal("0"),
        )
        labour = Decimal(str(run.labour_cost or 0))
        overhead = Decimal(str(run.overhead_cost or 0))
        batch_cost = material_cost + labour + overhead
        good_output = Decimal(str(run.actual_good_output or 0))
        unit_cost = batch_cost / good_output if good_output > 0 else Decimal("0")

        if good_output > 0:
            total_batch_cost += batch_cost
            total_costed_output += good_output

        cost_rows.append({
            "Batch": run.batch_number,
            "Good packets": f"{good_output:,.0f}",
            "Material cost": format_currency(material_cost),
            "Labour": format_currency(labour),
            "Overhead": format_currency(overhead),
            "Total batch cost": format_currency(batch_cost),
            "Cost / good packet": format_currency(unit_cost),
        })

    average_unit_cost = (
        total_batch_cost / total_costed_output
        if total_costed_output > 0 else Decimal("0")
    )

    c1, c2 = st.columns(2)
    c1.metric("Weighted average cost per good packet", format_currency(average_unit_cost))
    c2.metric("Costed production output", f"{total_costed_output:,.0f} packets")

    if cost_rows:
        st.dataframe(pd.DataFrame(cost_rows), use_container_width=True, hide_index=True)
        st.caption(
            "Cost per packet is calculated from recorded material consumption, labour and overhead "
            "for each production run. It is a production-cost measure, not a selling-price margin."
        )
    else:
        st.info("Production cost details will appear after a production run is completed.")

    st.divider()

    # -------------------------
    # Recent audit activity
    # -------------------------
    section_heading("🕒 Recent Business Activity")
    recent_events = db.scalars(
        select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(8)
    ).all()

    if recent_events:
        activity_rows = []
        for event in recent_events:
            activity_rows.append({
                "Time": event.timestamp.strftime("%d %b %Y, %I:%M %p") if event.timestamp else "—",
                "Action": event.action,
                "Record type": event.entity_type,
                "Record ID": event.entity_id,
                "Details": event.details or "",
            })
        st.dataframe(pd.DataFrame(activity_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No audit activity has been recorded yet.")

    st.caption(
        "Dashboard figures are calculated from the current NammaFactory database. "
        "Inventory is derived from stock movements rather than manually editable balances."
    )

def purchase_management_page(user):
    """Record supplier purchases and receive raw materials into stock."""
    db = SessionLocal()
    try:
        section_heading("📦 Purchase & Goods Receipt")
        st.write(
            "Record supplier invoices, receive raw materials and update the stock ledger "
            "with a traceable purchase reference."
        )

        suppliers = db.scalars(
            select(Supplier).order_by(Supplier.name)
        ).all()
        materials = db.scalars(
            select(RawMaterial).where(RawMaterial.is_active == True).order_by(RawMaterial.name)
        ).all()

        if not suppliers:
            st.warning("Add a supplier before recording a purchase.")
            return
        if not materials:
            st.warning("No active raw materials are available.")
            return

        with st.form("purchase_receipt_form", clear_on_submit=True):
            supplier_options = {f"{s.name}": s.id for s in suppliers}
            selected_supplier_label = st.selectbox(
                "Supplier", list(supplier_options.keys())
            )
            invoice_number = st.text_input("Supplier invoice / bill number")
            purchase_date = st.date_input("Purchase date", value=datetime.now().date())
            st.markdown("#### Purchased raw materials")
            purchase_lines = []
            for material in materials:
                with st.expander(f"{material.name} ({material.base_unit})", expanded=(material == materials[0])):
                    qty = st.number_input(
                        f"Quantity received — {material.name}",
                        min_value=0.0,
                        value=0.0,
                        step=1.0,
                        key=f"purchase_qty_{material.id}",
                    )
                    unit_price = st.number_input(
                        f"Purchase rate per {material.base_unit} (₹) — {material.name}",
                        min_value=0.0,
                        value=float(BENCHMARK_UNIT_COSTS.get(material.sku, Decimal("0.00"))),
                        step=1.0,
                        key=f"purchase_rate_{material.id}",
                    )
                    purchase_lines.append((material.id, qty, unit_price, material.base_unit, material.name))

            submitted = st.form_submit_button(
                "Receive Purchase & Update Stock",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not invoice_number.strip():
                st.error("Enter the supplier invoice number.")
                return
            selected_lines = [
                (mid, Decimal(str(qty)), Decimal(str(rate)), unit, name)
                for mid, qty, rate, unit, name in purchase_lines
                if Decimal(str(qty)) > 0
            ]
            if not selected_lines:
                st.error("Enter a quantity for at least one raw material.")
                return

            duplicate = db.scalar(
                select(Purchase).where(
                    Purchase.supplier_id == supplier_options[selected_supplier_label],
                    Purchase.invoice_number == invoice_number.strip(),
                )
            )
            if duplicate:
                st.error("This supplier invoice number has already been recorded.")
                return

            try:
                total = sum(
                    (qty * rate for _, qty, rate, _, _ in selected_lines),
                    Decimal("0.00"),
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                purchase = Purchase(
                    supplier_id=supplier_options[selected_supplier_label],
                    invoice_number=invoice_number.strip(),
                    purchase_date=datetime.combine(purchase_date, datetime.min.time()),
                    total_amount=total,
                    status="RECEIVED",
                )
                db.add(purchase)
                db.flush()

                for material_id, qty, rate, unit, material_name in selected_lines:
                    db.add(PurchaseItem(
                        purchase_id=purchase.id,
                        raw_material_id=material_id,
                        quantity=qty,
                        unit=unit,
                        unit_price=rate,
                    ))
                    db.add(StockMovement(
                        item_type="RAW_MATERIAL",
                        item_id=material_id,
                        movement_type="PURCHASE",
                        quantity=qty,
                        unit=unit,
                        reference_type="PURCHASE",
                        reference_id=purchase.id,
                        notes=f"Received {material_name}; supplier invoice {invoice_number.strip()}",
                        created_by=user["id"],
                        created_at=datetime.now(),
                    ))

                db.add(AuditLog(
                    user_id=user["id"],
                    action="PURCHASE_RECEIVED",
                    entity_type="Purchase",
                    entity_id=purchase.id,
                    details=(
                        f"Supplier invoice {invoice_number.strip()}; total {format_currency(total)}; "
                        + "; ".join(
                            f"{name}: {qty} {unit} @ {format_currency(rate)}"
                            for _, qty, rate, unit, name in selected_lines
                        )
                    ),
                    timestamp=datetime.now(),
                ))
                db.commit()
                st.success(
                    f"Purchase {invoice_number.strip()} received successfully. "
                    f"Stock ledger updated by {len(selected_lines)} material line(s)."
                )
                st.metric("Purchase total", format_currency(total))
            except Exception as exc:
                db.rollback()
                st.error(f"Purchase could not be saved: {exc}")

        st.divider()
        st.markdown("### Current weighted-average material rates")
        rate_rows = []
        for material in materials:
            rate_rows.append({
                "Raw material": material.name,
                "SKU": material.sku,
                "Weighted-average rate": format_currency(
                    get_weighted_average_unit_cost(db, material)
                ),
                "Unit": material.base_unit,
            })
        st.dataframe(pd.DataFrame(rate_rows), use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("### Purchase register")
        purchases = db.scalars(
            select(Purchase).order_by(Purchase.id.desc()).limit(50)
        ).all()
        if purchases:
            purchase_rows = []
            for purchase in purchases:
                supplier = db.get(Supplier, purchase.supplier_id)
                purchase_rows.append({
                    "Invoice": purchase.invoice_number,
                    "Supplier": supplier.name if supplier else "Unknown",
                    "Date": purchase.purchase_date.strftime("%d-%m-%Y") if purchase.purchase_date else "—",
                    "Total": format_currency(purchase.total_amount),
                    "Status": purchase.status,
                })
            st.dataframe(pd.DataFrame(purchase_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No supplier purchases have been recorded yet.")

    except Exception as exc:
        st.error(f"Unable to load purchase management: {exc}")
    finally:
        db.close()


def payments_management_page(user):
    """Record customer receipts, prevent overpayment and show receivable ageing."""
    db = SessionLocal()
    try:
        section_heading("💳 Customer Payments & Receivables")
        st.write(
            "Record full or partial customer receipts against posted GST invoices. "
            "Outstanding balances are calculated from invoice value less recorded payments."
        )

        invoices = db.scalars(
            select(Invoice).where(Invoice.status == "POSTED").order_by(Invoice.id.desc())
        ).all()

        invoice_balances = []
        for invoice in invoices:
            paid = db.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.invoice_id == invoice.id
                )
            )
            paid_amount = Decimal(str(paid or 0))
            invoice_total = Decimal(str(invoice.total_amount or 0))
            outstanding = invoice_total - paid_amount
            if outstanding > 0:
                order = db.get(SalesOrder, invoice.order_id)
                customer = db.get(Customer, order.customer_id) if order else None
                invoice_balances.append((invoice, customer, paid_amount, outstanding))

        if invoice_balances:
            st.markdown("### Record a customer receipt")
            with st.form("customer_payment_form", clear_on_submit=True):
                invoice_labels = {
                    f"{invoice.invoice_number} | {customer.name if customer else 'Customer'} | Due {format_currency(outstanding)}": invoice.id
                    for invoice, customer, paid_amount, outstanding in invoice_balances
                }
                selected_label = st.selectbox("Invoice", list(invoice_labels.keys()))
                selected_invoice_id = invoice_labels[selected_label]
                selected_tuple = next(
                    row for row in invoice_balances if row[0].id == selected_invoice_id
                )
                selected_invoice, selected_customer, selected_paid, selected_due = selected_tuple
                st.caption(
                    f"Invoice total: {format_currency(selected_invoice.total_amount)} · "
                    f"Already received: {format_currency(selected_paid)} · "
                    f"Outstanding: {format_currency(selected_due)}"
                )
                amount = st.number_input(
                    "Amount received (₹)",
                    min_value=0.01,
                    max_value=float(selected_due),
                    value=float(min(selected_due, Decimal("4000.00"))),
                    step=100.0,
                )
                method = st.selectbox(
                    "Payment method",
                    ["UPI", "Bank Transfer", "Cash", "Cheque", "Other"],
                )
                reference = st.text_input("Transaction / receipt reference")
                received_date = st.date_input("Payment date", value=datetime.now().date())
                submitted = st.form_submit_button(
                    "Record Payment",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                payment_amount = Decimal(str(amount)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                if payment_amount <= 0:
                    st.error("Payment amount must be greater than zero.")
                elif payment_amount > selected_due:
                    st.error("Payment exceeds the invoice's outstanding balance.")
                else:
                    try:
                        # Recalculate the balance immediately before committing.
                        current_paid = db.scalar(
                            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                                Payment.invoice_id == selected_invoice_id
                            )
                        )
                        current_due = (
                            Decimal(str(selected_invoice.total_amount))
                            - Decimal(str(current_paid or 0))
                        )
                        if payment_amount > current_due:
                            st.error("The outstanding balance changed. Refresh and try again.")
                            return

                        payment = Payment(
                            invoice_id=selected_invoice_id,
                            amount=payment_amount,
                            payment_method=method,
                            reference_number=reference.strip() or None,
                            payment_date=datetime.combine(received_date, datetime.min.time()),
                        )
                        db.add(payment)
                        db.flush()
                        db.add(AuditLog(
                            user_id=user["id"],
                            action="CUSTOMER_PAYMENT_RECORDED",
                            entity_type="Payment",
                            entity_id=payment.id,
                            details=(
                                f"Invoice {selected_invoice.invoice_number}; "
                                f"received {format_currency(payment_amount)} via {method}; "
                                f"reference {reference.strip() or 'not supplied'}"
                            ),
                            timestamp=datetime.now(),
                        ))
                        db.commit()
                        st.success(
                            f"Payment of {format_currency(payment_amount)} recorded "
                            f"for invoice {selected_invoice.invoice_number}."
                        )
                    except Exception as exc:
                        db.rollback()
                        st.error(f"Payment could not be recorded: {exc}")
        else:
            st.info("There are no posted invoices with outstanding balances.")

        st.divider()
        st.markdown("### Accounts receivable ageing")
        today = datetime.now().date()
        ageing_rows = []
        total_outstanding = Decimal("0.00")
        buckets = {
            "Current (0–30 days)": Decimal("0.00"),
            "31–60 days": Decimal("0.00"),
            "61–90 days": Decimal("0.00"),
            "Over 90 days": Decimal("0.00"),
        }

        for invoice in invoices:
            paid = db.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.invoice_id == invoice.id
                )
            )
            due = Decimal(str(invoice.total_amount or 0)) - Decimal(str(paid or 0))
            if due <= 0:
                continue
            order = db.get(SalesOrder, invoice.order_id)
            customer = db.get(Customer, order.customer_id) if order else None
            invoice_day = invoice.invoice_date.date() if invoice.invoice_date else today
            age_days = max(0, (today - invoice_day).days)
            if age_days <= 30:
                bucket = "Current (0–30 days)"
            elif age_days <= 60:
                bucket = "31–60 days"
            elif age_days <= 90:
                bucket = "61–90 days"
            else:
                bucket = "Over 90 days"
            buckets[bucket] += due
            total_outstanding += due
            ageing_rows.append({
                "Invoice": invoice.invoice_number,
                "Customer": customer.name if customer else "Unknown",
                "Invoice date": invoice_day.strftime("%d-%m-%Y"),
                "Age (days)": age_days,
                "Invoice value": format_currency(invoice.total_amount),
                "Outstanding": format_currency(due),
                "Ageing bucket": bucket,
            })

        m1, m2 = st.columns(2)
        m1.metric("Total receivables", format_currency(total_outstanding))
        m2.metric("Invoices with balance", len(ageing_rows))
        bucket_cols = st.columns(4)
        for col, (label, value) in zip(bucket_cols, buckets.items()):
            col.metric(label, format_currency(value))

        if ageing_rows:
            st.dataframe(
                pd.DataFrame(ageing_rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("All posted invoices are fully settled. No outstanding receivables.")

        st.divider()
        st.markdown("### Payment register")
        payments = db.scalars(
            select(Payment).order_by(Payment.id.desc()).limit(100)
        ).all()
        if payments:
            payment_rows = []
            for payment in payments:
                invoice = db.get(Invoice, payment.invoice_id)
                order = db.get(SalesOrder, invoice.order_id) if invoice else None
                customer = db.get(Customer, order.customer_id) if order else None
                payment_rows.append({
                    "Date": payment.payment_date.strftime("%d-%m-%Y") if payment.payment_date else "—",
                    "Invoice": invoice.invoice_number if invoice else "Unknown",
                    "Customer": customer.name if customer else "Unknown",
                    "Amount": format_currency(payment.amount),
                    "Method": payment.payment_method,
                    "Reference": payment.reference_number or "—",
                })
            st.dataframe(
                pd.DataFrame(payment_rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No customer payments have been recorded yet.")

    except Exception as exc:
        st.error(f"Unable to load payment management: {exc}")
    finally:
        db.close()


def reporting_and_exports_page():
    """Build operational registers and downloadable CSV / Excel reports."""
    db = SessionLocal()
    try:
        section_heading("📊 Reports & Data Exports")
        st.write(
            "Download reconciliable stock, sales, production, purchasing and "
            "payment registers for review and audit."
        )

        stock_balances = get_stock_balances(db)
        stock_rows = []
        for material in db.scalars(select(RawMaterial).order_by(RawMaterial.name)).all():
            stock_rows.append({
                "Item type": "Raw material",
                "Item": material.name,
                "SKU": material.sku,
                "Quantity on hand": float(stock_balances.get(("RAW_MATERIAL", material.id), Decimal("0"))),
                "Unit": material.base_unit,
                "Reorder level": float(material.reorder_level or 0),
            })
        for product in db.scalars(select(Product).order_by(Product.name)).all():
            stock_rows.append({
                "Item type": "Finished product",
                "Item": product.name,
                "SKU": product.sku,
                "Quantity on hand": float(stock_balances.get(("PRODUCT", product.id), Decimal("0"))),
                "Unit": product.unit,
                "Reorder level": None,
            })
        stock_df = pd.DataFrame(stock_rows)

        sales_rows = []
        for invoice in db.scalars(select(Invoice).order_by(Invoice.invoice_date.desc())).all():
            order = db.get(SalesOrder, invoice.order_id)
            customer = db.get(Customer, order.customer_id) if order else None
            sales_rows.append({
                "Invoice number": invoice.invoice_number,
                "Order number": order.order_number if order else "",
                "Invoice date": invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else "",
                "Customer": customer.name if customer else "Unknown",
                "State": customer.state if customer else "",
                "Taxable amount": float(invoice.taxable_amount or 0),
                "CGST": float(invoice.cgst or 0),
                "SGST": float(invoice.sgst or 0),
                "IGST": float(invoice.igst or 0),
                "Invoice total": float(invoice.total_amount or 0),
                "Status": invoice.status,
            })
        sales_df = pd.DataFrame(sales_rows)

        production_rows = []
        for run in db.scalars(select(ProductionRun).order_by(ProductionRun.production_date.desc())).all():
            product = db.get(Product, run.product_id)
            planned = Decimal(str(run.planned_output or 0))
            good = Decimal(str(run.actual_good_output or 0))
            yield_percent = (good / planned * Decimal("100")) if planned > 0 else Decimal("0")
            production_rows.append({
                "Batch": run.batch_number,
                "Product": product.name if product else "Unknown",
                "Date": run.production_date.strftime("%Y-%m-%d") if run.production_date else "",
                "Planned output": float(planned),
                "Good output": float(good),
                "Damaged quantity": float(run.damaged_quantity or 0),
                "Yield %": round(float(yield_percent), 2),
                "Labour cost": float(run.labour_cost or 0),
                "Overhead cost": float(run.overhead_cost or 0),
                "Status": run.status,
            })
        production_df = pd.DataFrame(production_rows)

        purchase_rows = []
        for purchase in db.scalars(select(Purchase).order_by(Purchase.purchase_date.desc())).all():
            supplier = db.get(Supplier, purchase.supplier_id)
            purchase_rows.append({
                "Supplier invoice": purchase.invoice_number,
                "Supplier": supplier.name if supplier else "Unknown",
                "Date": purchase.purchase_date.strftime("%Y-%m-%d") if purchase.purchase_date else "",
                "Total": float(purchase.total_amount or 0),
                "Status": purchase.status,
            })
        purchases_df = pd.DataFrame(purchase_rows)

        payment_rows = []
        for payment in db.scalars(select(Payment).order_by(Payment.payment_date.desc())).all():
            invoice = db.get(Invoice, payment.invoice_id)
            order = db.get(SalesOrder, invoice.order_id) if invoice else None
            customer = db.get(Customer, order.customer_id) if order else None
            payment_rows.append({
                "Payment date": payment.payment_date.strftime("%Y-%m-%d") if payment.payment_date else "",
                "Invoice": invoice.invoice_number if invoice else "Unknown",
                "Customer": customer.name if customer else "Unknown",
                "Amount": float(payment.amount or 0),
                "Method": payment.payment_method,
                "Reference": payment.reference_number or "",
            })
        payments_df = pd.DataFrame(payment_rows)

        st.markdown("### Report previews")
        report_tabs = st.tabs(["Stock", "Sales", "Production", "Purchases", "Payments"])
        for tab, dataframe in zip(
            report_tabs, [stock_df, sales_df, production_df, purchases_df, payments_df]
        ):
            with tab:
                if dataframe.empty:
                    st.info("No records available for this report yet.")
                else:
                    st.dataframe(dataframe, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("### Download reports")
        report_map = {
            "Stock Summary": stock_df,
            "Sales Register": sales_df,
            "Production Register": production_df,
            "Purchase Register": purchases_df,
            "Payment Register": payments_df,
        }
        selected_report = st.selectbox("Choose a report", list(report_map.keys()))
        selected_df = report_map[selected_report]
        csv_bytes = selected_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Download selected report (CSV)",
            data=csv_bytes,
            file_name=f"nammafactory_{selected_report.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            for sheet_name, dataframe in report_map.items():
                dataframe.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        excel_buffer.seek(0)
        st.download_button(
            "Download complete report workbook (Excel)",
            data=excel_buffer.getvalue(),
            file_name="NammaFactory_Management_Reports.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.caption(
            "The Excel workbook contains five worksheets: Stock Summary, Sales Register, "
            "Production Register, Purchase Register and Payment Register."
        )

    except Exception as exc:
        st.error(f"Unable to generate reports: {exc}")
    finally:
        db.close()







def system_health_page():
    """Read-only operational integrity checks across stock, sales and finance."""
    db = SessionLocal()
    try:
        section_heading(
            "🛡️ System Health & Data Integrity",
            "Run consistency checks across inventory movements, invoices, payments and production records.",
        )

        checks = []

        def add_check(name, status, count, details, recommendation):
            checks.append({
                "Check": name,
                "Status": status,
                "Issues": int(count),
                "Findings": details,
                "Recommended action": recommendation,
            })

        # Load the source records once for a consistent read-only snapshot.
        materials = db.scalars(select(RawMaterial)).all()
        products = db.scalars(select(Product)).all()
        movements = db.scalars(
            select(StockMovement).order_by(StockMovement.created_at.asc(), StockMovement.id.asc())
        ).all()
        invoices = db.scalars(select(Invoice)).all()
        payments = db.scalars(select(Payment)).all()
        orders = db.scalars(select(SalesOrder)).all()
        runs = db.scalars(select(ProductionRun)).all()

        # 1. Negative inventory balances.
        balances = get_stock_balances(db)
        item_names = {
            ("RAW_MATERIAL", item.id): item.name for item in materials
        }
        item_names.update({
            ("PRODUCT", item.id): item.name for item in products
        })
        negative_stock = []
        for key, balance in balances.items():
            if balance < 0:
                negative_stock.append({
                    "Item": item_names.get(key, f"{key[0]} #{key[1]}"),
                    "Item type": key[0],
                    "Balance": str(balance),
                })
        add_check(
            "Negative stock balances",
            "PASS" if not negative_stock else "WARNING",
            len(negative_stock),
            "No negative balances found." if not negative_stock else "; ".join(
                f"{row['Item']}: {row['Balance']}" for row in negative_stock
            ),
            "Investigate missing receipts, duplicate issues or incorrect dispatch quantities.",
        )

        # 2. Invalid stock movement references and quantities.
        invalid_movements = []
        known_types = {
            "OPENING", "PURCHASE", "PRODUCTION_OUTPUT", "STOCK_IN",
            "PRODUCTION_ISSUE", "DISPATCH", "STOCK_OUT",
        }
        for movement in movements:
            item_type = str(movement.item_type or "").upper()
            quantity = Decimal(str(movement.quantity or 0))
            valid_item = (
                item_type == "RAW_MATERIAL" and movement.item_id in {x.id for x in materials}
            ) or (
                item_type == "PRODUCT" and movement.item_id in {x.id for x in products}
            )
            if quantity <= 0 or not valid_item or str(movement.movement_type or "").upper() not in known_types:
                invalid_movements.append(
                    f"Movement #{movement.id}: type={movement.movement_type}, "
                    f"item={item_type} #{movement.item_id}, quantity={quantity}"
                )
        add_check(
            "Stock movement validity",
            "PASS" if not invalid_movements else "ERROR",
            len(invalid_movements),
            "All movement types, item references and quantities are valid."
            if not invalid_movements else "; ".join(invalid_movements[:10]),
            "Review the source transaction and correct it through an auditable adjustment; do not delete ledger history.",
        )

        # 3. Duplicate invoice per sales order.
        invoices_by_order = {}
        for invoice in invoices:
            invoices_by_order.setdefault(invoice.order_id, []).append(invoice)
        duplicate_invoice_orders = {
            order_id: rows for order_id, rows in invoices_by_order.items() if len(rows) > 1
        }
        duplicate_details = [
            f"Order #{order_id}: {', '.join(row.invoice_number for row in rows)}"
            for order_id, rows in duplicate_invoice_orders.items()
        ]
        add_check(
            "Duplicate invoices per order",
            "PASS" if not duplicate_details else "ERROR",
            len(duplicate_details),
            "No sales order has multiple invoices." if not duplicate_details else "; ".join(duplicate_details),
            "Review duplicate invoice records and resolve with a documented credit note or cancellation workflow.",
        )

        # 4. Invoice arithmetic and GST component consistency.
        invoice_errors = []
        for invoice in invoices:
            taxable = Decimal(str(invoice.taxable_amount or 0))
            cgst = Decimal(str(invoice.cgst or 0))
            sgst = Decimal(str(invoice.sgst or 0))
            igst = Decimal(str(invoice.igst or 0))
            total = Decimal(str(invoice.total_amount or 0))
            calculated = (taxable + cgst + sgst + igst).quantize(Decimal("0.01"))
            if calculated != total:
                invoice_errors.append(
                    f"{invoice.invoice_number}: stored total ₹{total}, calculated ₹{calculated}"
                )
            if igst > 0 and (cgst != 0 or sgst != 0):
                invoice_errors.append(
                    f"{invoice.invoice_number}: IGST and CGST/SGST are both populated"
                )
            if cgst != sgst:
                invoice_errors.append(
                    f"{invoice.invoice_number}: CGST ₹{cgst} differs from SGST ₹{sgst}"
                )
        add_check(
            "Invoice and GST arithmetic",
            "PASS" if not invoice_errors else "ERROR",
            len(invoice_errors),
            "Invoice totals and GST components are internally consistent."
            if not invoice_errors else "; ".join(invoice_errors[:10]),
            "Check invoice line calculations, tax type and rounding before issuing or reconciling.",
        )

        # 5. Payment allocations and outstanding balances.
        payment_totals = {}
        orphan_payments = []
        invalid_payments = []
        invoice_ids = {invoice.id for invoice in invoices}
        for payment in payments:
            amount = Decimal(str(payment.amount or 0))
            payment_totals[payment.invoice_id] = payment_totals.get(
                payment.invoice_id, Decimal("0")
            ) + amount
            if payment.invoice_id not in invoice_ids:
                orphan_payments.append(f"Payment #{payment.id} references missing invoice #{payment.invoice_id}")
            if amount <= 0:
                invalid_payments.append(f"Payment #{payment.id} has amount {amount}")

        overpaid_invoices = []
        for invoice in invoices:
            paid = payment_totals.get(invoice.id, Decimal("0"))
            total = Decimal(str(invoice.total_amount or 0))
            if paid > total:
                overpaid_invoices.append(
                    f"{invoice.invoice_number}: receipts ₹{paid} exceed invoice ₹{total}"
                )
        payment_issues = orphan_payments + invalid_payments + overpaid_invoices
        add_check(
            "Payment allocation integrity",
            "PASS" if not payment_issues else "WARNING",
            len(payment_issues),
            "Payment references and allocations are valid."
            if not payment_issues else "; ".join(payment_issues[:10]),
            "Verify receipt references and invoice allocation; investigate overpayments rather than hiding them.",
        )

        # 6. Production record completeness.
        consumption_run_ids = {
            row.production_run_id
            for row in db.scalars(select(ProductionConsumption)).all()
        }
        production_without_consumption = [
            run.batch_number for run in runs if run.id not in consumption_run_ids
        ]
        invalid_production = []
        for run in runs:
            planned = Decimal(str(run.planned_output or 0))
            good = Decimal(str(run.actual_good_output or 0))
            damaged = Decimal(str(run.damaged_quantity or 0))
            if planned <= 0 or good < 0 or damaged < 0:
                invalid_production.append(
                    f"{run.batch_number}: planned={planned}, good={good}, damaged={damaged}"
                )
        production_issues = invalid_production + [
            f"{batch}: no consumption rows" for batch in production_without_consumption
        ]
        add_check(
            "Production record completeness",
            "PASS" if not production_issues else "WARNING",
            len(production_issues),
            "Production runs have consumption details and valid output quantities."
            if not production_issues else "; ".join(production_issues[:10]),
            "Review legacy/test batches and confirm every completed run records material consumption and output.",
        )

        # 7. Order/invoice linkage.
        order_ids = {order.id for order in orders}
        orphan_invoices = [
            invoice.invoice_number for invoice in invoices if invoice.order_id not in order_ids
        ]
        add_check(
            "Invoice-to-order references",
            "PASS" if not orphan_invoices else "ERROR",
            len(orphan_invoices),
            "Every invoice references an existing sales order."
            if not orphan_invoices else ", ".join(orphan_invoices),
            "Investigate missing order references before financial reporting.",
        )

        # Summary
        error_count = sum(1 for item in checks if item["Status"] == "ERROR")
        warning_count = sum(1 for item in checks if item["Status"] == "WARNING")
        passed_count = sum(1 for item in checks if item["Status"] == "PASS")

        st.subheader("Integrity check summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Checks run", len(checks))
        c2.metric("Passed", passed_count)
        c3.metric("Warnings", warning_count)
        c4.metric("Errors", error_count)

        if error_count:
            st.error("Critical data integrity issues were detected. Review the findings below.")
        elif warning_count:
            st.warning("Some records need review. No critical errors were detected.")
        else:
            st.success("All current system integrity checks passed.")

        st.divider()
        section_heading("Detailed check results")
        results_df = pd.DataFrame(checks)
        st.dataframe(results_df, use_container_width=True, hide_index=True)

        st.download_button(
            "Download system health report (CSV)",
            data=results_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="NammaFactory_System_Health_Report.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.caption(
            "This page performs read-only diagnostics. It never edits stock, invoices, payments or production history. "
            "Warnings can include older test batches that were created before consumption tracking was added."
        )

    except Exception as exc:
        st.error(f"Unable to complete system health checks: {exc}")
    finally:
        db.close()


def gst_reconciliation_page():
    """Period-based GST summary and invoice-to-payment reconciliation."""
    db = SessionLocal()
    try:
        section_heading(
            "🧮 GST & Financial Reconciliation",
            "Reconcile posted invoices against receipts and review GST components for a selected period.",
        )

        invoices = db.scalars(
            select(Invoice).order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        ).all()
        payments = db.scalars(
            select(Payment).order_by(Payment.payment_date.desc(), Payment.id.desc())
        ).all()

        if not invoices:
            st.info("GST and reconciliation reports will appear after GST invoices are generated.")
            return

        invoice_dates = [
            inv.invoice_date.date()
            for inv in invoices
            if inv.invoice_date is not None
        ]
        if invoice_dates:
            min_date = min(invoice_dates)
            max_date = max(invoice_dates)
            selected_range = st.date_input(
                "GST reporting period",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        else:
            selected_range = ()

        if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
            start_date, end_date = selected_range
            period_invoices = [
                inv for inv in invoices
                if inv.invoice_date is not None
                and start_date <= inv.invoice_date.date() <= end_date
            ]
        else:
            period_invoices = invoices

        period_invoice_ids = {inv.id for inv in period_invoices}
        period_payments = [
            pay for pay in payments
            if pay.invoice_id in period_invoice_ids
        ]

        # GST values are calculated from the invoice date, while receipts are
        # allocated to the invoice for reconciliation, regardless of receipt date.
        gst_totals = {
            "Taxable value": Decimal("0"),
            "CGST": Decimal("0"),
            "SGST": Decimal("0"),
            "IGST": Decimal("0"),
            "Invoice value": Decimal("0"),
        }
        payment_by_invoice = {}
        for payment in payments:
            amount = Decimal(str(payment.amount or 0))
            payment_by_invoice[payment.invoice_id] = (
                payment_by_invoice.get(payment.invoice_id, Decimal("0")) + amount
            )

        reconciliation_rows = []
        ageing_buckets = {
            "Current (0–30 days)": Decimal("0"),
            "31–60 days": Decimal("0"),
            "61–90 days": Decimal("0"),
            "Over 90 days": Decimal("0"),
        }
        overpaid_rows = []
        today = datetime.now().date()
        total_receipts_for_period_invoices = Decimal("0")
        total_outstanding = Decimal("0")

        for invoice in period_invoices:
            taxable = Decimal(str(invoice.taxable_amount or 0))
            cgst = Decimal(str(invoice.cgst or 0))
            sgst = Decimal(str(invoice.sgst or 0))
            igst = Decimal(str(invoice.igst or 0))
            invoice_value = Decimal(str(invoice.total_amount or 0))
            paid = payment_by_invoice.get(invoice.id, Decimal("0"))
            balance = invoice_value - paid

            gst_totals["Taxable value"] += taxable
            gst_totals["CGST"] += cgst
            gst_totals["SGST"] += sgst
            gst_totals["IGST"] += igst
            gst_totals["Invoice value"] += invoice_value
            total_receipts_for_period_invoices += paid

            if balance > 0:
                total_outstanding += balance
                invoice_day = invoice.invoice_date.date() if invoice.invoice_date else today
                age = max(0, (today - invoice_day).days)
                if age <= 30:
                    bucket = "Current (0–30 days)"
                elif age <= 60:
                    bucket = "31–60 days"
                elif age <= 90:
                    bucket = "61–90 days"
                else:
                    bucket = "Over 90 days"
                ageing_buckets[bucket] += balance
                reconciliation_status = "Partially paid" if paid > 0 else "Unpaid"
            elif balance == 0:
                reconciliation_status = "Fully paid"
            else:
                reconciliation_status = "Overpaid"
                overpaid_rows.append({
                    "Invoice": invoice.invoice_number,
                    "Invoice value (₹)": float(invoice_value),
                    "Receipts allocated (₹)": float(paid),
                    "Excess receipt (₹)": float(-balance),
                })

            order = db.get(SalesOrder, invoice.order_id)
            customer = db.get(Customer, order.customer_id) if order else None
            reconciliation_rows.append({
                "Invoice": invoice.invoice_number,
                "Invoice date": invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else "",
                "Customer": customer.name if customer else "Unknown",
                "State": customer.state if customer else "",
                "Taxable (₹)": float(taxable),
                "CGST (₹)": float(cgst),
                "SGST (₹)": float(sgst),
                "IGST (₹)": float(igst),
                "Invoice total (₹)": float(invoice_value),
                "Receipts allocated (₹)": float(paid),
                "Balance (₹)": float(balance),
                "Reconciliation": reconciliation_status,
                "Invoice status": invoice.status,
            })

        total_gst = gst_totals["CGST"] + gst_totals["SGST"] + gst_totals["IGST"]
        st.subheader("GST summary for selected period")
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Taxable value", format_currency(gst_totals["Taxable value"]))
        g2.metric("CGST", format_currency(gst_totals["CGST"]))
        g3.metric("SGST", format_currency(gst_totals["SGST"]))
        g4.metric("IGST", format_currency(gst_totals["IGST"]))

        g5, g6 = st.columns(2)
        g5.metric("Total GST", format_currency(total_gst))
        g6.metric("Invoice value", format_currency(gst_totals["Invoice value"]))

        st.caption(
            "GST is grouped by invoice date. This is an operational summary of recorded invoices, "
            "not a statutory GST return or tax filing."
        )

        st.divider()
        section_heading("Invoice-to-payment reconciliation")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Invoices in period", f"{len(period_invoices):,}")
        r2.metric("Receipts allocated", format_currency(total_receipts_for_period_invoices))
        r3.metric("Outstanding", format_currency(total_outstanding))
        r4.metric("Overpaid invoices", f"{len(overpaid_rows):,}")

        reconciliation_df = pd.DataFrame(reconciliation_rows)
        st.dataframe(
            reconciliation_df,
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download invoice reconciliation (CSV)",
            data=reconciliation_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="NammaFactory_Invoice_Reconciliation.csv",
            mime="text/csv",
            use_container_width=True,
        )

        if overpaid_rows:
            st.warning(
                "One or more invoices have receipts exceeding their invoice value. "
                "Review these allocations; excess receipts are not treated as negative receivables."
            )
            st.dataframe(pd.DataFrame(overpaid_rows), use_container_width=True, hide_index=True)

        st.divider()
        section_heading("Receivables ageing for selected invoices")
        ageing_df = pd.DataFrame([
            {"Ageing bucket": label, "Outstanding (₹)": float(value)}
            for label, value in ageing_buckets.items()
        ])
        st.bar_chart(ageing_df.set_index("Ageing bucket"), use_container_width=True)
        st.dataframe(ageing_df, use_container_width=True, hide_index=True)

        st.divider()
        section_heading("Receipt register for selected invoice period")
        receipt_rows = []
        for payment in period_payments:
            invoice = db.get(Invoice, payment.invoice_id)
            order = db.get(SalesOrder, invoice.order_id) if invoice else None
            customer = db.get(Customer, order.customer_id) if order else None
            receipt_rows.append({
                "Receipt date": payment.payment_date.strftime("%Y-%m-%d") if payment.payment_date else "",
                "Invoice": invoice.invoice_number if invoice else "Unknown",
                "Customer": customer.name if customer else "Unknown",
                "Amount (₹)": float(payment.amount or 0),
                "Method": payment.payment_method,
                "Reference": payment.reference_number or "",
            })

        receipt_df = pd.DataFrame(receipt_rows)
        if receipt_df.empty:
            st.info("No receipts are linked to invoices in the selected period.")
        else:
            st.dataframe(receipt_df, use_container_width=True, hide_index=True)
            st.download_button(
                "Download receipt register (CSV)",
                data=receipt_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="NammaFactory_Receipt_Register.csv",
                mime="text/csv",
                use_container_width=True,
            )

    except Exception as exc:
        st.error(f"Unable to load GST and reconciliation reports: {exc}")
    finally:
        db.close()


def business_analytics_page():
    """Owner-facing commercial analytics for revenue, GST, collections and purchases."""
    db = SessionLocal()
    try:
        section_heading(
            "📊 Business Analytics",
            "Track revenue, customer contribution, GST liability, collections and purchasing trends.",
        )

        invoices = db.scalars(
            select(Invoice).order_by(Invoice.invoice_date.asc(), Invoice.id.asc())
        ).all()
        payments = db.scalars(
            select(Payment).order_by(Payment.payment_date.asc(), Payment.id.asc())
        ).all()
        purchases = db.scalars(
            select(Purchase).order_by(Purchase.purchase_date.asc(), Purchase.id.asc())
        ).all()

        if not invoices and not payments and not purchases:
            st.info("Business analytics will appear after invoices, payments and purchases are recorded.")
            return

        # Resolve invoice -> customer and aggregate values using Decimal.
        invoice_customer = {}
        customer_sales = {}
        monthly_sales = {}
        gst_summary = {
            "CGST": Decimal("0"),
            "SGST": Decimal("0"),
            "IGST": Decimal("0"),
        }
        taxable_revenue = Decimal("0")
        invoiced_value = Decimal("0")

        for invoice in invoices:
            order = db.get(SalesOrder, invoice.order_id)
            customer = db.get(Customer, order.customer_id) if order else None
            customer_name = customer.name if customer else "Unknown customer"
            invoice_customer[invoice.id] = customer_name

            taxable = Decimal(str(invoice.taxable_amount or 0))
            total = Decimal(str(invoice.total_amount or 0))
            cgst = Decimal(str(invoice.cgst or 0))
            sgst = Decimal(str(invoice.sgst or 0))
            igst = Decimal(str(invoice.igst or 0))

            taxable_revenue += taxable
            invoiced_value += total
            gst_summary["CGST"] += cgst
            gst_summary["SGST"] += sgst
            gst_summary["IGST"] += igst

            customer_sales[customer_name] = customer_sales.get(customer_name, Decimal("0")) + taxable

            if invoice.invoice_date:
                month_key = invoice.invoice_date.strftime("%Y-%m")
                monthly_sales[month_key] = monthly_sales.get(month_key, Decimal("0")) + taxable

        # Aggregate collections by invoice and month.
        collected_total = Decimal("0")
        payment_by_invoice = {}
        monthly_collections = {}

        for payment in payments:
            amount = Decimal(str(payment.amount or 0))
            collected_total += amount
            payment_by_invoice[payment.invoice_id] = (
                payment_by_invoice.get(payment.invoice_id, Decimal("0")) + amount
            )
            if payment.payment_date:
                month_key = payment.payment_date.strftime("%Y-%m")
                monthly_collections[month_key] = (
                    monthly_collections.get(month_key, Decimal("0")) + amount
                )

        # Calculate outstanding against each posted invoice, flooring at zero
        # so overpayments do not create negative receivables in this summary.
        outstanding_total = Decimal("0")
        receivable_rows = []
        for invoice in invoices:
            invoice_value = Decimal(str(invoice.total_amount or 0))
            paid_value = payment_by_invoice.get(invoice.id, Decimal("0"))
            balance = max(Decimal("0"), invoice_value - paid_value)
            outstanding_total += balance
            if balance > 0:
                receivable_rows.append({
                    "Invoice": invoice.invoice_number,
                    "Customer": invoice_customer.get(invoice.id, "Unknown customer"),
                    "Invoice date": invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else "",
                    "Invoice value (₹)": float(invoice_value),
                    "Collected (₹)": float(paid_value),
                    "Outstanding (₹)": float(balance),
                })

        # Purchase spend uses recorded purchase totals. The status is shown
        # separately so users can interpret drafts versus received purchases.
        purchase_spend = Decimal("0")
        purchase_rows = []
        monthly_purchases = {}
        for purchase in purchases:
            amount = Decimal(str(purchase.total_amount or 0))
            if str(purchase.status or "").upper() in {"RECEIVED", "POSTED", "COMPLETED"}:
                purchase_spend += amount
            supplier = db.get(Supplier, purchase.supplier_id)
            supplier_name = supplier.name if supplier else "Unknown supplier"
            purchase_rows.append({
                "Supplier invoice": purchase.invoice_number,
                "Supplier": supplier_name,
                "Date": purchase.purchase_date.strftime("%Y-%m-%d") if purchase.purchase_date else "",
                "Amount (₹)": float(amount),
                "Status": purchase.status,
            })
            if purchase.purchase_date:
                month_key = purchase.purchase_date.strftime("%Y-%m")
                monthly_purchases[month_key] = monthly_purchases.get(month_key, Decimal("0")) + amount

        gst_total = sum(gst_summary.values(), Decimal("0"))
        collection_rate = (
            collected_total / invoiced_value * Decimal("100")
            if invoiced_value > 0 else Decimal("0")
        )

        st.subheader("Commercial performance")
        a, b, c, d = st.columns(4)
        a.metric("Taxable revenue", format_currency(taxable_revenue))
        b.metric("Total invoice value", format_currency(invoiced_value))
        c.metric("Customer collections", format_currency(collected_total))
        d.metric("Outstanding receivables", format_currency(outstanding_total))

        e, f, g, h = st.columns(4)
        e.metric("GST on invoices", format_currency(gst_total))
        f.metric("Purchase spend (received)", format_currency(purchase_spend))
        g.metric("Collection rate", f"{collection_rate:.2f}%")
        h.metric("Invoices issued", f"{len(invoices):,}")

        st.divider()
        section_heading("Revenue and collection trends")

        trend_months = sorted(set(monthly_sales) | set(monthly_collections) | set(monthly_purchases))
        if trend_months:
            trend_rows = []
            for month in trend_months:
                trend_rows.append({
                    "Month": month,
                    "Taxable sales (₹)": float(monthly_sales.get(month, Decimal("0"))),
                    "Collections (₹)": float(monthly_collections.get(month, Decimal("0"))),
                    "Received purchases (₹)": float(monthly_purchases.get(month, Decimal("0"))),
                })
            trend_df = pd.DataFrame(trend_rows).set_index("Month")
            st.line_chart(
                trend_df[["Taxable sales (₹)", "Collections (₹)"]],
                use_container_width=True,
            )
            st.bar_chart(
                trend_df[["Taxable sales (₹)", "Received purchases (₹)"]],
                use_container_width=True,
            )
            st.dataframe(trend_df, use_container_width=True)
        else:
            st.info("No dated transactions are available for monthly trends.")

        st.divider()
        section_heading("Customer-wise sales contribution")
        if customer_sales:
            customer_df = pd.DataFrame([
                {"Customer": name, "Taxable sales (₹)": float(value)}
                for name, value in sorted(customer_sales.items(), key=lambda item: item[1], reverse=True)
            ])
            st.bar_chart(customer_df.set_index("Customer"), use_container_width=True)
            st.dataframe(customer_df, use_container_width=True, hide_index=True)
        else:
            st.info("No customer sales are available yet.")

        st.divider()
        section_heading("GST breakdown")
        gst_df = pd.DataFrame([
            {"Tax component": name, "Amount (₹)": float(value)}
            for name, value in gst_summary.items()
        ])
        gst_df.loc[len(gst_df)] = {
            "Tax component": "Total GST",
            "Amount (₹)": float(gst_total),
        }
        st.dataframe(gst_df, use_container_width=True, hide_index=True)
        st.caption(
            "This summary totals GST amounts recorded on invoices. It is an operational summary, "
            "not a filed GST return or a substitute for tax reconciliation."
        )

        st.divider()
        section_heading("Receivables and collections")
        if receivable_rows:
            receivables_df = pd.DataFrame(receivable_rows)
            st.dataframe(receivables_df, use_container_width=True, hide_index=True)
            st.download_button(
                "Download outstanding receivables (CSV)",
                data=receivables_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="NammaFactory_Outstanding_Receivables.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.success("There are no outstanding invoice balances.")

        st.divider()
        section_heading("Purchase expenditure")
        if purchase_rows:
            purchases_df = pd.DataFrame(purchase_rows)
            st.dataframe(purchases_df, use_container_width=True, hide_index=True)
            st.download_button(
                "Download purchase analysis (CSV)",
                data=purchases_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="NammaFactory_Purchase_Analysis.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("No purchase transactions have been recorded yet.")

    except Exception as exc:
        st.error(f"Unable to load business analytics: {exc}")
    finally:
        db.close()


def production_intelligence_page():
    """Owner-facing planned-versus-actual manufacturing analysis."""
    db = SessionLocal()
    try:
        section_heading(
            "🏭 Production Intelligence",
            "Understand batch yield, material consumption variance and the cost of good production.",
        )
        runs = db.scalars(
            select(ProductionRun).order_by(
                ProductionRun.production_date.desc(), ProductionRun.id.desc()
            )
        ).all()
        if not runs:
            st.info("Complete a production run to start building production intelligence.")
            return

        product_lookup = {x.id: x.name for x in db.scalars(select(Product)).all()}
        material_lookup = {x.id: x.name for x in db.scalars(select(RawMaterial)).all()}

        batch_rows, variance_rows = [], []
        total_planned = total_good = total_damaged = Decimal("0")
        total_cost = costed_output = Decimal("0")

        for run in runs:
            planned = Decimal(str(run.planned_output or 0))
            good = Decimal(str(run.actual_good_output or 0))
            damaged = Decimal(str(run.damaged_quantity or 0))
            yield_pct = good / planned * Decimal("100") if planned > 0 else Decimal("0")
            material_cost = Decimal("0")

            consumptions = db.scalars(
                select(ProductionConsumption).where(
                    ProductionConsumption.production_run_id == run.id
                )
            ).all()

            for item in consumptions:
                standard = Decimal(str(item.planned_quantity or 0))
                actual = Decimal(str(item.actual_quantity or 0))
                difference = actual - standard
                variance_pct = difference / standard * Decimal("100") if standard > 0 else Decimal("0")
                rate = Decimal(str(item.unit_cost or 0))
                line_cost = actual * rate
                material_cost += line_cost
                variance_rows.append({
                    "Batch": run.batch_number,
                    "Product": product_lookup.get(run.product_id, "Unknown"),
                    "Material": material_lookup.get(item.raw_material_id, "Unknown"),
                    "Planned quantity": float(standard),
                    "Actual quantity": float(actual),
                    "Variance quantity": float(difference),
                    "Variance %": round(float(variance_pct), 2),
                    "Unit": item.unit,
                    "Unit cost (₹)": float(rate),
                    "Actual material cost (₹)": float(line_cost),
                    "Status": "Over-consumed" if difference > 0 else "Under-consumed" if difference < 0 else "On standard",
                })

            labour = Decimal(str(run.labour_cost or 0))
            overhead = Decimal(str(run.overhead_cost or 0))
            batch_cost = material_cost + labour + overhead
            unit_cost = batch_cost / good if good > 0 else Decimal("0")

            batch_rows.append({
                "Batch": run.batch_number,
                "Date": run.production_date.strftime("%Y-%m-%d") if run.production_date else "",
                "Product": product_lookup.get(run.product_id, "Unknown"),
                "Planned output": float(planned),
                "Good output": float(good),
                "Damaged units": float(damaged),
                "Yield %": round(float(yield_pct), 2),
                "Yield variance (pp)": round(float(yield_pct - Decimal("100")), 2),
                "Material cost (₹)": float(material_cost),
                "Labour (₹)": float(labour),
                "Overhead (₹)": float(overhead),
                "Total batch cost (₹)": float(batch_cost),
                "Cost / good unit (₹)": float(unit_cost),
            })

            total_planned += planned
            total_good += good
            total_damaged += damaged
            if good > 0:
                total_cost += batch_cost
                costed_output += good

        overall_yield = total_good / total_planned * Decimal("100") if total_planned > 0 else Decimal("0")
        average_cost = total_cost / costed_output if costed_output > 0 else Decimal("0")

        st.subheader("Overall manufacturing performance")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Batches completed", f"{len(runs):,}")
        c2.metric("Good units produced", f"{total_good:,.0f}")
        c3.metric("Overall yield", f"{overall_yield:.2f}%")
        c4.metric("Average cost / good unit", format_currency(average_cost))
        c5, c6 = st.columns(2)
        c5.metric("Planned output", f"{total_planned:,.0f}")
        c6.metric("Damaged units", f"{total_damaged:,.0f}")

        st.divider()
        section_heading("Batch-wise production performance")
        batch_df = pd.DataFrame(batch_rows)
        st.dataframe(batch_df, use_container_width=True, hide_index=True)
        st.bar_chart(batch_df[["Batch", "Planned output", "Good output"]].set_index("Batch"), use_container_width=True)

        st.divider()
        section_heading("Material consumption variance")
        variance_df = pd.DataFrame(variance_rows)
        if variance_df.empty:
            st.info("No material consumption records are available for these production runs.")
        else:
            st.caption("Positive variance means actual consumption exceeded the BOM standard; negative variance means it was below standard.")
            st.dataframe(variance_df, use_container_width=True, hide_index=True)
            overused = variance_df[variance_df["Variance quantity"] > 0]
            if not overused.empty:
                st.warning(f"{len(overused)} material line(s) show consumption above the planned BOM quantity.")
            else:
                st.success("No material over-consumption detected in recorded production runs.")

        st.divider()
        section_heading("Export production analysis")
        st.download_button(
            "Download batch performance (CSV)",
            data=batch_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="NammaFactory_Batch_Performance.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Download material variance (CSV)",
            data=variance_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="NammaFactory_Material_Variance.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Yield variance is shown in percentage points against the 100% planned-output baseline.")
    except Exception as exc:
        st.error(f"Unable to load production intelligence: {exc}")
    finally:
        db.close()


def stock_ledger_page(db):
    """Read-only stock movement ledger with per-item running balances."""

    section_heading(
        "📚 Stock Ledger",
        "Trace every receipt, production issue, production output and dispatch with a running balance.",
    )

    raw_materials = db.scalars(
        select(RawMaterial).order_by(RawMaterial.name)
    ).all()
    products = db.scalars(
        select(Product).order_by(Product.name)
    ).all()
    movements = db.scalars(
        select(StockMovement).order_by(
            StockMovement.created_at.asc(),
            StockMovement.id.asc(),
        )
    ).all()

    item_names = {}
    item_units = {}
    for material in raw_materials:
        key = ("RAW_MATERIAL", material.id)
        item_names[key] = material.name
        item_units[key] = material.base_unit
    for product in products:
        key = ("PRODUCT", product.id)
        item_names[key] = product.name
        item_units[key] = product.unit

    incoming_types = {"OPENING", "PURCHASE", "PRODUCTION_OUTPUT", "STOCK_IN"}
    outgoing_types = {"PRODUCTION_ISSUE", "DISPATCH", "STOCK_OUT"}

    # Calculate running balances over the entire chronological ledger first.
    # Filtering is applied only after this calculation so opening balances
    # and earlier movements are never accidentally excluded.
    running_balances = {}
    ledger_rows = []

    users = db.scalars(select(User)).all()
    user_names = {u.id: u.full_name or u.username for u in users}

    for movement in movements:
        item_key = (str(movement.item_type).upper(), movement.item_id)
        item_name = item_names.get(
            item_key,
            f"Unknown item ({movement.item_type} #{movement.item_id})",
        )
        unit = movement.unit or item_units.get(item_key, "")
        quantity = Decimal(str(movement.quantity or 0))
        movement_type = str(movement.movement_type or "").upper()

        if movement_type in incoming_types:
            signed_quantity = quantity
            direction = "IN"
        elif movement_type in outgoing_types:
            signed_quantity = -quantity
            direction = "OUT"
        else:
            signed_quantity = Decimal("0")
            direction = "OTHER"

        running_balances[item_key] = (
            running_balances.get(item_key, Decimal("0")) + signed_quantity
        )

        ledger_rows.append({
            "Movement ID": movement.id,
            "Date & Time": (
                movement.created_at.strftime("%d %b %Y, %I:%M:%S %p")
                if movement.created_at else "—"
            ),
            "_timestamp": movement.created_at,
            "Item": item_name,
            "_item_key": item_key,
            "Item Type": str(movement.item_type),
            "Movement": movement_type,
            "Direction": direction,
            "Quantity": float(quantity),
            "Signed Quantity": float(signed_quantity),
            "Unit": unit,
            "Running Balance": float(running_balances[item_key]),
            "Reference": (
                f"{movement.reference_type or ''} "
                f"{movement.reference_id or ''}".strip()
            ),
            "Performed By": user_names.get(movement.created_by, "System"),
            "Notes": movement.notes or "",
        })

    if not ledger_rows:
        st.info("No stock movements have been recorded yet.")
        return

    ledger_df = pd.DataFrame(ledger_rows)

    # Current stock summary
    current_balances = get_stock_balances(db)
    summary_rows = []
    for key, item_name in item_names.items():
        summary_rows.append({
            "Item": item_name,
            "Type": key[0],
            "Current Balance": float(current_balances.get(key, Decimal("0"))),
            "Unit": item_units.get(key, ""),
        })

    section_heading("Current stock position")
    st.dataframe(
        pd.DataFrame(summary_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    section_heading("Filter stock movements")

    f1, f2, f3 = st.columns(3)
    item_labels = {
        f"{item_names[key]} ({key[0].replace('_', ' ').title()})": key
        for key in item_names
    }
    with f1:
        selected_item_label = st.selectbox(
            "Item",
            ["All items"] + sorted(item_labels.keys()),
        )
    with f2:
        movement_options = ["All movements"] + sorted(
            ledger_df["Movement"].dropna().unique().tolist()
        )
        selected_movement = st.selectbox("Movement type", movement_options)
    with f3:
        direction_filter = st.selectbox(
            "Direction",
            ["All", "IN", "OUT", "OTHER"],
        )

    search_term = st.text_input(
        "Search reference, notes or user",
        placeholder="e.g. purchase invoice, batch number, order number...",
    )

    timestamps = [v.date() for v in ledger_df["_timestamp"] if v is not None]
    if timestamps:
        date_filter = st.date_input(
            "Movement date range",
            value=(min(timestamps), max(timestamps)),
            min_value=min(timestamps),
            max_value=max(timestamps),
        )
    else:
        date_filter = ()

    filtered = ledger_df.copy()
    if selected_item_label != "All items":
        chosen_key = item_labels[selected_item_label]
        filtered = filtered[filtered["_item_key"] == chosen_key]
    if selected_movement != "All movements":
        filtered = filtered[filtered["Movement"] == selected_movement]
    if direction_filter != "All":
        filtered = filtered[filtered["Direction"] == direction_filter]

    if search_term.strip():
        term = search_term.strip().lower()
        searchable = (
            filtered["Reference"].fillna("").str.lower()
            + " " + filtered["Notes"].fillna("").str.lower()
            + " " + filtered["Performed By"].fillna("").str.lower()
        )
        filtered = filtered[searchable.str.contains(term, regex=False)]

    if isinstance(date_filter, (tuple, list)) and len(date_filter) == 2:
        start_date, end_date = date_filter
        filtered = filtered[
            filtered["_timestamp"].apply(
                lambda value: value is not None
                and start_date <= value.date() <= end_date
            )
        ]

    st.caption(
        f"Showing {len(filtered):,} of {len(ledger_df):,} stock movements. "
        "Running balances are calculated from the complete ledger before filters are applied."
    )

    display_columns = [
        "Movement ID", "Date & Time", "Item", "Item Type",
        "Movement", "Direction", "Quantity", "Unit",
        "Running Balance", "Reference", "Performed By", "Notes",
    ]
    display_df = filtered.sort_values(
        ["_timestamp", "Movement ID"],
        ascending=[False, False],
        na_position="last",
    )[display_columns]

    if display_df.empty:
        st.info("No stock movements match the selected filters.")
    else:
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Quantity": st.column_config.NumberColumn(format="%.3f"),
                "Running Balance": st.column_config.NumberColumn(format="%.3f"),
            },
        )

    csv_bytes = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download filtered stock ledger (CSV)",
        data=csv_bytes,
        file_name="NammaFactory_Stock_Ledger.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.caption(
        "This ledger is read-only. Stock balances are derived from recorded stock movements; "
        "the page does not directly edit inventory quantities."
    )


def audit_trail_page(db):
    """Read-only, filterable audit history for authorized management roles."""

    section_heading(
        "🧾 Audit Trail",
        "A chronological, read-only record of important actions performed in NammaFactory.",
    )

    try:
        events = db.scalars(
            select(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        ).all()

        users = db.scalars(select(User)).all()
        user_lookup = {
            user.id: f"{user.full_name} ({user.username})"
            for user in users
        }

        if not events:
            st.info("No audit events have been recorded yet.")
            return

        # Convert database events into a consistent display structure.
        rows = []
        for event in events:
            event_time = event.timestamp
            rows.append({
                "Event ID": event.id,
                "Date & Time": (
                    event_time.strftime("%d %b %Y, %I:%M:%S %p")
                    if event_time else "—"
                ),
                "_timestamp": event_time,
                "User": user_lookup.get(event.user_id, f"User #{event.user_id}"),
                "_user_id": event.user_id,
                "Action": str(event.action or "—"),
                "Record Type": str(event.entity_type or "—"),
                "Record ID": str(event.entity_id) if event.entity_id is not None else "—",
                "Details": str(event.details or ""),
            })

        audit_df = pd.DataFrame(rows)

        # Summary metrics use the complete event set, not the filtered view.
        total_events = len(audit_df)
        distinct_users = audit_df["_user_id"].nunique()
        distinct_actions = audit_df["Action"].nunique()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total audit events", f"{total_events:,}")
        m2.metric("Users represented", f"{distinct_users:,}")
        m3.metric("Action types", f"{distinct_actions:,}")

        st.divider()
        section_heading("Filter audit records")

        f1, f2, f3 = st.columns(3)
        with f1:
            user_options = ["All users"] + sorted(audit_df["User"].dropna().unique().tolist())
            selected_user = st.selectbox("Performed by", user_options)
        with f2:
            action_options = ["All actions"] + sorted(audit_df["Action"].dropna().unique().tolist())
            selected_action = st.selectbox("Action", action_options)
        with f3:
            type_options = ["All record types"] + sorted(audit_df["Record Type"].dropna().unique().tolist())
            selected_type = st.selectbox("Record type", type_options)

        search_text = st.text_input(
            "Search details, record ID or user",
            placeholder="e.g. invoice number, order number, payment...",
        )

        date_values = [value.date() for value in audit_df["_timestamp"] if value is not None]
        if date_values:
            min_date = min(date_values)
            max_date = max(date_values)
            date_range = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        else:
            date_range = ()

        filtered = audit_df.copy()

        if selected_user != "All users":
            filtered = filtered[filtered["User"] == selected_user]
        if selected_action != "All actions":
            filtered = filtered[filtered["Action"] == selected_action]
        if selected_type != "All record types":
            filtered = filtered[filtered["Record Type"] == selected_type]

        if search_text.strip():
            needle = search_text.strip().lower()
            searchable = (
                filtered["User"].fillna("").str.lower()
                + " " + filtered["Action"].fillna("").str.lower()
                + " " + filtered["Record Type"].fillna("").str.lower()
                + " " + filtered["Record ID"].fillna("").str.lower()
                + " " + filtered["Details"].fillna("").str.lower()
            )
            filtered = filtered[searchable.str.contains(needle, regex=False)]

        if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
            start_date, end_date = date_range
            filtered = filtered[
                filtered["_timestamp"].apply(
                    lambda value: value is not None
                    and start_date <= value.date() <= end_date
                )
            ]

        st.caption(f"Showing {len(filtered):,} of {total_events:,} audit events.")

        display_columns = [
            "Event ID", "Date & Time", "User", "Action",
            "Record Type", "Record ID", "Details",
        ]
        display_df = filtered[display_columns]

        if display_df.empty:
            st.info("No audit events match the selected filters.")
        else:
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Event ID": st.column_config.NumberColumn("Event ID", format="%d"),
                    "Details": st.column_config.TextColumn("Details", width="large"),
                },
            )

        export_df = display_df.copy()
        csv_data = export_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Download filtered audit trail (CSV)",
            data=csv_data,
            file_name="NammaFactory_Audit_Trail.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.caption(
            "Audit records are displayed read-only. This page does not provide edit or delete controls."
        )

    except Exception as exc:
        st.error(f"Unable to load the audit trail: {exc}")




def render_stock_ledger_page():
    """Open and reliably close the database session for the stock ledger."""
    db = SessionLocal()
    try:
        stock_ledger_page(db)
    finally:
        db.close()


def render_audit_trail_page():
    """Open and reliably close the database session for the audit page."""
    db = SessionLocal()
    try:
        audit_trail_page(db)
    finally:
        db.close()


# ============================================================
# 10. ROLE-SPECIFIC NAVIGATION
# ============================================================

ROLE_PAGES = {

    "admin": [
        "Dashboard",
        "Sales & Orders",
        "Dispatch",
        "Inventory",
        "Stock Ledger",
        "Production",
        "Purchases",
        "Reports",
        "System Health",
        "Audit Trail",
    ],

    "salesman": [
        "My Dashboard",
        "New Order",
        "My Orders",
        "My Customers",
    ],

    "production": [
        "Production Dashboard",
        "Production Entry",
        "BOM Management",
        "Inventory",
        "Stock Ledger",
    ],

    "accountant": [
        "Accounts Dashboard",
        "Invoices",
        "Payments",
        "Financial Reports",
        "GST & Reconciliation",
        "System Health",
        "Stock Ledger",
        "Audit Trail",
    ],

    "owner": [
        "Owner Dashboard",
        "Business Analytics",
        "Production Intelligence",
        "GST & Reconciliation",
        "System Health",
        "Reports",
        "Stock Ledger",
        "Audit Trail",
    ],
}


# ============================================================
# 11. INDIVIDUAL WORKSPACE PAGES
# ============================================================

def show_workspace_page(role, page, user):

    page_header(
        page,
        f"{THEMES[role]['name']} | NammaFactory",
    )

    # --------------------------------------------------------
    # ADMIN WORKSPACE
    # --------------------------------------------------------

    if role == "admin":

        if page == "Sales & Orders":

            admin_orders_page(user)

        elif page == "Dispatch":

            dispatch_page(user)

        elif page == "Inventory":

            show_inventory_page()

        elif page == "Stock Ledger":

            render_stock_ledger_page()

        elif page == "Production":

            production_entry_page(user)

        elif page == "Purchases":

            purchase_management_page(user)

        elif page == "Reports":

            reporting_and_exports_page()

        elif page == "Stock Ledger":

            render_stock_ledger_page()

        elif page == "System Health":

            system_health_page()

        elif page == "Audit Trail":

            render_audit_trail_page()

    # --------------------------------------------------------
    # SALESMAN WORKSPACE
    # --------------------------------------------------------

    elif role == "salesman":

        if page == "New Order":

            new_order_page(user)

        elif page == "My Orders":

            db = SessionLocal()

            try:

                orders = get_user_orders(db, user["id"])

                section_heading("My Order History")

                if orders:

                    data = [
                        {
                            "Order Number": o.order_number,
                            "Date": o.order_date.strftime("%d-%m-%Y"),
                            "Status": o.status,
                        }
                        for o in orders
                    ]

                    st.dataframe(
                        pd.DataFrame(data),
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    show_empty_state("No orders have been submitted yet.")

            finally:
                db.close()

        elif page == "My Customers":

            db = SessionLocal()

            try:

                customers = db.scalars(
                    select(Customer)
                ).all()

                if customers:

                    data = [
                        {
                            "Customer": c.name,
                            "Phone": c.phone,
                            "State": c.state,
                        }
                        for c in customers
                    ]

                    st.dataframe(
                        pd.DataFrame(data),
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    show_empty_state("No customers registered.")

            finally:
                db.close()

    # --------------------------------------------------------
    # PRODUCTION WORKSPACE
    # --------------------------------------------------------

    elif role == "production":

        if page == "Production Entry":

            production_entry_page(user)

        elif page == "BOM Management":

            section_heading("Bill of Materials")

            db = SessionLocal()

            try:

                boms = db.scalars(
                    select(BOM)
                ).all()

                products = {
                    p.id: p.name
                    for p in db.scalars(select(Product)).all()
                }

                if boms:

                    data = [
                        {
                            "Product": products.get(b.product_id, "Unknown"),
                            "Expected Batch Output": float(b.batch_output_quantity),
                            "Version": b.version,
                            "Active": b.is_active,
                        }
                        for b in boms
                    ]

                    st.dataframe(
                        pd.DataFrame(data),
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    show_empty_state("No BOM records found.")

            finally:
                db.close()

        elif page == "Inventory":

            show_inventory_page()

        elif page == "Stock Ledger":

            render_stock_ledger_page()

    # --------------------------------------------------------
    # ACCOUNTANT WORKSPACE
    # --------------------------------------------------------

    elif role == "accountant":

        if page == "Invoices":

            invoice_register_page(user)

        elif page == "Payments":

            payments_management_page(user)

        elif page == "Financial Reports":

            reporting_and_exports_page()

        elif page == "GST & Reconciliation":

            gst_reconciliation_page()

        elif page == "Stock Ledger":

            render_stock_ledger_page()

        elif page == "System Health":

            system_health_page()

        elif page == "Audit Trail":

            render_audit_trail_page()

    # --------------------------------------------------------
    # OWNER WORKSPACE
    # --------------------------------------------------------

    elif role == "owner":

        if page == "Reports":

            reporting_and_exports_page()

        elif page == "Stock Ledger":

            render_stock_ledger_page()

        elif page == "Audit Trail":

            render_audit_trail_page()

        elif page == "Business Analytics":

            business_analytics_page()

        elif page == "Production Intelligence":

            production_intelligence_page()

        elif page == "GST & Reconciliation":

            gst_reconciliation_page()

        elif page == "System Health":

            system_health_page()

        elif page == "Reports":

            section_heading("Management Reports")

            st.write(
                "Consolidated financial, inventory and production reports."
            )


# ============================================================
# GST INVOICE GENERATION
# ============================================================

def build_invoice_pdf(db, invoice):
    """Create a GST invoice PDF in memory and return its bytes."""
    order = db.get(SalesOrder, invoice.order_id)
    if not order:
        raise ValueError("The sales order linked to this invoice was not found.")

    customer = db.get(Customer, order.customer_id)
    if not customer:
        raise ValueError("The customer linked to this invoice was not found.")

    items = db.scalars(
        select(SalesOrderItem).where(SalesOrderItem.order_id == order.id)
    ).all()

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="InvoiceTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#173D32"),
        spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="SmallRight",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    ))

    story = [
        Paragraph("TAX INVOICE", styles["InvoiceTitle"]),
        Paragraph("<b>NammaFactory</b>", styles["Heading2"]),
        Paragraph("Tamil Nadu, India", styles["Normal"]),
        Spacer(1, 8),
    ]

    invoice_info = [
        ["Invoice Number", invoice.invoice_number, "Invoice Date", invoice.invoice_date.strftime("%d-%m-%Y")],
        ["Order Number", order.order_number, "Place of Supply", customer.state or "Not specified"],
    ]
    info_table = Table(invoice_info, colWidths=[30*mm, 58*mm, 30*mm, 58*mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F0")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#222222")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D4CE")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.extend([
        info_table,
        Spacer(1, 10),
        Paragraph("Bill To", styles["Heading3"]),
        Paragraph(f"<b>{customer.name}</b>", styles["Normal"]),
        Paragraph(f"State: {customer.state or 'Not specified'}", styles["Normal"]),
        Paragraph(f"Address: {customer.address or 'Not provided'}", styles["Normal"]),
        Paragraph(f"GSTIN: {customer.gstin or 'Not provided'}", styles["Normal"]),
        Spacer(1, 10),
    ])

    table_data = [[
        "Description", "HSN", "Qty", "Unit Price", "Taxable Value"
    ]]
    for item in items:
        product = db.get(Product, item.product_id)
        if not product:
            continue
        line_value = money(Decimal(str(item.quantity)) * Decimal(str(item.unit_price)))
        table_data.append([
            product.name,
            product.hsn_code or "-",
            f"{item.quantity} {product.unit}",
            f"Rs. {Decimal(str(item.unit_price)):,.2f}",
            f"Rs. {line_value:,.2f}",
        ])

    products_table = Table(
        table_data,
        colWidths=[48*mm, 20*mm, 28*mm, 32*mm, 40*mm],
        repeatRows=1,
    )
    products_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173D32")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C5BE")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#222222")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
    ]))
    story.extend([products_table, Spacer(1, 12)])

    tax_rows = [
        ["Taxable Amount", f"Rs. {Decimal(str(invoice.taxable_amount)):,.2f}"],
        ["CGST", f"Rs. {Decimal(str(invoice.cgst)):,.2f}"],
        ["SGST", f"Rs. {Decimal(str(invoice.sgst)):,.2f}"],
        ["IGST", f"Rs. {Decimal(str(invoice.igst)):,.2f}"],
        ["Invoice Total", f"Rs. {Decimal(str(invoice.total_amount)):,.2f}"],
    ]
    totals_table = Table(tax_rows, colWidths=[55*mm, 45*mm], hAlign="RIGHT")
    totals_table.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#222222")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D4CE")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#E4EFE8")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([
        totals_table,
        Spacer(1, 18),
        Paragraph(
            "This is a computer-generated invoice from NammaFactory.",
            styles["Normal"],
        ),
    ])

    document.build(story)
    return buffer.getvalue()


def invoice_register_page(user):

    section_heading(
        "GST Invoice Register",
        "Generate GST invoices for approved orders and review previously issued invoices.",
    )

    db = SessionLocal()

    try:
        all_orders = db.scalars(
            select(SalesOrder).order_by(SalesOrder.id.desc())
        ).all()

        existing_invoices = db.scalars(
            select(Invoice).order_by(Invoice.id.desc())
        ).all()

        invoiced_order_ids = {invoice.order_id for invoice in existing_invoices}

        eligible_orders = [
            order for order in all_orders
            if order.status == "APPROVED" and order.id not in invoiced_order_ids
        ]

        st.markdown("### Approved Orders Ready for Invoicing")

        if eligible_orders:
            for order in eligible_orders:
                customer = db.get(Customer, order.customer_id)
                items = db.scalars(
                    select(SalesOrderItem).where(
                        SalesOrderItem.order_id == order.id
                    )
                ).all()

                if not customer or not items:
                    st.warning(
                        f"Order {order.order_number} is missing customer or item details."
                    )
                    continue

                taxable_amount = Decimal("0")
                cgst_amount = Decimal("0")
                sgst_amount = Decimal("0")
                igst_amount = Decimal("0")

                for item in items:
                    product = db.get(Product, item.product_id)
                    if not product:
                        continue

                    line_taxable = money(
                        Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
                    )
                    gst_rate = Decimal(str(product.gst_rate))
                    line_gst = money(line_taxable * gst_rate / Decimal("100"))

                    taxable_amount += line_taxable

                    if is_intrastate_customer(customer.state):
                        half_tax = money(line_gst / Decimal("2"))
                        cgst_amount += half_tax
                        sgst_amount += half_tax
                    else:
                        igst_amount += line_gst

                total_amount = money(
                    taxable_amount + cgst_amount + sgst_amount + igst_amount
                )

                with st.container(border=True):
                    st.markdown(f"#### {order.order_number}")
                    st.write(f"**Customer:** {customer.name}")
                    st.write(f"**Customer state:** {customer.state}")
                    st.write(f"**Order date:** {order.order_date.strftime('%d-%m-%Y')}")
                    st.write(f"**Taxable value:** {format_currency(taxable_amount)}")

                    if is_intrastate_customer(customer.state):
                        st.write(f"**CGST:** {format_currency(cgst_amount)}")
                        st.write(f"**SGST:** {format_currency(sgst_amount)}")
                        st.write("**IGST:** ₹0.00")
                    else:
                        st.write("**CGST:** ₹0.00")
                        st.write("**SGST:** ₹0.00")
                        st.write(f"**IGST:** {format_currency(igst_amount)}")

                    st.metric("Invoice Total", format_currency(total_amount))

                    if st.button(
                        "Generate GST Invoice",
                        key=f"generate_invoice_{order.id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        # Recheck inside the transaction to avoid duplicate invoices.
                        duplicate = db.scalar(
                            select(Invoice).where(Invoice.order_id == order.id)
                        )

                        if duplicate:
                            st.warning("An invoice already exists for this order.")
                            st.rerun()

                        invoice_number = (
                            f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}-"
                            f"{secrets.token_hex(2).upper()}"
                        )

                        invoice = Invoice(
                            invoice_number=invoice_number,
                            order_id=order.id,
                            taxable_amount=money(taxable_amount),
                            cgst=money(cgst_amount),
                            sgst=money(sgst_amount),
                            igst=money(igst_amount),
                            total_amount=money(total_amount),
                            status="POSTED",
                            invoice_date=datetime.now(),
                        )

                        db.add(invoice)
                        db.flush()

                        db.add(
                            AuditLog(
                                user_id=user["id"],
                                action="GST_INVOICE_GENERATED",
                                entity_type="Invoice",
                                entity_id=invoice.id,
                                details=(
                                    f"Invoice {invoice_number} generated for "
                                    f"order {order.order_number}; taxable="
                                    f"{taxable_amount}; CGST={cgst_amount}; "
                                    f"SGST={sgst_amount}; IGST={igst_amount}; "
                                    f"total={total_amount}"
                                ),
                                timestamp=datetime.now(),
                            )
                        )

                        db.commit()
                        st.success(f"GST invoice {invoice_number} generated successfully.")
                        st.rerun()

        else:
            show_empty_state(
                "There are no approved, uninvoiced orders available. "
                "Approve a sales order first."
            )

        st.divider()
        st.markdown("### Issued Invoice Register")

        if existing_invoices:
            invoice_rows = []

            for invoice in existing_invoices:
                order = db.get(SalesOrder, invoice.order_id)
                customer = db.get(Customer, order.customer_id) if order else None

                invoice_rows.append(
                    {
                        "Invoice Number": invoice.invoice_number,
                        "Order Number": order.order_number if order else "Unknown",
                        "Customer": customer.name if customer else "Unknown",
                        "Date": invoice.invoice_date.strftime("%d-%m-%Y"),
                        "Taxable Amount": float(invoice.taxable_amount),
                        "CGST": float(invoice.cgst),
                        "SGST": float(invoice.sgst),
                        "IGST": float(invoice.igst),
                        "Total": float(invoice.total_amount),
                        "Status": invoice.status,
                    }
                )

            st.dataframe(
                pd.DataFrame(invoice_rows),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("### Download Invoice PDFs")
            for invoice in existing_invoices:
                try:
                    pdf_bytes = build_invoice_pdf(db, invoice)
                    st.download_button(
                        label=f"Download {invoice.invoice_number} (PDF)",
                        data=pdf_bytes,
                        file_name=f"{invoice.invoice_number}.pdf",
                        mime="application/pdf",
                        key=f"download_invoice_pdf_{invoice.id}",
                        use_container_width=True,
                    )
                except Exception as pdf_error:
                    st.error(
                        f"Could not prepare PDF for {invoice.invoice_number}: {pdf_error}"
                    )
        else:
            show_empty_state("No invoices have been generated yet.")

    except Exception as exc:
        db.rollback()
        st.error(f"Invoice operation failed: {exc}")

    finally:
        db.close()


# ============================================================
# 12. INVENTORY PAGE
# ============================================================

def show_inventory_page():

    section_heading(
        "📦 Inventory Management",
        "Current stock calculated from recorded stock movements.",
    )

    db = SessionLocal()

    try:

        balances = get_stock_balances(db)

        materials = db.scalars(
            select(RawMaterial)
        ).all()

        products = db.scalars(
            select(Product)
        ).all()

        inventory_rows = []

        for material in materials:

            key = ("RAW_MATERIAL", material.id)

            quantity = balances.get(key, Decimal("0"))

            inventory_rows.append(
                {
                    "Item": material.name,
                    "Category": "Raw Material",
                    "Quantity": float(quantity),
                    "Unit": material.base_unit,
                    "Reorder Level": float(material.reorder_level),
                    "Status": (
                        "LOW STOCK"
                        if quantity <= material.reorder_level
                        else "AVAILABLE"
                    ),
                }
            )

        for product in products:

            key = ("PRODUCT", product.id)

            quantity = balances.get(key, Decimal("0"))

            inventory_rows.append(
                {
                    "Item": product.name,
                    "Category": "Finished Goods",
                    "Quantity": float(quantity),
                    "Unit": product.unit,
                    "Reorder Level": 0,
                    "Status": "AVAILABLE",
                }
            )

        if inventory_rows:

            st.dataframe(
                pd.DataFrame(inventory_rows),
                use_container_width=True,
                hide_index=True,
            )

        else:

            show_empty_state("No inventory records found.")

        st.divider()

        section_heading("Stock Movement Ledger")

        movements = db.scalars(
            select(StockMovement).order_by(
                StockMovement.id.desc()
            ).limit(100)
        ).all()

        if movements:

            movement_rows = [
                {
                    "Movement ID": m.id,
                    "Item Type": m.item_type,
                    "Item ID": m.item_id,
                    "Movement": m.movement_type,
                    "Quantity": float(m.quantity),
                    "Unit": m.unit,
                    "Reference": m.reference_type,
                    "Date": m.created_at.strftime("%d-%m-%Y %H:%M"),
                }
                for m in movements
            ]

            st.dataframe(
                pd.DataFrame(movement_rows),
                use_container_width=True,
                hide_index=True,
            )

        else:

            show_empty_state("No stock movements found.")

    finally:
        db.close()


# ============================================================
# 13. NEW ORDER PAGE
# ============================================================

def new_order_page(user):

    section_heading(
        "🛒 Create New Customer Order",
        "Submit a customer order. It will remain pending until the factory admin reviews it.",
    )

    db = SessionLocal()

    try:
        customers = db.scalars(
            select(Customer).order_by(Customer.name)
        ).all()

        products = db.scalars(
            select(Product).where(Product.is_active == True).order_by(Product.name)
        ).all()

        if not customers or not products:
            st.warning(
                "Customer and active product master data are required before creating an order."
            )
            return

        customer_lookup = {customer.id: customer for customer in customers}
        product_lookup = {product.id: product for product in products}

        with st.form("new_order_form"):
            st.markdown("### Customer Information")
            selected_customer_id = st.selectbox(
                "Select Customer",
                list(customer_lookup),
                format_func=lambda customer_id: customer_lookup[customer_id].name,
            )
            customer = customer_lookup[selected_customer_id]

            st.caption(
                f"State: {customer.state} | Phone: {customer.phone or 'Not provided'}"
            )

            st.divider()
            st.markdown("### Product Information")
            selected_product_id = st.selectbox(
                "Select Product",
                list(product_lookup),
                format_func=lambda product_id: (
                    f"{product_lookup[product_id].name} "
                    f"({product_lookup[product_id].sku})"
                ),
            )
            product = product_lookup[selected_product_id]

            quantity = st.number_input(
                f"Quantity ({product.unit})",
                min_value=1,
                value=10,
                step=1,
            )

            unit_price = Decimal(str(product.selling_price))
            estimated_value = unit_price * Decimal(str(quantity))

            st.caption(f"Unit price: {format_currency(unit_price)}")
            st.metric("Estimated Taxable Order Value", format_currency(estimated_value))

            submitted = st.form_submit_button(
                "Submit Order for Approval",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            order_number = (
                f"NF-{datetime.now().strftime('%Y%m%d-%H%M%S')}-"
                f"{secrets.token_hex(2).upper()}"
            )

            order = SalesOrder(
                order_number=order_number,
                customer_id=customer.id,
                salesman_id=user["id"],
                status="PENDING",
                order_date=datetime.now(),
                approved_by=None,
            )

            db.add(order)
            db.flush()

            db.add(
                SalesOrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=Decimal(str(quantity)),
                    unit_price=unit_price,
                )
            )

            db.add(
                AuditLog(
                    user_id=user["id"],
                    action="ORDER_CREATED",
                    entity_type="SalesOrder",
                    entity_id=order.id,
                    details=(
                        f"Order {order_number} submitted for approval; "
                        f"customer={customer.name}; product={product.name}; "
                        f"quantity={quantity}; unit_price={unit_price}"
                    ),
                    timestamp=datetime.now(),
                )
            )

            db.commit()
            st.session_state.pop("order_preview", None)
            st.success(
                f"Order {order_number} submitted successfully! Its current status is PENDING."
            )
            st.info("The factory admin can now review this order in Sales & Orders.")
            st.rerun()

    except Exception as exc:
        db.rollback()
        st.error(f"Could not submit the order. No changes were saved. Details: {exc}")

    finally:
        db.close()


def admin_orders_page(user):

    section_heading(
        "Order Management",
        "Review salesman submissions and approve or reject pending orders.",
    )

    db = SessionLocal()

    try:
        orders = db.scalars(
            select(SalesOrder).order_by(SalesOrder.id.desc())
        ).all()
        pending_orders = [order for order in orders if order.status == "PENDING"]

        st.metric("Pending Approval", len(pending_orders))
        st.divider()

        if not orders:
            show_empty_state("No customer orders have been submitted yet.")
            return

        if pending_orders:
            st.markdown("### Orders Awaiting Approval")

            for order in pending_orders:
                customer = db.get(Customer, order.customer_id)
                salesman = db.get(User, order.salesman_id)
                items = db.scalars(
                    select(SalesOrderItem).where(
                        SalesOrderItem.order_id == order.id
                    )
                ).all()

                with st.container(border=True):
                    st.markdown(f"#### {order.order_number}")
                    st.write(f"**Customer:** {customer.name if customer else 'Unknown'}")
                    st.write(f"**Salesman:** {salesman.full_name if salesman else 'Unknown'}")
                    st.write(f"**Order date:** {order.order_date.strftime('%d-%m-%Y %H:%M')}")

                    order_total = Decimal("0")
                    for item in items:
                        product = db.get(Product, item.product_id)
                        line_total = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
                        order_total += line_total
                        st.write(
                            f"- {product.name if product else 'Unknown product'}: "
                            f"{item.quantity} × {format_currency(item.unit_price)} "
                            f"= {format_currency(line_total)}"
                        )

                    st.metric("Taxable Order Value", format_currency(order_total))
                    approve_col, reject_col = st.columns(2)

                    with approve_col:
                        approve_clicked = st.button(
                            "Approve Order",
                            key=f"approve_order_{order.id}",
                            type="primary",
                            use_container_width=True,
                        )

                    with reject_col:
                        reject_clicked = st.button(
                            "Reject Order",
                            key=f"reject_order_{order.id}",
                            use_container_width=True,
                        )

                    if approve_clicked:
                        order.status = "APPROVED"
                        order.approved_by = user["id"]
                        db.add(
                            AuditLog(
                                user_id=user["id"],
                                action="ORDER_APPROVED",
                                entity_type="SalesOrder",
                                entity_id=order.id,
                                details=f"Order {order.order_number} approved by factory admin.",
                                timestamp=datetime.now(),
                            )
                        )
                        db.commit()
                        st.success(f"{order.order_number} approved.")
                        st.rerun()

                    if reject_clicked:
                        order.status = "REJECTED"
                        db.add(
                            AuditLog(
                                user_id=user["id"],
                                action="ORDER_REJECTED",
                                entity_type="SalesOrder",
                                entity_id=order.id,
                                details=f"Order {order.order_number} rejected by factory admin.",
                                timestamp=datetime.now(),
                            )
                        )
                        db.commit()
                        st.warning(f"{order.order_number} rejected.")
                        st.rerun()
        else:
            show_empty_state("There are currently no orders awaiting approval.")

        st.divider()
        st.markdown("### All Orders")

        all_rows = []
        for order in orders:
            customer = db.get(Customer, order.customer_id)
            salesman = db.get(User, order.salesman_id)
            all_rows.append(
                {
                    "Order Number": order.order_number,
                    "Customer": customer.name if customer else "Unknown",
                    "Salesman": salesman.full_name if salesman else "Unknown",
                    "Date": order.order_date.strftime("%d-%m-%Y"),
                    "Status": order.status,
                }
            )

        st.dataframe(
            pd.DataFrame(all_rows),
            use_container_width=True,
            hide_index=True,
        )

    except Exception as exc:
        db.rollback()
        st.error(f"Unable to load or update orders: {exc}")

    finally:
        db.close()


# ============================================================
# 13. PRODUCTION ENTRY AND STOCK POSTING
# ============================================================

def production_entry_page(user):

    section_heading(
        "🏭 Production Control Centre",
        "Record a batch, consume raw materials and receive finished goods in one controlled transaction."
    )

    db = SessionLocal()

    try:
        active_boms = db.scalars(
            select(BOM).where(BOM.is_active == True).order_by(BOM.id)
        ).all()

        if not active_boms:
            st.warning("No active Bill of Materials is available. Create or activate a BOM before recording production.")
            return

        products = {p.id: p for p in db.scalars(select(Product)).all()}
        bom_labels = {
            bom.id: f"{products[bom.product_id].name} | BOM v{bom.version} | Batch standard: {bom.batch_output_quantity}"
            for bom in active_boms if bom.product_id in products
        }
        available_boms = [bom for bom in active_boms if bom.id in bom_labels]

        if not available_boms:
            st.warning("The active BOM records do not have valid products linked to them.")
            return

        selected_bom_id = st.selectbox(
            "Select product / BOM",
            options=[b.id for b in available_boms],
            format_func=lambda value: bom_labels[value],
            key="production_bom_select",
        )
        selected_bom = db.get(BOM, selected_bom_id)
        product = products[selected_bom.product_id]

        planned_output = st.number_input(
            "Planned production output (packets)",
            min_value=1.0,
            value=float(selected_bom.batch_output_quantity),
            step=1.0,
            key=f"planned_output_{selected_bom_id}",
        )

        bom_items = db.scalars(
            select(BOMItem).where(BOMItem.bom_id == selected_bom.id).order_by(BOMItem.id)
        ).all()

        if not bom_items:
            st.warning("This BOM has no material lines. Add BOM items before recording production.")
            return

        planned_decimal = Decimal(str(planned_output))
        standard_batch = Decimal(str(selected_bom.batch_output_quantity))
        if standard_batch <= 0:
            st.error("The BOM batch output must be greater than zero.")
            return

        scale = planned_decimal / standard_batch
        raw_materials = {m.id: m for m in db.scalars(select(RawMaterial)).all()}
        balances = get_stock_balances(db)

        planned_by_item = {}
        for line in bom_items:
            material = raw_materials.get(line.raw_material_id)
            if material:
                planned_by_item[line.id] = (
                    material,
                    Decimal(str(line.standard_quantity)) * scale,
                    line.unit,
                )

        st.divider()
        st.markdown("### 1. Production output")
        out1, out2, out3 = st.columns(3)
        with out1:
            good_output = st.number_input(
                "Actual good packets",
                min_value=0.0,
                max_value=float(planned_output * 2),
                value=float(planned_output),
                step=1.0,
                key=f"good_output_{selected_bom_id}",
            )
        with out2:
            damaged_quantity = st.number_input(
                "Damaged packets / pouches",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key=f"damaged_{selected_bom_id}",
            )
        with out3:
            cartons_default = max(0, int(float(good_output) // 20))
            cartons_used = st.number_input(
                "Cartons used",
                min_value=0.0,
                value=float(cartons_default),
                step=1.0,
                key=f"cartons_{selected_bom_id}",
            )

        labour_cost = st.number_input(
            "Direct labour cost (₹)", min_value=0.0, value=0.0, step=100.0,
            key=f"labour_{selected_bom_id}",
        )
        overhead_cost = st.number_input(
            "Power / gas / overhead cost (₹)", min_value=0.0, value=0.0, step=100.0,
            key=f"overhead_{selected_bom_id}",
        )

        st.divider()
        st.markdown("### 2. Actual raw-material consumption")
        st.caption("Planned quantities are calculated from the selected BOM. Enter the actual quantities issued to this batch.")

        actual_values = {}
        with st.form(key=f"production_form_{selected_bom_id}"):
            for line_id, (material, planned_qty, unit) in planned_by_item.items():
                available_qty = balances.get(("RAW_MATERIAL", material.id), Decimal("0"))
                material_label = f"{material.name} ({unit})"
                st.write(f"**{material_label}** — Planned: {planned_qty:.3f} {unit} | Available: {available_qty:.3f} {unit}")
                # Packaging damage is included in actual pouch consumption, not in good finished output.
                default_actual = planned_qty
                material_text = (material.name + " " + material.sku).lower()
                if "pouch" in material_text or "packet" in material_text:
                    default_actual = max(Decimal("0"), Decimal(str(good_output)) + Decimal(str(damaged_quantity)))
                if "carton" in material_text:
                    default_actual = Decimal(str(cartons_used))
                actual_values[line_id] = st.number_input(
                    f"Actual quantity — {material.name}",
                    min_value=0.0,
                    value=float(default_actual),
                    step=0.1 if unit.lower() in ("kg", "litre", "l") else 1.0,
                    key=f"actual_material_{selected_bom_id}_{line_id}",
                )

            submitted = st.form_submit_button(
                "Post Production & Update Stock",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            actual_good = Decimal(str(good_output))
            damaged = Decimal(str(damaged_quantity))
            cartons = Decimal(str(cartons_used))
            labour = Decimal(str(labour_cost)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            overhead = Decimal(str(overhead_cost)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            if actual_good <= 0:
                st.error("Actual good output must be greater than zero.")
                return
            if damaged < 0 or cartons < 0:
                st.error("Damaged quantity and cartons used cannot be negative.")
                return

            # Re-read balances immediately before posting. No partial stock updates are allowed.
            db.rollback()
            fresh_balances = get_stock_balances(db)
            consumption_rows = []
            shortage_messages = []

            for line in bom_items:
                material = db.get(RawMaterial, line.raw_material_id)
                if not material:
                    shortage_messages.append("A raw material in the BOM no longer exists.")
                    continue
                planned_qty = Decimal(str(line.standard_quantity)) * scale
                actual_qty = Decimal(str(actual_values.get(line.id, 0)))
                available_qty = fresh_balances.get(("RAW_MATERIAL", material.id), Decimal("0"))
                if actual_qty <= 0:
                    shortage_messages.append(f"{material.name}: actual consumption must be greater than zero.")
                elif available_qty < actual_qty:
                    shortage_messages.append(
                        f"{material.name}: required {actual_qty} {line.unit}, available {available_qty} {line.unit}."
                    )
                consumption_rows.append((material, planned_qty, actual_qty, line.unit))

            if shortage_messages:
                st.error("Production was not posted. Please resolve these issues:")
                for message in shortage_messages:
                    st.write(f"- {message}")
                return

            try:
                batch_number = f"NF-PROD-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(2).upper()}"
                run = ProductionRun(
                    batch_number=batch_number,
                    product_id=product.id,
                    bom_id=selected_bom.id,
                    planned_output=planned_decimal,
                    actual_good_output=actual_good,
                    damaged_quantity=damaged,
                    cartons_used=cartons,
                    labour_cost=labour,
                    overhead_cost=overhead,
                    status="COMPLETED",
                    production_date=datetime.now(),
                    created_by=user["id"],
                )
                db.add(run)
                db.flush()

                for material, planned_qty, actual_qty, unit in consumption_rows:
                    db.add(ProductionConsumption(
                        production_run_id=run.id,
                        raw_material_id=material.id,
                        planned_quantity=planned_qty,
                        actual_quantity=actual_qty,
                        unit=unit,
                        unit_cost=get_weighted_average_unit_cost(db, material),
                    ))
                    db.add(StockMovement(
                        item_type="RAW_MATERIAL",
                        item_id=material.id,
                        movement_type="PRODUCTION_ISSUE",
                        quantity=actual_qty,
                        unit=unit,
                        reference_type="PRODUCTION_RUN",
                        reference_id=run.id,
                        notes=f"Actual material issue for {batch_number}",
                        created_by=user["id"],
                        created_at=datetime.now(),
                    ))

                db.add(StockMovement(
                    item_type="PRODUCT",
                    item_id=product.id,
                    movement_type="PRODUCTION_OUTPUT",
                    quantity=actual_good,
                    unit=product.unit,
                    reference_type="PRODUCTION_RUN",
                    reference_id=run.id,
                    notes=f"Good finished output from {batch_number}; damaged quantity {damaged}",
                    created_by=user["id"],
                    created_at=datetime.now(),
                ))
                db.add(AuditLog(
                    user_id=user["id"],
                    action="PRODUCTION_COMPLETED",
                    entity_type="ProductionRun",
                    entity_id=run.id,
                    details=(
                        f"{batch_number}: planned {planned_decimal}, good output {actual_good}, "
                        f"damaged {damaged}; materials: "
                        + "; ".join(f"{m.name} {actual} {unit}" for m, _, actual, unit in consumption_rows)
                    ),
                    timestamp=datetime.now(),
                ))
                db.commit()

                yield_pct = (actual_good / planned_decimal * Decimal("100")) if planned_decimal else Decimal("0")
                st.success(f"Production batch {batch_number} posted successfully!")
                m1, m2, m3 = st.columns(3)
                m1.metric("Good finished packets", f"{actual_good:,.0f}")
                m2.metric("Yield", f"{yield_pct:.2f}%")
                m3.metric("Damaged", f"{damaged:,.0f}")
                st.info("Raw-material issues, finished-goods receipt and audit entry were committed together.")

            except Exception as exc:
                db.rollback()
                st.error(f"Production could not be posted. No stock changes were saved. Details: {exc}")

        st.divider()
        st.markdown("### 3. Production history")
        recent_runs = db.scalars(
            select(ProductionRun).order_by(ProductionRun.id.desc()).limit(20)
        ).all()
        if recent_runs:
            history = []
            for run in recent_runs:
                run_product = db.get(Product, run.product_id)
                history.append({
                    "Batch": run.batch_number,
                    "Product": run_product.name if run_product else "Unknown",
                    "Planned": float(run.planned_output),
                    "Good Output": float(run.actual_good_output),
                    "Damaged": float(run.damaged_quantity),
                    "Status": run.status,
                    "Date": run.production_date.strftime("%d-%m-%Y %H:%M"),
                })
            st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
        else:
            show_empty_state("No production batches have been recorded yet.")

        # Production variance analysis: compare actual batch results with BOM-scaled standards.
        st.divider()
        st.markdown("### 4. Planned vs actual variance analysis")
        variance_runs = db.scalars(
            select(ProductionRun).order_by(ProductionRun.id.desc()).limit(20)
        ).all()

        if variance_runs:
            yield_rows = []
            material_variance_rows = []

            for variance_run in variance_runs:
                planned_qty = Decimal(str(variance_run.planned_output or 0))
                good_qty = Decimal(str(variance_run.actual_good_output or 0))
                yield_pct = (good_qty / planned_qty * Decimal("100")) if planned_qty > 0 else Decimal("0")
                yield_variance = yield_pct - Decimal("100")

                yield_rows.append({
                    "Batch": variance_run.batch_number,
                    "Planned packets": float(planned_qty),
                    "Good packets": float(good_qty),
                    "Yield %": round(float(yield_pct), 2),
                    "Yield variance (pp)": round(float(yield_variance), 2),
                    "Damaged": float(variance_run.damaged_quantity or 0),
                })

                consumption_lines = db.scalars(
                    select(ProductionConsumption).where(
                        ProductionConsumption.production_run_id == variance_run.id
                    ).order_by(ProductionConsumption.id)
                ).all()

                for consumption in consumption_lines:
                    material = db.get(RawMaterial, consumption.raw_material_id)
                    planned_material = Decimal(str(consumption.planned_quantity or 0))
                    actual_material = Decimal(str(consumption.actual_quantity or 0))
                    difference = actual_material - planned_material
                    variance_pct = (
                        difference / planned_material * Decimal("100")
                        if planned_material > 0 else Decimal("0")
                    )
                    material_variance_rows.append({
                        "Batch": variance_run.batch_number,
                        "Raw material": material.name if material else f"Material #{consumption.raw_material_id}",
                        "Planned": float(planned_material),
                        "Actual": float(actual_material),
                        "Variance": float(difference),
                        "Variance %": round(float(variance_pct), 2),
                        "Unit": consumption.unit,
                        "Status": "Overconsumption" if difference > 0 else (
                            "Underconsumption" if difference < 0 else "On standard"
                        ),
                    })

            st.markdown("**Batch yield performance**")
            st.dataframe(pd.DataFrame(yield_rows), use_container_width=True, hide_index=True)

            st.markdown("**Raw-material consumption variance**")
            if material_variance_rows:
                st.dataframe(
                    pd.DataFrame(material_variance_rows),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Material consumption records will appear after a production batch is posted.")
            st.caption(
                "Yield variance is measured against 100% of planned output. "
                "Material variance = actual consumption minus BOM-scaled planned consumption. "
                "Positive material variance indicates overconsumption."
            )
        else:
            st.info("Variance analysis will appear after the first production batch is posted.")

        # Batch costing using transparent assignment benchmark valuation rates.
        st.divider()
        st.markdown("### 5. Production costing")
        st.caption(
            "Benchmark valuation basis: flour ₹43.125/kg (weighted average of "
            "100 kg at ₹42 and 60 kg at ₹45); oil ₹140/L; spice ₹200/kg; "
            "pouch ₹2.50 each; carton ₹15 each. Labour and overhead are taken "
            "from each production batch."
        )

        costing_runs = db.scalars(
            select(ProductionRun).order_by(ProductionRun.id.desc()).limit(20)
        ).all()

        if costing_runs:
            costing_rows = []
            costing_details = {}

            for costing_run in costing_runs:
                consumption_lines = db.scalars(
                    select(ProductionConsumption).where(
                        ProductionConsumption.production_run_id == costing_run.id
                    ).order_by(ProductionConsumption.id)
                ).all()

                material_total = Decimal("0.00")
                material_breakdown = []

                for consumption in consumption_lines:
                    material = db.get(RawMaterial, consumption.raw_material_id)
                    sku = material.sku if material else ""
                    stored_rate = Decimal(str(consumption.unit_cost or 0))
                    rate = stored_rate if stored_rate > 0 else get_weighted_average_unit_cost(
                        db, material
                    ) if material else Decimal("0.00")
                    quantity = Decimal(str(consumption.actual_quantity or 0))
                    line_cost = (quantity * rate).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    material_total += line_cost
                    material_breakdown.append({
                        "Material": material.name if material else f"Material #{consumption.raw_material_id}",
                        "Quantity": f"{quantity} {consumption.unit}",
                        "Rate": format_currency(rate),
                        "Cost": format_currency(line_cost),
                    })

                labour_total = Decimal(str(costing_run.labour_cost or 0))
                overhead_total = Decimal(str(costing_run.overhead_cost or 0))
                total_cost = material_total + labour_total + overhead_total
                good_quantity = Decimal(str(costing_run.actual_good_output or 0))
                cost_per_good = (
                    total_cost / good_quantity
                    if good_quantity > 0 else Decimal("0.00")
                )

                costing_rows.append({
                    "Batch": costing_run.batch_number,
                    "Material cost": float(material_total),
                    "Labour": float(labour_total),
                    "Overhead": float(overhead_total),
                    "Total batch cost": float(total_cost),
                    "Good packets": float(good_quantity),
                    "Cost / good packet": float(cost_per_good.quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )),
                })
                costing_details[costing_run.id] = (
                    material_breakdown,
                    material_total,
                    labour_total,
                    overhead_total,
                    total_cost,
                    cost_per_good,
                )

            st.dataframe(
                pd.DataFrame(costing_rows),
                use_container_width=True,
                hide_index=True,
            )

            selected_cost_run_id = st.selectbox(
                "View batch cost breakdown",
                options=[run.id for run in costing_runs],
                format_func=lambda run_id: next(
                    run.batch_number for run in costing_runs if run.id == run_id
                ),
                key="production_cost_breakdown_select",
            )
            breakdown, material_total, labour_total, overhead_total, total_cost, cost_per_good = (
                costing_details[selected_cost_run_id]
            )
            st.markdown("**Material cost breakdown**")
            if breakdown:
                st.dataframe(
                    pd.DataFrame(breakdown),
                    use_container_width=True,
                    hide_index=True,
                )
            c1, c2, c3 = st.columns(3)
            c1.metric("Raw-material cost", format_currency(material_total))
            c2.metric("Total production cost", format_currency(total_cost))
            c3.metric("Cost per good packet", format_currency(
                cost_per_good.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ))
            st.info(
                "Cost per good packet = (raw-material cost + direct labour + "
                "overhead) ÷ actual good packets. Damaged packaging is included "
                "in consumed material cost, while only good packets are used "
                "as the output denominator."
            )
        else:
            st.info("Batch costing will appear after the first production batch is posted.")

    except Exception as exc:
        db.rollback()
        st.error(f"Unable to load production workspace: {exc}")

    finally:
        db.close()


# ============================================================
# 14. DISPATCH MANAGEMENT
# ============================================================

def dispatch_page(user):

    section_heading(
        "🚚 Dispatch Management",
        "Dispatch invoiced orders while protecting finished-goods stock."
    )

    db = SessionLocal()

    try:
        invoices = db.scalars(
            select(Invoice).where(Invoice.status == "POSTED").order_by(Invoice.id.desc())
        ).all()

        dispatchable = []
        for invoice in invoices:
            order = db.get(SalesOrder, invoice.order_id)
            if order and order.status == "APPROVED":
                dispatchable.append((invoice, order))

        already_dispatched = [
            order for order in db.scalars(select(SalesOrder)).all()
            if order.status == "DISPATCHED"
        ]

        c1, c2 = st.columns(2)
        c1.metric("Ready for Dispatch", len(dispatchable))
        c2.metric("Already Dispatched", len(already_dispatched))
        st.divider()

        if not dispatchable:
            show_empty_state("There are no posted invoices awaiting dispatch.")
        else:
            for invoice, order in dispatchable:
                customer = db.get(Customer, order.customer_id)
                items = db.scalars(
                    select(SalesOrderItem).where(SalesOrderItem.order_id == order.id)
                ).all()

                with st.container(border=True):
                    st.markdown(f"#### {invoice.invoice_number}")
                    st.write(f"**Order:** {order.order_number}")
                    st.write(f"**Customer:** {customer.name if customer else 'Unknown'}")
                    st.write(f"**Invoice total:** {format_currency(invoice.total_amount)}")

                    requested_rows = []
                    order_quantities = []
                    all_available = True
                    balances = get_stock_balances(db)

                    for item in items:
                        product = db.get(Product, item.product_id)
                        if not product:
                            all_available = False
                            continue
                        requested = Decimal(str(item.quantity))
                        available = balances.get(("PRODUCT", product.id), Decimal("0"))
                        sufficient = available >= requested
                        all_available = all_available and sufficient
                        requested_rows.append({
                            "Product": product.name,
                            "Requested": float(requested),
                            "Available": float(available),
                            "After dispatch": float(available - requested) if sufficient else "Insufficient stock",
                        })
                        order_quantities.append((product, requested, available))

                    if requested_rows:
                        st.dataframe(pd.DataFrame(requested_rows), use_container_width=True, hide_index=True)

                    if not all_available:
                        st.warning("Insufficient finished-goods stock. Dispatch is blocked; produce or receive stock before retrying.")

                    if st.button(
                        "Confirm Dispatch",
                        key=f"confirm_dispatch_{invoice.id}",
                        type="primary",
                        disabled=not all_available or not order_quantities,
                        use_container_width=True,
                    ):
                        # Revalidate inside the write transaction to prevent stale-stock dispatch.
                        db.rollback()
                        current_order = db.get(SalesOrder, order.id)
                        current_invoice = db.get(Invoice, invoice.id)

                        duplicate_dispatch = db.scalar(
                            select(StockMovement).where(
                                StockMovement.movement_type == "DISPATCH",
                                StockMovement.reference_type == "INVOICE",
                                StockMovement.reference_id == invoice.id,
                            )
                        )

                        if not current_order or current_order.status != "APPROVED":
                            st.error("This order is no longer eligible for dispatch.")
                            st.rerun()

                        if not current_invoice or current_invoice.status != "POSTED" or duplicate_dispatch:
                            st.error("This invoice has already been dispatched or is no longer valid.")
                            st.rerun()

                        current_balances = get_stock_balances(db)
                        current_items = db.scalars(
                            select(SalesOrderItem).where(SalesOrderItem.order_id == current_order.id)
                        ).all()
                        movement_rows = []
                        shortage = None

                        for current_item in current_items:
                            current_product = db.get(Product, current_item.product_id)
                            if not current_product:
                                shortage = "A product on this order no longer exists."
                                break
                            requested_qty = Decimal(str(current_item.quantity))
                            available_qty = current_balances.get(("PRODUCT", current_product.id), Decimal("0"))
                            if available_qty < requested_qty:
                                shortage = (
                                    f"Insufficient stock for {current_product.name}: "
                                    f"requested {requested_qty}, available {available_qty}."
                                )
                                break
                            movement_rows.append((current_product, requested_qty))

                        if shortage:
                            db.rollback()
                            st.error(shortage + " No stock was deducted.")
                            st.rerun()

                        for current_product, requested_qty in movement_rows:
                            db.add(StockMovement(
                                item_type="PRODUCT",
                                item_id=current_product.id,
                                movement_type="DISPATCH",
                                quantity=requested_qty,
                                unit=current_product.unit,
                                reference_type="INVOICE",
                                reference_id=current_invoice.id,
                                notes=f"Dispatch against {current_invoice.invoice_number} / {current_order.order_number}",
                                created_by=user["id"],
                                created_at=datetime.now(),
                            ))

                        current_order.status = "DISPATCHED"
                        db.add(AuditLog(
                            user_id=user["id"],
                            action="ORDER_DISPATCHED",
                            entity_type="SalesOrder",
                            entity_id=current_order.id,
                            details=(
                                f"Order {current_order.order_number} dispatched against "
                                f"invoice {current_invoice.invoice_number}; "
                                + "; ".join(
                                    f"{prod.name}: {qty} {prod.unit}"
                                    for prod, qty in movement_rows
                                )
                            ),
                            timestamp=datetime.now(),
                        ))
                        db.commit()
                        st.success(f"{current_order.order_number} dispatched successfully. Finished stock has been deducted.")
                        st.rerun()

        if already_dispatched:
            st.divider()
            st.markdown("### Dispatch History")
            history_rows = []
            for order in already_dispatched:
                customer = db.get(Customer, order.customer_id)
                invoice = db.scalar(select(Invoice).where(Invoice.order_id == order.id))
                history_rows.append({
                    "Order Number": order.order_number,
                    "Invoice": invoice.invoice_number if invoice else "—",
                    "Customer": customer.name if customer else "Unknown",
                    "Status": order.status,
                })
            st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)

    except Exception as exc:
        db.rollback()
        st.error(f"Dispatch operation failed: {exc}")

    finally:
        db.close()


# ============================================================
# 14. LOGIN SCREEN
# ============================================================

def show_login():

    st.markdown(
        """
        <div class="main-title">🏭 NammaFactory</div>
        <div class="subtitle">
        Smart Manufacturing & Business Intelligence Platform
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    left, center, right = st.columns([1, 1.2, 1])

    with center:

        st.markdown("### Welcome back")
        st.write("Sign in to access your department workspace.")

        with st.form("login_form"):

            username = st.text_input(
                "Username",
                placeholder="Enter username",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password",
            )

            submitted = st.form_submit_button(
                "Sign in",
                use_container_width=True,
                type="primary",
            )

            if submitted:

                if not username or not password:

                    st.error(
                        "Please enter both username and password."
                    )

                else:

                    user = authenticate_user(
                        username,
                        password,
                    )

                    if user:

                        st.session_state.authenticated = True
                        st.session_state.user_id = user["id"]
                        st.session_state.username = user["username"]
                        st.session_state.full_name = user["full_name"]
                        st.session_state.role = user["role"]

                        st.rerun()

                    else:

                        st.error(
                            "Invalid username or password."
                        )


# ============================================================
# 15. ROLE-BASED APPLICATION ROUTER
# ============================================================

def show_application():

    user = {
        "id": st.session_state.user_id,
        "username": st.session_state.username,
        "full_name": st.session_state.full_name,
        "role": st.session_state.role,
    }

    role = user["role"]

    if role not in ROLE_PAGES:

        st.error("Your account does not have a valid role.")
        logout()
        return

    apply_role_theme(role)

    pages = ROLE_PAGES[role]

    dashboard_pages = {
        "admin": "Dashboard",
        "salesman": "My Dashboard",
        "production": "Production Dashboard",
        "accountant": "Accounts Dashboard",
        "owner": "Owner Dashboard",
    }

    with st.sidebar:

        st.markdown(
            f"## {THEMES[role]['emoji']} NammaFactory"
        )

        st.caption(THEMES[role]["name"])

        st.divider()

        st.caption("SIGNED IN AS")

        st.markdown(f"**{user['full_name']}**")

        st.caption(role.upper())

        st.divider()

        selected_page = st.radio(
            "Workspace Navigation",
            pages,
            key=f"navigation_{role}",
        )

        st.divider()

        if st.button(
            "Log out",
            use_container_width=True,
        ):

            st.session_state.pop("order_preview", None)
            logout()

    db = SessionLocal()

    try:

        # Route each selected navigation item to its own screen.

        if selected_page == dashboard_pages[role]:

            if role == "admin":
                admin_dashboard(db)

            elif role == "salesman":
                salesman_dashboard(db, user)

            elif role == "production":
                production_dashboard(db)

            elif role == "accountant":
                accountant_dashboard(db)

            elif role == "owner":
                owner_dashboard(db)

        else:

            show_workspace_page(
                role,
                selected_page,
                user,
            )

        st.divider()

        st.caption(
            f"NammaFactory | {THEMES[role]['name']}"
        )

    finally:

        db.close()


# ============================================================
# 16. APPLICATION ENTRY POINT
# ============================================================

if st.session_state.get("authenticated", False):

    show_application()

else:

    show_login()
