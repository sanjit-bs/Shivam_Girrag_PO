import streamlit as st
import requests
from datetime import date

# Sidebar Admin Authentication
st.sidebar.title("🔐 Access Control")
admin_pin = st.sidebar.text_input("Enter Admin PIN to edit:", type="password")

IS_ADMIN = (admin_pin == "2000") # Replace with your secure PIN

if IS_ADMIN:
    st.sidebar.success("🔓 Admin Mode Active")
    tab1, tab2, tab3 = st.tabs(["📊 Live Dashboard", "📝 New Order Entry", "🔍 Verify Orders"])
else:
    st.sidebar.info("👁️ View-Only Mode Active")
    tab1 = st.tabs(["📊 Live Dashboard"])[0]

with tab1:
    st.subheader("📋 Purchase Order Status (Read-Only)")

# ==========================================
# 🔗 PASTE YOUR APPS SCRIPT WEB APP URL HERE
# ==========================================
PURCHASE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby1ET3Xhkvm1j8Hz_CZzQOgEsM8tIqI3RaRP7KLFYCbvx9U9zaw8PxoWQ962Lqenqnf/exec"

CREDITORS_LIST = [
    "Select Creditor...", "BALAJI ENTERPRISE", "DHANUKA UDYOG PRIVATE LIMITED", 
    "EVEREST PAPER MILLS (P) LTD.", "KRISHNA TRADERS", "PAPERS (India)", 
    "PS INDUSTRIES", "Reflection Papers Pvt. Ltd.", "RIPCO TRADERS PVT. LTD.", 
    "RM INDUSTRIAL EQUIPMENTS", "Samir Board World", "SHIV SHAKTI TRADERS", 
    "Shree Durga Trading Co.", "Star Trading Corporation", "STARK RIDGE PAPER PVT LTD", 
    "The Synthetic Glue & Chemical Industries", "VIJAY ENTERPRISE"
]

UNITS_LIST = ["Pcs", "Kg", "Mtr", "Box", "Set", "Roll", "Packet", "Gsm", "Ream"]

st.set_page_config(page_title="Purchase Order Manager", layout="wide")
st.title("📦 Purchase Order & Verification System")

tab1, tab2 = st.tabs(["📝 New Order Entry", "🔍 Verify Pending Deliveries"])

# Initialize session state tracking
if "item_count" not in st.session_state:
    st.session_state.item_count = 1
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# ------------------------------------------------------
# TAB 1: NEW MULTI-PRODUCT ORDER ENTRY
# ------------------------------------------------------
with tab1:
    def add_product_row():
        st.session_state.item_count += 1

    v = st.session_state.form_version  # Version suffix for widget keys

    with st.container(border=True):
        col1, col2, col3 = st.columns([1.5, 1.5, 2])
        with col1:
            order_date = st.date_input("Order Date", value=date.today(), key=f"date_{v}")
        with col2:
            po_number = st.text_input("PO Number *", key=f"po_{v}")
        with col3:
            creditor = st.selectbox("Supplier / Creditor *", CREDITORS_LIST, key=f"creditor_{v}")

    st.markdown("#### Product Details")
    order_items = []
    grand_total = 0.0

    with st.container(border=True):
        for i in range(st.session_state.item_count):
            st.markdown(f"**Item {i+1}**")
            c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 1.2, 1.8])
            
            with c1:
                p_desc = st.text_input("Product Description", key=f"prod_{v}_{i}")
            with c2:
                p_rate = st.number_input("Rate (₹)", min_value=0.0, step=1.0, format="%.2f", key=f"rate_{v}_{i}")
            with c3:
                p_qty = st.number_input("Quantity", min_value=0.0, step=1.0, key=f"qty_{v}_{i}")
            with c4:
                p_unit = st.selectbox("Unit", UNITS_LIST, key=f"unit_{v}_{i}")
            
            p_amt = p_rate * p_qty
            grand_total += p_amt
            
            with c5:
                st.metric(label="Amount", value=f"₹ {p_amt:,.2f}")
                
            if p_desc.strip():
                order_items.append({
                    "Product": p_desc.strip(),
                    "Rate": p_rate,
                    "Quantity": p_qty,
                    "Unit": p_unit,
                    "Amount": p_amt
                })
                
        st.button("➕ Add Another Product", on_click=add_product_row)

    st.metric("Grand Total (₹)", f"₹ {grand_total:,.2f}")

    if st.button("Save New Order", type="primary"):
        if not po_number.strip():
            st.warning("⚠️ Please enter a PO Number.")
        elif creditor == "Select Creditor...":
            st.warning("⚠️ Please select a Creditor.")
        elif not order_items:
            st.warning("⚠️ Please enter at least one product with a description.")
        else:
            payload = {
                "action": "insert",
                "Date": order_date.strftime("%Y-%m-%d"),
                "PONumber": po_number.strip(),
                "Creditor": creditor,
                "Status": "⏳ Pending Delivery",
                "CancellationReason": "",
                "Items": order_items
            }
            try:
                with st.spinner("Saving to Google Sheets..."):
                    res = requests.post(PURCHASE_APPS_SCRIPT_URL, json=payload, timeout=15)
                    if res.status_code == 200:
                        st.toast(f"✅ Saved {len(order_items)} item(s) for PO #{po_number} ({creditor})!")
                        
                        st.session_state.form_version += 1
                        st.session_state.item_count = 1
                        st.rerun()
                    else:
                        st.error(f"⚠️ Server returned status code {res.status_code}")
            except Exception as e:
                st.error(f"❌ Connection error: {e}")

