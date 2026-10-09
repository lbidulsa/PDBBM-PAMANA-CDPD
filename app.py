import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from PIL import Image, ExifTags
import os
import random
import string
import datetime

# Attempt browser GPS if available
try:
    from streamlit_js_eval import get_geolocation
    HAS_GEO_EVAL = True
except ImportError:
    HAS_GEO_EVAL = False

# ---------------------------------------------------------
# PAGE CONFIGURATION & CUSTOM STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="PAMANA Peace & Dev Management System",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #F4F6F9;
    }
    .main-title { 
        font-size: 26px; 
        font-weight: 800; 
        color: #1F4E78; 
        margin-bottom: 5px; 
    }
    .sub-title {
        font-size: 14px;
        color: #5A6A85;
        margin-bottom: 20px;
    }
    .stMetric { 
        background-color: #FFFFFF; 
        padding: 16px; 
        border-radius: 12px; 
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .role-badge { 
        background: linear-gradient(135deg, #1F4E78 0%, #2B6CB0 100%); 
        color: white; 
        padding: 5px 12px; 
        border-radius: 20px; 
        font-size: 12px; 
        font-weight: 600;
        display: inline-block;
    }
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F2A4A !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #E2E8F0 !important;
    }
    /* High Visibility Logout Button */
    .stSidebar div.stButton > button {
        background-color: #E2E8F0 !important;
        color: #0F2A4A !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
    }
    .stSidebar div.stButton > button:hover {
        background-color: #FFFFFF !important;
        color: #C53030 !important;
        border-color: #E53E3E !important;
    }
    .mov-box {
        background-color: #FFFFFF;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #CBD5E1;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATA PRIVACY ACT (RA 10173) AUTOMATIC POP-UP MODAL
# ---------------------------------------------------------
if "privacy_accepted" not in st.session_state:
    st.session_state["privacy_accepted"] = False

if hasattr(st, "dialog"):
    @st.dialog("🔒 DATA PRIVACY ACT COMPLIANCE REMINDER (RA 10173)")
    def privacy_modal():
        st.markdown("""
        **DSWD FIELD OFFICE X • PAMANA PEACE & DEVELOPMENT PROGRAM**
        
        Pursuant to **Republic Act No. 10173 (Data Privacy Act of 2012)**:
        
        1. **Authorized Access Only:** This system contains official program records, CEAC activity logs, and financial disbursements.
        2. **Confidentiality Notice:** Any unauthorized extraction, downloading, or distribution of internal records is strictly prohibited.
        3. **Audit Trail:** All encoding sessions, file uploads, and data entries are timestamped and logged under registered user credentials.
        """)
        st.divider()
        if st.button("✅ I Agree & Proceed to Portal", use_container_width=True):
            st.session_state["privacy_accepted"] = True
            st.rerun()

    if not st.session_state["privacy_accepted"]:
        privacy_modal()

def get_logo_path():
    if os.path.exists("logo.png"):
        return "logo.png"
    elif os.path.exists("Peace and Dev LOGO.jpg"):
        return "Peace and Dev LOGO.jpg"
    return None

logo_file = get_logo_path()

os.makedirs("uploaded_movs", exist_ok=True)
os.makedirs("uploaded_photos", exist_ok=True)

# EXIF GPS EXTRACTOR FUNCTION
def extract_gps_from_image(image_file):
    try:
        img = Image.open(image_file)
        exif = img._getexif()
        if not exif:
            return None, None
            
        geotagging = {}
        for (idx, tag) in ExifTags.TAGS.items():
            if tag == 'GPSInfo':
                if idx not in exif:
                    return None, None
                for (key, val) in ExifTags.GPSTAGS.items():
                    if key in exif[idx]:
                        geotagging[val] = exif[idx][key]
        
        if not geotagging:
            return None, None
            
        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        lat = convert_to_degrees(geotagging['GPSLatitude'])
        if geotagging['GPSLatitudeRef'] != 'N':
            lat = -lat

        lon = convert_to_degrees(geotagging['GPSLongitude'])
        if geotagging['GPSLongitudeRef'] != 'E':
            lon = -lon

        return str(round(lat, 6)), str(round(lon, 6))
    except Exception:
        return None, None

# ---------------------------------------------------------
# 1. LOCAL SQLITE DATABASE INITIALIZATION
# ---------------------------------------------------------
DB_FILE = "pamana_database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # CEAC Municipal Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CEAC_Municipal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_name TEXT,
            region TEXT DEFAULT 'REGION X',
            province TEXT,
            municipality TEXT,
            cycle_batch TEXT,
            activity_date TEXT,
            date_encoded TEXT,
            encoded_by TEXT,
            mov_status TEXT,
            encoded_status TEXT,
            mov_attendance TEXT,
            mov_minutes TEXT,
            mov_lgu_minutes TEXT,
            mov_grs_files TEXT,
            remarks TEXT
        )
    """)
    
    # CEAC Barangay Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CEAC_Barangay (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_name TEXT,
            region TEXT DEFAULT 'REGION X',
            province TEXT,
            municipality TEXT,
            barangay TEXT,
            cycle_batch TEXT,
            activity_date TEXT,
            date_encoded TEXT,
            encoded_by TEXT,
            mov_status TEXT,
            encoded_status TEXT,
            mov_attendance TEXT,
            mov_brgy_minutes TEXT,
            mov_lgu_minutes TEXT,
            mov_cv_files TEXT,
            remarks TEXT
        )
    """)
    
    # Geotagged Photos Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Geotagged_Photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sp_id TEXT,
            sp_name TEXT,
            stage TEXT,
            latitude TEXT,
            longitude TEXT,
            photo_file TEXT,
            date_uploaded TEXT,
            encoder TEXT
        )
    """)
    
    # Disbursement Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Disbursement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sp_id TEXT,
            sp_name TEXT,
            dv_number TEXT,
            check_number TEXT,
            payee TEXT,
            amount REAL,
            tax_amount REAL,
            net_amount REAL,
            disbursement_date TEXT,
            status TEXT,
            encoded_status TEXT,
            mov_file TEXT,
            attachment TEXT
        )
    """)
    
    # Sub-Project Closeout Tracker Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Sub_Project_Closeout_Tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sp_id TEXT,
            sp_name TEXT,
            municipality TEXT,
            barangay TEXT,
            cycle_batch TEXT,
            functionality_audit_status TEXT,
            functionality_audit_date TEXT,
            spcr_status TEXT,
            spcr_date_submitted TEXT,
            closing_accounts_status TEXT,
            date_account_closed TEXT,
            booking_assets_status TEXT,
            date_booking_assets TEXT,
            overall_closeout_status TEXT,
            encoded_status TEXT,
            mov_file TEXT,
            remarks TEXT,
            target_hhs INTEGER DEFAULT 0,
            actual_hhs INTEGER DEFAULT 0,
            male_beneficiaries INTEGER DEFAULT 0,
            female_beneficiaries INTEGER DEFAULT 0,
            total_beneficiaries INTEGER DEFAULT 0,
            hh_variance INTEGER DEFAULT 0
        )
    """)
    
    # Summary Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            municipality TEXT,
            total_sps INTEGER,
            total_grant REAL,
            total_disbursed REAL,
            total_liquidated REAL,
            unliquidated_balance REAL
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

def load_db_table(table_name):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# ---------------------------------------------------------
# 2. USER AUTHENTICATION & LOGIN PORTAL WITH RESET PASSWORD
# ---------------------------------------------------------
if "users" not in st.session_state:
    st.session_state["users"] = {
        "superuser": {
            "password": "superuser123",
            "role": "Superuser",
            "name": "System Administrator",
            "email": "superuser@pamana.gov.ph"
        },
        "admin": {
            "password": "admin123",
            "role": "Admin",
            "name": "Program Admin",
            "email": "admin@pamana.gov.ph"
        }
    }

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["user_role"] = None
    st.session_state["user_name"] = None

if "reset_otp" not in st.session_state:
    st.session_state["reset_otp"] = None
    st.session_state["reset_user"] = None

def login():
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_center, c_right = st.columns([1, 2, 1])
    
    with c_center:
        if logo_file:
            l_col1, l_col2, l_col3 = st.columns([1, 3, 1])
            with l_col2:
                st.image(logo_file, use_container_width=True)
        
        st.markdown("<h2 style='text-align: center; color: #1F4E78; margin-top: 10px;'>🕊️ PAMANA CDPD System</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #5A6A85;'>Peace and Development Executive Management Portal</p>", unsafe_allow_html=True)
        
        auth_tab1, auth_tab2 = st.tabs(["🔑 Login Portal", "🔓 Forgot / Reset Password"])
        
        with auth_tab1:
            with st.form("login_form"):
                username = st.text_input("Username").strip().lower()
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("🔑 Login to Dashboard", use_container_width=True)
                
                if submit:
                    users = st.session_state["users"]
                    if username in users and users[username]["password"] == password:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.session_state["user_role"] = users[username]["role"]
                        st.session_state["user_name"] = users[username]["name"]
                        st.success(f"Welcome back, {users[username]['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password!")

        with auth_tab2:
            st.markdown("##### 🔑 Request Password Reset Verification Code")
            reset_email = st.text_input("Enter Registered Email Address:")
            
            if st.button("📩 Send Code via Email", use_container_width=True):
                found_user = None
                for u, details in st.session_state["users"].items():
                    if details["email"].lower() == reset_email.strip().lower():
                        found_user = u
                        break
                
                if found_user:
                    otp = "".join(random.choices(string.digits, k=6))
                    st.session_state["reset_otp"] = otp
                    st.session_state["reset_user"] = found_user
                    st.success(f"Reset Verification Code has been dispatched to {reset_email}!")
                    st.info(f"📬 [SYSTEM NOTIFICATION]: Your 6-digit Verification Reset Code is: **{otp}**")
                else:
                    st.error("No account associated with the provided email address!")

            if st.session_state.get("reset_otp"):
                st.markdown("---")
                st.markdown("##### 🔐 Verify Code & Change Password")
                entered_otp = st.text_input("Enter 6-Digit OTP Code:")
                new_pass = st.text_input("New Password:", type="password")
                confirm_pass = st.text_input("Confirm New Password:", type="password")
                
                if st.button("💾 Save New Password", use_container_width=True):
                    if entered_otp == st.session_state["reset_otp"]:
                        if new_pass and new_pass == confirm_pass:
                            user_to_update = st.session_state["reset_user"]
                            st.session_state["users"][user_to_update]["password"] = new_pass
                            st.success("Password updated successfully! You may now proceed to login.")
                            st.session_state["reset_otp"] = None
                            st.session_state["reset_user"] = None
                        else:
                            st.error("Passwords do not match or field is empty!")
                    else:
                        st.error("Invalid OTP Code provided!")

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ---------------------------------------------------------
# 3. GLOBAL CONFIGURATIONS & ACTIVITIES LISTS
# ---------------------------------------------------------
REGIONS = ["REGION X"]
PROVINCES = ["Misamis Occidental", "Lanao del Norte"]
MUNICIPALITIES = ["Oroquieta City", "Kauswagan"]
CYCLE_BATCHES = ["Cycle 1 - 2026", "Cycle 2 - 2026", "Cycle 3 - 2026"]
ENCODED_OPTIONS = ["YES", "NO"]
CLOSEOUT_STATUSES = ["Pending", "In Progress", "Passed / Completed", "Failed / For Revision", "Closed / Booked", "N/A"]
MOV_STATUSES = ["Completed & Uploaded", "Pending MOV", "For Review", "N/A"]

MUNICIPAL_ACTIVITIES = [
    "Municipal_Profile",
    "Municipal_Orientation",
    "1st_MDC_Meeting",
    "2nd_MDC_Meeting",
    "2nd_BDC_Meeting",
    "PPDW",
    "Technical_Review",
    "Pre_Implementation_Training",
    "OM",
    "MAR_CAR",
    "Sustainability_Planning_Workshop",
    "GRS Instake"
]

BARANGAY_ACTIVITIES = [
    "Brgy_Profile",
    "1st_BDC_Meeting",
    "BPSA",
    "1st_BA",
    "2nd_BDC_Meeting",
    "BAR",
    "OM",
    "2nd_BA",
    "Grievance_Intake",
    "GRS_Installation_Checklist",
    "CV",
    "ERS"
]

TABS = [
    "Executive Dashboard",
    "User Management Portal",
    "CEAC_Municipal",
    "CEAC_Barangay",
    "Geotagged_Photos",
    "Disbursement",
    "Sub_Project_Closeout_Tracker",
    "Summary",
    "Finance"
]

# Helper function to save single uploaded file
def save_uploaded_file(file_obj):
    if file_obj is not None:
        file_path = os.path.join("uploaded_movs", file_obj.name)
        with open(file_path, "wb") as f:
            f.write(file_obj.getbuffer())
        return file_obj.name
    return ""

# Helper function to save multiple uploaded files
def save_multiple_files(files_list):
    saved_names = []
    if files_list:
        for file_obj in files_list:
            file_path = os.path.join("uploaded_movs", file_obj.name)
            with open(file_path, "wb") as f:
                f.write(file_obj.getbuffer())
            saved_names.append(file_obj.name)
    return ", ".join(saved_names)

# ---------------------------------------------------------
# 4. POLISHED SIDEBAR NAVIGATION & LOGO WITH DEVELOPER CREDIT
# ---------------------------------------------------------
if logo_file:
    st.sidebar.image(logo_file, width=220)

st.sidebar.markdown(f"**Logged User:** {st.session_state['user_name']}")
st.sidebar.markdown(f"**System Role:** <span class='role-badge'>{st.session_state['user_role']}</span>", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["user_role"] = None
    st.session_state["user_name"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("📌 System Navigation")
selected_view = st.sidebar.radio("Select Active Module:", TABS)

# DEVELOPER OWNERSHIP CREDIT
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="text-align: center; font-size: 0.8em; color: #CBD5E1;">
        💻 <b>System Developer & Architect</b><br>
        Developed with ❤️ by <br><b style="color:#00E6FF;">LOUIE B. IDULSA - PDBBM ITO I</b><br>
        <i>DSWD FO X - PAMANA CDPD © 2026</i>
    </div>
    """, 
    unsafe_allow_html=True
)

