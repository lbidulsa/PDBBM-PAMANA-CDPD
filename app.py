import datetime
import os
import random
import secrets
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from PIL import ExifTags, Image
import plotly.express as px
from sqlalchemy import create_engine, text
import streamlit as st

# Timezone Support
try:
    from zoneinfo import ZoneInfo
    PH_TZ = ZoneInfo("Asia/Manila")
except ImportError:
    import pytz
    PH_TZ = pytz.timezone("Asia/Manila")

try:
    from streamlit_js_eval import get_geolocation
    HAS_GEO_EVAL = True
except ImportError:
    HAS_GEO_EVAL = False

# ---------------------------------------------------------
# 🇵🇭 TIMEZONE HELPER FUNCTION FOR PHILIPPINE STANDARD TIME
# ---------------------------------------------------------
def get_ph_time():
    """Returns current datetime in Philippine Standard Time (Asia/Manila UTC+8)"""
    return datetime.datetime.now(PH_TZ)

def format_ph_time(dt_val):
    """Converts database timestamp into formatted Philippine Standard Time string"""
    if dt_val is None or pd.isna(dt_val):
        return "Never Logged In"
    try:
        if isinstance(dt_val, str):
            dt_val = pd.to_datetime(dt_val)

        if dt_val.tzinfo is None:
            dt_ph = dt_val.replace(tzinfo=datetime.timezone.utc).astimezone(PH_TZ)
        else:
            dt_ph = dt_val.astimezone(PH_TZ)

        return dt_ph.strftime("%B %d, %Y - %I:%M %p")
    except Exception:
        return str(dt_val)

