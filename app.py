import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from ui_common import configure_app_shell, PLAN_LIFECYCLE_MODULE_MAP, ULIP_VARIANTS
from term_plan_ui import render_term_plan_ui
from saving_plan_ui import render_saving_plan_ui
from ulip_plan_ui import render_ulip_plan_ui


def main ():
    configure_app_shell()

    if "app_selected_plan_type" not in st.session_state:
        st.session_state["app_selected_plan_type"] = "term plan"
    if "app_last_plan_type" not in st.session_state:
        st.session_state["app_last_plan_type"] = st.session_state["app_selected_plan_type"]

    with st.sidebar:
        # Logout sits at the very top of the sidebar.
        if st.button(
            "Logout", key="logout_btn", type="primary", use_container_width=True
        ):
            st.session_state["logged_in"] = False
            st.rerun()

        st.header("Plan Selection")
        selected_plan_type = st.selectbox(
            "Plan Type",
            options=list(PLAN_LIFECYCLE_MODULE_MAP.keys()),
            key="app_selected_plan_type",
        )
        if selected_plan_type == "ulip plan":
            st.selectbox(
                "Product Variant",
                options=ULIP_VARIANTS,
                key="ulip_variant_selector",
            )

    # A variant switch changes the logic module, so treat it like a plan change
    # and clear the epic/config state built for the previous variant.
    selected_ulip_variant = st.session_state.get("ulip_variant_selector")
    variant_changed = selected_ulip_variant != st.session_state.get(
        "app_last_ulip_variant"
    )
    st.session_state["app_last_ulip_variant"] = selected_ulip_variant

    if selected_plan_type != st.session_state.get("app_last_plan_type") or variant_changed:
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
    return login_id


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
                login_id = _log_login_activity(username.strip(), emp_id)
                # Keep these in session_state so later actions (e.g. Generate Test Cases)
                # can log activity tagged with the same login_id for this session.
                st.session_state["login_id"] = login_id
                st.session_state["username"] = username.strip()
                st.session_state["emp_id"] = emp_id
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