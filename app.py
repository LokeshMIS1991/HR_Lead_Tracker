import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# Page Config
st.set_page_config(
    page_title="HR & Insights Sales Portal",
    page_icon="📞",
    layout="wide"
)

# Connect to Google Sheets
@st.cache_resource
def get_gspread_client():
    return gspread.service_account(filename="service_account.json")

# Connection handling
try:
    gc = get_gspread_client()
    # Google Sheet URL / Name connection
    sheet = gc.open_by_key("19qxH3Ga3xJrpsbQrqunJ6EpT5PVQXAAFodlZGZcLTzI").sheet1
    gsheets_connected = True
except Exception as e:
    gsheets_connected = False

# Sidebar Navigation
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Select Page:", ["📤 Bulk Lead Upload (Manager)", "📞 Preeti's Dialer"])

# ==========================================
# PAGE 1: BULK LEAD UPLOAD (MANAGER PORTAL)
# ==========================================
if page == "📤 Bulk Lead Upload (Manager)":
    st.title("📤 Bulk Lead Upload Portal")
    st.markdown("Aap apni **Excel Sheet (Lead_Data.xlsx)** ko directly upload kar sakte hain.")

    uploaded_file = st.file_uploader("Upload Excel / CSV File", type=["xlsx", "xls", "csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        
        st.write("### Uploaded Data Preview:")
        st.dataframe(df.head())

        if st.button("Google Sheet Mein Upload Karein"):
            if not gsheets_connected:
                st.error("Google Sheet connected nahi hai. Check service_account.json key!")
            else:
                with st.spinner("Data upload ho raha hai..."):
                    existing_records = sheet.get_all_records()
                    existing_client_ids = [str(r.get("Client ID")) for r in existing_records]
                    
                    rows_to_add = []
                    for idx, row in df.iterrows():
                        client_id = str(row.get("Client ID", f"CL-{len(existing_records) + idx + 1:04d}"))
                        
                        # Avoid duplicates
                        if client_id not in existing_client_ids:
                            rows_to_add.append([
                                client_id,
                                str(row.get("Date Stamp", "")),
                                str(row.get("Client Name", "")),
                                str(row.get("Company Name", "")),
                                str(row.get("Number", "")),
                                str(row.get("Email", "")),
                                str(row.get("Product", "")),
                                str(row.get("Qty", "")),
                                str(row.get("Address", "")),
                                str(row.get("City", "")),
                                str(row.get("State", "")),
                                str(row.get("Source", "")),
                                str(row.get("Assigned Salesperson", "")),
                                str(row.get("Type of client", "")),
                                str(row.get("Final Status", "")),
                                str(row.get("Remarks", "")),
                                "Pending",  # Call Status
                                "",         # Preeti Remarks
                                "",         # New Requirement
                                "",         # Next Followup Date
                                ""          # Calling Date
                            ])
                    
                    if rows_to_add:
                        sheet.append_rows(rows_to_add)
                        st.success(f"Successfully {len(rows_to_add)} new leads Google Sheet mein add ho gayi hain!")
                    else:
                        st.warning("Koi naya record nahi mila ya saare Client IDs pehle se exist karte hain.")

# ==========================================
# PAGE 2: PREETI'S CALLING DIALER PORTAL
# ==========================================
elif page == "📞 Preeti's Dialer":
    st.title("📞 Preeti's Lead Calling Portal")

    if not gsheets_connected:
        st.error("Google Sheet connect nahi hai. Service account key check karein.")
    else:
        records = sheet.get_all_records()
        df = pd.DataFrame(records)

        if df.empty:
            st.info("Abhi Google Sheet mein koi leads nahi hain. Pehle Page 1 se upload karein.")
        else:
            # Metrics Summary in Sidebar
            st.sidebar.markdown("---")
            st.sidebar.subheader("📊 Lead Summary")
            
            total_leads = len(df)
            pending_cnt = len(df[df['Call Status'].isin(['Pending', 'Not Called', ''])])
            approved_cnt = len(df[df['Call Status'] == 'Approved/Interested'])
            callback_cnt = len(df[df['Call Status'] == 'Callback Required'])
            unreachable_cnt = len(df[df['Call Status'] == 'Not Reachable'])
            rejected_cnt = len(df[df['Call Status'] == 'Not Interested / Rejected'])

            st.sidebar.metric("Total Leads", total_leads)
            st.sidebar.metric("⏳ Pending", pending_cnt)
            st.sidebar.metric("✅ Approved", approved_cnt)
            st.sidebar.metric("📞 Callback", callback_cnt)
            st.sidebar.metric("🚫 Not Reachable", unreachable_cnt)
            st.sidebar.metric("❌ Rejected", rejected_cnt)

            # Filter Pending Queue
            pending_df = df[df['Call Status'].isin(['Pending', 'Not Called', 'Callback Required', 'Not Reachable', ''])].reset_index(drop=True)

            if pending_df.empty:
                st.balloons()
                st.success("Bohot badiya! Saari pending calls update ho chuki hain.")
            else:
                if 'lead_idx' not in st.session_state:
                    st.session_state.lead_idx = 0
                
                if st.session_state.lead_idx >= len(pending_df):
                    st.session_state.lead_idx = 0
                    
                current_lead = pending_df.iloc[st.session_state.lead_idx]
                
                col1, col2 = st.columns([1, 1])
                
                # Column 1: Complete Client Details Card
                with col1:
                    st.subheader("📋 Client Details")
                    st.info(f"**Client ID:** {current_lead['Client ID']} | **Type:** {current_lead.get('Type of client', '')}")
                    st.markdown(f"**Client Name:** {current_lead['Client Name']}")
                    st.markdown(f"**Company:** {current_lead.get('Company Name', 'N/A')}")
                    st.markdown(f"**Phone:** `{current_lead['Number']}` | **Email:** {current_lead.get('Email', 'N/A')}")
                    st.markdown(f"**Location:** {current_lead.get('City', '')}, {current_lead.get('State', '')}")
                    st.warning(f"**Old Requirement:** {current_lead.get('Product', '')} (Qty: {current_lead.get('Qty', '')})")
                    st.error(f"**Old Rejection/Remarks:** {current_lead.get('Old Remarks', 'N/A')}")
                    
                    phone_no = str(current_lead['Number']).replace(" ", "").replace("-", "")
                    if phone_no and phone_no != 'nan':
                        st.markdown(f"[📞 Call Client](tel:{phone_no}) | [💬 Open WhatsApp](https://wa.me/91{phone_no})")

                # Column 2: Follow-up Status Form
                with col2:
                    st.subheader("📝 Update Call Status")
                    with st.form("update_form"):
                        new_status = st.selectbox(
                            "Call Outcome Status",
                            ["Approved/Interested", "Callback Required", "Not Reachable", "Not Interested / Rejected"]
                        )
                        new_req = st.text_area("New Requirement (If Approved)", value=str(current_lead.get('New Requirement', '')))
                        remarks = st.text_area("Preeti's Remarks / Discussion Summary", value=str(current_lead.get('Preeti Remarks', '')))
                        next_date = st.date_input("Next Follow-up Date")
                        
                        if st.form_submit_button("Save & Next Lead ➡️"):
                            cell = sheet.find(str(current_lead['Client ID']))
                            row_num = cell.row
                            
                            # Google Sheet updates: Q(17)=Status, R(18)=Remarks, S(19)=New Req, T(20)=Next Date, U(21)=Calling Date
                            sheet.update_cell(row_num, 17, new_status)
                            sheet.update_cell(row_num, 18, remarks)
                            sheet.update_cell(row_num, 19, new_req)
                            sheet.update_cell(row_num, 20, str(next_date))
                            sheet.update_cell(row_num, 21, datetime.today().strftime('%Y-%m-%d'))
                            
                            st.success("Lead Update Ho Gayi!")
                            st.session_state.lead_idx += 1
                            st.rerun()

            # Daily Calling Utilization Report Table
            st.markdown("---")
            st.subheader("📈 Preeti's Daily Calling Activity Summary")
            called_df = df[df['Calling Date'] != ""]
            if not called_df.empty:
                daily_summary = called_df.groupby(['Calling Date', 'Call Status']).size().unstack(fill_value=0)
                st.dataframe(daily_summary, use_container_width=True)
