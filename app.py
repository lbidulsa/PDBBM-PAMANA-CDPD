import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
from PIL import Image, ExifTags
import os
import random
import string
import datetime
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    section[data-testid="stSidebar"] {
        background-color: #0F2A4A !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #E2E8F0 !important;
    }
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
    .active-user-card {
        background: #FFFFFF;
        border-left: 4px solid #10B981;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
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

def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def send_credentials_email(recipient_email, recipient_name, temp_password, user_role="User"):
    sender_email = "lbidulsa.fo10@dswd.gov.ph"
    sender_password = "rkgqurmorpvfgktq"
    system_link = "https://pdbbmpamanacdpd.streamlit.app/"
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"DSWD FO X PAMANA CDPD System <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = "🔒 Official Account Credentials - PAMANA CDPD Portal"
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #1F4E78; border-radius: 8px;">
              <h2 style="color: #1F4E78; text-align: center;">🕊️ DSWD Field Office X - PAMANA CDPD System</h2>
              <hr style="border: 0; border-top: 1px solid #1F4E78;">
              <p>Dear <b>{recipient_name}</b>,</p>
              <p>Your official user account for the <b>PAMANA Peace & Development Management System</b> has been successfully configured.</p>
              
              <div style="background-color: #F4F6F9; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #1F4E78;">
                <p style="margin: 5px 0;"><b>Login Email:</b> <code style="font-size: 1.1em; color: #1F4E78;">{recipient_email}</code></p>
                <p style="margin: 5px 0;"><b>Assigned Role:</b> {user_role}</p>
                <p style="margin: 5px 0;"><b>Temporary Password:</b> <code style="font-size: 1.2em; color: #C53030; font-weight: bold;">{temp_password}</code></p>
              </div>

              <!-- DIRECT SYSTEM ACCESS LINK & BUTTON -->
              <div style="text-align: center; margin: 25px 0;">
                <a href="{system_link}" target="_blank" style="background-color: #1F4E78; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 14px;">
                  🚀 Click Here to Access System Portal
                </a>
                <p style="font-size: 0.85em; color: #5A6A85; margin-top: 8px;">
                  Or copy and paste this link to your browser:<br>
                  <a href="{system_link}" style="color: #1F4E78;">{system_link}</a>
                </p>
              </div>

              <p><b>Security Notice:</b> Please login to the PAMANA CDPD Portal and change your temporary password upon first system access.</p>
              <br>
              <p style="font-size: 0.85em; color: #6c757d; text-align: center;">
                <i>This is an automated system dispatch. Please do not reply directly to this email.</i><br>
                <b>DSWD FO X Peace & Development Program © 2026</b>
              </p>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

def get_logo_path():
    if os.path.exists("logo.png"):
        return "logo.png"
    elif os.path.exists("Peace and Dev LOGO.jpg"):
        return "Peace and Dev LOGO.jpg"
    return None

logo_file = get_logo_path()

os.makedirs("uploaded_movs", exist_ok=True)
os.makedirs("uploaded_photos", exist_ok=True)

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
# 1. CENTRALIZED SUPABASE CLOUD DATABASE INITIALIZATION
# ---------------------------------------------------------
DEFAULT_DB_URL = "postgresql+psycopg2://postgres.oxyvjstdncnnefbkilaa:5GLJZg5tWE28Wud9@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

@st.cache_resource
def get_db_engine():
    try:
        db_url = st.secrets.get("SUPABASE_URL", DEFAULT_DB_URL)
    except Exception:
        db_url = DEFAULT_DB_URL
    return create_engine(db_url, pool_pre_ping=True)

engine = get_db_engine()

def load_db_table(table_name):
    try:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", engine)
    except Exception:
        return pd.DataFrame()

# Automatic database column check for last_login
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE user_accounts ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;"))
except Exception:
    pass

# ---------------------------------------------------------
# 2. LOGIN PORTAL & FORGOT/RESET PASSWORD
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_email"] = None
    st.session_state["user_role"] = None
    st.session_state["user_name"] = None
    st.session_state["must_change_pass"] = False

if "reset_otp" not in st.session_state:
    st.session_state["reset_otp"] = None
    st.session_state["reset_user_email"] = None

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
                login_email = st.text_input("Email Address").strip()
                login_pass = st.text_input("Password", type="password")
                submit = st.form_submit_button("🔑 Login to Dashboard", use_container_width=True)
                
                if submit:
                    with engine.connect() as conn:
                        res = conn.execute(
                            text("SELECT id, full_name, email, password, user_role, require_change_pass FROM user_accounts WHERE lower(email) = lower(:email) AND password = :password"),
                            {"email": login_email, "password": login_pass}
                        ).fetchone()

                    if res:
                        display_name = res[1] if (res[1] and str(res[1]).strip() != "" and str(res[1]).lower() != "none") else res[2]
                        
                        st.session_state["logged_in"] = True
                        st.session_state["user_email"] = res[2]
                        st.session_state["user_role"] = res[4]
                        st.session_state["user_name"] = display_name
                        st.session_state["must_change_pass"] = bool(res[5])

                        # UPDATE LAST LOGIN TIMESTAMP
                        try:
                            with engine.begin() as conn_up:
                                conn_up.execute(
                                    text("UPDATE user_accounts SET last_login = NOW() WHERE id = :uid"),
                                    {"uid": res[0]}
                                )
                        except Exception:
                            pass

                        st.toast(f"Welcome back, {display_name}!", icon="👋")
                        st.success(f"Welcome back, {display_name}!")
                        st.rerun()
                    else:
                        st.error("Invalid Email Address or Password!")

        with auth_tab2:
            st.markdown("##### 🔑 Request Password Reset Verification Code")
            reset_email = st.text_input("Enter Registered Email Address:")
            
            if st.button("📩 Send Code via Email", use_container_width=True):
                with engine.connect() as conn:
                    found_user = conn.execute(
                        text("SELECT full_name, email, user_role FROM user_accounts WHERE lower(email) = lower(:email)"),
                        {"email": reset_email.strip()}
                    ).fetchone()
                
                if found_user:
                    otp = "".join(random.choices(string.digits, k=6))
                    st.session_state["reset_otp"] = otp
                    st.session_state["reset_user_email"] = found_user[1]
                    
                    target_name = found_user[0] if (found_user[0] and str(found_user[0]).lower() != "none") else found_user[1]
                    sent_ok, msg_res = send_credentials_email(found_user[1], target_name, otp, found_user[2])
                    if sent_ok:
                        st.toast("Verification code sent!", icon="📩")
                        st.success(f"📩 Reset Verification Code has been dispatched directly to {found_user[1]}!")
                    else:
                        st.warning(f"⚠️ Email dispatch status: {msg_res}")
                        st.info(f"📬 [SYSTEM BACKUP RESET CODE]: Your Verification Reset Code is: **{otp}**")
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
                            u_email = st.session_state["reset_user_email"]
                            with engine.begin() as conn:
                                conn.execute(
                                    text("UPDATE user_accounts SET password = :p, require_change_pass = 0 WHERE lower(email) = lower(:e)"),
                                    {"p": new_pass, "e": u_email}
                                )
                            st.toast("Password updated successfully!", icon="✅")
                            st.success("Password updated successfully! You may now proceed to login.")
                            st.session_state["reset_otp"] = None
                            st.session_state["reset_user_email"] = None
                        else:
                            st.error("Passwords do not match or field is empty!")
                    else:
                        st.error("Invalid OTP Code provided!")

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ---------------------------------------------------------
# MANDATORY FIRST-LOGIN CHANGE PASSWORD MODAL
# ---------------------------------------------------------
if st.session_state.get("must_change_pass"):
    if hasattr(st, "dialog"):
        @st.dialog("🔑 MANDATORY PASSWORD CHANGE REQUIRED")
        def change_password_modal():
            st.warning("⚠️ You are currently using a temporary password. Please configure your new custom password to proceed.")
            with st.form("must_change_pass_form"):
                new_p1 = st.text_input("New Password*", type="password")
                new_p2 = st.text_input("Confirm New Password*", type="password")
                submit_chg = st.form_submit_button("💾 Save & Proceed to System", use_container_width=True)
                
                if submit_chg:
                    if new_p1 and new_p1 == new_p2:
                        with engine.begin() as conn:
                            conn.execute(
                                text("UPDATE user_accounts SET password = :p, require_change_pass = 0 WHERE lower(email) = lower(:e)"),
                                {"p": new_p1, "e": st.session_state["user_email"]}
                            )
                        st.session_state["must_change_pass"] = False
                        st.toast("Password changed successfully!", icon="✅")
                        st.success("✅ Password changed successfully!")
                        st.rerun()
                    else:
                        st.error("⚠️ Passwords do not match or field is empty.")
        change_password_modal()
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
    "Municipal_Profile", "Municipal_Orientation", "1st_MDC_Meeting", "2nd_MDC_Meeting", 
    "2nd_BDC_Meeting", "PPDW", "Technical_Review", "Pre_Implementation_Training", 
    "OM", "MAR_CAR", "Sustainability_Planning_Workshop", "GRS Instake"
]

