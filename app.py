import base64
import datetime
import io
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
# BASE64 CONVERT HELPER FOR PERMANENT IMAGE STORAGE
# ---------------------------------------------------------
def convert_image_to_base64(uploaded_file):
    """Converts uploaded photo directly to Base64 string for database storage"""
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
        return f"data:{uploaded_file.type};base64,{base64_encoded}"
    return ""

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
    chars = string.ascii_letters + string.digits + "@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))

def send_credentials_email(recipient_email, recipient_name, temp_password, user_role="User"):
    sender_email = st.secrets.get("EMAIL_SENDER", "lbidulsa.fo10@dswd.gov.ph")
    sender_password = st.secrets.get("EMAIL_PASSWORD", "rkgqurmorpvfgktq")
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
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300
    )

engine = get_db_engine()

def load_db_table(table_name):
    try:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", engine)
    except Exception:
        return pd.DataFrame()

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE user_accounts ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;"))
        conn.execute(text("ALTER TABLE geotagged_photos ADD COLUMN IF NOT EXISTS image_base64 TEXT;"))
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
                login_pass = st.text_input("Password", type="password").strip()
                submit = st.form_submit_button("🔑 Login to Dashboard", use_container_width=True)

                if submit:
                    with engine.connect() as conn:
                        res = conn.execute(
                            text("SELECT id, full_name, email, password, user_role, require_change_pass FROM user_accounts WHERE lower(trim(email)) = lower(trim(:email)) AND trim(password) = trim(:password)"),
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

ALL_TABS = [
    "Executive Dashboard", "User Management Portal", "CEAC_Municipal", "CEAC_Barangay",
    "Geotagged_Photos", "Disbursement", "Sub_Project_Closeout_Tracker", "SP_Profile", "Summary", "Finance",
    "Data Extraction & Export"
]

current_role = st.session_state.get("user_role", "AC")

if current_role == "Superuser":
    TABS = ALL_TABS
else:
    TABS = [tab for tab in ALL_TABS if tab != "User Management Portal"]

def can_edit_module(role, module):
    if role in ["Superuser", "Admin"]:
        return True
    elif role == "AC" and module in ["CEAC_Municipal", "CEAC_Barangay", "Sub_Project_Closeout_Tracker", "SP_Profile"]:
        return True
    elif role == "TF" and module in ["Geotagged_Photos", "Sub_Project_Closeout_Tracker", "SP_Profile"]:
        return True
    elif role == "MFA" and module == "Disbursement":
        return True
    elif role == "MDM" and module in ["CEAC_Municipal", "CEAC_Barangay"]:
        return True
    elif role == "CEF":
        return False
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

col_side_btn1, col_side_btn2 = st.sidebar.columns(2)
with col_side_btn1:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.toast("🔄 System cache refreshed successfully!", icon="✨")
        st.rerun()
with col_side_btn2:
    if st.button("🚪 Logout", use_container_width=True):
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
# 6. USER MANAGEMENT PORTAL (SUPERUSER ONLY - ALL ACCOUNTS INCLUDED)
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

    @st.cache_data(ttl=10)
    def fetch_users_fast():
        with engine.connect() as conn:
            return conn.execute(
                text("SELECT id, full_name, email, user_role, last_login FROM user_accounts ORDER BY last_login DESC NULLS LAST LIMIT 50")
            ).fetchall()

    try:
        active_logs = fetch_users_fast()
    except Exception:
        active_logs = []

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

            st.markdown("---")
            st.markdown("##### ✏️ Direct Set Custom Password (Manual Fix)")
            manual_custom_pass = st.text_input("Enter Manual Password for Selected User:", key="man_pass_in").strip()
            if st.button("💾 Set Exact Custom Password", use_container_width=True, key="btn_set_man_pass"):
                if manual_custom_pass:
                    r_id, r_email, r_name, r_role = u_dict[selected_reset]
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE user_accounts SET password = trim(:p), require_change_pass = 0 WHERE id = :id"), {"p": manual_custom_pass, "id": r_id})
                        st.toast("✅ Custom password updated!", icon="🔑")
                        st.success(f"✅ Password for {r_email} manually set to: `{manual_custom_pass}`! (Direct Login Enabled)")
                    except Exception as ex:
                        st.error(f"❌ DATABASE ERROR: {ex}")
                else:
                    st.error("Palihug sulati ang manual password.")
        else:
            st.info("No matching users found.")

    st.markdown("---")
    st.subheader("📋 Registered Users Masterlist & Login Timestamps")
    
    try:
        df_users = pd.read_sql_query(
            text("SELECT id, full_name, email, user_role, require_change_pass, last_login FROM user_accounts ORDER BY id DESC"),
            engine
        )
        if not df_users.empty and "last_login" in df_users.columns:
            df_users["last_login"] = df_users["last_login"].apply(format_ph_time)
        st.dataframe(df_users, use_container_width=True, hide_index=True)

        st.markdown("---")
        with st.expander("⚙️ Superuser Action Panel (Delete / Remove User Account)"):
            u_del_list = df_users[df_users["user_role"] != "Superuser"]["id"].tolist() if "id" in df_users.columns else []
            if u_del_list:
                sel_del_uid = st.selectbox("Select User ID to Delete from Database:", u_del_list, key="sel_del_uid_box")
                u_info_row = df_users[df_users["id"] == sel_del_uid].iloc[0]
                st.warning(f"⚠️ Imong idelete si **{u_info_row.get('full_name', '')}** (`{u_info_row.get('email', '')}`).")
                if st.button("🗑️ Permanently Delete User Account", use_container_width=True, key="btn_del_user_acct"):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM user_accounts WHERE id = :id"), {"id": sel_del_uid})
                        st.cache_data.clear()
                        st.toast("✅ User account removed from database!", icon="🗑️")
                        st.success("User account deleted successfully!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"❌ DATABASE ERROR: {ex}")
            else:
                st.info("No deletable user accounts found.")
    except Exception:
        pass