# ------------------------------------------------------
# TAB 2: VERIFICATION DASHBOARD (PENDING ORDERS)
# ------------------------------------------------------
with tab2:
    st.subheader("📋 Pending Deliveries & Verification")
    
    if st.button("🔄 Refresh Pending List"):
        st.rerun()

    pending_list = []
    try:
        payload = {"action": "read_pending"}
        response = requests.post(PURCHASE_APPS_SCRIPT_URL, json=payload, timeout=15)
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                data = response.json()
                if isinstance(data, list):
                    pending_list = data
                elif isinstance(data, dict) and "error" in data:
                    st.error(f"Apps Script Error: {data['error']}")
            else:
                st.error("⚠️ Access Denied: Apps Script returned HTML instead of JSON.")
        else:
            st.error(f"Failed with status code: {response.status_code}")
    except Exception as e:
        st.error(f"Failed to fetch pending list: {e}")

    if not pending_list:
        st.info("🎉 No pending orders found in 'purchase_order_entry'!")
    else:
        st.markdown(f"Found **{len(pending_list)}** item(s) awaiting delivery verification.")
        
        for idx, item in enumerate(pending_list):
            with st.container(border=True):
                po_disp = item.get('po_number') or 'N/A'
                st.markdown(f"##### 📅 Date: `{item.get('date')}` | PO No: **{po_disp}** | Creditor: **{item.get('creditor')}**")
                
                c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 1.2, 1.8])
                c1.write(f"**Product:** {item.get('product')}")
                c2.write(f"**Rate:** ₹{item.get('rate')}")
                c3.write(f"**Qty:** {item.get('quantity')}")
                c4.write(f"**Unit:** {item.get('unit', 'Pcs')}")
                c5.write(f"**Total:** ₹{item.get('amount')}")

                st.markdown("---")
                
                act_col1, act_col2 = st.columns([2, 4])
                
                with act_col1:
                    action_choice = st.radio(
                        "Verification Action:",
                        ["Keep Pending", "✅ Verify Order", "❌ Cancel Order"],
                        key=f"act_{idx}"
                    )

                with act_col2:
                    reason_text = ""
                    if action_choice == "❌ Cancel Order":
                        reason_text = st.text_input(
                            "Cancellation Reason *", 
                            placeholder="Enter reason (e.g., Damaged goods, Rate mismatch)", 
                            key=f"reason_{idx}"
                        )

                    if action_choice != "Keep Pending":
                        btn_label = "Confirm & Cancel" if action_choice == "❌ Cancel Order" else "Confirm & Verify"
                        
                        if st.button(btn_label, key=f"btn_{idx}", type="primary"):
                            if action_choice == "❌ Cancel Order" and not reason_text.strip():
                                st.warning("⚠️ Please provide a cancellation reason before submitting.")
                            else:
                                new_status = "✅ Verified" if action_choice == "✅ Verify Order" else "❌ Cancelled"
                                
                                update_payload = {
                                    "action": "update_status",
                                    "rowIndex": item.get("rowIndex"),
                                    "colCount": item.get("colCount", 10),
                                    "status": new_status,
                                    "cancellationReason": reason_text.strip()
                                }

                                try:
                                    with st.spinner("Updating status..."):
                                        res = requests.post(PURCHASE_APPS_SCRIPT_URL, json=update_payload, timeout=15)
                                        if res.status_code == 200:
                                            st.toast(f"Status updated to {new_status}!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to update status in Google Sheet.")
                                except Exception as e:
                                    st.error(f"Error updating record: {e}")