BARANGAY_ACTIVITIES = [
    "Brgy_Profile", "1st_BDC_Meeting", "BPSA", "1st_BA", "2nd_BDC_Meeting", 
    "BAR", "OM", "2nd_BA", "Grievance_Intake", "GRS_Installation_Checklist", "CV", "ERS"
]

# --- ROLE-BASED NAVIGATION MODULE FILTERING ---
# Note: User Management Portal is visible ONLY to Superuser
ALL_TABS = [
    "Executive Dashboard", "User Management Portal", "CEAC_Municipal", "CEAC_Barangay", 
    "Geotagged_Photos", "Disbursement", "Sub_Project_Closeout_Tracker", "Summary", "Finance"
]

current_role = st.session_state.get("user_role", "AC")

if current_role == "Superuser":
    TABS = ALL_TABS
else:
    # Dili magpakita ang User Management Portal sa laing roles
    TABS = [tab for tab in ALL_TABS if tab != "User Management Portal"]

# EDIT PERMISSION HELPER FUNCTION
def can_edit_module(role, module):
    if role in ["Superuser", "Admin"]:
        return True
    elif role == "AC" and module in ["CEAC_Municipal", "CEAC_Barangay", "Sub_Project_Closeout_Tracker"]:
        return True
    elif role == "TF" and module in ["Geotagged_Photos", "Sub_Project_Closeout_Tracker"]:
        return True
    elif role == "MFA" and module == "Disbursement":
        return True
    elif role == "MDM" and module in ["CEAC_Municipal", "CEAC_Barangay"]:
        return True
    return False

