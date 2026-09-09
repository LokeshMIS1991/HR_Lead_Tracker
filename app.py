import streamlit as st
import pandas as pd
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

try:
    gc = get_gspread_client()
    sheet = gc.open("HR_Lead_Tracker").sheet1
except Exception as e:
    st.error("Google Sheets connect nahi ho paya! Key file ya Sheet name verify karein.")

# Sidebar Navigation (Page Switching)
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Select Page:", ["📤 Upload Leads (Manager)", "📞 Preeti's Dialer"])

# ==========================================
# PAGE 1: BULK LEAD UPLOAD (MANAGER PORTAL)
# ==========================================
if page == "📤 Upload Leads (Manager)":
    st.title("📤 Bulk Lead Upload Portal")
    st.markdown("Yahan aap last 8-months ki rejected leads upload kar sakte hain.")

    uploaded_file = st.file_uploader("Select CSV ya Excel File Upload karein", type=["csv", "xlsx"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        
        st.write("### Data Preview:")
        st.dataframe(df.head())

        if st.button("Upload to Google Sheets"):
            with st.spinner("Data upload ho raha hai..."):
                req_cols = ["Client_Name", "Phone_Number", "Old_Requirement", "Rejection_Reason"]
                missing = [c for c in req_cols if c not in df.columns]
                
                if missing:
                    st.error(f"Aapki file mein ye mandatory columns nahi hain: {missing}")
                else:
                    existing_data = sheet.get_all_records()
                    start_id = len(existing_data) + 1
                    
                    rows_to_add = []
                    for idx, row in df.iterrows():
                        client_id = f"CL-{start_id + idx:04d}"
                        rows_to_add.append([
                            client_id,
                            str(row.get("Client_Name", "")),
                            str(row.get("Phone_Number", "")),
                            str(row.get("Old_Requirement", "")),
                            str(row.get("Rejection_Reason", "")),
                            "Pending",  # Default Status
                            "",         # Preeti Remarks
                            "",         # New Requirement
                            ""          # Next Followup Date
                        ])
                    
                    sheet.append_rows(rows_to_add)
                    st.success(f"Successfully {len(rows_to_add)} leads upload ho gayi hain!")

# ==========================================
# PAGE 2: PREETI'S CALLING DIALER PORTAL
# ==========================================
elif page == "📞 Preeti's Dialer":
    st.title("📞 Preeti's Lead Calling Portal")

    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        st.info("Abhi Google Sheet mein koi leads nahi hain. Pehle Upload page se leads upload karein.")
    else:
        # Filter Pending, Callback, or Not Reachable leads
        pending_df = df[df['Status'].isin(['Pending', 'Callback Required', 'Not Reachable'])].reset_index(drop=True)
        
        st.sidebar.markdown("---")
        st.sidebar.metric("Pending Leads", len(pending_df))
        st.sidebar.metric("Approved / Converted", len(df[df['Status'] == 'Approved/Interested']))
        
        if pending_df.empty:
            st.balloons()
            st.success("Bohot badiya! Saari pending leads update ho chuki hain.")
        else:
            if 'lead_idx' not in st.session_state:
                st.session_state.lead_idx = 0
            
            if st.session_state.lead_idx >= len(pending_df):
                st.session_state.lead_idx = 0
                
            current_lead = pending_df.iloc[st.session_state.lead_idx]
            
            col1, col2 = st.columns([1, 1])
            
            # Left Box: Lead Details
            with col1:
                st.subheader("📋 Client Details")
                st.info(f"**Client ID:** {current_lead['Client_ID']}")
                st.markdown(f"**Client Name:** {current_lead['Client_Name']}")
                st.markdown(f"**Phone Number:** `{current_lead['Phone_Number']}`")
                st.warning(f"**Old Requirement:** {current_lead['Old_Requirement']}")
                st.error(f"**Rejection Reason (8 Months Ago):** {current_lead['Rejection_Reason']}")
                
                phone_no = str(current_lead['Phone_Number']).replace(" ", "")
                st.markdown(f"[📞 Call Client](tel:{phone_no}) | [💬 Open WhatsApp](https://wa.me/91{phone_no})")

            # Right Box: Update Form
            with col2:
                st.subheader("📝 Update Call Status")
                with st.form("update_form"):
                    new_status = st.selectbox(
                        "Call Status",
                        ["Approved/Interested", "Callback Required", "Not Reachable", "Not Interested / Rejected"]
                    )
                    new_req = st.text_area("New Requirement (If Approved)", value=str(current_lead.get('New_Requirement', '')))
                    remarks = st.text_area("Preeti's Remarks / Discussion", value=str(current_lead.get('Preeti_Remarks', '')))
                    next_date = st.date_input("Next Follow-up Date")
                    
                    if st.form_submit_button("Save & Next Lead ➡️"):
                        cell = sheet.find(str(current_lead['Client_ID']))
                        row_num = cell.row
                        
                        sheet.update_cell(row_num, 6, new_status)
                        sheet.update_cell(row_num, 7, remarks)
                        sheet.update_cell(row_num, 8, new_req)
                        sheet.update_cell(row_num, 9, str(next_date))
                        
                        st.success("Lead Update Ho Gayi!")
                        st.session_state.lead_idx += 1
                        st.rerun()
