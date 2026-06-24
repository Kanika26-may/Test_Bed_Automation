import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from ui_common import configure_app_shell, PLAN_LIFECYCLE_MODULE_MAP
from term_plan_ui import render_term_plan_ui
from saving_plan_ui import render_saving_plan_ui
from ulip_plan_ui import render_ulip_plan_ui


def main ():
    configure_app_shell()

    # Logout button at top right
    st.markdown(
        """
        <style>
        .logout-btn-container {
            position: fixed;
            top: 0.6rem;
            right: 1rem;
            z-index: 999999;
        }
        .logout-btn-container button {
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 0.3rem 0.8rem;
            border-radius: 6px;
            font-size: 0.85rem;
            cursor: pointer;
            font-weight: 600;
        }
        .logout-btn-container button:hover {
            background-color: #c0392b;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        _, col_logout = st.columns([9, 1])
        with col_logout:
            if st.button("Logout", key="logout_btn", type="primary"):
                st.session_state["logged_in"] = False
                st.rerun()

    if "app_selected_plan_type" not in st.session_state:
        st.session_state["app_selected_plan_type"] = "term plan"
    if "app_last_plan_type" not in st.session_state:
        st.session_state["app_last_plan_type"] = st.session_state["app_selected_plan_type"]

    with st.sidebar:
        st.header("Plan Selection")
        selected_plan_type = st.selectbox(
            "Plan Type",
            options=list(PLAN_LIFECYCLE_MODULE_MAP.keys()),
            key="app_selected_plan_type",
        )

    if selected_plan_type != st.session_state.get("app_last_plan_type"):
        reset_keys = [
            "generated_df",
            "selected_module_name_py",
            "selected_display_name",
            "processing",
            "epic_counts_to_generate",
            "epic_counts_to_generate_rider",
            "config_loaded",
            "selected_lifecycle_for_output",
            "post_issuance_selected_header",
            "product_display_name_input",
            "product_code_input",
            "count_mode_selector",
            "lifecycle_to_generate",
        ]
        for key in reset_keys:
            st.session_state.pop(key, None)
        st.session_state["app_last_plan_type"] = selected_plan_type

    if selected_plan_type == "term plan":
        render_term_plan_ui()
    elif selected_plan_type == "saving plan":
        render_saving_plan_ui()
    elif selected_plan_type == "ulip plan":
        render_ulip_plan_ui()
    else:
        st.error("Unknown plan type. Please select a valid plan.")


def _get_login_records():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["login_spreadsheet_id"]).worksheet("login")
    return sheet.get_all_records()


def _log_login_activity(username, emp_id):
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["login_spreadsheet_id"]).worksheet("login_activity")
    # row count includes header, so next login_id = number of existing rows (header + data rows so far)
    login_id = len(sheet.get_all_values())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([login_id, username, emp_id, timestamp])


def login():
    st.set_page_config(
        page_title="Test Data Generator",
        page_icon="bl_logo.png",
        layout="centered",
    )
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            records = _get_login_records()
            valid = any(
                str(r.get("username", "")).strip() == username.strip()
                and str(r.get("password", "")).strip() == password.strip()
                for r in records
            )
            if valid:
                emp_id = next((str(r.get("emp_id", "")) for r in records if str(r.get("username", "")).strip() == username.strip()), "")
                _log_login_activity(username.strip(), emp_id)
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Invalid username or password")
        except Exception as e:
            st.error(f"Login error ({type(e).__name__}): {repr(e)}")

if __name__=="__main__":
    if not st.session_state.get("logged_in"):
        login()
    else:
        main()