def save_uploaded_file(file_obj):
    if file_obj is not None:
        file_path = os.path.join("uploaded_movs", file_obj.name)
        with open(file_path, "wb") as f:
            f.write(file_obj.getbuffer())
        return file_obj.name
    return ""

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

st.sidebar.markdown(f"**Logged User:** `{st.session_state['user_name']}`")
st.sidebar.markdown(f"**Email:** `{st.session_state['user_email']}`")
st.sidebar.markdown(f"**System Role:** <span class='role-badge'>{st.session_state['user_role']}</span>", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state["logged_in"] = False
    st.session_state["user_email"] = None
    st.session_state["user_role"] = None
    st.session_state["user_name"] = None
    st.rerun()

with st.sidebar.expander("🔑 Change My Password"):
    with st.form("self_change_pass_pamana"):
        old_p = st.text_input("Current Password*", type="password")
        new_p1 = st.text_input("New Password*", type="password")
        new_p2 = st.text_input("Confirm New Password*", type="password")
        if st.form_submit_button("Update Password", use_container_width=True):
            if new_p1 == new_p2 and new_p1 != "":
                with engine.connect() as conn:
                    res_p = conn.execute(
                        text("SELECT password FROM user_accounts WHERE lower(email) = lower(:e)"),
                        {"e": st.session_state["user_email"]}
                    ).fetchone()
                if res_p and res_p[0] == old_p:
                    with engine.begin() as conn:
                        conn.execute(
                            text("UPDATE user_accounts SET password = :p, require_change_pass = 0 WHERE lower(email) = lower(:e)"),
                            {"p": new_p1, "e": st.session_state["user_email"]}
                        )
                    st.toast("✅ Password updated successfully!", icon="🔑")
                    st.success("✅ Password successfully updated!")
                else:
                    st.error("❌ Incorrect current password.")
            else:
                st.error("⚠️ Passwords do not match or empty.")

st.sidebar.markdown("---")
st.sidebar.title("📌 System Navigation")
selected_view = st.sidebar.radio("Select Active Module:", TABS)

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
    df_sp = load_db_table("sub_project_closeout_tracker")
    df_disb = load_db_table("disbursement")

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
# 6. USER MANAGEMENT PORTAL (SUPERUSER ONLY)
# ---------------------------------------------------------
elif selected_view == "User Management Portal":
    if current_role != "Superuser":
        st.error("⛔ ACCESS DENIED: Only Superuser can access the User Management Portal.")
        st.stop()
        
    st.subheader("👤 System User Management & Live Login Monitor")
    
    if "gen_temp_pass" not in st.session_state:
        st.session_state["gen_temp_pass"] = generate_random_password()
    
    USER_ROLES_LIST = ["Superuser", "Admin", "AC", "TF", "MFA", "MDM"]

    # --- SUPERUSER LIVE LOGGED USERS AUDIT SECTION ---
    st.markdown("##### 🔴 Live System User Login Activity & Audit Log:")
    
    with engine.connect() as conn:
        active_logs = conn.execute(text("SELECT id, full_name, email, user_role, last_login FROM user_accounts ORDER BY last_login DESC NULLS LAST")).fetchall()

    if active_logs:
        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            st.markdown("###### **Recently Active Users / Login Sessions:**")
            for u in active_logs[:5]:
                u_name = u[1] if (u[1] and str(u[1]).lower() != "none") else u[2]
                last_time = u[4].strftime("%B %d, %Y - %I:%M %p") if u[4] else "Never Logged In"
                
                is_curr = "🟢 CURRENT SESSION ONLINE" if u[2] == st.session_state["user_email"] else f"🕒 Last Online: {last_time}"
                
                st.markdown(f"""
                    <div class="active-user-card">
                        <b>👤 {u_name}</b> (`{u[2]}`) &nbsp;|&nbsp; 
                        Role: <span class='role-badge'>{u[3]}</span> &nbsp;|&nbsp; 
                        <span style="color:#0284C7; font-weight:bold;">{is_curr}</span>
                    </div>
                """, unsafe_allow_html=True)
        
        with col_act2:
            st.info(f"📊 **Total Accounts:** `{len(active_logs)}` Users\n\n🛡️ **Superuser Privileges:** Live real-time login timestamp monitoring active.")

    st.markdown("---")
    
    col_u1, col_u2 = st.columns(2)
    
    with col_u1:
        st.markdown("##### ➕ Add New System User")
        with st.form("add_user_form", clear_on_submit=True):
            new_fullname = st.text_input("Full Name*")
            new_email = st.text_input("User Email Address*").strip()
            new_role = st.selectbox("Assigned Role*", USER_ROLES_LIST)
            
            curr_temp_pass = st.session_state["gen_temp_pass"]
            st.text_input("Generated Temporary Password (Auto):", value=curr_temp_pass, disabled=True)
            send_via_email = st.checkbox("📧 Send Credentials via Direct Email to User", value=True)
            
            submit_user = st.form_submit_button("💾 Create User Account", use_container_width=True)
            if submit_user:
                if new_fullname and new_email:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("SELECT setval(pg_get_serial_sequence('user_accounts', 'id'), COALESCE(MAX(id), 1)) FROM user_accounts;"))
                            conn.execute(
                                text("INSERT INTO user_accounts (full_name, email, password, user_role, require_change_pass) VALUES (:fn, :e, :p, :r, 1)"),
                                {"fn": new_fullname, "e": new_email, "p": curr_temp_pass, "r": new_role}
                            )
                        
                        st.toast(f"✅ User '{new_fullname}' created!", icon="👤")
                        st.success(f"✅ User '{new_fullname}' ({new_role}) successfully created!")
                        
                        if send_via_email:
                            sent_ok, msg_res = send_credentials_email(new_email, new_fullname, curr_temp_pass, new_role)
                            if sent_ok:
                                st.success(f"📩 Account credentials emailed directly to {new_email}!")
                            else:
                                st.warning(f"⚠️ Email dispatch status: {msg_res}")
                                st.info(f"🔑 **BACKUP DISPLAY PASS:** `{curr_temp_pass}`")
                        else:
                            st.info(f"🔑 **USER TEMPORARY PASS:** `{curr_temp_pass}`")
                                
                        st.session_state["gen_temp_pass"] = generate_random_password()
                        st.rerun()
                    except Exception as ex:
                        st.error(f"⚠️ Error creating user account: {ex}")
                else:
                    st.error("Please fill in Full Name and Email Address.")

    with col_u2:
        st.markdown("##### 🔑 Reset User Password (with Live Search)")
        user_search = st.text_input("🔍 Search User Name or Email:")
        
        query_u = "SELECT id, full_name, email, user_role FROM user_accounts WHERE user_role != 'Superuser'"
        params_u = {}
        
        if user_search:
            query_u += " AND (lower(full_name) LIKE lower(:s) OR lower(email) LIKE lower(:s))"
            params_u["s"] = f"%{user_search.strip()}%"
            
        with engine.connect() as conn:
            u_list = conn.execute(text(query_u), params_u).fetchall()
        
        if u_list:
            u_dict = {f"{r[1] or r[2]} ({r[2]}) - [{r[3]}]": (r[0], r[2], r[1] or r[2], r[3]) for r in u_list}
            selected_reset = st.selectbox("Select Filtered User Account:", list(u_dict.keys()))
            send_reset_mail = st.checkbox("📧 Email New Password Directly to User", value=True, key="rst_m_chk")
            
            if st.button("🔄 Reset Password Now", use_container_width=True):
                r_id, r_email, r_name, r_role = u_dict[selected_reset]
                new_temp = generate_random_password()
                
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("UPDATE user_accounts SET password = :p, require_change_pass = 1 WHERE id = :id"),
                            {"p": new_temp, "id": r_id}
                        )
                    
                    st.toast("🔑 Password reset initiated!", icon="🔐")
                    st.success(f"✅ Reset Password initiated for {r_email}!")
                    
                    if send_reset_mail:
                        sent_ok, msg_res = send_credentials_email(r_email, r_name, new_temp, r_role)
                        if sent_ok:
                            st.success(f"📩 Reset password emailed directly to {r_email}!")
                        else:
                            st.warning(f"⚠️ Email dispatch status: {msg_res}")
                            st.info(f"🔑 **BACKUP RESET PASS:** `{new_temp}`")
                    else:
                        st.info(f"🔑 **NEW TEMPORARY PASS:** `{new_temp}`")
                except Exception as ex:
                    st.error(f"❌ DATABASE ERROR: {ex}")
        else:
            st.info("No matching users found.")

    st.markdown("---")
    st.subheader("📋 Registered Users Masterlist & Login Timestamps")
    df_users = load_db_table("user_accounts")
    if not df_users.empty and "password" in df_users.columns:
        df_users = df_users.drop(columns=["password"])
    st.dataframe(df_users, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 7. GEOTAGGED PHOTOS MODULE
# ---------------------------------------------------------
elif selected_view == "Geotagged_Photos":
    st.subheader("📸 Geotagged Photos & Progress File Uploads")
    
    # Check if current user role has edit access to Geotagged Photos
    if can_edit_module(current_role, "Geotagged_Photos"):
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
                    sp_id = st.text_input("Sub-Project ID / Code*")
                    sp_name = st.text_input("Sub-Project Name")
                    stage = st.selectbox("Stage", ["BEFORE Construction", "DURING Construction", "AFTER / Completed"])
                    latitude = st.text_input("Latitude (GPS)*", value=detected_lat)
                with col_u2:
                    longitude = st.text_input("Longitude (GPS)*", value=detected_lon)
                    st.caption("📷 File preview or auto-detected metadata will reflect automatically.")

                submit_photo = st.form_submit_button("⬆️ Submit & Save Photo")
                if submit_photo:
                    if not uploaded_file or not sp_id.strip():
                        st.error("⚠️ **REQUIRED FIELDS MISSING:** Palihug mag-upload og file ug isulat ang Sub-Project ID!")
                    else:
                        try:
                            file_path = os.path.join("uploaded_photos", uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            with engine.begin() as conn:
                                conn.execute(
                                    text("""
                                        INSERT INTO geotagged_photos (sp_id, sp_name, stage, latitude, longitude, photo_file, date_uploaded, encoder)
                                        VALUES (:sp_id, :sp_name, :stage, :lat, :lon, :file, CURRENT_DATE, :encoder)
                                    """),
                                    {
                                        "sp_id": sp_id.strip(), "sp_name": sp_name, "stage": stage,
                                        "lat": latitude, "lon": longitude, "file": uploaded_file.name,
                                        "encoder": st.session_state["user_name"]
                                    }
                                )

                            st.toast("✅ Geotagged photo saved to Supabase!", icon="📸")
                            st.success(f"Photo '{uploaded_file.name}' saved to database successfully!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"❌ DATABASE ERROR: {ex}")
    else:
        st.info(f"👁️ **VIEW-ONLY MODE:** Your assigned role (`{current_role}`) is restricted from uploading new photos in this module.")

    st.markdown("---")
    st.subheader("📋 Listed Geotagged Photos Records")
    df_photos = load_db_table("geotagged_photos")
    st.dataframe(df_photos, use_container_width=True)

# ---------------------------------------------------------
# 8. FINANCE MODULE
# ---------------------------------------------------------
elif selected_view == "Finance":
    st.subheader("💰 Finance - Monitoring Evaluation Report")
    st.caption("Live Synchronization Viewer • Official Executive Finance Tracking")

    sheet_url = "https://docs.google.com/spreadsheets/d/1d_QZrY3tF6wajFQiOx5yTtv55_GyrIYW/edit?usp=sharing"
    embed_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT51CpWr5YaWUkDCfJYmUCAFduSjlC8Nlbxqb2DGceLH2CuaQ9EIOva6HRVj5ikVQ/pubhtml?gid=1476863389&single=true&widget=false&headers=false"

    c_f1, c_f2 = st.columns([3, 1])
    with c_f1:
        st.info("📊 **Monitoring Evaluation Report**: Live single sheet embedded viewer.")
    with c_f2:
        st.link_button("🔗 Open Full Google Sheet", sheet_url, use_container_width=True)

    st.markdown("---")

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

    # Check permission to edit/add entry for current module
    has_edit_perm = can_edit_module(current_role, selected_view)

    if has_edit_perm:
        if st.button("➕ Add New Activity / Record", use_container_width=True):
            st.session_state["show_add_form"] = not st.session_state.get("show_add_form", False)

        if st.session_state.get("show_add_form", True):
            with st.expander(f"📝 Comprehensive Entry Form: {selected_view}", expanded=True):
                
                if selected_view == "CEAC_Municipal":
                    col_left, col_right = st.columns(2)
                    with col_left:
                        selected_m_act = st.selectbox("Select Municipal Activity", MUNICIPALITIES if selected_view == "Summary" else MUNICIPAL_ACTIVITIES, key="cm_act")
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
                        try:
                            with engine.begin() as conn:
                                conn.execute(
                                    text("""
                                        INSERT INTO ceac_municipal (activity_name, region, province, municipality, cycle_batch, activity_date, date_encoded, encoded_by, mov_status, encoded_status, mov_attendance, mov_minutes, mov_lgu_minutes, mov_grs_files, remarks)
                                        VALUES (:act, :reg, :prov, :mun, :cyc, :dt, :denc, :enc, :mst, :est, :att, :min, :lgu, :grs, :rem)
                                    """),
                                    {
                                        "act": selected_m_act, "reg": cm_region, "prov": cm_province, "mun": cm_municipality,
                                        "cyc": cm_cycle, "dt": cm_date, "denc": cm_date_enc, "enc": cm_encoder,
                                        "mst": cm_mov_st, "est": cm_enc_st, "att": att_saved, "min": min_saved,
                                        "lgu": lgu_saved, "grs": grs_saved, "rem": cm_remarks
                                    }
                                )
                            st.toast("✅ Municipal Activity record saved to Supabase!", icon="🎉")
                            st.success("Municipal Activity record saved to database successfully!")
                            st.session_state["show_add_form"] = False
                            st.rerun()
                        except Exception as ex:
                            st.error(f"❌ DATABASE ERROR: {ex}")

                elif selected_view == "CEAC_Barangay":
                    col_left, col_right = st.columns(2)
                    with col_left:
                        selected_b_act = st.selectbox("Select Barangay Activity", BARANGAY_ACTIVITIES, key="cb_act")
                        cb_region = st.selectbox("Region", REGIONS, key="cb_reg")
                        cb_province = st.selectbox("Province", PROVINCES, key="cb_prov")
                        cb_municipality = st.selectbox("Municipality", MUNICIPALITIES, key="cb_mun")
                        cb_barangay = st.text_input("Barangay Name*", key="cb_brgy")
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
                        if not cb_barangay.strip():
                            st.error("⚠️ **REQUIRED FIELD MISSING:** Palihug sulati ang Barangay Name!")
                        else:
                            try:
                                with engine.begin() as conn:
                                    conn.execute(
                                        text("""
                                            INSERT INTO ceac_barangay (activity_name, region, province, municipality, barangay, cycle_batch, activity_date, date_encoded, encoded_by, mov_status, encoded_status, mov_attendance, mov_brgy_minutes, mov_lgu_minutes, mov_cv_files, remarks)
                                            VALUES (:act, :reg, :prov, :mun, :brgy, :cyc, :dt, :denc, :enc, :mst, :est, :att, :bmin, :lgu, :cv, :rem)
                                        """),
                                        {
                                            "act": selected_b_act, "reg": cb_region, "prov": cb_province, "mun": cb_municipality,
                                            "brgy": cb_barangay.strip(), "cyc": cb_cycle, "dt": cb_date, "denc": cb_date_enc,
                                            "enc": cb_encoder, "mst": cb_mov_st, "est": cb_enc_st, "att": att_saved,
                                            "bmin": brgy_min_saved, "lgu": lgu_saved, "cv": cv_saved, "rem": cb_remarks
                                        }
                                    )
                                st.toast("✅ Barangay Activity record saved to Supabase!", icon="🎉")
                                st.success("Barangay Activity record saved to database successfully!")
                                st.session_state["show_add_form"] = False
                                st.rerun()
                            except Exception as ex:
                                st.error(f"❌ DATABASE ERROR: {ex}")

                else:
                    with st.form(f"form_add_{selected_view}"):
                        form_data = {}
                        col_left, col_right = st.columns(2)

                        if selected_view == "Sub_Project_Closeout_Tracker":
                            with col_left:
                                form_data["sp_id"] = st.text_input("Sub-Project ID / Code*", key="sp_id_in")
                                form_data["sp_name"] = st.text_input("Sub-Project Name*", key="sp_name_in")
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
                                form_data["sp_id"] = st.text_input("Sub-Project ID / Code*", key="d_spid")
                                form_data["sp_name"] = st.text_input("Sub-Project Name", key="d_spname")
                                form_data["municipality"] = st.selectbox("Municipality*", MUNICIPALITIES, key="d_mun")
                                form_data["dv_number"] = st.text_input("Disbursement Voucher (DV) No.*", key="d_dv")
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
                            valid = True
                            if selected_view == "Sub_Project_Closeout_Tracker" and (not form_data.get("sp_id") or not form_data.get("sp_name")):
                                st.error("⚠️ **REQUIRED FIELDS MISSING:** Palihug sulati ang Sub-Project ID ug Sub-Project Name!")
                                valid = False
                            elif selected_view == "Disbursement" and (not form_data.get("sp_id") or not form_data.get("dv_number")):
                                st.error("⚠️ **REQUIRED FIELDS MISSING:** Palihug sulati ang Sub-Project ID ug DV Number!")
                                valid = False

                            if valid:
                                table_low = selected_view.lower()
                                col_names_str = ", ".join(form_data.keys())
                                placeholders = ", ".join([f":{k}" for k in form_data.keys()])
                                
                                try:
                                    with engine.begin() as conn:
                                        conn.execute(
                                            text(f"INSERT INTO {table_low} ({col_names_str}) VALUES ({placeholders})"),
                                            form_data
                                        )

                                        # AUTO-REFLECT DISBURSEMENT TO SUMMARY MODULE
                                        if selected_view == "Disbursement":
                                            d_mun = form_data.get("municipality")
                                            d_amt = form_data.get("amount", 0.0)
                                            
                                            if d_mun:
                                                sum_res = conn.execute(
                                                    text("SELECT total_disbursed, total_liquidated FROM summary WHERE lower(municipality) = lower(:m)"),
                                                    {"m": d_mun}
                                                ).fetchone()

                                                if sum_res:
                                                    curr_disb = float(sum_res[0] or 0.0) + float(d_amt)
                                                    curr_liq = float(sum_res[1] or 0.0)
                                                    new_unliq = curr_disb - curr_liq
                                                    
                                                    conn.execute(
                                                        text("""
                                                            UPDATE summary 
                                                            SET total_disbursed = :td, unliquidated_balance = :ub 
                                                            WHERE lower(municipality) = lower(:m)
                                                        """),
                                                        {"td": curr_disb, "ub": new_unliq, "m": d_mun}
                                                    )
                                                else:
                                                    conn.execute(
                                                        text("""
                                                            INSERT INTO summary (municipality, total_sps, total_grant, total_disbursed, total_liquidated, unliquidated_balance)
                                                            VALUES (:m, 1, :td, :td, 0.0, :td)
                                                        """),
                                                        {"m": d_mun, "td": float(d_amt)}
                                                    )

                                    st.toast(f"✅ Record saved to {selected_view} & Auto-Reflected to Summary!", icon="💾")
                                    st.success("Record saved and Summary Module updated successfully!")
                                    st.session_state["show_add_form"] = False
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"❌ DATABASE ERROR: {ex}")
    else:
        st.info(f"👁️ **VIEW-ONLY MODE:** Your assigned role (`{current_role}`) is restricted from adding or editing records in '{selected_view}'.")

    st.markdown("---")
    st.subheader(f"📊 Added Activities Masterlist ({selected_view})")
    
    df_current = load_db_table(selected_view.lower())
    search_q = st.text_input("🔍 Quick Keyword Search Across Records:", "")
    df_filtered = df_current.copy()
    if search_q and not df_filtered.empty:
        mask = df_filtered.astype(str).apply(lambda row: row.str.contains(search_q, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]

    if not df_filtered.empty:
        # Hide sync button if user doesn't have edit rights
        can_sync_table = (current_role in ["Superuser", "Admin"]) or has_edit_perm
        
        edited_df = st.data_editor(
            df_filtered,
            use_container_width=True,
            num_rows="dynamic" if can_sync_table else "fixed",
            disabled=not can_sync_table,
            key=f"editor_{selected_view}"
        )
        if can_sync_table and st.button("💾 Sync Table Changes to Database"):
            table_low = selected_view.lower()
            try:
                with engine.begin() as conn:
                    edited_df.to_sql(table_low, conn, if_exists="replace", index=False)
                st.toast("✅ Table changes synchronized to Supabase!", icon="🎉")
                st.success("Database synchronized successfully!")
                st.rerun()
            except Exception as ex:
                st.error(f"❌ DATABASE ERROR: {ex}")

    else:
        st.info(f"No records found in '{selected_view}'.")

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