# ---------------------------------------------------------
# PAGE CONFIGURATION & CUSTOM STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="PAMANA Peace & Dev Management System",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #F4F6F9; }
    .main-title { font-size: 26px; font-weight: 800; color: #1F4E78; margin-bottom: 5px; }
    .sub-title { font-size: 14px; color: #5A6A85; margin-bottom: 20px; }
    
    .stMetric { 
        background-color: #FFFFFF !important; 
        padding: 16px !important; 
        border-radius: 12px !important; 
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    .stMetric:hover {
        transform: translateY(-4px) scale(1.02) !important;
        border-color: #E53E3E !important;
        box-shadow: 0 0 15px rgba(229, 62, 62, 0.6), 0 0 25px rgba(229, 62, 62, 0.3) !important;
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
    
    div.stButton > button, 
    div.stFormSubmitButton > button,
    .stSidebar div.stButton > button {
        background-color: #E2E8F0 !important;
        color: #0F2A4A !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        padding: 8px 20px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    div.stButton > button:hover, 
    div.stFormSubmitButton > button:hover,
    .stSidebar div.stButton > button:hover {
        background-color: #FFFFFF !important;
        color: #C53030 !important;
        border-color: #E53E3E !important;
        box-shadow: 0 0 15px rgba(229, 62, 62, 0.6), 0 0 25px rgba(229, 62, 62, 0.3) !important;
        transform: translateY(-2px) scale(1.01) !important;
    }
    
    div.stButton > button:active, 
    div.stFormSubmitButton > button:active,
    .stSidebar div.stButton > button:active {
        transform: translateY(1px) scale(0.99) !important;
        box-shadow: 0 0 5px rgba(229, 62, 62, 0.4) !important;
    }
    
    .active-user-card {
        background: #FFFFFF;
        border-left: 4px solid #10B981;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        transition: all 0.3s ease;
    }
    .active-user-card:hover {
        transform: translateX(4px);
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }
    </style>
""",
    unsafe_allow_html=True,
)

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
    return "".join(secrets.choice(chars) for _ in range(length))

def send_credentials_email(recipient_email, recipient_name, temp_password, user_role="User"):
    sender_email = "lbidulsa.fo10@dswd.gov.ph"
    sender_password = "rkgqurmorpvfgktq"
    system_link = "https://pdbbmpamanacdpd.streamlit.app/"

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"DSWD FO X PAMANA CDPD System <{sender_email}>"
        msg["To"] = recipient_email
        msg["Subject"] = "🔒 Official Account Credentials - PAMANA CDPD Portal"

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
        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
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
        for idx, tag in ExifTags.TAGS.items():
            if tag == "GPSInfo":
                if idx not in exif:
                    return None, None
                for key, val in ExifTags.GPSTAGS.items():
                    if key in exif[idx]:
                        geotagging[val] = exif[idx][key]

        if not geotagging:
            return None, None

        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        lat = convert_to_degrees(geotagging["GPSLatitude"])
        if geotagging["GPSLatitudeRef"] != "N":
            lat = -lat

        lon = convert_to_degrees(geotagging["GPSLongitude"])
        if geotagging["GPSLongitudeRef"] != "E":
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

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE user_accounts ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;"))
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
                            {"email": login_email, "password": login_pass},
                        ).fetchone()

                    if res:
                        display_name = (
                            res[1] if (res[1] and str(res[1]).strip() != "" and str(res[1]).lower() != "none") else res[2]
                        )

                        st.session_state["logged_in"] = True
                        st.session_state["user_email"] = res[2]
                        st.session_state["user_role"] = res[4]
                        st.session_state["user_name"] = display_name
                        st.session_state["must_change_pass"] = bool(res[5])

                        try:
                            ph_now = get_ph_time()
                            with engine.begin() as conn_up:
                                conn_up.execute(text("UPDATE user_accounts SET last_login = :ll WHERE id = :uid"), {"ll": ph_now, "uid": res[0]})
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
                        {"email": reset_email.strip()},
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
                                    {"p": new_pass, "e": u_email},
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
                                {"p": new_p1, "e": st.session_state["user_email"]},
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

# 🌟 ALL_TABS INCLUDES THE SPI_MASTERLIST MODULE
ALL_TABS = [
    "Executive Dashboard", "User Management Portal", "CEAC_Municipal", "CEAC_Barangay",
    "Geotagged_Photos", "Disbursement", "Sub_Project_Closeout_Tracker", "SPI_Masterlist", "Summary", "Finance"
]

current_role = st.session_state.get("user_role", "AC")

if current_role == "Superuser":
    TABS = ALL_TABS
else:
    TABS = [tab for tab in ALL_TABS if tab != "User Management Portal"]

def can_edit_module(role, module):
    if role in ["Superuser", "Admin"]:
        return True
    elif role == "AC" and module in ["CEAC_Municipal", "CEAC_Barangay", "Sub_Project_Closeout_Tracker", "SPI_Masterlist"]:
        return True
    elif role == "TF" and module in ["Geotagged_Photos", "Sub_Project_Closeout_Tracker", "SPI_Masterlist"]:
        return True
    elif role == "MFA" and module == "Disbursement":
        return True
    elif role == "MDM" and module in ["CEAC_Municipal", "CEAC_Barangay"]:
        return True
    elif role == "CEF":
        return False  # CEF is strictly View-Only across all modules
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
                        {"e": st.session_state["user_email"]},
                    ).fetchone()
                if res_p and res_p[0] == old_p:
                    with engine.begin() as conn:
                        conn.execute(
                            text("UPDATE user_accounts SET password = :p, require_change_pass = 0 WHERE lower(email) = lower(:e)"),
                            {"p": new_p1, "e": st.session_state["user_email"]},
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
    unsafe_allow_html=True,
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
                x="Gender", y="Count", color="Gender", text_auto=",.0f",
                color_discrete_map={"Male": "#1F4E78", "Female": "#E06666"},
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

    USER_ROLES_LIST = ["Superuser", "Admin", "AC", "TF", "MFA", "MDM", "CEF"]

    st.markdown("##### 🔴 Live System User Login Activity & Audit Log:")

    with engine.connect() as conn:
        active_logs = conn.execute(text("SELECT id, full_name, email, user_role, last_login FROM user_accounts ORDER BY last_login DESC NULLS LAST")).fetchall()

    if active_logs:
        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            st.markdown("###### **Recently Active Users / Login Sessions:**")
            for u in active_logs[:5]:
                u_name = u[1] if (u[1] and str(u[1]).lower() != "none") else u[2]
                last_time = format_ph_time(u[4])
                is_curr = "🟢 CURRENT SESSION ONLINE" if u[2] == st.session_state["user_email"] else f"🕒 Last Online: {last_time}"

                st.markdown(
                    f"""
                    <div class="active-user-card">
                        <b>👤 {u_name}</b> (`{u[2]}`) &nbsp;|&nbsp; 
                        Role: <span class='role-badge'>{u[3]}</span> &nbsp;|&nbsp; 
                        <span style="color:#0284C7; font-weight:bold;">{is_curr}</span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

        with col_act2:
            st.info(f"📊 **Total Accounts:** `{len(active_logs)}` Users\n\n🛡️ **Superuser Privileges:** Live real-time login timestamp monitoring active (Asia/Manila PST).")

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
                                {"fn": new_fullname, "e": new_email, "p": curr_temp_pass, "r": new_role},
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
                        conn.execute(text("UPDATE user_accounts SET password = :p, require_change_pass = 1 WHERE id = :id"), {"p": new_temp, "id": r_id})

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
    if not df_users.empty:
        if "password" in df_users.columns:
            df_users = df_users.drop(columns=["password"])
        if "last_login" in df_users.columns:
            df_users["last_login"] = df_users["last_login"].apply(format_ph_time)
    st.dataframe(df_users, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 7. GEOTAGGED PHOTOS MODULE
# ---------------------------------------------------------
elif selected_view == "Geotagged_Photos":
    st.subheader("📸 Geotagged Photos & Progress File Uploads")

    if can_edit_module(current_role, "Geotagged_Photos"):
        with st.expander("📤 Upload New Geotagged Photo", expanded=True):
            uploaded_file = st.file_uploader("Choose Photo / File (JPG / PNG)", type=["jpg", "jpeg", "png", "pdf"], key="geo_upl_file")

            st.info("💡 **Note:** You can use timestamp photos/images to detect Latitude and Longitude.")

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
                        if location and "coords" in location:
                            detected_lat = str(round(location["coords"]["latitude"], 6))
                            detected_lon = str(round(location["coords"]["longitude"], 6))
                            st.info(f"🌐 **BROWSER LIVE GPS DETECTED:** Latitude: `{detected_lat}` | Longitude: `{detected_lon}`")

            with st.form("photo_upload_form", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    sp_id = st.text_input("Sub-Project ID / Code (Put 'N/A' if no SP ID)*")
                    sp_name = st.text_input("Sub-Project Name")
                    stage = st.selectbox("Stage", ["BEFORE Construction", "DURING Construction", "AFTER / Completed"])
                    latitude = st.text_input("Latitude (GPS)*", value=detected_lat)
                with col_u2:
                    longitude = st.text_input("Longitude (GPS)*", value=detected_lon)
                    st.caption("📷 File preview or auto-detected metadata will reflect automatically.")

                submit_photo = st.form_submit_button("⬆️ Submit & Save Photo")
                if submit_photo:
                    if not uploaded_file or not sp_id.strip():
                        st.error("⚠️ **REQUIRED FIELDS MISSING:** Palihug mag-upload og file ug isulat ang Sub-Project ID (o 'N/A')!")
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
                                        "encoder": st.session_state["user_name"],
                                    },
                                )

                            st.toast("✅ Geotagged photo saved to Supabase!", icon="📸")
                            st.success(f"Photo '{uploaded_file.name}' saved to database successfully!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"❌ DATABASE ERROR: {ex}")
    else:
        st.info(f"👁️ **VIEW-ONLY MODE:** Your assigned role (`{current_role}`) is restricted from uploading new photos in this module.")

    st.markdown("---")
    
    col_gal_hdr, col_gal_btn = st.columns([3, 1])
    with col_gal_hdr:
        st.subheader("🖼️ Geotagged Photos Gallery & Interactive Viewer")
    with col_gal_btn:
        if st.button("🔄 Refresh Photos / Reload Gallery", use_container_width=True, key="btn_refresh_photos"):
            st.cache_data.clear()
            st.toast("⚡ Gallery Refreshed!", icon="🔄")
            st.rerun()

    df_photos = load_db_table("geotagged_photos")

    if not df_photos.empty:
        sp_filter = st.text_input("🔍 Search Photo by Sub-Project ID, Name, or Stage:", "", key="photo_search_input")
        df_p_filtered = df_photos.copy()
        
        if sp_filter:
            mask = df_p_filtered.astype(str).apply(lambda row: row.str.contains(sp_filter, case=False).any(), axis=1)
            df_p_filtered = df_p_filtered[mask]

        if not df_p_filtered.empty:
            st.markdown("##### 📷 Uploaded Photos Cards Grid:")
            cols = st.columns(3)
            
            for idx, (_, row) in enumerate(df_p_filtered.iterrows()):
                col_target = cols[idx % 3]
                p_file_name = row.get("photo_file", "")
                p_path = os.path.join("uploaded_photos", str(p_file_name)) if p_file_name else ""

                with col_target:
                    st.markdown(f"**📌 {row.get('sp_name', 'Sub-Project')}**")
                    st.caption(f"🆔 **SP ID:** `{row.get('sp_id', 'N/A')}` | 🏗️ **Stage:** `{row.get('stage', 'N/A')}`")

                    rot_deg = st.selectbox(
                        f"🔄 Rotate Photo ({row.get('id', idx)})",
                        options=[0, 90, 180, 270],
                        format_func=lambda x: f"Original (0°)" if x == 0 else f"Rotate {x}°",
                        key=f"rot_{row.get('id', idx)}"
                    )

                    if p_path and os.path.exists(p_path):
                        try:
                            img_obj = Image.open(p_path)
                            if rot_deg > 0:
                                img_obj = img_obj.rotate(360 - rot_deg, expand=True)

                            st.image(img_obj, use_container_width=True, caption=f"📸 File: {p_file_name}")
                        except Exception:
                            st.warning(f"⚠️ Photo file '{p_file_name}' cannot be opened.")
                    else:
                        st.info(f"📁 File Name: `{p_file_name}`\n\n*(Local preview file not found in uploaded_photos directory)*")

                    st.markdown(f"📍 **GPS:** `{row.get('latitude', '')}, {row.get('longitude', '')}`")
                    st.caption(f"👤 Encoder: {row.get('encoder', 'N/A')} | 📅 Date: {row.get('date_uploaded', 'N/A')}")
                    st.markdown("---")
        else:
            st.info("No matching geotagged photo records found.")

        st.markdown("---")
        st.subheader("📋 Raw Geotagged Photos Database Masterlist")
        st.dataframe(df_photos, use_container_width=True)

        if current_role == "Superuser" and "id" in df_photos.columns:
            with st.expander("⚙️ Superuser Action Panel (Delete Photo Record)"):
                photo_ids = df_photos["id"].tolist()
                sel_pid = st.selectbox("Select Photo Record ID to Delete:", photo_ids, key="sel_pid_m")
                
                if st.button("🗑️ Delete Selected Photo Record", use_container_width=True, key="del_photo_btn"):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM geotagged_photos WHERE id = :id"), {"id": sel_pid})
                        st.toast("✅ Record deleted!", icon="🗑️")
                        st.success(f"Record ID {sel_pid} deleted successfully!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"❌ ERROR: {ex}")
    else:
        st.info("No geotagged photos uploaded yet.")

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
        <iframe src="{embed_url}" width="100%" height="750" style="border: 1px solid #CBD5E1; border-radius: 8px;" allowfullscreen></iframe>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# 9. SPI MASTERLIST MODULE (EXACT 74 HIGHLIGHTED COLUMNS)
# ---------------------------------------------------------
elif selected_view == "SPI_Masterlist":
    st.subheader("📊 SPI Masterlist Management Module")

    has_edit_perm = can_edit_module(current_role, "SPI_Masterlist")

    if has_edit_perm:
        if st.button("➕ Add New SPI Masterlist Record", use_container_width=True):
            st.session_state["show_add_spi"] = not st.session_state.get("show_add_spi", False)

        if st.session_state.get("show_add_spi", True):
            with st.expander("📝 Comprehensive Entry Form: SPI Masterlist (All Highlighted Fields Included)", expanded=True):
                with st.form("form_add_spi_masterlist"):
                    spi_data = {}

                    st.markdown("#### 1. Basic Sub-Project Profile & Category")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        spi_data["spid"] = st.text_input("Sub-Project ID (SPID)*", key="spi_spid")
                        spi_data["sp_title"] = st.text_input("Sub-Project Title*", key="spi_sptitle")
                        spi_data["major_category"] = st.text_input("Major Category", key="spi_majcat")
                    with c2:
                        spi_data["project_type"] = st.text_input("Project Type", key="spi_ptype")
                        spi_data["no_of_package"] = st.number_input("No. of Packages", min_value=0, step=1, key="spi_nopack")
                    with c3:
                        spi_data["total_awarded"] = st.number_input("Total Awarded (₱)", min_value=0.0, key="spi_taward")
                        spi_data["total_delivered"] = st.number_input("Total Delivered (₱)", min_value=0.0, key="spi_tdeliv")

                    st.markdown("---")
                    st.markdown("#### 2. Project Cost, Grants & Tranches")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        spi_data["kcgrant_amountmibf"] = st.number_input("KC Grant Amount MIBF (₱)", min_value=0.0, key="spi_kcg")
                        spi_data["lcc_amount_mibf"] = st.number_input("LCC Amount MIBF (₱)", min_value=0.0, key="spi_lcca")
                        spi_data["lcc_actual_amount"] = st.number_input("LCC Actual Amount (₱)", min_value=0.0, key="spi_lccact")
                        spi_data["operation_maintainance_cost"] = st.number_input("Operation & Maintenance Cost (₱)", min_value=0.0, key="spi_omc")
                    with c2:
                        spi_data["final_grant_amount_mibf"] = st.number_input("Final Grant Amount MIBF (₱)", min_value=0.0, key="spi_fgrant")
                        spi_data["final_lcc_amount_mibf"] = st.number_input("Final LCC Amount MIBF (₱)", min_value=0.0, key="spi_flcc")
                        spi_data["total_release"] = st.number_input("Total Release (₱)", min_value=0.0, key="spi_totrel")
                        spi_data["gross_utilization"] = st.number_input("Gross Utilization (₱)", min_value=0.0, key="spi_gutil")
                    with c3:
                        spi_data["first_tranche_actual_btf"] = st.number_input("1st Tranche BTF (₱)", min_value=0.0, key="spi_t1")
                        spi_data["date_downloaded_trans_1"] = st.date_input("1st Tranche Date", datetime.date.today(), key="spi_t1d").strftime("%Y-%m-%d")
                        spi_data["second_tranche_actual_btf"] = st.number_input("2nd Tranche BTF (₱)", min_value=0.0, key="spi_t2")
                        spi_data["date_downloaded_trans_2"] = st.date_input("2nd Tranche Date", datetime.date.today(), key="spi_t2d").strftime("%Y-%m-%d")
                        spi_data["third_tranche_actual_btf"] = st.number_input("3rd Tranche BTF (₱)", min_value=0.0, key="spi_t3")
                        spi_data["date_downloaded_trans_3"] = st.date_input("3rd Tranche Date", datetime.date.today(), key="spi_t3d").strftime("%Y-%m-%d")
                        spi_data["gross_liquidation"] = st.number_input("Gross Liquidation (₱)", min_value=0.0, key="spi_gliq")
                        spi_data["refunded"] = st.number_input("Refunded Amount (₱)", min_value=0.0, key="spi_ref")

                    st.markdown("---")
                    st.markdown("#### 3. Dates, Physical Accomplishment & Status")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        spi_data["date_started"] = st.date_input("Date Started", datetime.date.today(), key="spi_ds").strftime("%Y-%m-%d")
                        spi_data["date_of_completion"] = st.date_input("Date of Completion", datetime.date.today(), key="spi_dc").strftime("%Y-%m-%d")
                        spi_data["planned_date_of_completion"] = st.date_input("Planned Date of Completion", datetime.date.today(), key="spi_pdc").strftime("%Y-%m-%d")
                        spi_data["final_date_of_completion"] = st.date_input("Final Date of Completion", datetime.date.today(), key="spi_fdc").strftime("%Y-%m-%d")
                        spi_data["final_date_of_completion_v2"] = st.date_input("Final Date of Completion V2", datetime.date.today(), key="spi_fdcv2").strftime("%Y-%m-%d")
                    with c2:
                        spi_data["physical_accomplishment_percentage_original_pow"] = st.number_input("Physical Accomplishment % (Original POW)", min_value=0.0, max_value=100.0, key="spi_pa_pow")
                        spi_data["physical_status_original_pow"] = st.text_input("Physical Status (Original POW)", key="spi_ps_pow")
                        spi_data["physical_accomplishment_percentage_as_per_vo"] = st.number_input("Physical Accomplishment % (VO)", min_value=0.0, max_value=100.0, key="spi_pa_vo")
                        spi_data["date_of_completion_as_per_vo"] = st.date_input("Completion Date (per VO)", datetime.date.today(), key="spi_dc_vo").strftime("%Y-%m-%d")
                        spi_data["final_physical_status"] = st.selectbox("Final Physical Status", ["Completed", "On-going", "For Implementation", "Cancelled"], key="spi_fps")
                        spi_data["final_physical_accomplishment"] = st.number_input("Final Physical Accomplishment %", min_value=0.0, max_value=100.0, key="spi_fpa")
                    with c3:
                        # 🌟 CHECKBOXES FOR YES/NO FIELDS
                        spi_data["has_variation_order"] = "Yes" if st.checkbox("Has Variation Order?", key="spi_c_vo") else "No"
                        spi_data["has_booked"] = "Yes" if st.checkbox("Has Booked Asset?", key="spi_c_bk") else "No"
                        spi_data["booked_date"] = st.date_input("Booked Date", datetime.date.today(), key="spi_bd").strftime("%Y-%m-%d")
                        spi_data["closed_account"] = "Yes" if st.checkbox("Closed Bank Account?", key="spi_c_ca") else "No"

                    st.markdown("---")
                    st.markdown("#### 4. Complete Beneficiary Breakdown")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        spi_data["no_of_household_beneficiaries_target"] = st.number_input("Target HH Beneficiaries", min_value=0, step=1, key="spi_thh")
                        spi_data["no_of_ip_household_bene_target"] = st.number_input("Target IP HH Beneficiaries", min_value=0, step=1, key="spi_tip_hh")
                        spi_data["no_of_household_beneficiaries_actual"] = st.number_input("Actual HH Beneficiaries", min_value=0, step=1, key="spi_ahh")
                        spi_data["no_of_families_beneficiaries_target"] = st.number_input("Target Family Beneficiaries", min_value=0, step=1, key="spi_tfam")
                        spi_data["no_of_families_beneficiaries_actual"] = st.number_input("Actual Family Beneficiaries", min_value=0, step=1, key="spi_afam")
                    with c2:
                        spi_data["no_actual_pantawid_households"] = st.number_input("Actual Pantawid HHs", min_value=0, step=1, key="spi_pthh")
                        spi_data["no_actual_pantawid_families"] = st.number_input("Actual Pantawid Families", min_value=0, step=1, key="spi_ptfam")
                        spi_data["no_actual_slp_households"] = st.number_input("Actual SLP HHs", min_value=0, step=1, key="spi_slphh")
                        spi_data["no_actual_slp_families"] = st.number_input("Actual SLP Families", min_value=0, step=1, key="spi_slpfam")
                    with c3:
                        spi_data["no_actual_ip_households"] = st.number_input("Actual IP HHs", min_value=0, step=1, key="spi_ip_hh")
                        spi_data["no_actual_ip_families"] = st.number_input("Actual IP Families", min_value=0, step=1, key="spi_ip_fam")
                        spi_data["no_actual_male"] = st.number_input("Actual Male Beneficiaries", min_value=0, step=1, key="spi_mb")
                        spi_data["no_actual_female"] = st.number_input("Actual Female Beneficiaries", min_value=0, step=1, key="spi_fb")

                    st.markdown("---")
                    st.markdown("#### 5. Environmental & Social Safeguards and Land Acquisition (All Checkboxes)")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        spi_data["has_scanned_spcr"] = "Yes" if st.checkbox("Has Scanned SPCR?", key="spi_c_spcr") else "No"
                        spi_data["has_turnover_certificate"] = "Yes" if st.checkbox("Has Turnover Certificate?", key="spi_c_toc") else "No"
                        spi_data["with_ip_presence"] = "Yes" if st.checkbox("With IP Presence?", key="spi_c_ipp") else "No"
                        spi_data["with_esmp"] = "Yes" if st.checkbox("With ESMP?", key="spi_c_esmp") else "No"
                        spi_data["with_essc"] = "Yes" if st.checkbox("With ESSC?", key="spi_c_essc") else "No"
                        spi_data["with_cnc"] = "Yes" if st.checkbox("With CNC?", key="spi_c_cnc") else "No"
                        spi_data["with_cadt"] = "Yes" if st.checkbox("With CADT?", key="spi_c_cadt") else "No"
                        spi_data["with_ecc"] = "Yes" if st.checkbox("With ECC?", key="spi_c_ecc") else "No"
                        spi_data["on_process"] = "Yes" if st.checkbox("Safeguards On Process?", key="spi_c_proc") else "No"
                    with c2:
                        spi_data["land_acq_with_deed_of_donation"] = "Yes" if st.checkbox("Deed of Donation?", key="spi_c_dod") else "No"
                        spi_data["land_aq_with_unsfruct"] = "Yes" if st.checkbox("Usufruct Agreement?", key="spi_c_usu") else "No"
                        spi_data["land_acq_with_right_of_way_agreement"] = "Yes" if st.checkbox("Right of Way Agreement?", key="spi_c_row") else "No"
                        spi_data["land_acq_with_quit_claim"] = "Yes" if st.checkbox("Quit Claim?", key="spi_c_qc") else "No"
                        spi_data["land_acq_with_permit_to_construc_enter"] = "Yes" if st.checkbox("Permit to Construct / Enter?", key="spi_c_pce") else "No"
                        spi_data["land_acq_with_blgu_resolution"] = "Yes" if st.checkbox("BLGU Resolution?", key="spi_c_blgu") else "No"
                        spi_data["land_acq_with_deped_certification"] = "Yes" if st.checkbox("DepEd Certification?", key="spi_c_deped") else "No"
                        spi_data["land_acq_with_other_permit_clearance"] = "Yes" if st.checkbox("Other Permits / Clearances?", key="spi_c_operm") else "No"
                        spi_data["sps_with_land_acquisition_documents"] = "Yes" if st.checkbox("SPs with Land Acquisition Docs?", key="spi_c_ladoc") else "No"
                    with c3:
                        spi_data["submitted_request_validation_ncip_sps_with_ip_population"] = "Yes" if st.checkbox("Submitted Request Validation NCIP?", key="spi_c_ncip_req") else "No"
                        spi_data["validation_conducted_for_sps_with_ip_population"] = "Yes" if st.checkbox("Validation Conducted NCIP?", key="spi_c_ncip_val") else "No"
                        spi_data["with_cp_for_sps_with_ip_population"] = "Yes" if st.checkbox("With Certificate Precondition (CP)?", key="spi_c_cp") else "No"
                        spi_data["with_cno_for_sps_with_ip_population"] = "Yes" if st.checkbox("With Certificate of Non-Overlap (CNO)?", key="spi_c_cno") else "No"
                        spi_data["with_cp_or_with_cno_for_sps_with_ip_population"] = "Yes" if st.checkbox("With CP or CNO?", key="spi_c_cpcno") else "No"
                        spi_data["created_date"] = datetime.date.today().strftime("%Y-%m-%d")
                        spi_data["created_by"] = st.session_state["user_name"]

                    st.markdown("---")
                    save_spi_btn = st.form_submit_button("💾 Save Full SPI Record to Database", use_container_width=True)

                    if save_spi_btn:
                        if not spi_data.get("spid") or not spi_data.get("sp_title"):
                            st.error("⚠️ **REQUIRED FIELDS MISSING:** Palihug sulati ang Sub-Project ID (SPID) ug Sub-Project Title!")
                        else:
                            col_names_str = ", ".join(spi_data.keys())
                            placeholders = ", ".join([f":{k}" for k in spi_data.keys()])
                            try:
                                with engine.begin() as conn:
                                    conn.execute(
                                        text(f"INSERT INTO spi_masterlist ({col_names_str}) VALUES ({placeholders})"),
                                        spi_data,
                                    )
                                st.toast("✅ Full SPI Masterlist record saved to Supabase!", icon="🎉")
                                st.success("Record saved successfully!")
                                st.session_state["show_add_spi"] = False
                                st.rerun()
                            except Exception as ex:
                                st.error(f"❌ DATABASE ERROR: {ex}")
    else:
        st.info(f"👁️ **VIEW-ONLY MODE:** Your assigned role (`{current_role}`) is restricted from adding or editing records in SPI Masterlist.")

    st.markdown("---")
    st.subheader("📊 SPI Masterlist Master Database Table")

    df_spi = load_db_table("spi_masterlist")
    search_spi = st.text_input("🔍 Search SPI Masterlist Records:", "", key="spi_search_kw")
    df_spi_filtered = df_spi.copy()

    if search_spi and not df_spi_filtered.empty:
        mask = df_spi_filtered.astype(str).apply(lambda row: row.str.contains(search_spi, case=False).any(), axis=1)
        df_spi_filtered = df_spi_filtered[mask]

    if not df_spi_filtered.empty:
        can_sync_spi = (current_role in ["Superuser", "Admin"]) or has_edit_perm

        edited_spi_df = st.data_editor(
            df_spi_filtered,
            use_container_width=True,
            num_rows="dynamic" if can_sync_spi else "fixed",
            disabled=not can_sync_spi,
            key="editor_spi_masterlist",
        )

        if can_sync_spi and st.button("💾 Sync SPI Table Changes to Database", key="sync_btn_spi"):
            try:
                with engine.begin() as conn:
                    edited_spi_df.to_sql("spi_masterlist", conn, if_exists="replace", index=False)
                st.toast("✅ SPI Table synchronized to Supabase!", icon="🎉")
                st.success("Database synchronized successfully!")
                st.rerun()
            except Exception as ex:
                st.error(f"❌ DATABASE ERROR: {ex}")

        # 👑 SUPERUSER ACTION PANEL (EDIT / DELETE ROW)
        if current_role == "Superuser" and "id" in df_spi_filtered.columns:
            st.markdown("---")
            with st.expander("⚙️ Superuser Record Action Panel (Edit / Delete Row in SPI Masterlist)"):
                row_ids = df_spi_filtered["id"].tolist()
                selected_row_id = st.selectbox("Select Row ID to Edit or Delete:", row_ids, key="sel_id_spi_masterlist")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("✏️ Edit Selected Record", use_container_width=True, key="btn_edit_spi_masterlist"):
                        st.session_state["editing_id_spi_masterlist"] = selected_row_id

                with col_btn2:
                    if st.button("🗑️ Delete Selected Record", use_container_width=True, key="btn_del_spi_masterlist"):
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM spi_masterlist WHERE id = :id"), {"id": selected_row_id})
                            st.toast("✅ Record deleted from Supabase!", icon="🗑️")
                            st.success(f"Record ID {selected_row_id} deleted successfully!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"❌ DATABASE ERROR: {ex}")

                if st.session_state.get("editing_id_spi_masterlist") == selected_row_id:
                    st.markdown(f"##### 📝 Editing Record ID: `{selected_row_id}`")
                    row_data = df_spi_filtered[df_spi_filtered["id"] == selected_row_id].iloc[0].to_dict()

                    with st.form(f"form_edit_spi_{selected_row_id}"):
                        updated_vals = {}
                        col_e1, col_e2 = st.columns(2)
                        keys = [k for k in row_data.keys() if k != "id"]

                        for idx, k in enumerate(keys):
                            val = row_data[k]
                            target_col = col_e1 if idx % 2 == 0 else col_e2
                            if isinstance(val, (int, float)) and not pd.isna(val):
                                updated_vals[k] = target_col.number_input(f"{k}", value=float(val))
                            else:
                                updated_vals[k] = target_col.text_input(f"{k}", value=str(val) if not pd.isna(val) else "")

                        save_edit_btn = st.form_submit_button("💾 Save Updated Record Changes", use_container_width=True)
                        if save_edit_btn:
                            try:
                                set_clause = ", ".join([f"{k} = :{k}" for k in updated_vals.keys()])
                                updated_vals["id"] = selected_row_id

                                with engine.begin() as conn:
                                    conn.execute(text(f"UPDATE spi_masterlist SET {set_clause} WHERE id = :id"), updated_vals)

                                st.toast("✅ Record updated successfully!", icon="💾")
                                st.success(f"Record ID {selected_row_id} updated!")
                                st.session_state["editing_id_spi_masterlist"] = None
                                st.rerun()
                            except Exception as ex:
                                st.error(f"❌ DATABASE ERROR: {ex}")
    else:
        st.info("No records found in SPI Masterlist.")

# ---------------------------------------------------------
# 10. CEAC MUNICIPAL, BARANGAY, DISBURSEMENT & CLOSEOUT TRACKER MODULES
# ---------------------------------------------------------
else:
    st.subheader(f"📋 Data Management & Encoding: {selected_view}")

    has_edit_perm = can_edit_module(current_role, selected_view)

    if has_edit_perm:
        if st.button("➕ Add New Activity / Record", use_container_width=True):
            st.session_state["show_add_form"] = not st.session_state.get("show_add_form", False)

        if st.session_state.get("show_add_form", True):
            with st.expander(f"📝 Comprehensive Entry Form: {selected_view}", expanded=True):

                if selected_view == "CEAC_Municipal":
                    col_left, col_right = st.columns(2)
                    with col_left:
                        selected_m_act = st.selectbox("Select Municipal Activity", (MUNICIPALITIES if selected_view == "Summary" else MUNICIPAL_ACTIVITIES), key="cm_act")
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
                                        "lgu": lgu_saved, "grs": grs_saved, "rem": cm_remarks,
                                    },
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
                                            "bmin": brgy_min_saved, "lgu": lgu_saved, "cv": cv_saved, "rem": cb_remarks,
                                        },
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
                                form_data["sp_id"] = st.text_input("Sub-Project ID / Code (Put 'N/A' if no SP ID)*", key="sp_id_in")
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
                                form_data["sp_id"] = st.text_input("Sub-Project ID / Code (Put 'N/A' if no SP ID)*", key="d_spid")
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
                                st.error("⚠️ **REQUIRED FIELDS MISSING:** Palihug sulati ang Sub-Project ID (o 'N/A') ug Sub-Project Name!")
                                valid = False
                            elif selected_view == "Disbursement" and (not form_data.get("sp_id") or not form_data.get("dv_number")):
                                st.error("⚠️ **REQUIRED FIELDS MISSING:** Palihug sulati ang Sub-Project ID (o 'N/A') ug DV Number!")
                                valid = False

                            if valid:
                                table_low = selected_view.lower()
                                col_names_str = ", ".join(form_data.keys())
                                placeholders = ", ".join([f":{k}" for k in form_data.keys()])

                                try:
                                    with engine.begin() as conn:
                                        conn.execute(
                                            text(f"INSERT INTO {table_low} ({col_names_str}) VALUES ({placeholders})"),
                                            form_data,
                                        )

                                        if selected_view == "Disbursement":
                                            d_mun = form_data.get("municipality")
                                            d_amt = form_data.get("amount", 0.0)

                                            if d_mun:
                                                sum_res = conn.execute(
                                                    text("SELECT total_disbursed, total_liquidated FROM summary WHERE lower(municipality) = lower(:m)"),
                                                    {"m": d_mun},
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
                                                        {"td": curr_disb, "ub": new_unliq, "m": d_mun},
                                                    )
                                                else:
                                                    conn.execute(
                                                        text("""
                                                            INSERT INTO summary (municipality, total_sps, total_grant, total_disbursed, total_liquidated, unliquidated_balance)
                                                            VALUES (:m, 1, :td, :td, 0.0, :td)
                                                        """),
                                                        {"m": d_mun, "td": float(d_amt)},
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
        can_sync_table = (current_role in ["Superuser", "Admin"]) or has_edit_perm

        edited_df = st.data_editor(
            df_filtered,
            use_container_width=True,
            num_rows="dynamic" if can_sync_table else "fixed",
            disabled=not can_sync_table,
            key=f"editor_{selected_view}",
        )
        if can_sync_table and st.button("💾 Sync Table Changes to Database", key=f"sync_btn_{selected_view}"):
            table_low = selected_view.lower()
            try:
                with engine.begin() as conn:
                    edited_df.to_sql(table_low, conn, if_exists="replace", index=False)
                st.toast("✅ Table changes synchronized to Supabase!", icon="🎉")
                st.success("Database synchronized successfully!")
                st.rerun()
            except Exception as ex:
                st.error(f"❌ DATABASE ERROR: {ex}")

        # 👑 SUPERUSER ACTION PANEL
        if current_role == "Superuser" and "id" in df_filtered.columns:
            st.markdown("---")
            with st.expander(f"⚙️ Superuser Record Action Panel (Edit / Delete Row in {selected_view})"):
                row_ids = df_filtered["id"].tolist()
                selected_row_id = st.selectbox("Select Row ID to Edit or Delete:", row_ids, key=f"sel_id_{selected_view}")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("✏️ Edit Selected Record", use_container_width=True, key=f"btn_edit_{selected_view}"):
                        st.session_state[f"editing_id_{selected_view}"] = selected_row_id
                
                with col_btn2:
                    if st.button("🗑️ Delete Selected Record", use_container_width=True, key=f"btn_del_{selected_view}"):
                        try:
                            table_low = selected_view.lower()
                            with engine.begin() as conn:
                                conn.execute(text(f"DELETE FROM {table_low} WHERE id = :id"), {"id": selected_row_id})
                            st.toast("✅ Record deleted from Supabase!", icon="🗑️")
                            st.success(f"Record ID {selected_row_id} deleted successfully!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"❌ DATABASE ERROR: {ex}")

                if st.session_state.get(f"editing_id_{selected_view}") == selected_row_id:
                    st.markdown(f"##### 📝 Editing Record ID: `{selected_row_id}`")
                    row_data = df_filtered[df_filtered["id"] == selected_row_id].iloc[0].to_dict()
                    
                    with st.form(f"form_edit_row_{selected_view}_{selected_row_id}"):
                        updated_vals = {}
                        col_e1, col_e2 = st.columns(2)
                        keys = [k for k in row_data.keys() if k != "id"]
                        
                        for idx, k in enumerate(keys):
                            val = row_data[k]
                            target_col = col_e1 if idx % 2 == 0 else col_e2
                            if isinstance(val, (int, float)) and not pd.isna(val):
                                updated_vals[k] = target_col.number_input(f"{k}", value=float(val))
                            else:
                                updated_vals[k] = target_col.text_input(f"{k}", value=str(val) if not pd.isna(val) else "")
                        
                        save_edit_btn = st.form_submit_button("💾 Save Updated Record Changes", use_container_width=True)
                        if save_edit_btn:
                            try:
                                set_clause = ", ".join([f"{k} = :{k}" for k in updated_vals.keys()])
                                updated_vals["id"] = selected_row_id
                                table_low = selected_view.lower()
                                
                                with engine.begin() as conn:
                                    conn.execute(text(f"UPDATE {table_low} SET {set_clause} WHERE id = :id"), updated_vals)
                                
                                st.toast("✅ Record updated successfully!", icon="💾")
                                st.success(f"Record ID {selected_row_id} updated!")
                                st.session_state[f"editing_id_{selected_view}"] = None
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
    unsafe_allow_html=True,
)