# Top Header
c_hdr1, c_hdr2 = st.columns([3, 1])
with c_hdr1:
    st.markdown('<div class="main-title">🕊️ PAMANA Peace & Development Program System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Community-Driven Peace and Development (CDPD) Executive Management Suite</div>', unsafe_allow_html=True)
with c_hdr2:
    if logo_file:
        st.image(logo_file, width=220)

st.markdown("---")

# ---------------------------------------------------------
# 5. EXECUTIVE DASHBOARD
# ---------------------------------------------------------
if selected_view == "Executive Dashboard":
    df_sp = load_db_table("Sub_Project_Closeout_Tracker")
    df_disb = load_db_table("Disbursement")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Sub-Projects", len(df_sp) if not df_sp.empty else 0)
    with col2:
        tot_disb = df_disb["amount"].sum() if not df_disb.empty and "amount" in df_disb.columns else 0
        st.metric("Total Disbursed", f"₱{tot_disb:,.2f}")
    with col3:
        tot_hh = df_sp["actual_hhs"].sum() if not df_sp.empty and "actual_hhs" in df_sp.columns else 0
        st.metric("Actual HHs Benefited", f"{tot_hh:,.0f}")
    with col4:
        tot_male = df_sp["male_beneficiaries"].sum() if not df_sp.empty and "male_beneficiaries" in df_sp.columns else 0
        st.metric("Male Beneficiaries", f"{tot_male:,.0f}")
    with col5:
        tot_female = df_sp["female_beneficiaries"].sum() if not df_sp.empty and "female_beneficiaries" in df_sp.columns else 0
        st.metric("Female Beneficiaries", f"{tot_female:,.0f}")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Sub-Project Closeout Status")
        if not df_sp.empty and "overall_closeout_status" in df_sp.columns:
            fig_status = px.pie(df_sp, names="overall_closeout_status", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("No closeout status records found.")

    with c2:
        st.subheader("👥 Beneficiary Gender Breakdown")
        if not df_sp.empty and "male_beneficiaries" in df_sp.columns and "female_beneficiaries" in df_sp.columns:
            m_sum = df_sp["male_beneficiaries"].sum()
            f_sum = df_sp["female_beneficiaries"].sum()
            fig_gender = px.bar(
                pd.DataFrame({"Gender": ["Male", "Female"], "Count": [m_sum, f_sum]}),
                x="Gender", y="Count", color="Gender", text_auto=',.0f',
                color_discrete_map={"Male": "#1F4E78", "Female": "#E06666"}
            )
            st.plotly_chart(fig_gender, use_container_width=True)
        else:
            st.info("No beneficiary records found.")

# ---------------------------------------------------------
# 6. USER MANAGEMENT PORTAL
# ---------------------------------------------------------
elif selected_view == "User Management Portal":
    st.subheader("👤 System User Management Portal")
    
    if st.session_state["user_role"] == "Superuser":
        with st.expander("➕ Add New System User", expanded=True):
            with st.form("add_user_form", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    new_uname = st.text_input("Username").strip().lower()
                    new_fullname = st.text_input("Full Name")
                    new_email = st.text_input("Email Address")
                with col_u2:
                    new_pass = st.text_input("Password", type="password")
                    new_role = st.selectbox("Assigned Role", ["Admin", "Superuser"])
                
                submit_user = st.form_submit_button("💾 Create User Account")
                if submit_user:
                    if new_uname and new_pass and new_email:
                        if new_uname in st.session_state["users"]:
                            st.error("Username already registered!")
                        else:
                            st.session_state["users"][new_uname] = {
                                "password": new_pass, "role": new_role,
                                "name": new_fullname, "email": new_email
                            }
                            st.success(f"User '{new_fullname}' ({new_role}) created successfully!")
                            st.rerun()
                    else:
                        st.error("Please fill in Username, Password, and Email.")

    st.markdown("---")
    st.subheader("📋 Registered Users Masterlist")
    users_data = [{"Username": u, "Full Name": i["name"], "Role": i["role"], "Email": i["email"]} for u, i in st.session_state["users"].items()]
    st.dataframe(pd.DataFrame(users_data), use_container_width=True)

# ---------------------------------------------------------
# 7. GEOTAGGED PHOTOS MODULE WITH AUTO-GPS DETECT
# ---------------------------------------------------------
elif selected_view == "Geotagged_Photos":
    st.subheader("📸 Geotagged Photos & Progress File Uploads")
    
    with st.expander("📤 Upload New Geotagged Photo", expanded=True):
        uploaded_file = st.file_uploader("Choose Photo / File (JPG / PNG)", type=["jpg", "jpeg", "png", "pdf"], key="geo_upl_file")
        
        detected_lat, detected_lon = "", ""
        if uploaded_file and uploaded_file.type in ["image/jpeg", "image/png"]:
            exif_lat, exif_lon = extract_gps_from_image(uploaded_file)
            if exif_lat and exif_lon:
                detected_lat, detected_lon = exif_lat, exif_lon
                st.success(f"⚡ **AUTO-DETECTED GPS EXIF METADATA:** Latitude: `{detected_lat}` | Longitude: `{detected_lon}`")
            else:
                st.warning("⚠️ No EXIF GPS metadata found in photo. Attempting live browser location or manual entry...")
                if HAS_GEO_EVAL:
                    location = get_geolocation()
                    if location and 'coords' in location:
                        detected_lat = str(round(location['coords']['latitude'], 6))
                        detected_lon = str(round(location['coords']['longitude'], 6))
                        st.info(f"🌐 **BROWSER LIVE GPS DETECTED:** Latitude: `{detected_lat}` | Longitude: `{detected_lon}`")

        with st.form("photo_upload_form", clear_on_submit=True):
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                sp_id = st.text_input("Sub-Project ID / Code")
                sp_name = st.text_input("Sub-Project Name")
                stage = st.selectbox("Stage", ["BEFORE Construction", "DURING Construction", "AFTER / Completed"])
                latitude = st.text_input("Latitude (GPS)*", value=detected_lat)
            with col_u2:
                longitude = st.text_input("Longitude (GPS)*", value=detected_lon)
                st.caption("📷 File preview or auto-detected metadata will reflect automatically.")

            submit_photo = st.form_submit_button("⬆️ Submit & Save Photo")
            if submit_photo and uploaded_file and sp_id:
                file_path = os.path.join("uploaded_photos", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Geotagged_Photos (sp_id, sp_name, stage, latitude, longitude, photo_file, date_uploaded, encoder)
                    VALUES (?, ?, ?, ?, ?, ?, DATE('now'), ?)
                """, (sp_id, sp_name, stage, latitude, longitude, uploaded_file.name, st.session_state["user_name"]))
                conn.commit()
                conn.close()

                st.success(f"Photo '{uploaded_file.name}' saved to database successfully!")
                if uploaded_file.type in ["image/jpeg", "image/png"]:
                    st.image(Image.open(uploaded_file), caption=f"Preview: {stage} - {sp_id} (Lat: {latitude}, Lon: {longitude})", width=350)
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Listed Geotagged Photos Records")
    df_photos = load_db_table("Geotagged_Photos")
    st.dataframe(df_photos, use_container_width=True)

# ---------------------------------------------------------
# 8. FINANCE MODULE (SINGLE SHEET: MONITORING EVALUATION REPORT)
# ---------------------------------------------------------
elif selected_view == "Finance":
    st.subheader("💰 Finance - Monitoring Evaluation Report")
    st.caption("Live Synchronization Viewer • Official Executive Finance Tracking")

    # Full Spreadsheet Edit Link for Button
    sheet_url = "https://docs.google.com/spreadsheets/d/1d_QZrY3tF6wajFQiOx5yTtv55_GyrIYW/edit?usp=sharing"
    
    # Specific Single Sheet Publish Embed Link (Hides all other tabs)
    # Target: MONITORING EVALUATION REPORT tab only (gid=1285370211)
    embed_single_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT1-GyrIYW_placeholder/pubhtml?gid=1285370211&single=true&widget=false&headers=false"
    
    # Direct Published Sheet Viewer Link with Single Sheet Parameter
    embed_url = "https://docs.google.com/spreadsheets/d/1d_QZrY3tF6wajFQiOx5yTtv55_GyrIYW/pubhtml?gid=1285370211&single=true&widget=false&headers=false"

    c_f1, c_f2 = st.columns([3, 1])
    with c_f1:
        st.info("📊 **Monitoring Evaluation Report**: Gi-isolate ug gi-display lang ang KANI nga specific sheet.")
    with c_f2:
        st.link_button("🔗 Open Full Google Sheet", sheet_url, use_container_width=True)

    st.markdown("---")

    # Embed Single Sheet Viewer (Nawala na ang laing tabs sa ubos)
    st.markdown(
        f"""
        <iframe src="{embed_url}" 
                width="100%" 
                height="750" 
                style="border: 1px solid #CBD5E1; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);" 
                allowfullscreen>
        </iframe>
        """, 
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# 9. CEAC MUNICIPAL, BARANGAY, DISBURSEMENT & CLOSEOUT TRACKER MODULES
# ---------------------------------------------------------
else:
    st.subheader(f"📋 Data Management & Encoding: {selected_view}")

    if st.button("➕ Add New Activity / Record", use_container_width=True):
        st.session_state["show_add_form"] = not st.session_state.get("show_add_form", False)

    if st.session_state.get("show_add_form", True):
        with st.expander(f"📝 Comprehensive Entry Form: {selected_view}", expanded=True):
            
            # CEAC MUNICIPAL DYNAMIC FORM OUTSIDE PRE-RENDER
            if selected_view == "CEAC_Municipal":
                col_left, col_right = st.columns(2)
                with col_left:
                    selected_m_act = st.selectbox("Select Municipal Activity", MUNICIPAL_ACTIVITIES, key="cm_act")
                    cm_region = st.selectbox("Region", REGIONS, key="cm_reg")
                    cm_province = st.selectbox("Province", PROVINCES, key="cm_prov")
                    cm_municipality = st.selectbox("Municipality", MUNICIPALITIES, key="cm_mun")
                    cm_cycle = st.selectbox("Cycle / Batch", CYCLE_BATCHES, key="cm_cyc")
                    cm_date = st.date_input("Activity Date", datetime.date.today(), key="cm_dt").strftime("%Y-%m-%d")
                
                with col_right:
                    cm_date_enc = datetime.date.today().strftime("%Y-%m-%d")
                    st.text_input("Date Encoded (Auto)", value=cm_date_enc, disabled=True, key="cm_de_dis")
                    cm_encoder = st.session_state["user_name"]
                    st.text_input("Encoded By (Auto Logged User)", value=cm_encoder, disabled=True, key="cm_eb_dis")
                    cm_mov_st = st.selectbox("MOV Status", MOV_STATUSES, key="cm_mov_st")
                    cm_enc_st = st.selectbox("Encoded Status", ENCODED_OPTIONS, key="cm_enc_st")
                    cm_remarks = st.text_area("Remarks", key="cm_rem")

                st.markdown("---")
                
                # DYNAMIC FORM SWITCHING BASED ON GRS INTAKE
                if selected_m_act == "GRS Instake":
                    st.markdown("##### 📁 Upload GRS Intake Files (Multiple Upload - Up to 10 Files)")
                    grs_files = st.file_uploader("Choose GRS Files (Max 10)", type=["pdf", "png", "jpg", "jpeg", "docx"], accept_multiple_files=True, key="cm_grs_files")
                    if grs_files and len(grs_files) > 10:
                        st.error("⚠️ Exceeded maximum 10 files! Processing only the first 10 files.")
                        grs_files = grs_files[:10]
                    
                    att_saved, min_saved, lgu_saved = "N/A - GRS Intake", "N/A - GRS Intake", "N/A - GRS Intake"
                    grs_saved = save_multiple_files(grs_files)
                else:
                    st.markdown("##### 📁 Upload MOVs (Separate Buttons for Municipal Activities)")
                    mov_col1, mov_col2, mov_col3 = st.columns(3)
                    with mov_col1:
                        st.markdown("**1. Upload Attendance**")
                        att_file = st.file_uploader("Choose Attendance File/Image", type=["pdf", "png", "jpg", "jpeg", "docx"], key="cm_att")
                        att_saved = save_uploaded_file(att_file)

                    with mov_col2:
                        st.markdown("**2. Upload Minutes of Activity**")
                        min_file = st.file_uploader("Choose Minutes File/Image", type=["pdf", "png", "jpg", "jpeg", "docx"], key="cm_min")
                        min_saved = save_uploaded_file(min_file)

                    with mov_col3:
                        st.markdown("**3. Upload LGU Minutes of Activity**")
                        lgu_min_file = st.file_uploader("Choose LGU Minutes File/Image", type=["pdf", "png", "jpg", "jpeg", "docx"], key="cm_lgu_min")
                        lgu_saved = save_uploaded_file(lgu_min_file)
                    
                    grs_saved = ""

                st.markdown("---")
                b1, b2, b3 = st.columns([2, 2, 1])
                if b1.button("💾 Save Record to Database", use_container_width=True, key="cm_save_btn"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO CEAC_Municipal (activity_name, region, province, municipality, cycle_batch, activity_date, date_encoded, encoded_by, mov_status, encoded_status, mov_attendance, mov_minutes, mov_lgu_minutes, mov_grs_files, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (selected_m_act, cm_region, cm_province, cm_municipality, cm_cycle, cm_date, cm_date_enc, cm_encoder, cm_mov_st, cm_enc_st, att_saved, min_saved, lgu_saved, grs_saved, cm_remarks))
                    conn.commit()
                    conn.close()
                    st.success("Municipal Activity record saved to database successfully!")
                    st.session_state["show_add_form"] = False
                    st.rerun()

            # CEAC BARANGAY DYNAMIC FORM
            elif selected_view == "CEAC_Barangay":
                col_left, col_right = st.columns(2)
                with col_left:
                    selected_b_act = st.selectbox("Select Barangay Activity", BARANGAY_ACTIVITIES, key="cb_act")
                    cb_region = st.selectbox("Region", REGIONS, key="cb_reg")
                    cb_province = st.selectbox("Province", PROVINCES, key="cb_prov")
                    cb_municipality = st.selectbox("Municipality", MUNICIPALITIES, key="cb_mun")
                    cb_barangay = st.text_input("Barangay Name", key="cb_brgy")
                    cb_cycle = st.selectbox("Cycle / Batch", CYCLE_BATCHES, key="cb_cyc")
                    cb_date = st.date_input("Activity Date", datetime.date.today(), key="cb_dt").strftime("%Y-%m-%d")
                
                with col_right:
                    cb_date_enc = datetime.date.today().strftime("%Y-%m-%d")
                    st.text_input("Date Encoded (Auto)", value=cb_date_enc, disabled=True, key="cb_de_dis")
                    cb_encoder = st.session_state["user_name"]
                    st.text_input("Encoded By (Auto Logged User)", value=cb_encoder, disabled=True, key="cb_eb_dis")
                    cb_mov_st = st.selectbox("MOV Status", MOV_STATUSES, key="cb_mov_st")
                    cb_enc_st = st.selectbox("Encoded Status", ENCODED_OPTIONS, key="cb_enc_st")
                    cb_remarks = st.text_area("Remarks", key="cb_rem")

                st.markdown("---")
                
                # DYNAMIC FORM SWITCHING BASED ON CV (COMMUNITY VOLUNTEERS)
                if selected_b_act == "CV":
                    st.markdown("##### 📁 Upload CV Files (Multiple Upload - Up to 30 CVs)")
                    cv_files = st.file_uploader("Choose CV Files (Max 30)", type=["pdf", "png", "jpg", "jpeg", "docx"], accept_multiple_files=True, key="cb_cv_files")
                    if cv_files and len(cv_files) > 30:
                        st.error("⚠️ Exceeded maximum 30 files! Processing only the first 30 files.")
                        cv_files = cv_files[:30]
                    
                    att_saved, brgy_min_saved, lgu_saved = "N/A - CV", "N/A - CV", "N/A - CV"
                    cv_saved = save_multiple_files(cv_files)
                else:
                    st.markdown("##### 📁 Upload MOVs (Separate Buttons for Barangay Activities)")
                    mov_col1, mov_col2, mov_col3 = st.columns(3)
                    with mov_col1:
                        st.markdown("**1. Upload Attendance**")
                        att_file = st.file_uploader("Choose Attendance File/Image", type=["pdf", "png", "jpg", "jpeg", "docx"], key="cb_att")
                        att_saved = save_uploaded_file(att_file)

                    with mov_col2:
                        st.markdown("**2. Upload Brgy Minutes of Activity**")
                        brgy_min_file = st.file_uploader("Choose Brgy Minutes File/Image", type=["pdf", "png", "jpg", "jpeg", "docx"], key="cb_brgy_min")
                        brgy_min_saved = save_uploaded_file(brgy_min_file)

                    with mov_col3:
                        st.markdown("**3. Upload LGU Minutes of Activity**")
                        lgu_min_file = st.file_uploader("Choose LGU Minutes File/Image", type=["pdf", "png", "jpg", "jpeg", "docx"], key="cb_lgu_min")
                        lgu_saved = save_uploaded_file(lgu_min_file)
                    
                    cv_saved = ""

                st.markdown("---")
                b1, b2, b3 = st.columns([2, 2, 1])
                if b1.button("💾 Save Record to Database", use_container_width=True, key="cb_save_btn"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO CEAC_Barangay (activity_name, region, province, municipality, barangay, cycle_batch, activity_date, date_encoded, encoded_by, mov_status, encoded_status, mov_attendance, mov_brgy_minutes, mov_lgu_minutes, mov_cv_files, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (selected_b_act, cb_region, cb_province, cb_municipality, cb_barangay, cb_cycle, cb_date, cb_date_enc, cb_encoder, cb_mov_st, cb_enc_st, att_saved, brgy_min_saved, lgu_saved, cv_saved, cb_remarks))
                    conn.commit()
                    conn.close()
                    st.success("Barangay Activity record saved to database successfully!")
                    st.session_state["show_add_form"] = False
                    st.rerun()

            else:
                with st.form(f"form_add_{selected_view}"):
                    form_data = {}
                    col_left, col_right = st.columns(2)

                    if selected_view == "Sub_Project_Closeout_Tracker":
                        with col_left:
                            form_data["sp_id"] = st.text_input("Sub-Project ID / Code", key="sp_id_in")
                            form_data["sp_name"] = st.text_input("Sub-Project Name", key="sp_name_in")
                            form_data["municipality"] = st.selectbox("Municipality", MUNICIPALITIES, key="sp_mun")
                            form_data["barangay"] = st.text_input("Barangay Name", key="sp_brgy")
                            form_data["cycle_batch"] = st.selectbox("Cycle / Batch", CYCLE_BATCHES, key="sp_cyc")
                            form_data["functionality_audit_status"] = st.selectbox("Functionality Audit Status", CLOSEOUT_STATUSES, key="sp_fas")
                            form_data["functionality_audit_date"] = st.date_input("Functionality Audit Date", datetime.date.today(), key="sp_fad").strftime("%Y-%m-%d")
                            form_data["spcr_status"] = st.selectbox("SPCR Status", CLOSEOUT_STATUSES, key="sp_spcrs")
                            form_data["spcr_date_submitted"] = st.date_input("SPCR Date Submitted", datetime.date.today(), key="sp_spcrd").strftime("%Y-%m-%d")
                        
                        with col_right:
                            form_data["closing_accounts_status"] = st.selectbox("Closing Accounts Status", CLOSEOUT_STATUSES, key="sp_cas")
                            form_data["date_account_closed"] = st.date_input("Date Account Closed", datetime.date.today(), key="sp_dac").strftime("%Y-%m-%d")
                            form_data["booking_assets_status"] = st.selectbox("Booking Assets Status", CLOSEOUT_STATUSES, key="sp_bas")
                            form_data["date_booking_assets"] = st.date_input("Date Booking Assets", datetime.date.today(), key="sp_dba").strftime("%Y-%m-%d")
                            form_data["overall_closeout_status"] = st.selectbox("Overall Closeout Status", ["Ongoing Implementation", "For Closeout", "Fully Closed & Turned Over", "On Hold"], key="sp_ocs")
                            form_data["encoded_status"] = st.selectbox("Encoded Status", ENCODED_OPTIONS, key="sp_enc")
                            form_data["target_hhs"] = st.number_input("Target HHs", min_value=0, step=1, key="sp_thh")
                            form_data["actual_hhs"] = st.number_input("Actual HHs", min_value=0, step=1, key="sp_ahh")
                            form_data["male_beneficiaries"] = st.number_input("Male Beneficiaries", min_value=0, step=1, key="sp_mb")
                            form_data["female_beneficiaries"] = st.number_input("Female Beneficiaries", min_value=0, step=1, key="sp_fb")
                            form_data["remarks"] = st.text_area("Remarks", key="sp_rem")
                            form_data["mov_file"] = ""

                        form_data["total_beneficiaries"] = form_data["male_beneficiaries"] + form_data["female_beneficiaries"]
                        form_data["hh_variance"] = form_data["actual_hhs"] - form_data["target_hhs"]

                    elif selected_view == "Disbursement":
                        with col_left:
                            form_data["sp_id"] = st.text_input("Sub-Project ID / Code", key="d_spid")
                            form_data["sp_name"] = st.text_input("Sub-Project Name", key="d_spname")
                            form_data["dv_number"] = st.text_input("Disbursement Voucher (DV) No.", key="d_dv")
                            form_data["check_number"] = st.text_input("Check / LDDAP No.", key="d_chk")
                            form_data["payee"] = st.text_input("Payee / Recipient", key="d_payee")
                            form_data["disbursement_date"] = st.date_input("Disbursement Date", datetime.date.today(), key="d_dt").strftime("%Y-%m-%d")
                        with col_right:
                            form_data["amount"] = st.number_input("Gross Amount (₱)", min_value=0.0, step=100.0, key="d_amt")
                            form_data["tax_amount"] = st.number_input("Tax Amount (₱)", min_value=0.0, step=100.0, key="d_tax")
                            form_data["net_amount"] = form_data["amount"] - form_data["tax_amount"]
                            form_data["status"] = st.selectbox("Disbursement Status", ["Released", "Pending Liquidation", "Liquidated", "Cancelled"], key="d_stat")
                            form_data["encoded_status"] = st.selectbox("Encoded Status", ENCODED_OPTIONS, key="d_enc")
                            form_data["mov_file"] = ""
                            form_data["attachment"] = ""

                    else:
                        with col_left:
                            form_data["municipality"] = st.selectbox("Municipality", MUNICIPALITIES, key="sum_mun")
                            form_data["total_sps"] = st.number_input("Total Sub-Projects", min_value=0, step=1, key="sum_sps")
                            form_data["total_grant"] = st.number_input("Total Grant Allocation (₱)", min_value=0.0, step=1000.0, key="sum_grant")
                        with col_right:
                            form_data["total_disbursed"] = st.number_input("Total Disbursed Amount (₱)", min_value=0.0, step=1000.0, key="sum_disb")
                            form_data["total_liquidated"] = st.number_input("Total Liquidated Amount (₱)", min_value=0.0, step=1000.0, key="sum_liq")
                            form_data["unliquidated_balance"] = form_data["total_disbursed"] - form_data["total_liquidated"]

                    st.markdown("---")
                    b1, b2, b3 = st.columns([2, 2, 1])
                    save_btn = b1.form_submit_button("💾 Save Record to Database", use_container_width=True)
                    cancel_btn = b3.form_submit_button("❌ Cancel", use_container_width=True)

                    if save_btn:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        col_names_str = ", ".join(form_data.keys())
                        placeholders = ", ".join(["?"] * len(form_data))
                        cursor.execute(f"INSERT INTO {selected_view} ({col_names_str}) VALUES ({placeholders})", list(form_data.values()))
                        conn.commit()
                        conn.close()

                        st.success("Record saved to database successfully!")
                        st.session_state["show_add_form"] = False
                        st.rerun()

    # LIVE DATA TABLE DISPLAY & LACKING ACTIVITIES/MOVS CALCULATOR
    st.markdown("---")
    st.subheader(f"📊 Added Activities Masterlist ({selected_view})")
    
    df_current = load_db_table(selected_view)
    search_q = st.text_input("🔍 Quick Keyword Search Across Records:", "")
    df_filtered = df_current.copy()
    if search_q and not df_filtered.empty:
        mask = df_filtered.astype(str).apply(lambda row: row.str.contains(search_q, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]

    if not df_filtered.empty:
        edited_df = st.data_editor(
            df_filtered,
            use_container_width=True,
            num_rows="dynamic" if st.session_state["user_role"] == "Superuser" else "fixed",
            key=f"editor_{selected_view}"
        )
        if st.session_state["user_role"] == "Superuser" and st.button("💾 Sync Table Changes to Database"):
            conn = get_db_connection()
            edited_df.to_sql(selected_view, conn, if_exists="replace", index=False)
            conn.close()
            st.success("Database synchronized successfully!")
            st.rerun()

        # LACKING ACTIVITIES & LACKING MOVs TRACKER SUMMARY AT THE BOTTOM
        if selected_view in ["CEAC_Municipal", "CEAC_Barangay"]:
            st.markdown("---")
            st.markdown("### ⚠️ Lacking Activities & Lacking MOVs Audit Trail Tracker")
            
            ref_activities = MUNICIPAL_ACTIVITIES if selected_view == "CEAC_Municipal" else BARANGAY_ACTIVITIES
            conducted_acts = df_filtered["activity_name"].dropna().unique().tolist() if "activity_name" in df_filtered.columns else []
            lacking_acts = [act for act in ref_activities if act not in conducted_acts]
            
            c_lak1, c_lak2 = st.columns(2)
            with c_lak1:
                st.markdown("#### 📌 Activities Not Yet Conducted:")
                if lacking_acts:
                    for act in lacking_acts:
                        st.error(f"❌ **{act}** - Not Yet Conducted")
                else:
                    st.success("🎉 All CEAC Activities completed and encoded!")

            with c_lak2:
                st.markdown("#### 📄 Records with Lacking MOVs:")
                lacking_mov_count = 0
                for _, row in df_filtered.iterrows():
                    act_n = row.get("activity_name", "N/A")
                    missing_movs = []
                    
                    if act_n == "GRS Instake":
                        if not str(row.get("mov_grs_files", "")).strip():
                            missing_movs.append("GRS Multiple Files")
                    elif act_n == "CV":
                        if not str(row.get("mov_cv_files", "")).strip():
                            missing_movs.append("CV Multiple Files")
                    else:
                        if not str(row.get("mov_attendance", "")).strip():
                            missing_movs.append("Attendance")
                        
                        min_col = "mov_minutes" if selected_view == "CEAC_Municipal" else "mov_brgy_minutes"
                        if not str(row.get(min_col, "")).strip():
                            missing_movs.append("Minutes of Activity")
                            
                        if not str(row.get("mov_lgu_minutes", "")).strip():
                            missing_movs.append("LGU Minutes")

                    if missing_movs:
                        lacking_mov_count += 1
                        st.warning(f"⚠️ **ID #{row.get('id', '')} - {act_n}:** Missing ({', '.join(missing_movs)})")

                if lacking_mov_count == 0:
                    st.success("✅ All encoded records have complete MOVs uploaded!")

    else:
        st.info(f"No records found in '{selected_view}'. Use the '➕ Add New Activity / Record' button above to create entry.")

# DEVELOPER FOOTER BADGE
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; font-size: 0.85em; color: #6c757d; padding-bottom: 20px;">
        ⚙️ <b>PAMANA Peace & Development Program Management System</b> | Powered by Streamlit & Python<br>
        Designed & Developed by <b>LOUIE B. IDULSA - PDBBM ITO I</b> • DSWD Field Office X
    </div>
    """, 
    unsafe_allow_html=True
)
