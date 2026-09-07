import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(
    page_title="HR & Insights Sales Portal",
    page_icon="📞",
    layout="wide"
)

# Sidebar Navigation
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Select Page:", ["📤 Upload Leads (Manager)", "📞 Preeti's Dialer"])

# Sample Initial Data (Temporary for testing before Google Sheets connection)
if 'leads_data' not in st.session_state:
    st.session_state.leads_data = pd.DataFrame([
        {
            "Client_ID": "CL-0001",
            "Client_Name": "Rahul Sharma",
            "Phone_Number": "9876543210",
            "Old_Requirement": "Software Development - 5 licenses",
            "Rejection_Reason": "Budget Constraints 8 months ago",
            "Status": "Pending",
            "Preeti_Remarks": "",
            "New_Requirement": "",
            "Next_Followup_Date": ""
        },
        {
            "Client_ID": "CL-0002",
            "Client_Name": "Priya Verma",
            "Phone_Number": "9123456789",
            "Old_Requirement": "HR Consulting Services",
            "Rejection_Reason": "Timing was not right",
            "Status": "Pending",
            "Preeti_Remarks": "",
            "New_Requirement": "",
            "Next_Followup_Date": ""
        }
    ])

# ==========================================
# PAGE 1: BULK LEAD UPLOAD (MANAGER PORTAL)
# ==========================================
if page == "📤 Upload Leads (Manager)":
    st.title("📤 Bulk Lead Upload Portal")
    st.markdown("Upload 8-month-old rejected leads via CSV or Excel.")

    uploaded_file = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        
        st.write("### Data Preview:")
        st.dataframe(df.head())

        if st.button("Upload & Add to App"):
            req_cols = ["Client_Name", "Phone_Number", "Old_Requirement", "Rejection_Reason"]
            missing = [c for c in req_cols if c not in df.columns]
            
            if missing:
                st.error(f"Missing required columns in file: {missing}")
            else:
                start_id = len(st.session_state.leads_data) + 1
                new_rows = []
                for idx, row in df.iterrows():
                    new_rows.append({
                        "Client_ID": f"CL-{start_id + idx:04d}",
                        "Client_Name": str(row.get("Client_Name", "")),
                        "Phone_Number": str(row.get("Phone_Number", "")),
                        "Old_Requirement": str(row.get("Old_Requirement", "")),
                        "Rejection_Reason": str(row.get("Rejection_Reason", "")),
                        "Status": "Pending",
                        "Preeti_Remarks": "",
                        "New_Requirement": "",
                        "Next_Followup_Date": ""
                    })
                
                st.session_state.leads_data = pd.concat([st.session_state.leads_data, pd.DataFrame(new_rows)], ignore_index=True)
                st.success(f"Successfully uploaded {len(new_rows)} leads!")

    st.markdown("---")
    st.write("### Current Active Leads Database Preview:")
    st.dataframe(st.session_state.leads_data)

# ==========================================
# PAGE 2: PREETI'S CALLING DIALER PORTAL
# ==========================================
elif page == "📞 Preeti's Dialer":
    st.title("📞 Preeti's Lead Calling Portal")

    df = st.session_state.leads_data

    if df.empty:
        st.info("No leads available right now. Please upload leads first!")
    else:
        pending_df = df[df['Status'].isin(['Pending', 'Callback Required', 'Not Reachable'])].reset_index(drop=True)
        
        st.sidebar.markdown("---")
        st.sidebar.metric("Pending Leads", len(pending_df))
        st.sidebar.metric("Approved / Converted", len(df[df['Status'] == 'Approved/Interested']))
        
        if pending_df.empty:
            st.balloons()
            st.success("Great job! All pending leads have been updated.")
        else:
            if 'lead_idx' not in st.session_state:
                st.session_state.lead_idx = 0
            
            if st.session_state.lead_idx >= len(pending_df):
                st.session_state.lead_idx = 0
                
            current_lead = pending_df.iloc[st.session_state.lead_idx]
            
            col1, col2 = st.columns([1, 1])
            
            # Client Info Display Card
            with col1:
                st.subheader("📋 Client Details")
                st.info(f"**Client ID:** {current_lead['Client_ID']}")
                st.markdown(f"**Client Name:** {current_lead['Client_Name']}")
                st.markdown(f"**Phone Number:** `{current_lead['Phone_Number']}`")
                st.warning(f"**Old Requirement:** {current_lead['Old_Requirement']}")
                st.error(f"**Rejection Reason (8 Months Ago):** {current_lead['Rejection_Reason']}")
                
                phone_no = str(current_lead['Phone_Number']).replace(" ", "")
                st.markdown(f"[📞 Call Client](tel:{phone_no}) | [💬 Open WhatsApp](https://wa.me/91{phone_no})")

            # Call Action Form
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
                        # Update temporary session data
                        idx = st.session_state.leads_data[st.session_state.leads_data['Client_ID'] == current_lead['Client_ID']].index[0]
                        st.session_state.leads_data.at[idx, 'Status'] = new_status
                        st.session_state.leads_data.at[idx, 'Preeti_Remarks'] = remarks
                        st.session_state.leads_data.at[idx, 'New_Requirement'] = new_req
                        st.session_state.leads_data.at[idx, 'Next_Followup_Date'] = str(next_date)
                        
                        st.success("Lead Status Updated!")
                        st.session_state.lead_idx += 1
                        st.rerun()