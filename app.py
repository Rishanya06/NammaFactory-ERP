
import streamlit as st
from sqlalchemy import select, func

from database import SessionLocal
from models import User, Product, RawMaterial, Customer, StockMovement
from modules.authentication import authenticate_user, logout


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="NammaFactory | Manufacturing ERP",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b1220;
    }

    [data-testid="stSidebar"] {
        background-color: #111c2e;
    }

    .main-title {
        font-size: 34px;
        font-weight: 750;
        color: #e8f1fa;
    }

    .subtitle {
        color: #9aacc0;
        font-size: 15px;
    }

    .login-card {
        padding: 28px;
        border: 1px solid #26364d;
        border-radius: 16px;
        background-color: #111c2e;
    }

    div[data-testid="stMetric"] {
        background: #142238;
        padding: 18px;
        border: 1px solid #26364d;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# DATABASE HELPERS
# --------------------------------------------------

def get_dashboard_counts():
    db = SessionLocal()

    try:
        return {
            "users": db.scalar(select(func.count(User.id))) or 0,
            "products": db.scalar(select(func.count(Product.id))) or 0,
            "materials": db.scalar(
                select(func.count(RawMaterial.id))
            ) or 0,
            "customers": db.scalar(
                select(func.count(Customer.id))
            ) or 0,
            "movements": db.scalar(
                select(func.count(StockMovement.id))
            ) or 0,
        }

    finally:
        db.close()


# --------------------------------------------------
# LOGIN SCREEN
# --------------------------------------------------

def show_login():

    st.markdown(
        '<div class="main-title">🏭 NammaFactory</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">Smart Manufacturing & Business Intelligence Platform</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    left, center, right = st.columns([1, 1.2, 1])

    with center:

        st.markdown("### Welcome back")
        st.write("Sign in to access your factory workspace.")

        with st.form("login_form"):

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )

            submitted = st.form_submit_button(
                "Sign in",
                use_container_width=True,
                type="primary",
            )

            if submitted:

                if not username or not password:
                    st.error("Please enter both username and password.")

                else:
                    user = authenticate_user(username, password)

                    if user:

                        st.session_state.authenticated = True
                        st.session_state.user_id = user["id"]
                        st.session_state.username = user["username"]
                        st.session_state.full_name = user["full_name"]
                        st.session_state.role = user["role"]

                        st.rerun()

                    else:
                        st.error("Invalid username or password.")

        st.caption(
            "Development demo accounts are listed in the project README."
        )


# --------------------------------------------------
# ROLE-BASED NAVIGATION
# --------------------------------------------------

ROLE_PAGES = {
    "admin": [
        "Dashboard",
        "Sales & Orders",
        "Inventory",
        "Production",
        "Purchases",
        "Reports",
        "Audit Trail",
    ],

    "salesman": [
        "My Dashboard",
        "New Order",
        "My Orders",
    ],

    "production": [
        "Production Dashboard",
        "Production Entry",
        "BOM Management",
        "Inventory",
    ],

    "accountant": [
        "Accounts Dashboard",
        "Invoices",
        "Payments",
        "Financial Reports",
    ],

    "owner": [
        "Owner Dashboard",
        "Business Analytics",
        "Production Intelligence",
        "Reports",
    ],
}


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

def show_dashboard():

    role = st.session_state.role
    pages = ROLE_PAGES.get(role, ["Dashboard"])

    with st.sidebar:

        st.markdown("## 🏭 NammaFactory")
        st.caption("Manufacturing Intelligence")

        st.divider()

        st.write("SIGNED IN AS")
        st.markdown(f"**{st.session_state.full_name}**")
        st.caption(role.upper())

        selected_page = st.radio(
            "Navigation",
            pages,
        )

        st.divider()

        if st.button("Log out", use_container_width=True):
            logout()

    st.markdown(
        '<div class="main-title">Factory Overview</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"Welcome, **{st.session_state.full_name}**!"
    )

    st.caption(
        f"Your workspace: {role.title()} | "
        "NammaFactory Manufacturing ERP"
    )

    st.divider()

    counts = get_dashboard_counts()

    st.subheader("Factory at a glance")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Products", counts["products"])
    col2.metric("Raw Materials", counts["materials"])
    col3.metric("Customers", counts["customers"])
    col4.metric("Stock Movements", counts["movements"])

    st.divider()

    st.subheader("Your workspace")

    st.info(
        f"You are viewing the **{selected_page}** section. "
        "We will connect its business operations in the next development milestones."
    )

    left, right = st.columns(2)

    with left:
        st.markdown("### Factory master data")
        st.write("Finished products and raw materials")
        st.write("Customer and supplier records")
        st.write("Bill of Materials configuration")

    with right:
        st.markdown("### Production workflow")
        st.write("Raw material issue")
        st.write("Production output and wastage")
        st.write("Finished goods inventory")


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------

if st.session_state.get("authenticated", False):
    show_dashboard()
else:
    show_login()
