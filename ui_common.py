import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import os
import importlib.util
import json
from logic_modules.term_plan_post_issuance import get_post_issuance_epics_for_plan
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import xlsxwriter

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIC_MODULE_DIR = os.path.join(APP_DIR, "logic_modules")
LIFECYCLE_OPTIONS = ["pre issuance", "issuance", "post issuance"]
LIFECYCLE_PREFIX_MAP = {
    "pre issuance": "pre_issuance",
    "issuance": "issuance",
    "post issuance": "post_issuance",
}

PLAN_LIFECYCLE_MODULE_MAP = {
    "term plan": {
        "pre issuance": "term_plan_pre_issuance",
        "issuance": "term_plan_issuance",
        "post issuance": "term_plan_post_issuance",
    },
    "saving plan": {
        "pre issuance": "saving_plan_pre_issuance",
        "issuance": "saving_plan_issuance",
        "post issuance": "saving_plan_post_issuance",
    },
    "ulip plan": {
        "pre issuance": "ulip_plan_pre_issuance",
        "issuance": "ulip_plan_issuance",
        "post issuance": "ulip_plan_post_issuance",
    },
}

# Google Sheets Configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def configure_app_shell():
    st.set_page_config(
        page_title="Test Data Generator",
        page_icon="bl_logo.png",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_app_header():
    # Hide Streamlit's default menu and footer
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Inject custom CSS
    st.markdown(
        """
        <style>
        .custom-title {
            font-size:40px !important;
            font-weight: bold;
            color: #2E86C1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    title = "\U00002699\ufe0f Product Rule Validation Test Data Generator"
    st.markdown(f'<h1 class="custom-title">{title}</h1>', unsafe_allow_html=True)


def get_google_sheets_service():
    """Initialize Google Sheets API service using Streamlit secrets"""
    try:
        # Load credentials from Streamlit secrets
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES,
        )
        service = build("sheets", "v4", credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Error initializing Google Sheets API: {e}")
        st.info("Please configure Google Sheets credentials in Streamlit secrets.")
        return None


def get_or_create_spreadsheet():
    """Get spreadsheet ID from secrets or create new one"""
    try:
        # Check if spreadsheet ID exists in secrets
        if "spreadsheet_id" in st.secrets:
            return st.secrets["spreadsheet_id"]
        st.warning("\u26a0\ufe0f No spreadsheet_id found in secrets. Please add it to .streamlit/secrets.toml")
        st.info("Create a Google Sheet and add its ID to secrets.toml")
        return None
    except Exception as e:
        st.error(f"Error getting spreadsheet ID: {e}")
        return None


def init_google_sheets():
    """Initialize Google Sheets with headers if needed"""
    try:
        service = get_google_sheets_service()
        if not service:
            return False

        spreadsheet_id = get_or_create_spreadsheet()
        if not spreadsheet_id:
            return False

        sheet = service.spreadsheets()

        # Try to read the sheet to check if it exists
        try:
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range="Configurations!A1:D1",
            ).execute()

            # If sheet exists but no headers, add them
            if not result.get("values"):
                headers = [["config_name", "config_data", "created_at", "updated_at"]]
                sheet.values().update(
                    spreadsheetId=spreadsheet_id,
                    range="Configurations!A1:D1",
                    valueInputOption="RAW",
                    body={"values": headers},
                ).execute()
        except HttpError:
            # Sheet doesn't exist, create it
            body = {
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": "Configurations",
                                "gridProperties": {"frozenRowCount": 1},
                            }
                        }
                    }
                ]
            }
            sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

            # Add headers
            headers = [["config_name", "config_data", "created_at", "updated_at"]]
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range="Configurations!A1:D1",
                valueInputOption="RAW",
                body={"values": headers},
            ).execute()

        return True
    except Exception as e:
        st.error(f"Error initializing Google Sheets: {e}")
        return False


# --- Configuration Management Functions ---

def save_configuration(config_name, config_data):
    """Save configuration to Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return False

        spreadsheet_id = get_or_create_spreadsheet()
        if not spreadsheet_id:
            return False

        sheet = service.spreadsheets()

        # Get all existing configurations
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range="Configurations!A2:D",
        ).execute()

        values = result.get("values", [])
        config_json = json.dumps(config_data)
        timestamp = datetime.now().isoformat()

        # Check if configuration already exists
        row_index = None
        for i, row in enumerate(values):
            if row and row[0] == config_name:
                row_index = i + 2  # +2 because of header row and 0-indexing
                break

        if row_index:
            # Update existing configuration
            range_name = f"Configurations!A{row_index}:D{row_index}"
            new_values = [
                [
                    config_name,
                    config_json,
                    row[2] if len(row) > 2 else timestamp,
                    timestamp,
                ]
            ]
        else:
            # Add new configuration
            range_name = f"Configurations!A{len(values) + 2}:D{len(values) + 2}"
            new_values = [[config_name, config_json, timestamp, timestamp]]

        sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body={"values": new_values},
        ).execute()

        return True
    except Exception as e:
        st.error(f"Error saving configuration: {e}")
        return False


def load_configuration(config_name):
    """Load configuration from Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return None

        spreadsheet_id = get_or_create_spreadsheet()
        if not spreadsheet_id:
            return None

        sheet = service.spreadsheets()

        # Get all configurations
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range="Configurations!A2:D",
        ).execute()

        values = result.get("values", [])

        # Find the configuration
        for row in values:
            if row and row[0] == config_name:
                return json.loads(row[1])

        return None
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        return None


def get_saved_configurations():
    """Get list of saved configuration names from Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return []

        spreadsheet_id = get_or_create_spreadsheet()
        if not spreadsheet_id:
            return []

        sheet = service.spreadsheets()

        # Get all configuration names
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range="Configurations!A2:A",
        ).execute()

        values = result.get("values", [])
        configs = [row[0] for row in values if row]

        return sorted(configs)
    except Exception as e:
        st.error(f"Error getting configurations: {e}")
        return []


def delete_configuration(config_name):
    """Delete a saved configuration from Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return False

        spreadsheet_id = get_or_create_spreadsheet()
        if not spreadsheet_id:
            return False

        sheet = service.spreadsheets()

        # Get all configurations
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range="Configurations!A2:D",
        ).execute()

        values = result.get("values", [])

        # Find the row to delete
        row_index = None
        for i, row in enumerate(values):
            if row and row[0] == config_name:
                row_index = i + 2  # +2 because of header row and 0-indexing
                break

        if row_index:
            # Delete the row
            body = {
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": 0,  # Assuming first sheet
                                "dimension": "ROWS",
                                "startIndex": row_index - 1,
                                "endIndex": row_index,
                            }
                        }
                    }
                ]
            }
            sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
            return True

        return False
    except Exception as e:
        st.error(f"Error deleting configuration: {e}")
        return False


def export_all_configurations():
    """Export all configurations as a JSON file for backup"""
    try:
        service = get_google_sheets_service()
        if not service:
            return None

        spreadsheet_id = get_or_create_spreadsheet()
        if not spreadsheet_id:
            return None

        sheet = service.spreadsheets()

        # Get all configurations
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range="Configurations!A2:D",
        ).execute()

        values = result.get("values", [])
        all_configs = {}

        for row in values:
            if row and len(row) >= 2:
                all_configs[row[0]] = json.loads(row[1])

        return json.dumps(all_configs, indent=2)
    except Exception as e:
        st.error(f"Error exporting configurations: {e}")
        return None


def import_configurations(json_data):
    """Import configurations from JSON backup to Google Sheets"""
    try:
        configs = json.loads(json_data)
        success_count = 0

        for config_name, config_data in configs.items():
            if save_configuration(config_name, config_data):
                success_count += 1

        return success_count > 0
    except Exception as e:
        st.error(f"Error importing configurations: {e}")
        return False


def get_scoped_config_name(config_name, plan_name):
    return f"{plan_name}::{config_name}"


def strip_scoped_config_name(scoped_name, plan_name):
    prefix = f"{plan_name}::"
    if scoped_name.startswith(prefix):
        return scoped_name[len(prefix):]
    return scoped_name


def collect_current_config():
    """Collect current UI state into a configuration dictionary"""
    config = {
        "product_display_name": st.session_state.get("product_display_name_input", ""),
        "product_code": st.session_state.get("product_code_input", ""),
        "count_mode": st.session_state.get(
            "count_mode_selector", "Apply Same Count to All Epics"
        ),
        "selected_plan_type": st.session_state.get("plan_type_selector", "term plan"),
        "lifecycle_to_generate": st.session_state.get(
            "lifecycle_to_generate", "pre issuance"
        ),
        "ui_state": {},
    }

    # Collect all relevant session state keys
    key_fragments = [
        "epic_cb_",
        "epic_pos_",
        "epic_neg_",
        "ppt_enabled_",
        "portfolio_type_",
        "entry_age_slider_",
        "maturity_age_slider_",
        "freq_cb_",
        "sa_enabled_",
        "min_sp_",
        "max_sp_",
        "pos_sp_",
        "neg_sp_",
        "min_oth_",
        "max_oth_",
        "pos_oth_",
        "neg_oth_",
        "select_all_epics_master",
        "post_header_",
        "post_epic_cb_",
        "post_epic_pos_",
        "post_cfg_",
        "post_select_all_",
    ]
    for key, value in st.session_state.items():
        if any(fragment in key for fragment in key_fragments):
            # Convert non-serializable types
            if isinstance(value, (int, float, str, bool, list, dict, type(None))):
                config["ui_state"][key] = value
            elif isinstance(value, tuple):
                config["ui_state"][key] = list(value)

    return config


def apply_config_to_ui(config):
    """Apply saved configuration to UI state"""
    # Apply product info
    if "product_display_name" in config:
        st.session_state["product_display_name_input"] = config["product_display_name"]
    if "product_code" in config:
        st.session_state["product_code_input"] = config["product_code"]
    if "count_mode" in config:
        st.session_state["count_mode_selector"] = config["count_mode"]
    if "selected_plan_type" in config:
        st.session_state["plan_type_selector"] = config["selected_plan_type"]
    if "lifecycle_to_generate" in config:
        st.session_state["lifecycle_to_generate"] = config["lifecycle_to_generate"]

    # Apply UI state
    if "ui_state" in config:
        for key, value in config["ui_state"].items():
            # Convert lists back to tuples for sliders
            if "slider" in key and isinstance(value, list) and len(value) == 2:
                st.session_state[key] = tuple(value)
            else:
                st.session_state[key] = value


# --- All helper functions (display_generation_summary, etc.) remain unchanged ---

def display_generation_summary(df_results):
    st.subheader("\U0001F4CA Generation Summary")
    total_cases_summary = len(df_results)

    positive_cases = 0
    negative_cases = 0
    if "Test_Type" in df_results.columns:
        test_type_counts = df_results["Test_Type"].value_counts()
        positive_cases = test_type_counts.get("Positive", 0)
        negative_cases = test_type_counts.get("Negative", 0)

    col_sum1, col_sum2, col_sum3 = st.columns(3)
    col_sum1.metric("Total Cases", total_cases_summary)
    col_sum2.metric("\u2714\ufe0f Positive Cases", positive_cases)
    col_sum3.metric("\u274c Negative Cases", negative_cases)

    if "Epic" in df_results.columns:
        epic_counts = df_results["Epic"].value_counts()
        with st.expander("Case Distribution by Epic", expanded=False):
            if not epic_counts.empty:
                st.bar_chart(epic_counts)
            else:
                st.caption("No Epic data to display or 'Epic' column missing.")


def highlight_rule_outcomes(s):
    def get_style(val_str):
        if "Fail" in val_str:
            return "background-color: #FFE0E0; color: #A00000;"
        if val_str == "Pass":
            return "background-color: #E0FFE0; color: #006000;"
        return ""

    return [get_style(str(v)) for v in s]


def get_available_logic_modules():
    modules = {}
    if not os.path.exists(LOGIC_MODULE_DIR):
        return modules
    try:
        for filename in os.listdir(LOGIC_MODULE_DIR):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name_py_file = filename[:-3]
                try:
                    spec = importlib.util.spec_from_file_location(
                        module_name_py_file,
                        os.path.join(LOGIC_MODULE_DIR, filename),
                    )
                    module_obj = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module_obj)
                    display_name = getattr(
                        module_obj,
                        "MODULE_NAME",
                        module_name_py_file.replace("_", " ").title(),
                    )
                    modules[display_name] = module_name_py_file
                except Exception:
                    modules[module_name_py_file.replace("_", " ").title()] = (
                        module_name_py_file
                    )
    except Exception as e:
        st.sidebar.error(f"Error listing logic modules: {e}")
    return modules


def load_logic_module(
    module_name_py, override_display_name=None, override_product_code=None
):
    """
    Load the logic module and optionally override its MODULE_NAME and PRODUCT_CODE
    with values provided from the UI.
    """
    try:
        module_path = os.path.join(LOGIC_MODULE_DIR, f"{module_name_py}.py")
        spec = importlib.util.spec_from_file_location(module_name_py, module_path)
        logic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(logic_module)
        # Apply overrides if provided
        try:
            if override_display_name:
                setattr(logic_module, "MODULE_NAME", override_display_name)
            if override_product_code:
                setattr(logic_module, "PRODUCT_CODE", override_product_code)
        except Exception:
            pass
        return logic_module
    except Exception as e:
        st.error(f"Error loading logic module '{module_name_py}': {e}")
        st.exception(e)
        return None


def resolve_plan_lifecycle_module(plan_type, lifecycle_name):
    plan_modules = PLAN_LIFECYCLE_MODULE_MAP.get(
        plan_type,
        PLAN_LIFECYCLE_MODULE_MAP["term plan"],
    )
    return plan_modules.get(lifecycle_name, plan_modules["pre issuance"])


def lifecycle_key(lifecycle_key_prefix, raw_key):
    return f"{lifecycle_key_prefix}__{raw_key}"


def sync_post_header_selection(shared_key, widget_key):
    st.session_state[shared_key] = st.session_state.get(widget_key)
    st.session_state[f"{shared_key}__last_changed"] = widget_key




# --- Plan-specific PPT config ---
PPT_CONFIGS = {
    "term plan": {
        "ppt_names": [
            "Single Pay",
            "Limited Pay (5 pay)",
            "Limited Pay (10 pay)",
            "Limited Pay (15 pay)",
            "Limited Pay (Pay till age 60)",
            "Regular Pay",
        ],
        "entry_age": {
            "Single Pay": (18, 65),
            "Limited Pay (5 pay)": (18, 65),
            "Limited Pay (10 pay)": (18, 65),
            "Limited Pay (15 pay)": (18, 65),
            "Limited Pay (Pay till age 60)": (18, 55),
            "Regular Pay": (18, 65),
        },
        "policy_term": {
            "Single Pay": (1, 5),
            "Limited Pay (5 pay)": (10, 67),
            "Limited Pay (10 pay)": (15, 67),
            "Limited Pay (15 pay)": (20, 67),
            "Limited Pay (Pay till age 60)": (5, 67),
            "Regular Pay": (5, 67),
        },
        "maturity_age": {
            "Single Pay": (19, 85),
            "Limited Pay (5 pay)": (24, 85),
            "Limited Pay (10 pay)": (29, 85),
            "Limited Pay (15 pay)": (34, 85),
            "Limited Pay (Pay till age 60)": (65, 85),
            "Regular Pay": (23, 85),
        },
        "premium_paying_term": {
            "Single Pay": (1, 1),
            "Limited Pay (5 pay)": (5, 5),
            "Limited Pay (10 pay)": (10, 10),
            "Limited Pay (15 pay)": (15, 15),
            "Limited Pay (Pay till age 60)": (5, 42),
            "Regular Pay": (5, 67),
        },
        "sum_assured": {
            "Single Pay": (2500000, 5000000),
            "Others": (5000000, 20000000),
        },
    },
    "saving plan": {
        # Use same as term plan for now
        "ppt_names": [
            "Regular Pay",
        ],
        "policy_term": {
            "Regular Pay": (9, 17),
        },
        "min_entry_age": {
            "Regular Pay": 18,
        },
        "entry_age": {
            "Regular Pay": (18, 21),
        },
        "maturity_age": {
            "Regular Pay": (27, 85),
        },
        "MaximumEntryAgePlanOption1": {
            "Regular Pay": 50,
        },
        "MaximumEntryAgePlanOption2": {
            "Regular Pay": 45,
        },
        "MaximumEntryAgePlanOption3": {
            "Regular Pay": 45,
        },
        "MaximumEntryAgePlanOption4": {
            "Regular Pay": 45,
        },
        "ChildEntryAge": {
            "Regular Pay": (0, 21),
        },
        "MinimumMaturityAge": {
            "Regular Pay": 27,
        },
        "MaximumMaturityAgePlanOption1": {
            "Regular Pay": 67,
        },
        "MaximumMaturityAgePlanOption2": {
            "Regular Pay": 62,
        },
        "MaximumMaturityAgePlanOption3": {
            "Regular Pay": 62,
        },
        "MaximumMaturityAgePlanOption4": {
            "Regular Pay": 62,
        },
        "PaymentFrequency": {
            "Regular Pay": (23, 85),
        },
        "premium_paying_term": {
            "Regular Pay": (23, 85),
        }, 
        # "PremiumValidation": { 
        #     "Regular Pay": (23, 85),
        # }, 
        "PremiumValidation": {
            "Regular Pay": (36000, 20000000),
        }, 
        "IncomePeriodPPT8": {
            "Regular Pay": (23, 85),
        }, 
        "IncomePeriodPPT10And12": {
            "Regular Pay": (23, 85),
        }, 
        "DefermentPeriod": {
            "Regular Pay": (1, 5),
        },  
        "IncomeShieldPayoutDuration": {
            "Regular Pay": (23, 85),
        }, 
        "IncomePayoutFrequency": {
            "Regular Pay": (23, 85),
        },  
        "AdvanceFeatureOption": {
            "Regular Pay": (23, 85),
        }, 
        "PlanOptions": {
            "Regular Pay": (23, 85),
        }, 
        "ExistingCustomer": {
            "Regular Pay": 20,
        }, 
        "BandhanLifeEmployee": {
            "Regular Pay": 20,
        }, 
        "sum_assured": {
            "Others": (378000, 20000000),
        },
    },
    "ulip plan": {
        "ppt_names": [
            "Single Pay",
            "Limited Pay (5 pay)",
            "Limited Pay (7 pay)",
            "Limited Pay (10 pay)",
            "Limited Pay (15 pay)",
            "Limited Pay (20 pay)",
            "Regular Pay",
        ],
        "entry_age": {
            "Single Pay": (0, 65),
            "Limited Pay (5 pay)": (0, 60),
            "Limited Pay (7 pay)": (0, 60),
            "Limited Pay (10 pay)": (0, 60),
            "Limited Pay (15 pay)": (0, 60),
            "Limited Pay (20 pay)": (0, 60),
            "Regular Pay": (0, 60),
        },
        "policy_term": {
            "Single Pay": (10, 40),
            "Limited Pay (5 pay)": (10, 40),
            "Limited Pay (7 pay)": (10, 40),
            "Limited Pay (10 pay)": (10, 40),
            "Limited Pay (15 pay)": (10, 40),
            "Limited Pay (20 pay)": (10, 40),
            "Regular Pay": (10, 40),
        },
        "maturity_age": {
            "Single Pay": (18, 75),
            "Limited Pay (5 pay)": (18, 75),
            "Limited Pay (7 pay)": (18, 75),
            "Limited Pay (10 pay)": (18, 75),
            "Limited Pay (15 pay)": (18, 75),
            "Limited Pay (20 pay)": (18, 75),
            "Regular Pay": (18, 75),
        },
        "premium_paying_term": {
            "Single Pay": (1, 1),
            "Limited Pay (5 pay)": (5, 5),
            "Limited Pay (7 pay)": (7, 7),
            "Limited Pay (10 pay)": (10, 10),
            "Limited Pay (15 pay)": (15, 15),
            "Limited Pay (20 pay)": (20, 20),
            "Regular Pay": (5, 40),
        },
        "sum_assured": {
            "Single Pay": (2500000, 5000000),
            "Others": (5000000, 20000000),
        },
    },
}

POST_ISSUANCE_FREQUENCY_OPTIONS = [
    "Annual",
    "Half-Yearly",
    "Quarterly",
    "Monthly",
    "Single Pay",
]

POST_ISSUANCE_FREQUENCY_MAP = {
    "Annual": 1,
    "Half-Yearly": 2,
    "Quarterly": 3,
    "Monthly": 4,
    "Single Pay": 5,
}

def get_ppt_config(plan_type):
    return PPT_CONFIGS.get(plan_type, PPT_CONFIGS["term plan"])

def get_post_issuance_defaults(plan_type):
    cfg = get_ppt_config(plan_type)
    return {
        "ppt_names": cfg["ppt_names"],
        "entry_age": cfg["entry_age"],
        "policy_term": cfg["policy_term"],
        "maturity_age": cfg["maturity_age"],
        "premium_paying_term": cfg["premium_paying_term"],
        "sum_assured": cfg["sum_assured"],
    }

POST_ISSUANCE_FREQUENCY_OPTIONS = [
    "Annual",
    "Half-Yearly",
    "Quarterly",
    "Monthly",
    "Single Pay",
]

POST_ISSUANCE_FREQUENCY_MAP = {
    "Annual": 1,
    "Half-Yearly": 2,
    "Quarterly": 3,
    "Monthly": 4,
    "Single Pay": 5,
}


def _render_post_issuance_range_block(
    config_prefix,
    block_name,
    label,
    default_ranges,
    slider_min,
    slider_max,
):
    """Render post-issuance PPT range controls and return enabled ranges."""
    plan_type = st.session_state.get("plan_type_selector", "term plan")
    ppt_config = get_post_issuance_defaults(plan_type)
    with st.expander(label, expanded=False):
        ranges = {}

        header = st.columns([0.6, 2.4, 2])
        with header[1]:
            st.markdown("**PPT Name**")
        with header[2]:
            st.markdown("**Min/Max**")

        for ppt_name in ppt_config["ppt_names"]:
            enabled_key = lifecycle_key(
                config_prefix,
                f"post_cfg_{block_name}_enabled_{ppt_name}",
            )
            slider_key = lifecycle_key(
                config_prefix,
                f"post_cfg_{block_name}_range_{ppt_name}",
            )

            if enabled_key not in st.session_state:
                st.session_state[enabled_key] = True

            default_min, default_max = default_ranges.get(ppt_name, (0, 0))

            row = st.columns([0.6, 2.4, 2])
            with row[0]:
                is_enabled = st.checkbox(
                    "Enable",
                    key=enabled_key,
                    label_visibility="collapsed",
                )
            with row[1]:
                st.markdown(ppt_name)
            with row[2]:
                if default_min == default_max:
                    selected_value = st.slider(
                        label,
                        min_value=slider_min,
                        max_value=slider_max,
                        value=default_min,
                        key=slider_key,
                        label_visibility="collapsed",
                    )
                    min_value, max_value = int(selected_value), int(selected_value)
                else:
                    min_value, max_value = st.slider(
                        label,
                        min_value=slider_min,
                        max_value=slider_max,
                        value=(default_min, default_max),
                        key=slider_key,
                        label_visibility="collapsed",
                    )

            if is_enabled:
                ranges[ppt_name] = (int(min_value), int(max_value))

    return ranges


def _render_post_issuance_constraints(config_prefix):
    """Render shared post-issuance constraint controls across all headers for a tab."""
    st.markdown("### Configure Seed Values")
    st.caption(
        "These values are shared across all post-issuance headers in this tab and used during post-issuance generation."
    )

    freq_cols = st.columns(len(POST_ISSUANCE_FREQUENCY_OPTIONS))
    selected_frequency_options = []

    for index, frequency_label in enumerate(POST_ISSUANCE_FREQUENCY_OPTIONS):
        freq_key = lifecycle_key(config_prefix, f"post_cfg_freq_{frequency_label}")
        if freq_key not in st.session_state:
            st.session_state[freq_key] = True

        with freq_cols[index]:
            if st.checkbox(frequency_label, key=freq_key):
                selected_frequency_options.append(
                    POST_ISSUANCE_FREQUENCY_MAP[frequency_label]
                )

    plan_type = st.session_state.get("plan_type_selector", "term plan")
    ppt_config = get_post_issuance_defaults(plan_type)
    entry_age_ranges = _render_post_issuance_range_block(
        config_prefix,
        "entry_age",
        "Entry Age",
        ppt_config["entry_age"],
        0,
        85,
    )
    policy_term_ranges = _render_post_issuance_range_block(
        config_prefix,
        "policy_term",
        "Policy Term",
        ppt_config["policy_term"],
        1,
        80,
    )
    maturity_age_ranges = _render_post_issuance_range_block(
        config_prefix,
        "maturity_age",
        "Maturity Age",
        ppt_config["maturity_age"],
        1,
        90,
    )
    premium_paying_term_ranges = _render_post_issuance_range_block(
        config_prefix,
        "premium_paying_term",
        "Premium Paying Term",
        ppt_config["premium_paying_term"],
        1,
        85,
    )

    with st.expander("Sum Assured", expanded=False):
        sum_assured_ranges = {}

        default_sum_assured = ppt_config["sum_assured"]

        single_enabled_key = lifecycle_key(
            config_prefix, "post_cfg_sum_assured_single_enabled"
        )
        others_enabled_key = lifecycle_key(
            config_prefix, "post_cfg_sum_assured_others_enabled"
        )

        if single_enabled_key not in st.session_state:
            st.session_state[single_enabled_key] = True
        if others_enabled_key not in st.session_state:
            st.session_state[others_enabled_key] = True

        single_row = st.columns([0.6, 2.4, 1.5, 1.5])
        with single_row[0]:
            single_enabled = st.checkbox(
                "Enable", key=single_enabled_key, label_visibility="collapsed"
            )
        with single_row[1]:
            st.markdown("Single Pay")
        with single_row[2]:
            min_single = st.number_input(
                "Min Single Pay",
                min_value=0,
                value=default_sum_assured["Single Pay"][0],
                key=lifecycle_key(config_prefix, "post_cfg_sum_assured_single_min"),
                label_visibility="collapsed",
            )
        with single_row[3]:
            max_single = st.number_input(
                "Max Single Pay",
                min_value=int(min_single),
                value=default_sum_assured["Single Pay"][1],
                key=lifecycle_key(config_prefix, "post_cfg_sum_assured_single_max"),
                label_visibility="collapsed",
            )

        others_row = st.columns([0.6, 2.4, 1.5, 1.5])
        with others_row[0]:
            others_enabled = st.checkbox(
                "Enable", key=others_enabled_key, label_visibility="collapsed"
            )
        with others_row[1]:
            st.markdown("Others")
        with others_row[2]:
            min_others = st.number_input(
                "Min Others",
                min_value=0,
                value=default_sum_assured["Others"][0],
                key=lifecycle_key(config_prefix, "post_cfg_sum_assured_others_min"),
                label_visibility="collapsed",
            )
        with others_row[3]:
            max_others = st.number_input(
                "Max Others",
                min_value=int(min_others),
                value=default_sum_assured["Others"][1],
                key=lifecycle_key(config_prefix, "post_cfg_sum_assured_others_max"),
                label_visibility="collapsed",
            )

        if single_enabled:
            sum_assured_ranges["Single Pay"] = {
                "min_val": int(min_single),
                "max_val": int(max_single),
            }
        if others_enabled:
            sum_assured_ranges["Others"] = {
                "min_val": int(min_others),
                "max_val": int(max_others),
            }

    return {
        "payment_frequency_options": selected_frequency_options,
        "entry_age_ranges": entry_age_ranges,
        "policy_term_ranges": policy_term_ranges,
        "maturity_age_ranges": maturity_age_ranges,
        "premium_paying_term_ranges": premium_paying_term_ranges,
        "sum_assured_ranges": sum_assured_ranges,
    }


def _build_post_issuance_epic_payload(pos_count, selected_header, constraints):
    """Build per-epic post-issuance payload with shared constraint configuration."""
    return {
        "positive": int(pos_count),
        "negative": 0,
        "header": selected_header,
        "payment_frequency_options": list(
            constraints.get("payment_frequency_options", [])
        ),
        "entry_age_ranges": dict(constraints.get("entry_age_ranges", {})),
        "policy_term_ranges": dict(constraints.get("policy_term_ranges", {})),
        "maturity_age_ranges": dict(constraints.get("maturity_age_ranges", {})),
        "premium_paying_term_ranges": dict(
            constraints.get("premium_paying_term_ranges", {})
        ),
        "sum_assured_ranges": {
            key: dict(value)
            for key, value in constraints.get("sum_assured_ranges", {}).items()
        },
    }


def render_post_issuance_epics(
    plan_type,
    lifecycle_key_prefix,
    count_mode,
    num_positive_global,
    shared_lifecycle_prefix=None,
):
    epic_headers = get_post_issuance_epics_for_plan(plan_type)
    selected_epics = []
    epic_counts = {}

    if not epic_headers:
        st.info("No post-issuance epic headers configured for this plan yet.")
        return None, selected_epics, epic_counts

    shared_prefix = shared_lifecycle_prefix or lifecycle_key_prefix
    shared_header_key = lifecycle_key(shared_prefix, "post_header_selected_shared")
    radio_key = lifecycle_key(lifecycle_key_prefix, "post_header_radio")
    last_changed_key = f"{shared_header_key}__last_changed"

    if (
        shared_header_key not in st.session_state
        or st.session_state[shared_header_key] not in epic_headers
    ):
        st.session_state[shared_header_key] = list(epic_headers.keys())[0]

    if radio_key not in st.session_state or st.session_state[radio_key] not in epic_headers:
        st.session_state[radio_key] = st.session_state[shared_header_key]

    if (
        st.session_state.get(last_changed_key) != radio_key
        and st.session_state[radio_key] != st.session_state[shared_header_key]
    ):
        st.session_state[radio_key] = st.session_state[shared_header_key]

    selected_header = st.session_state.get(radio_key)

    # Create a radio button for exclusive header selection
    selected_header = st.radio(
        "Select a post-issuance test-case:",
        list(epic_headers.keys()),
        index=list(epic_headers.keys()).index(selected_header)
        if selected_header in epic_headers
        else 0,
        key=radio_key,
        on_change=sync_post_header_selection,
        args=(shared_header_key, radio_key),
        horizontal=True,
    )

    # Store the selected header back into session state
    st.session_state[shared_header_key] = selected_header
    st.session_state[last_changed_key] = radio_key
    st.session_state[
        lifecycle_key(lifecycle_key_prefix, "post_header_selected")
    ] = selected_header

    # Show expander only for the selected header
    header_epics = epic_headers[selected_header]

    select_all_key = lifecycle_key(
        lifecycle_key_prefix, f"post_select_all_{selected_header}"
    )
    select_all_prev_key = lifecycle_key(
        lifecycle_key_prefix, f"post_select_all_prev_{selected_header}"
    )

    if select_all_key not in st.session_state:
        st.session_state[select_all_key] = True
    if select_all_prev_key not in st.session_state:
        st.session_state[select_all_prev_key] = st.session_state[select_all_key]

    select_all_state = st.checkbox("Select all", key=select_all_key)
    if select_all_state != st.session_state[select_all_prev_key]:
        for epic_index, _ in enumerate(header_epics):
            checkbox_key = lifecycle_key(
                lifecycle_key_prefix,
                f"post_epic_cb_{selected_header}_{epic_index}",
            )
            st.session_state[checkbox_key] = select_all_state
    st.session_state[select_all_prev_key] = select_all_state

    selected_epic_positive_counts = {}

    with st.expander(selected_header, expanded=True):
        for epic_index, epic_name in enumerate(header_epics):
            checkbox_key = lifecycle_key(
                lifecycle_key_prefix,
                f"post_epic_cb_{selected_header}_{epic_index}",
            )
            pos_count_key = lifecycle_key(
                lifecycle_key_prefix,
                f"post_epic_pos_{selected_header}_{epic_index}",
            )

            if count_mode == "Set Individual Counts for Each Epic":
                row = st.columns([4, 2])
                with row[0]:
                    is_selected = st.checkbox(epic_name, value=True, key=checkbox_key)
                with row[1]:
                    pos_count = st.number_input(
                        f"Pos {epic_name}",
                        min_value=0,
                        value=5,
                        key=pos_count_key,
                        label_visibility="collapsed",
                        placeholder="Pos",
                    )
            else:
                is_selected = st.checkbox(epic_name, value=True, key=checkbox_key)
                pos_count = num_positive_global

            if is_selected:
                selected_epics.append(epic_name)
                selected_epic_positive_counts[epic_name] = int(pos_count)

    post_constraints = _render_post_issuance_constraints(lifecycle_key_prefix)

    for epic_name in selected_epics:
        epic_counts[epic_name] = _build_post_issuance_epic_payload(
            selected_epic_positive_counts.get(epic_name, num_positive_global),
            selected_header,
            post_constraints,
        )

    return selected_header, selected_epics, epic_counts


def render_base_plan_epics(
    logic_module,
    lifecycle_key_prefix,
    count_mode,
    num_positive_global,
    num_negative_global,
):
    epic_counts = {}
    selected_epics = []
    if not logic_module or not hasattr(logic_module, "EPIC_MAP"):
        return selected_epics, epic_counts

    epic_map = getattr(logic_module, "EPIC_MAP")
    plan_type = st.session_state.get("plan_type_selector", "term plan")
    ppt_config = get_ppt_config(plan_type)
    ppt_names = ppt_config["ppt_names"]
    entry_age_ppt_ranges = ppt_config["entry_age"]
    policy_term_ppt_ranges = ppt_config["policy_term"]
    maturity_age_ppt_ranges = ppt_config["maturity_age"]
    premium_paying_ppt_ranges = ppt_config["premium_paying_term"]
    sum_assured_ranges = ppt_config["sum_assured"]

    if plan_type == "saving plan":
        child_entry_age=ppt_config["ChildEntryAge"]["Regular Pay"]
        DefermentPeriod_ranges=ppt_config["DefermentPeriod"]["Regular Pay"]
        min_entry_age_val=ppt_config["min_entry_age"]["Regular Pay"]
        max_entry_age_opt1=ppt_config["MaximumEntryAgePlanOption1"]["Regular Pay"]
        max_entry_age_opt2=ppt_config["MaximumEntryAgePlanOption2"]["Regular Pay"]
        max_entry_age_opt3=ppt_config["MaximumEntryAgePlanOption3"]["Regular Pay"]
        max_entry_age_opt4=ppt_config["MaximumEntryAgePlanOption4"]["Regular Pay"]
        min_maturity_age_val=ppt_config["MinimumMaturityAge"]["Regular Pay"]
        max_maturity_age_opt1=ppt_config["MaximumMaturityAgePlanOption1"]["Regular Pay"]
        max_maturity_age_opt2=ppt_config["MaximumMaturityAgePlanOption2"]["Regular Pay"]
        max_maturity_age_opt3=ppt_config["MaximumMaturityAgePlanOption3"]["Regular Pay"]
        max_maturity_age_opt4=ppt_config["MaximumMaturityAgePlanOption4"]["Regular Pay"]
        existing_customer_age=ppt_config["ExistingCustomer"]["Regular Pay"]
        bandhan_employee_age=ppt_config["BandhanLifeEmployee"]["Regular Pay"]
        premium_validation_range=ppt_config["PremiumValidation"]["Regular Pay"]



    min_entry_age = ppt_config["entry_age"]["Regular Pay"][0]
    selected_plan_option = None
    select_all = st.checkbox(
        "Select/Deselect All Epics",
        value=True,
        key=lifecycle_key(lifecycle_key_prefix, "select_all_epics_master"),
    )

    with st.expander("\u2139\ufe0f Configure Epics and Case Counts", expanded=True):
        for epic_key, epic_desc in epic_map.items():

            if count_mode == "Set Individual Counts for Each Epic":
                if epic_key in [
                    "PolicyTerm",
                    "EntryAge",
                    "MaximumEntryAgePlanOption1",
                    "MaximumEntryAgePlanOption2",
                    "MaximumEntryAgePlanOption3",
                    "MaximumEntryAgePlanOption4",
                    "ChildEntryAge",
                    "MaturityAge",
                    "MaximumMaturityAgePlanOption1",
                    "MaximumMaturityAgePlanOption2",
                    "MaximumMaturityAgePlanOption3",
                    "MaximumMaturityAgePlanOption4",
                    # "PaymentFrequency",
                    "PremiumPayingTerm",
                    "PremiumValidation",
                    "IncomePeriodPPT8",
                    "IncomePeriodPPT10And12",
                    "DefermentPeriod",
                    # "SumAssuredValidation",
                    "IncomeShieldPayoutDuration",
                    "IncomePayoutFrequency",
                    "AdvanceFeatureOption",
                    "PlanOptions",
                    "ExistingCustomer",
                    "BandhanLifeEmployee",
                ]:
                    is_selected = st.checkbox(
                        epic_desc,
                        value=select_all,
                        key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                    )
                    with st.expander("Show/Hide PPT Configuration", expanded=False):
                        ppt_age_ranges, ppt_pos_counts, ppt_neg_counts, ppt_enabled = (
                            {},
                            {},
                            {},
                            {},
                        )

                        header = st.columns([0.5, 2, 2, 1, 1])
                        with header[1]:
                            st.markdown("**PPT Name**")
                        with header[2]:
                            st.markdown("**Min/Max**")
                        with header[3]:
                            st.markdown("**Pos**")
                        with header[4]:
                            st.markdown("**Neg**")

                        for ppt in ppt_names:
                            row = st.columns([0.5, 2, 2, 1, 1])
                            with row[0]:
                                enabled = st.checkbox(
                                    "Enable",
                                    value=is_selected,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"ppt_enabled_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            with row[1]:
                                st.markdown(ppt)
                            with row[2]:
                                if epic_key == "PolicyTerm":
                                    min_age, max_age = st.slider(
                                        "Policy Term",
                                        0,
                                        85,
                                        policy_term_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"entry_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "EntryAge":
                                    default_min = entry_age_ppt_ranges[ppt][0]
                                    default_max = entry_age_ppt_ranges[ppt][1]
                                    min_age = st.number_input(
                                        "Min Entry Age",
                                        min_value=0,
                                        max_value=120,
                                        value=default_min,
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"entry_age_min_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                    # When a saving plan and plan option selected, limit max to plan-option max
                                    max_limit = entry_age_ppt_ranges[ppt][1]
                                    max_age = st.number_input(
                                        "Max Entry Age",
                                        min_value=min_age,
                                        max_value=120,
                                        value=default_max,
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"entry_age_max_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaximumEntryAgePlanOption1":
                                    min_age, max_age = st.slider(
                                        "MaximumEntryAgePlanOption1",
                                        18,
                                        90,
                                        entry_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"maturity_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaximumEntryAgePlanOption2":
                                    min_age, max_age = st.slider(
                                        "MaximumEntryAgePlanOption2",
                                        18,
                                        90,
                                        entry_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"maturity_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )    
                                elif epic_key == "MaximumEntryAgePlanOption3":
                                    min_age, max_age = st.slider(
                                        "MaximumEntryAgePlanOption3",
                                        18,
                                        90,
                                        entry_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"maturity_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaximumEntryAgePlanOption4":
                                    min_age, max_age = st.slider(
                                        "MaximumEntryAgePlanOption4",
                                        18,
                                        90,
                                        entry_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"maturity_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "ChildEntryAge":
                                    min_age, max_age = st.slider(
                                        "Child Entry Age",
                                        0,
                                        25,
                                        entry_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"child_entry_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaturityAge":
                                    default_min = maturity_age_ppt_ranges[ppt][0]
                                    default_max = maturity_age_ppt_ranges[ppt][1]
                                    min_age = st.number_input(
                                        "Min Maturity Age",
                                        min_value=0,
                                        max_value=120,
                                        value=default_min,
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"maturity_age_min_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                    max_age = st.number_input(
                                        "Max Maturity Age",
                                        min_value=min_age,
                                        max_value=120,
                                        value=default_max,
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"maturity_age_max_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaximumMaturityAgePlanOption1":
                                    min_age, max_age = st.slider(
                                        "Maximum Maturity Age Plan Option 1",
                                        18,
                                        90,
                                        maturity_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"max_maturity_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaximumMaturityAgePlanOption2":
                                    min_age, max_age = st.slider(
                                        "Maximum Maturity Age Plan Option 2",
                                        18,
                                        90,
                                        maturity_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"max_maturity_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaximumMaturityAgePlanOption3":   
                                    min_age, max_age = st.slider(
                                        "Maximum Maturity Age Plan Option 3",
                                        18,
                                        90,
                                        maturity_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"max_maturity_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaximumMaturityAgePlanOption4":
                                    min_age, max_age = st.slider(
                                        "Maximum Maturity Age Plan Option 4",
                                        18,
                                        90,
                                        maturity_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"max_maturity_age_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                # elif epic_key == "PaymentFrequency":
                                #     min_age, max_age = st.slider(
                                #         "Payment Frequency",
                                #         1,
                                #         85,
                                #         premium_paying_ppt_ranges[ppt],
                                #         key=lifecycle_key(
                                #             lifecycle_key_prefix,
                                #             f"payment_frequency_slider_{epic_key}_{ppt}",
                                #         ),
                                #         label_visibility="collapsed",
                                #     )    
                                elif epic_key == "PremiumPayingTerm":
                                    min_age, max_age = st.slider(
                                        "Premium Paying Term",
                                        1,
                                        85,
                                        premium_paying_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"premium_paying_term_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "PremiumValidation":
                                    min_age, max_age = st.slider(
                                        "Premium Validation",
                                        1,
                                        85,
                                        premium_paying_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"premium_validation_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )    
                                elif epic_key == "IncomePeriodPPT8":
                                    min_age, max_age = st.slider(
                                        "Income Period PPT 8",
                                        1,
                                        85,
                                        premium_paying_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"income_period_ppt_8_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "IncomePeriodPPT10And12":
                                    min_age, max_age = st.slider(
                                        "Income Period PPT 10 and 12",
                                        1,
                                        85,
                                        premium_paying_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"income_period_ppt_10_12_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )           
                                elif  epic_key == "DefermentPeriod":
                                    min_age, max_age = st.slider(
                                        "Deferment Period",
                                        0,
                                        30,
                                        premium_paying_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"deferment_period_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )   
                                  
                                elif epic_key == "IncomeShieldPayoutDuration":
                                    min_age, max_age = st.slider(
                                        "Income Shield Payout Duration",
                                        1,
                                        40,
                                        premium_paying_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"income_shield_payout_duration_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "IncomePayoutFrequency":       
                                    min_age, max_age = st.slider(
                                        "Income Payout Frequency",
                                        1,
                                        12,
                                        premium_paying_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"income_payout_frequency_slider_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )    
                                elif epic_key == "AdvanceFeatureOption":    
                                        min_age, max_age = st.slider(
                                            "Advance Feature Option",
                                            1,
                                            85,
                                            premium_paying_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"advance_feature_option_slider_{epic_key}_{ppt}",
                                            ),
                                            label_visibility="collapsed",
                                        )
                                elif epic_key == "PlanOptions":   
                                        min_age, max_age = st.slider(
                                            "Plan Options",
                                            1,
                                            85,
                                            premium_paying_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"plan_options_slider_{epic_key}_{ppt}",
                                            ),
                                            label_visibility="collapsed",
                                        )
                                elif epic_key == "ExistingCustomer":    
                                        min_age, max_age = st.slider(
                                            "Existing Customer",
                                            1,
                                            85,
                                            premium_paying_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"existing_customer_slider_{epic_key}_{ppt}",
                                            ),
                                            label_visibility="collapsed",
                                        )
                                elif epic_key == "BandhanLifeEmployee":
                                        min_age, max_age = st.slider(
                                            "Bandhan Life Employee",
                                            1,
                                            85,
                                            premium_paying_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"bandhan_life_employee_slider_{epic_key}_{ppt}",
                                            ),
                                            label_visibility="collapsed",
                                        )                                                                                              
                                else:
                                    if (
                                        premium_paying_ppt_ranges[ppt][0]
                                        == premium_paying_ppt_ranges[ppt][1]
                                    ):
                                        min_age = max_age = st.slider(
                                            "Entry Age",
                                            0,
                                            85,
                                            premium_paying_ppt_ranges[ppt][0],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"entry_age_slider_{epic_key}_{ppt}",
                                            ),
                                            label_visibility="collapsed",
                                        )
                                    else:
                                        min_age, max_age = st.slider(
                                            "Entry Age",
                                            0,
                                            85,
                                            premium_paying_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"entry_age_slider_{epic_key}_{ppt}",
                                            ),
                                            label_visibility="collapsed",
                                        )
                            with row[3]:
                                pos = st.number_input(
                                    "Pos",
                                    0,
                                    value=5,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"epic_pos_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            with row[4]:
                                neg = st.number_input(
                                    "Neg",
                                    0,
                                    value=5,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"epic_neg_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )

                            if enabled:
                                ppt_age_ranges[ppt] = (min_age, max_age)
                                ppt_pos_counts[ppt] = pos
                                ppt_neg_counts[ppt] = neg
                                ppt_enabled[ppt] = True
                            else:
                                ppt_enabled[ppt] = False

                        if is_selected and any(ppt_enabled.values()):
                            selected_epics.append(epic_key)
                            epic_counts[epic_key] = {
                                "ppt_age_ranges": ppt_age_ranges,
                                "ppt_pos_counts": ppt_pos_counts,
                                "ppt_neg_counts": ppt_neg_counts,
                                "ppt_enabled": ppt_enabled,
                            }
                            if (
                                plan_type == "saving plan"
                                and selected_plan_option
                                and epic_key in ["EntryAge", "MaturityAge"]
                            ):
                                epic_counts[epic_key]["plan_option"] = (
                                    selected_plan_option
                                )

                elif epic_key == "PaymentFrequency":
                    row = st.columns([2, 1.5, 1.5])
                    with row[0]:
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                    with row[1]:
                        pos_count = st.number_input(
                            f"Pos {epic_key}",
                            min_value=0,
                            value=5,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_pos_{epic_key}"
                            ),
                            label_visibility="collapsed",
                            placeholder="Pos",
                        )
                    with row[2]:
                        neg_count = st.number_input(
                            f"Neg {epic_key}",
                            min_value=0,
                            value=5,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_neg_{epic_key}"
                            ),
                            label_visibility="collapsed",
                            placeholder="Neg",
                        )

                    frequency_options = [
                        "Annual",
                        "Half-Yearly",
                        "Quarterly",
                        "Monthly",
                        "Single Pay",
                    ]
                    frequency_map = {
                        "Annual": 1,
                        "Half-Yearly": 2,
                        "Quarterly": 3,
                        "Monthly": 4,
                        "Single Pay": 5,
                    }
                    freq_cols = st.columns(len(frequency_options) + 1)
                    selected_frequencies = []
                    for i, freq in enumerate(frequency_options):
                        with freq_cols[i + 1]:
                            if st.checkbox(
                                freq,
                                value=is_selected,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"freq_cb_{freq}"
                                ),
                            ):
                                selected_frequencies.append(freq)

                    mapped_frequencies = [frequency_map[f] for f in selected_frequencies]

                    if is_selected:
                        selected_epics.append(epic_key)
                        epic_counts[epic_key] = {
                            "positive": pos_count,
                            "negative": neg_count,
                            "payment_frequency_options": mapped_frequencies,
                        }

                elif epic_key == "SumAssuredValidation":
                    is_selected = st.checkbox(
                        epic_desc,
                        value=select_all,
                        key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                    )
                    with st.expander("Show/Hide PPT Configuration", expanded=False):
                        header = st.columns([0.5, 2, 1, 1, 1, 1])
                        with header[1]:
                            st.markdown("**PPT Type**")
                        with header[2]:
                            st.markdown("**Min**")
                        with header[3]:
                            st.markdown("**Max**")
                        with header[4]:
                            st.markdown("**Pos**")
                        with header[5]:
                            st.markdown("**Neg**")

                        row_sp = st.columns([0.5, 2, 1, 1, 1, 1])
                        with row_sp[0]:
                            sp = st.checkbox(
                                "Enable",
                                value=is_selected,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"sa_enabled_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[1]:
                            st.markdown("SinglePay")
                        with row_sp[2]:
                            min_sp = st.number_input(
                                "Min SinglePay",
                                min_value=0,
                                value=sum_assured_ranges["Single Pay"][0],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"min_sp_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[3]:
                            max_sp = st.number_input(
                                "Max SinglePay",
                                min_value=min_sp,
                                value=sum_assured_ranges["Single Pay"][1],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"max_sp_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[4]:
                            pos_sp = st.number_input(
                                "Pos SinglePay",
                                min_value=0,
                                value=5,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"pos_sp_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[5]:
                            neg_sp = st.number_input(
                                "Neg SinglePay",
                                min_value=0,
                                value=5,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"neg_sp_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )

                        row_oth = st.columns([0.5, 2, 1, 1, 1, 1])
                        with row_oth[0]:
                            oth = st.checkbox(
                                "Enable",
                                value=is_selected,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"oth_enabled_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[1]:
                            st.markdown("Others")
                        with row_oth[2]:
                            min_oth = st.number_input(
                                "Min Others",
                                min_value=0,
                                value=sum_assured_ranges["Others"][0],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"min_oth_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[3]:
                            max_oth = st.number_input(
                                "Max Others",
                                min_value=min_oth,
                                value=sum_assured_ranges["Others"][1],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"max_oth_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[4]:
                            pos_oth = st.number_input(
                                "Pos Others",
                                min_value=0,
                                value=5,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"pos_oth_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[5]:
                            neg_oth = st.number_input(
                                "Neg Others",
                                min_value=0,
                                value=5,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"neg_oth_{epic_key}"
                                ),
                                label_visibility="collapsed",
                            )

                        if is_selected:
                            selected_epics.append(epic_key)
                            if epic_key not in epic_counts:
                                epic_counts[epic_key] = {}
                            if sp:
                                epic_counts[epic_key]["Single Pay"] = {
                                    "min_val": min_sp,
                                    "max_val": max_sp,
                                    "positive": pos_sp,
                                    "negative": neg_sp,
                                }
                            if oth:
                                epic_counts[epic_key]["Others"] = {
                                    "min_val": min_oth,
                                    "max_val": max_oth,
                                    "positive": pos_oth,
                                    "negative": neg_oth,
                                }
                else:
                    row = st.columns([2, 1.5, 1.5])
                    with row[0]:
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                    with row[1]:
                        pos_count = st.number_input(
                            f"Pos {epic_key}",
                            min_value=0,
                            value=5,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_pos_{epic_key}"
                            ),
                            label_visibility="collapsed",
                            placeholder="Pos",
                        )
                    with row[2]:
                        neg_count = st.number_input(
                            f"Neg {epic_key}",
                            min_value=0,
                            value=5,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_neg_{epic_key}"
                            ),
                            label_visibility="collapsed",
                            placeholder="Neg",
                        )
                    if is_selected:
                        selected_epics.append(epic_key)
                        epic_counts[epic_key] = {
                            "positive": pos_count,
                            "negative": neg_count,
                        }

            else:  # Apply Same Count to All Epics
                if plan_type == "saving plan":
                    ppt="Regular Pay"  # For saving plan, show sliders for Regular Pay configuration as default
                    if epic_key in [
                        "PolicyTerm",
                        "DefermentPeriod",
                        "ChildEntryAge"
                    ]:  
                        ppt_age_ranges, ppt_enabled = {}, {}
                        row = st.columns([0.5, 2])
                        with row[0]:
                            is_selected = st.checkbox(
                                epic_desc,
                                value=select_all,
                                key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                            )
                        with row[1]:
                            if epic_key == "PolicyTerm":
                                min_age, max_age = st.slider(
                                    "Policy Term",
                                    5,
                                    80,
                                    policy_term_ppt_ranges[ppt],
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"entry_age_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                                    
                            elif epic_key == "ChildEntryAge":
                                min_age = st.slider(
                                    "ChildEntryAge",
                                    5,
                                    80,
                                    child_entry_age,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"ChildEntryAge_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )

                            elif epic_key == "DefermentPeriod":
                                min_age, max_age = st.slider(
                                    "Deferment Period",
                                    0,
                                    20,
                                    DefermentPeriod_ranges,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"DefermentPeriod_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )

                        if is_selected:
                            ppt_age_ranges[ppt] = (min_age, max_age)
                            ppt_enabled[ppt] = True
                            selected_epics.append(epic_key)
                            epic_counts[epic_key] = {
                                "ppt_age_ranges": ppt_age_ranges,
                                "ppt_enabled": ppt_enabled,
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                            }

                    elif epic_key in [
                        "MinimumEntryAge",
                        "MaximumEntryAgePlanOption1",
                        "MaximumEntryAgePlanOption2",
                        "MaximumEntryAgePlanOption3",
                        "MaximumEntryAgePlanOption4",
                        "MinimumMaturityAge",
                        "MaximumMaturityAgePlanOption1",
                        "MaximumMaturityAgePlanOption2",
                        "MaximumMaturityAgePlanOption3",
                        "MaximumMaturityAgePlanOption4",
                        "ExistingCustomer",
                        "BandhanLifeEmployee",
                    ]:
                        ppt_age_ranges, ppt_enabled = {}, {}
                        row = st.columns([0.5, 2])
                        with row[0]:
                            is_selected = st.checkbox(
                                epic_desc,
                                value=select_all,
                                key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                            )
                        with row[1]:
                            if epic_key == "MinimumEntryAge":
                                age_val = st.slider(
                                    "Min Entry Age",
                                    0,
                                    100,
                                    min_entry_age_val,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MinEntryAge_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "MaximumEntryAgePlanOption1":
                                age_val = st.slider(
                                    "Max Entry Age Option 1",
                                    0,
                                    80,
                                    max_entry_age_opt1,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxEntryAgeOpt1_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "MaximumEntryAgePlanOption2":
                                age_val = st.slider(
                                    "Max Entry Age Option 2",
                                    0,
                                    80,
                                    max_entry_age_opt2,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxEntryAgeOpt2_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "MaximumEntryAgePlanOption3":
                                age_val = st.slider(
                                    "Max Entry Age Option 3",
                                    0,
                                    80,
                                    max_entry_age_opt3,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxEntryAgeOpt3_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "MaximumEntryAgePlanOption4":
                                age_val = st.slider(
                                    "Max Entry Age Option 4",
                                    0,
                                    80,
                                    max_entry_age_opt4,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxEntryAgeOpt4_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "MinimumMaturityAge":
                                age_val = st.slider(
                                    "Maturity Age",
                                    0,
                                    80,
                                    min_maturity_age_val,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MinimumMaturityAge_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "MaximumMaturityAgePlanOption1":
                                age_val = st.slider(
                                    "Max Maturity Age Option 1",
                                    0,
                                    80,
                                    max_maturity_age_opt1,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxMaturityAgeOpt1_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "MaximumMaturityAgePlanOption2":
                                age_val = st.slider(
                                    "Max Maturity Age Option 2",
                                    0,
                                    80,
                                    max_maturity_age_opt2,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxMaturityAgeOpt2_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "MaximumMaturityAgePlanOption3":
                                age_val = st.slider(
                                    "Max Maturity Age Option 3",
                                    0,
                                    80,
                                    max_maturity_age_opt3,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxMaturityAgeOpt3_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "MaximumMaturityAgePlanOption4":
                                age_val = st.slider(
                                    "Max Maturity Age Option 4",
                                    0,
                                    80,
                                    max_maturity_age_opt4,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxMaturityAgeOpt4_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "ExistingCustomer":
                                age_val = st.slider(
                                    "Existing Customer",
                                    0,
                                    80,
                                    existing_customer_age,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxMaturityAgeOpt4_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )
                            elif epic_key == "BandhanLifeEmployee":
                                age_val = st.slider(
                                    "Bandhan Life Employee",
                                    0,
                                    80,
                                    bandhan_employee_age,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"MaxMaturityAgeOpt4_slider_{epic_key}_{ppt}",
                                    ),
                                    label_visibility="collapsed",
                                )        
                        if is_selected:
                            ppt_age_ranges[ppt] = age_val
                            ppt_enabled[ppt] = True
                            selected_epics.append(epic_key)
                            epic_counts[epic_key] = {
                                "ppt_age_ranges": ppt_age_ranges,
                                "ppt_enabled": ppt_enabled,
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                            }

                    elif epic_key in [
                        "IncomePeriodPPT8",
                        "IncomePeriodPPT10And12",
                        "IncomePayoutFrequency",
                        "PremiumPayingTerm",
                        "IncomeShieldPayoutDuration",
                        "AdvanceFeatureOption",
                    ]:
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                        if is_selected:
                            selected_epics.append(epic_key)
                            epic_counts[epic_key] = {
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                            }
                    elif epic_key == "PaymentFrequency":
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                        frequency_options = [
                            "Annual",
                            "Half-Yearly",
                            "Quarterly",
                            "Monthly",
                            "Single Pay",
                        ]
                        frequency_map = {
                            "Annual": 1,
                            "Half-Yearly": 2,
                            "Quarterly": 3,
                            "Monthly": 4,
                            "Single Pay": 5,
                        }
                        freq_cols = st.columns(len(frequency_options) + 1)
                        selected_frequencies = []
                        for i, freq in enumerate(frequency_options):
                            with freq_cols[i + 1]:
                                if st.checkbox(
                                    freq,
                                    value=is_selected,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"freq_cb_{freq}"
                                    ),
                                ):
                                    selected_frequencies.append(freq)

                        mapped_frequencies = [frequency_map[f] for f in selected_frequencies]

                        if is_selected:
                            selected_epics.append(epic_key)
                            epic_counts[epic_key] = {
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                                "payment_frequency_options": mapped_frequencies,
                            }
                    elif epic_key == "PlanOptions":
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                        plan_option_options = [
                            "CareerStart Income",
                            "CareerStart Health Shield Income",
                            "CareerStart Secure Income",
                            "CareerStart Life Shield Income",
                        ]
                        plan_option_cols = st.columns(len(plan_option_options) + 1)
                        selected_plan_options = []
                        for i, option in enumerate(plan_option_options):
                            with plan_option_cols[i + 1]:
                                if st.checkbox(
                                    option,
                                    value=is_selected,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"plan_option_cb_{option}"
                                    ),
                                ):
                                    selected_plan_options.append(option)
                        if is_selected:
                            selected_epics.append(epic_key)
                            epic_counts[epic_key] = {
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                                "plan_option_options": selected_plan_options,
                            }
                    elif epic_key == "SumAssuredValidation":
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                        if is_selected:
                            cols = st.columns([1, 1])
                            with cols[0]:
                                min_val = st.number_input(
                                    "Min Value",
                                    min_value=0,
                                    value=sum_assured_ranges["Others"][0],
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"min_val_{epic_key}"
                                    ),
                                )
                            with cols[1]:
                                max_val = st.number_input(
                                    "Max Value",
                                    min_value=min_val,
                                    value=sum_assured_ranges["Others"][1],
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"max_val_{epic_key}"
                                    ),
                                )
                            selected_epics.append(epic_key)
                            if epic_key not in epic_counts:
                                epic_counts[epic_key] = {}
                            epic_counts[epic_key] = {
                                "min_val": min_val,
                                "max_val": max_val,
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                            }
                    elif epic_key == "PremiumValidation":
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                        if is_selected:
                            cols = st.columns([1, 1])
                            with cols[0]:
                                min_val = st.number_input(
                                    "Min Value",
                                    min_value=0,
                                    value=premium_validation_range[0],
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"min_val_{epic_key}"
                                    ),
                                )
                            with cols[1]:
                                max_val = st.number_input(
                                    "Max Value",
                                    min_value=min_val,
                                    value=premium_validation_range[1],
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"max_val_{epic_key}"
                                    ),
                                )
                            selected_epics.append(epic_key)
                            if epic_key not in epic_counts:
                                epic_counts[epic_key] = {}
                            epic_counts[epic_key] = {
                                "min_val": min_val,
                                "max_val": max_val,
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                            }                             
                else:    # For term and ulip plans, show sliders for all PPT configurations
                    if epic_key in [
                        "EntryAge",
                        "PremiumPayingTerm",
                        "PolicyTerm",
                        "MaturityAge",
                    ]:
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                        with st.expander("Show/Hide PPT Configuration", expanded=False):
                            ppt_age_ranges, ppt_enabled = {}, {}

                            for ppt in ppt_names:
                                row = st.columns([0.5, 2, 2])
                                with row[0]:
                                    enabled = st.checkbox(
                                        "Enable",
                                        value=is_selected,
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"ppt_enabled_all_{epic_key}_{ppt}",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                with row[1]:
                                    st.markdown(ppt)
                                with row[2]:
                                    if epic_key == "EntryAge":
                                        min_age, max_age = st.slider(
                                            "Entry Age",
                                            0,
                                            85,
                                            entry_age_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"entry_age_slider_{epic_key}_{ppt}",
                                            ),
                                            label_visibility="collapsed",
                                        )
                                    elif epic_key == "PolicyTerm":
                                        min_age, max_age = st.slider(
                                            "Policy Term",
                                            5,
                                            80,
                                            policy_term_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"entry_age_slider_{epic_key}_{ppt}",
                                            ),
                                            label_visibility="collapsed",
                                        )
                                    elif epic_key == "MaturityAge":
                                        min_age, max_age = st.slider(
                                            "Maturity Age",
                                            1,
                                            90,
                                            maturity_age_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"maturity_age_slider_{epic_key}_{ppt}",
                                            ),
                                            label_visibility="collapsed",
                                        )
                                    else:
                                        if (
                                            premium_paying_ppt_ranges[ppt][0]
                                            == premium_paying_ppt_ranges[ppt][1]
                                        ):
                                            min_age = max_age = st.slider(
                                                "Entry Age",
                                                0,
                                                85,
                                                premium_paying_ppt_ranges[ppt][0],
                                                key=lifecycle_key(
                                                    lifecycle_key_prefix,
                                                    f"entry_age_slider_{epic_key}_{ppt}",
                                                ),
                                                label_visibility="collapsed",
                                            )
                                        else:
                                            min_age, max_age = st.slider(
                                                "Entry Age",
                                                0,
                                                85,
                                                premium_paying_ppt_ranges[ppt],
                                                key=lifecycle_key(
                                                    lifecycle_key_prefix,
                                                    f"entry_age_slider_{epic_key}_{ppt}",
                                                ),
                                                label_visibility="collapsed",
                                            )
                                if enabled:
                                    ppt_age_ranges[ppt] = (min_age, max_age)
                                    ppt_enabled[ppt] = True
                                else:
                                    ppt_enabled[ppt] = False

                            if is_selected and any(ppt_enabled.values()):
                                selected_epics.append(epic_key)
                                epic_counts[epic_key] = {
                                    "ppt_age_ranges": ppt_age_ranges,
                                    "ppt_enabled": ppt_enabled,
                                    "positive": num_positive_global,
                                    "negative": num_negative_global,
                                }

                    elif epic_key == "PaymentFrequency":
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                        frequency_options = [
                            "Annual",
                            "Half-Yearly",
                            "Quarterly",
                            "Monthly",
                            "Single Pay",
                        ]
                        frequency_map = {
                            "Annual": 1,
                            "Half-Yearly": 2,
                            "Quarterly": 3,
                            "Monthly": 4,
                            "Single Pay": 5,
                        }
                        freq_cols = st.columns(len(frequency_options) + 1)
                        selected_frequencies = []
                        for i, freq in enumerate(frequency_options):
                            with freq_cols[i + 1]:
                                if st.checkbox(
                                    freq,
                                    value=is_selected,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"freq_cb_{freq}"
                                    ),
                                ):
                                    selected_frequencies.append(freq)

                        mapped_frequencies = [frequency_map[f] for f in selected_frequencies]

                        if is_selected:
                            selected_epics.append(epic_key)
                            epic_counts[epic_key] = {
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                                "payment_frequency_options": mapped_frequencies,
                            }

                    elif epic_key == "SumAssuredValidation":
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                        with st.expander("Show/Hide PPT Configuration", expanded=False):
                            header = st.columns([0.5, 2, 1, 1])
                            with header[1]:
                                st.markdown("**PPT Type**")
                            with header[2]:
                                st.markdown("**Min**")
                            with header[3]:
                                st.markdown("**Max**")

                            row_sp = st.columns([0.5, 2, 1, 1])
                            with row_sp[0]:
                                sp = st.checkbox(
                                    "Enable",
                                    value=is_selected,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"sa_enabled_{epic_key}"
                                    ),
                                    label_visibility="collapsed",
                                )
                            with row_sp[1]:
                                st.markdown("SinglePay")
                            with row_sp[2]:
                                min_sp = st.number_input(
                                    "Min SinglePay",
                                    min_value=0,
                                    value=sum_assured_ranges["Single Pay"][0],
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"min_sp_{epic_key}"
                                    ),
                                    label_visibility="collapsed",
                                )
                            with row_sp[3]:
                                max_sp = st.number_input(
                                    "Max SinglePay",
                                    min_value=min_sp,
                                    value=sum_assured_ranges["Single Pay"][1],
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"max_sp_{epic_key}"
                                    ),
                                    label_visibility="collapsed",
                                )

                            row_oth = st.columns([0.5, 2, 1, 1])
                            with row_oth[0]:
                                oth = st.checkbox(
                                    "Enable",
                                    value=is_selected,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"oth_enabled_{epic_key}"
                                    ),
                                    label_visibility="collapsed",
                                )
                            with row_oth[1]:
                                st.markdown("Others")
                            with row_oth[2]:
                                min_oth = st.number_input(
                                    "Min Others",
                                    min_value=0,
                                    value=sum_assured_ranges["Others"][0],
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"min_oth_{epic_key}"
                                    ),
                                    label_visibility="collapsed",
                                )
                            with row_oth[3]:
                                max_oth = st.number_input(
                                    "Max Others",
                                    min_value=min_oth,
                                    value=sum_assured_ranges["Others"][1],
                                    key=lifecycle_key(
                                        lifecycle_key_prefix, f"max_oth_{epic_key}"
                                    ),
                                    label_visibility="collapsed",
                                )

                            if is_selected:
                                selected_epics.append(epic_key)
                                if epic_key not in epic_counts:
                                    epic_counts[epic_key] = {}
                                if sp:
                                    epic_counts[epic_key]["Single Pay"] = {
                                        "min_val": min_sp,
                                        "max_val": max_sp,
                                        "positive": num_positive_global,
                                        "negative": num_negative_global,
                                    }
                                if oth:
                                    epic_counts[epic_key]["Others"] = {
                                        "min_val": min_oth,
                                        "max_val": max_oth,
                                        "positive": num_positive_global,
                                        "negative": num_negative_global,
                                    }
                    else:
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all,
                            key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}"),
                        )
                        if is_selected:
                            selected_epics.append(epic_key)
                            epic_counts[epic_key] = {
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                            }

    return selected_epics, epic_counts


def render_rider_epics(
    logic_module,
    lifecycle_key_prefix,
    count_mode,
    num_positive_global,
    num_negative_global,
):
    epic_counts_rider = {}
    selected_epics_rider = []
    if not logic_module or not hasattr(logic_module, "EPIC_MAP_RIDER"):
        return selected_epics_rider, epic_counts_rider

    epic_map_rider = getattr(logic_module, "EPIC_MAP_RIDER")
    plan_type = st.session_state.get("plan_type_selector", "term plan")
    ppt_config = get_ppt_config(plan_type)
    ppt_names = ppt_config["ppt_names"]
    # For ULIP, rider ranges are same as base; for term/saving, keep as before
    if plan_type == "ulip plan":
        entry_age_ppt_ranges = ppt_config["entry_age"]
        policy_term_ppt_ranges = ppt_config["policy_term"]
        maturity_age_ppt_ranges = ppt_config["maturity_age"]
        premium_paying_ppt_ranges = ppt_config["premium_paying_term"]
    else:
        entry_age_ppt_ranges = {
            "Single Pay": (18, 65),
            "Limited Pay (5 pay)": (18, 65),
            "Limited Pay (10 pay)": (18, 65),
            "Limited Pay (15 pay)": (18, 65),
            "Limited Pay (Pay till age 60)": (18, 55),
            "Regular Pay": (18, 65),
        }
        policy_term_ppt_ranges = {
            "Single Pay": (1, 5),
            "Limited Pay (5 pay)": (10, 67),
            "Limited Pay (10 pay)": (15, 67),
            "Limited Pay (15 pay)": (20, 67),
            "Limited Pay (Pay till age 60)": (5, 67),
            "Regular Pay": (5, 67),
        }
        maturity_age_ppt_ranges = {
            "Single Pay": (23, 75),
            "Limited Pay (5 pay)": (23, 75),
            "Limited Pay (10 pay)": (23, 75),
            "Limited Pay (15 pay)": (23, 75),
            "Limited Pay (Pay till age 60)": (23, 75),
            "Regular Pay": (23, 75),
        }
        premium_paying_ppt_ranges = {
            "Single Pay": (1, 1),
            "Limited Pay (5 pay)": (5, 5),
            "Limited Pay (10 pay)": (10, 10),
            "Limited Pay (15 pay)": (15, 15),
            "Limited Pay (Pay till age 60)": (5, 42),
            "Regular Pay": (5, 67),
        }
    sum_assured_ranges = ppt_config["sum_assured"]
    select_all_rider = st.checkbox(
        "Select/Deselect All Epics",
        value=True,
        key=lifecycle_key(lifecycle_key_prefix, "select_all_epics_master_rider"),
    )

    with st.expander("\u2139\ufe0f Configure Rider Epics and Case Counts", expanded=True):
        for epic_key, epic_desc in epic_map_rider.items():

            if count_mode == "Set Individual Counts for Each Epic":
                if epic_key in [
                    "EntryAge",
                    "PremiumPayingTerm",
                    "PolicyTerm",
                    "MaturityAge",
                ]:
                    is_selected = st.checkbox(
                        epic_desc,
                        value=select_all_rider,
                        key=lifecycle_key(
                            lifecycle_key_prefix, f"epic_cb_{epic_key}_rider"
                        ),
                    )
                    with st.expander("Show/Hide PPT Configuration", expanded=False):
                        ppt_age_ranges, ppt_pos_counts, ppt_neg_counts, ppt_enabled = (
                            {},
                            {},
                            {},
                            {},
                        )

                        header = st.columns([0.5, 2, 2, 1, 1])
                        with header[1]:
                            st.markdown("**PPT Name**")
                        with header[2]:
                            st.markdown("**Min/Max**")
                        with header[3]:
                            st.markdown("**Pos**")
                        with header[4]:
                            st.markdown("**Neg**")

                        for ppt in ppt_names:
                            row = st.columns([0.5, 2, 2, 1, 1])
                            with row[0]:
                                enabled = st.checkbox(
                                    "Enable",
                                    value=is_selected,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"ppt_enabled_{epic_key}_{ppt}_rider",
                                    ),
                                    label_visibility="collapsed",
                                )
                            with row[1]:
                                st.markdown(ppt)
                            with row[2]:
                                if epic_key == "EntryAge":
                                    min_age, max_age = st.slider(
                                        "Entry Age",
                                        0,
                                        85,
                                        entry_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"entry_age_slider_{epic_key}_{ppt}_rider",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "PolicyTerm":
                                    min_age, max_age = st.slider(
                                        "Policy Term",
                                        5,
                                        80,
                                        policy_term_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"entry_age_slider_{epic_key}_{ppt}_rider",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaturityAge":
                                    min_age, max_age = st.slider(
                                        "Maturity Age",
                                        1,
                                        90,
                                        maturity_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"maturity_age_slider_{epic_key}_{ppt}_rider",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                else:
                                    if (
                                        premium_paying_ppt_ranges[ppt][0]
                                        == premium_paying_ppt_ranges[ppt][1]
                                    ):
                                        min_age = max_age = st.slider(
                                            "Entry Age",
                                            0,
                                            85,
                                            premium_paying_ppt_ranges[ppt][0],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"entry_age_slider_{epic_key}_{ppt}_rider",
                                            ),
                                            label_visibility="collapsed",
                                        )
                                    else:
                                        min_age, max_age = st.slider(
                                            "Entry Age",
                                            0,
                                            85,
                                            premium_paying_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"entry_age_slider_{epic_key}_{ppt}_rider",
                                            ),
                                            label_visibility="collapsed",
                                        )
                            with row[3]:
                                pos = st.number_input(
                                    "Pos",
                                    0,
                                    value=5,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"epic_pos_{epic_key}_{ppt}_rider",
                                    ),
                                    label_visibility="collapsed",
                                )
                            with row[4]:
                                neg = st.number_input(
                                    "Neg",
                                    0,
                                    value=5,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"epic_neg_{epic_key}_{ppt}_rider",
                                    ),
                                    label_visibility="collapsed",
                                )

                            if enabled:
                                ppt_age_ranges[ppt] = (min_age, max_age)
                                ppt_pos_counts[ppt] = pos
                                ppt_neg_counts[ppt] = neg
                                ppt_enabled[ppt] = True
                            else:
                                ppt_enabled[ppt] = False

                        if is_selected and any(ppt_enabled.values()):
                            selected_epics_rider.append(epic_key)
                            epic_counts_rider[epic_key] = {
                                "ppt_age_ranges": ppt_age_ranges,
                                "ppt_pos_counts": ppt_pos_counts,
                                "ppt_neg_counts": ppt_neg_counts,
                                "ppt_enabled": ppt_enabled,
                            }

                elif epic_key == "PaymentFrequency":
                    row = st.columns([2, 1.5, 1.5])
                    with row[0]:
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all_rider,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_cb_{epic_key}_rider"
                            ),
                        )
                    with row[1]:
                        pos_count = st.number_input(
                            f"Pos {epic_key}",
                            min_value=0,
                            value=5,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_pos_{epic_key}_rider"
                            ),
                            label_visibility="collapsed",
                            placeholder="Pos",
                        )
                    with row[2]:
                        neg_count = st.number_input(
                            f"Neg {epic_key}",
                            min_value=0,
                            value=5,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_neg_{epic_key}_rider"
                            ),
                            label_visibility="collapsed",
                            placeholder="Neg",
                        )

                    frequency_options = [
                        "Annual",
                        "Half-Yearly",
                        "Quarterly",
                        "Monthly",
                        "Single Pay",
                    ]
                    frequency_map = {
                        "Annual": 1,
                        "Half-Yearly": 2,
                        "Quarterly": 3,
                        "Monthly": 4,
                        "Single Pay": 5,
                    }
                    freq_cols = st.columns(len(frequency_options) + 1)
                    selected_frequencies = []
                    for i, freq in enumerate(frequency_options):
                        with freq_cols[i + 1]:
                            if st.checkbox(
                                freq,
                                value=is_selected,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"freq_cb_{freq}_rider"
                                ),
                            ):
                                selected_frequencies.append(freq)

                    mapped_frequencies = [frequency_map[f] for f in selected_frequencies]

                    if is_selected:
                        selected_epics_rider.append(epic_key)
                        epic_counts_rider[epic_key] = {
                            "positive": pos_count,
                            "negative": neg_count,
                            "payment_frequency_options": mapped_frequencies,
                        }

                elif epic_key == "SumAssuredValidation":
                    is_selected = st.checkbox(
                        epic_desc,
                        value=select_all_rider,
                        key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}_rider"),
                    )
                    with st.expander("Show/Hide PPT Configuration", expanded=False):
                        header = st.columns([0.5, 2, 1, 1, 1, 1])
                        with header[1]:
                            st.markdown("**PPT Type**")
                        with header[2]:
                            st.markdown("**Min**")
                        with header[3]:
                            st.markdown("**Max**")
                        with header[4]:
                            st.markdown("**Pos**")
                        with header[5]:
                            st.markdown("**Neg**")

                        row_sp = st.columns([0.5, 2, 1, 1, 1, 1])
                        with row_sp[0]:
                            sp = st.checkbox(
                                "Enable",
                                value=is_selected,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"sa_enabled_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[1]:
                            st.markdown("SinglePay")
                        with row_sp[2]:
                            min_sp = st.number_input(
                                "Min SinglePay",
                                min_value=0,
                                value=sum_assured_ranges["Single Pay"][0],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"min_sp_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[3]:
                            max_sp = st.number_input(
                                "Max SinglePay",
                                min_value=min_sp,
                                value=sum_assured_ranges["Single Pay"][1],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"max_sp_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[4]:
                            pos_sp = st.number_input(
                                "Pos SinglePay",
                                min_value=0,
                                value=5,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"pos_sp_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[5]:
                            neg_sp = st.number_input(
                                "Neg SinglePay",
                                min_value=0,
                                value=5,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"neg_sp_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )

                        row_oth = st.columns([0.5, 2, 1, 1, 1, 1])
                        with row_oth[0]:
                            oth = st.checkbox(
                                "Enable",
                                value=is_selected,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"oth_enabled_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[1]:
                            st.markdown("Others")
                        with row_oth[2]:
                            min_oth = st.number_input(
                                "Min Others",
                                min_value=0,
                                value=sum_assured_ranges["Others"][0],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"min_oth_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[3]:
                            max_oth = st.number_input(
                                "Max Others",
                                min_value=min_oth,
                                value=sum_assured_ranges["Others"][1],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"max_oth_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[4]:
                            pos_oth = st.number_input(
                                "Pos Others",
                                min_value=0,
                                value=5,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"pos_oth_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[5]:
                            neg_oth = st.number_input(
                                "Neg Others",
                                min_value=0,
                                value=5,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"neg_oth_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )

                        if is_selected:
                            selected_epics_rider.append(epic_key)
                            if epic_key not in epic_counts_rider:
                                epic_counts_rider[epic_key] = {}
                            if sp:
                                epic_counts_rider[epic_key]["Single Pay"] = {
                                    "min_val": min_sp,
                                    "max_val": max_sp,
                                    "positive": pos_sp,
                                    "negative": neg_sp,
                                }
                            if oth:
                                epic_counts_rider[epic_key]["Others"] = {
                                    "min_val": min_oth,
                                    "max_val": max_oth,
                                    "positive": pos_oth,
                                    "negative": neg_oth,
                                }

                else:
                    row = st.columns([2, 1.5, 1.5])
                    with row[0]:
                        is_selected = st.checkbox(
                            epic_desc,
                            value=select_all_rider,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_cb_{epic_key}_rider"
                            ),
                        )
                    with row[1]:
                        pos_count = st.number_input(
                            f"Pos {epic_key}",
                            min_value=0,
                            value=5,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_pos_{epic_key}_rider"
                            ),
                            label_visibility="collapsed",
                            placeholder="Pos",
                        )
                    with row[2]:
                        neg_count = st.number_input(
                            f"Neg {epic_key}",
                            min_value=0,
                            value=5,
                            key=lifecycle_key(
                                lifecycle_key_prefix, f"epic_neg_{epic_key}_rider"
                            ),
                            label_visibility="collapsed",
                            placeholder="Neg",
                        )
                    if is_selected:
                        selected_epics_rider.append(epic_key)
                        epic_counts_rider[epic_key] = {
                            "positive": pos_count,
                            "negative": neg_count,
                        }

            else:  # Apply Same Count to All Epics
                if epic_key in [
                    "EntryAge",
                    "PremiumPayingTerm",
                    "PolicyTerm",
                    "MaturityAge",
                ]:
                    is_selected = st.checkbox(
                        epic_desc,
                        value=select_all_rider,
                        key=lifecycle_key(
                            lifecycle_key_prefix, f"epic_cb_{epic_key}_rider"
                        ),
                    )
                    with st.expander("Show/Hide PPT Configuration", expanded=False):
                        ppt_age_ranges, ppt_enabled = {}, {}

                        for ppt in ppt_names:
                            row = st.columns([0.5, 2, 2])
                            with row[0]:
                                enabled = st.checkbox(
                                    "Enable",
                                    value=is_selected,
                                    key=lifecycle_key(
                                        lifecycle_key_prefix,
                                        f"ppt_enabled_all_{epic_key}_{ppt}_rider",
                                    ),
                                    label_visibility="collapsed",
                                )
                            with row[1]:
                                st.markdown(ppt)
                            with row[2]:
                                if epic_key == "EntryAge":
                                    min_age, max_age = st.slider(
                                        "Entry Age",
                                        0,
                                        85,
                                        entry_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"entry_age_slider_{epic_key}_{ppt}_rider",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "PolicyTerm":
                                    min_age, max_age = st.slider(
                                        "Policy Term",
                                        5,
                                        80,
                                        policy_term_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"entry_age_slider_{epic_key}_{ppt}_rider",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                elif epic_key == "MaturityAge":
                                    min_age, max_age = st.slider(
                                        "Maturity Age",
                                        1,
                                        90,
                                        maturity_age_ppt_ranges[ppt],
                                        key=lifecycle_key(
                                            lifecycle_key_prefix,
                                            f"maturity_age_slider_{epic_key}_{ppt}_rider",
                                        ),
                                        label_visibility="collapsed",
                                    )
                                else:
                                    if (
                                        premium_paying_ppt_ranges[ppt][0]
                                        == premium_paying_ppt_ranges[ppt][1]
                                    ):
                                        min_age = max_age = st.slider(
                                            "Entry Age",
                                            0,
                                            85,
                                            premium_paying_ppt_ranges[ppt][0],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"entry_age_slider_{epic_key}_{ppt}_rider",
                                            ),
                                            label_visibility="collapsed",
                                        )
                                    else:
                                        min_age, max_age = st.slider(
                                            "Entry Age",
                                            0,
                                            85,
                                            premium_paying_ppt_ranges[ppt],
                                            key=lifecycle_key(
                                                lifecycle_key_prefix,
                                                f"entry_age_slider_{epic_key}_{ppt}_rider",
                                            ),
                                            label_visibility="collapsed",
                                        )
                            if enabled:
                                ppt_age_ranges[ppt] = (min_age, max_age)
                                ppt_enabled[ppt] = True
                            else:
                                ppt_enabled[ppt] = False

                        if is_selected and any(ppt_enabled.values()):
                            selected_epics_rider.append(epic_key)
                            epic_counts_rider[epic_key] = {
                                "ppt_age_ranges": ppt_age_ranges,
                                "ppt_enabled": ppt_enabled,
                                "positive": num_positive_global,
                                "negative": num_negative_global,
                            }

                elif epic_key == "PaymentFrequency":
                    is_selected = st.checkbox(
                        epic_desc,
                        value=select_all_rider,
                        key=lifecycle_key(
                            lifecycle_key_prefix, f"epic_cb_{epic_key}_rider"
                        ),
                    )
                    frequency_options = [
                        "Annual",
                        "Half-Yearly",
                        "Quarterly",
                        "Monthly",
                        "Single Pay",
                    ]
                    frequency_map = {
                        "Annual": 1,
                        "Half-Yearly": 2,
                        "Quarterly": 3,
                        "Monthly": 4,
                        "Single Pay": 5,
                    }
                    freq_cols = st.columns(len(frequency_options) + 1)
                    selected_frequencies = []
                    for i, freq in enumerate(frequency_options):
                        with freq_cols[i + 1]:
                            if st.checkbox(
                                freq,
                                value=is_selected,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"freq_cb_{freq}_rider"
                                ),
                            ):
                                selected_frequencies.append(freq)

                    mapped_frequencies = [frequency_map[f] for f in selected_frequencies]

                    if is_selected:
                        selected_epics_rider.append(epic_key)
                        epic_counts_rider[epic_key] = {
                            "positive": num_positive_global,
                            "negative": num_negative_global,
                            "payment_frequency_options": mapped_frequencies,
                        }

                elif epic_key == "SumAssuredValidation":
                    is_selected = st.checkbox(
                        epic_desc,
                        value=select_all_rider,
                        key=lifecycle_key(lifecycle_key_prefix, f"epic_cb_{epic_key}_rider"),
                    )
                    with st.expander("Show/Hide PPT Configuration", expanded=False):
                        header = st.columns([0.5, 2, 1, 1])
                        with header[1]:
                            st.markdown("**PPT Type**")
                        with header[2]:
                            st.markdown("**Min**")
                        with header[3]:
                            st.markdown("**Max**")

                        row_sp = st.columns([0.5, 2, 1, 1])
                        with row_sp[0]:
                            sp = st.checkbox(
                                "Enable",
                                value=is_selected,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"sa_enabled_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[1]:
                            st.markdown("SinglePay")
                        with row_sp[2]:
                            min_sp = st.number_input(
                                "Min SinglePay",
                                min_value=0,
                                value=sum_assured_ranges["Single Pay"][0],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"min_sp_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_sp[3]:
                            max_sp = st.number_input(
                                "Max SinglePay",
                                min_value=min_sp,
                                value=sum_assured_ranges["Single Pay"][1],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"max_sp_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )

                        row_oth = st.columns([0.5, 2, 1, 1])
                        with row_oth[0]:
                            oth = st.checkbox(
                                "Enable",
                                value=is_selected,
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"oth_enabled_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[1]:
                            st.markdown("Others")
                        with row_oth[2]:
                            min_oth = st.number_input(
                                "Min Others",
                                min_value=0,
                                value=sum_assured_ranges["Others"][0],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"min_oth_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )
                        with row_oth[3]:
                            max_oth = st.number_input(
                                "Max Others",
                                min_value=min_oth,
                                value=sum_assured_ranges["Others"][1],
                                key=lifecycle_key(
                                    lifecycle_key_prefix, f"max_oth_{epic_key}_rider"
                                ),
                                label_visibility="collapsed",
                            )

                        if is_selected:
                            selected_epics_rider.append(epic_key)
                            if epic_key not in epic_counts_rider:
                                epic_counts_rider[epic_key] = {}
                            if sp:
                                epic_counts_rider[epic_key]["Single Pay"] = {
                                    "min_val": min_sp,
                                    "max_val": max_sp,
                                    "positive": num_positive_global,
                                    "negative": num_negative_global,
                                }
                            if oth:
                                epic_counts_rider[epic_key]["Others"] = {
                                    "min_val": min_oth,
                                    "max_val": max_oth,
                                    "positive": num_positive_global,
                                    "negative": num_negative_global,
                                }

                else:
                    is_selected = st.checkbox(
                        epic_desc,
                        value=select_all_rider,
                        key=lifecycle_key(
                            lifecycle_key_prefix, f"epic_cb_{epic_key}_rider"
                        ),
                    )
                    if is_selected:
                        selected_epics_rider.append(epic_key)
                        epic_counts_rider[epic_key] = {
                            "positive": num_positive_global,
                            "negative": num_negative_global,
                        }

    return selected_epics_rider, epic_counts_rider


def _initialize_session_state():
    if "generated_df" not in st.session_state:
        st.session_state.generated_df = None
    if "selected_module_name_py" not in st.session_state:
        st.session_state.selected_module_name_py = None
    if "selected_display_name" not in st.session_state:
        st.session_state.selected_display_name = None
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "epic_counts_to_generate" not in st.session_state:
        st.session_state.epic_counts_to_generate = {}
    if "epic_counts_to_generate_rider" not in st.session_state:
        st.session_state.epic_counts_to_generate_rider = {}
    if "config_loaded" not in st.session_state:
        st.session_state.config_loaded = False
    if "selected_lifecycle_for_output" not in st.session_state:
        st.session_state.selected_lifecycle_for_output = "pre issuance"
    if "plan_type_selector" not in st.session_state:
        st.session_state.plan_type_selector = "term plan"
    if "post_issuance_selected_header" not in st.session_state:
        st.session_state.post_issuance_selected_header = None


def _render_generation_output(df_to_display):
    st.header(
        f"Generated using: {st.session_state.selected_display_name} ({st.session_state.get('selected_lifecycle_for_output', 'pre issuance')})"
    )
    st.divider()

    display_generation_summary(df_to_display)
    st.divider()

    st.subheader(
        f"\U0001F4D1 Sample Data (10 random rows from {len(df_to_display)} total)"
    )
    rule_columns_to_style = [
        col for col in df_to_display.columns if col.startswith("Rule_")
    ]

    sample_df = df_to_display.sample(min(10, len(df_to_display)))
    st.dataframe(
        sample_df.style.apply(highlight_rule_outcomes, subset=rule_columns_to_style),
        height=400,
        use_container_width=True,
    )
    st.divider()

    st.subheader("\U0001F4BE Download Results")
    current_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    file_prefix = f"{st.session_state.selected_module_name_py}_test_cases_{current_timestamp}"

    output_excel = BytesIO()
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        df_to_display.to_excel(writer, index=False, sheet_name="TestCases")

        workbook = writer.book
        worksheet = writer.sheets["TestCases"]

        # Format: wrap + center + middle
        cell_format = workbook.add_format(
            {"text_wrap": True, "align": "center", "valign": "vcenter"}
        )

        header_format = workbook.add_format(
            {"bold": True, "text_wrap": True, "align": "center", "valign": "vcenter"}
        )

        # Apply header format
        for col_num, col_name in enumerate(df_to_display.columns):
            worksheet.write(0, col_num, col_name, header_format)

        # Auto column width
        for col_num, col_name in enumerate(df_to_display.columns):
            max_length = len(str(col_name))

            for cell_value in df_to_display[col_name]:
                if pd.notna(cell_value):
                    max_length = max(max_length, len(str(cell_value)))

            # Add padding and cap width (important for very long text)
            adjusted_width = min(max_length + 1, 50)

            worksheet.set_column(col_num, col_num, adjusted_width, cell_format)

    excel_data = output_excel.getvalue()

    csv_data = df_to_display.to_csv(index=False).encode("utf-8")

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="\U0001F4E5 Download Excel File (.xlsx)",
            data=excel_data,
            file_name=f"{file_prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_excel",
        )
    with col_dl2:
        st.download_button(
            label="\U0001F4C4 Download CSV File (.csv)",
            data=csv_data,
            file_name=f"{file_prefix}.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_csv",
        )
    st.caption("Files will download automatically after clicking.")


def render_plan_ui(plan_type, display_name_default=None):
    _initialize_session_state()
    st.session_state["plan_type_selector"] = plan_type
    render_app_header()

    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("\U0001F6E0\ufe0f Configuration Management")

        # Configuration Save/Load Section
        with st.expander("\U0001F4BE Save/Load Configurations", expanded=False):
            # Save Configuration
            st.subheader("Save Current Configuration")
            save_config_name = st.text_input(
                "Configuration Name", key="save_config_name_input"
            )
            selected_plan_for_configs = plan_type
            if st.button("\U0001F4BE Save Configuration", use_container_width=True):
                if save_config_name:
                    config = collect_current_config()
                    scoped_name = get_scoped_config_name(
                        save_config_name, selected_plan_for_configs
                    )
                    if save_configuration(scoped_name, config):
                        st.success(
                            f"\u2705 Configuration '{save_config_name}' saved successfully!"
                        )
                        st.rerun()
                else:
                    st.warning("Please enter a configuration name")

            # Load Configuration
            st.subheader("Load Saved Configuration")
            scoped_prefix = f"{selected_plan_for_configs}::"
            all_saved_configs = get_saved_configurations()
            saved_configs = sorted(
                [
                    strip_scoped_config_name(config_name, selected_plan_for_configs)
                    for config_name in all_saved_configs
                    if config_name.startswith(scoped_prefix)
                ]
            )
            if saved_configs:
                selected_config = st.selectbox(
                    "Select Configuration", saved_configs, key="load_config_select"
                )
                selected_scoped_config = get_scoped_config_name(
                    selected_config, selected_plan_for_configs
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("\U0001F4C2 Load", use_container_width=True):
                        config = load_configuration(selected_scoped_config)
                        if config:
                            apply_config_to_ui(config)
                            st.session_state.config_loaded = True
                            st.success(f"\u2705 Configuration '{selected_config}' loaded!")
                            st.rerun()

                with col2:
                    if st.button("\U0001F5D1\ufe0f Delete", use_container_width=True):
                        if delete_configuration(selected_scoped_config):
                            st.success(
                                f"\u2705 Configuration '{selected_config}' deleted!"
                            )
                            st.rerun()
            else:
                st.info(
                    f"No saved configurations found for '{selected_plan_for_configs}'"
                )

        selected_lifecycle_for_module = st.session_state.get(
            "lifecycle_to_generate", "pre issuance"
        )
        selected_module_for_plan = resolve_plan_lifecycle_module(
            plan_type, selected_lifecycle_for_module
        )
        selected_module_path = os.path.join(
            LOGIC_MODULE_DIR, f"{selected_module_for_plan}.py"
        )
        if not os.path.exists(selected_module_path):
            st.error(
                f"Logic module file '{selected_module_for_plan}.py' not found in '{LOGIC_MODULE_DIR}'."
            )
            st.stop()

        # Initialize session defaults if missing
        if "product_display_name_input" not in st.session_state:
            default_name = display_name_default or plan_type.title()
            st.session_state["product_display_name_input"] = default_name
        if "product_code_input" not in st.session_state:
            # prefer any existing stored code, else empty
            st.session_state["product_code_input"] = (
                st.session_state.get("product_code", "") or ""
            )
        st.session_state["selected_module_name_py"] = selected_module_for_plan

        # Let user type a display name and a product code
        st.markdown(
            """
            <style>
            input[type="text"] {
                font-size: 20px !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Input fields
        st.text_input("Product display name", key="product_display_name_input")
        st.text_input("Product code", key="product_code_input")

        # mirror to commonly used session keys for backward compatibility
        st.session_state["selected_display_name"] = st.session_state.get(
            "product_display_name_input"
        )
        st.session_state["product_code"] = st.session_state.get("product_code_input")
        # ensure the module pointer remains aligned to selected plan type
        st.session_state["selected_module_name_py"] = selected_module_for_plan

        st.header("Configure Case Counts")

        count_mode = st.radio(
            "Select Count Mode:",
            options=[
                "Apply Same Count to All Epics",
                "Set Individual Counts for Each Epic",
            ],
            index=0,
            key="count_mode_selector",
        )

        num_positive_global, num_negative_global = 5, 5
        if count_mode == "Apply Same Count to All Epics":
            col1, col2 = st.columns(2)
            with col1:
                num_positive_global = st.number_input(
                    "Positive Cases", min_value=0, value=5
                )
            with col2:
                num_negative_global = st.number_input(
                    "Negative Cases", min_value=0, value=5
                )

    # --- Epic and Case Count Selection on Main Canvas ---
    lifecycle_options = LIFECYCLE_OPTIONS
    lifecycle_prefix_map = LIFECYCLE_PREFIX_MAP

    phase_configs = {
        option: {
            "selected_epics": [],
            "epic_counts": {},
            "selected_epics_rider": [],
            "epic_counts_rider": {},
            "selected_header": None,
        }
        for option in lifecycle_options
    }

    if st.session_state.selected_module_name_py and st.session_state.generated_df is None:
        st.markdown(
            """
                    <style>
                    div[data-testid="stExpander"] button * ,
                    div[data-testid="stExpander"] summary * ,
                    div[data-testid="stExpander"] [role="button"] * {
                        font-size: 16px !important;
                        font-weight: 600 !important;
                    }
                """,
            unsafe_allow_html=True,
        )

        lifecycle_tabs = st.tabs(lifecycle_options)
        for lifecycle_name, lifecycle_tab in zip(lifecycle_options, lifecycle_tabs):
            with lifecycle_tab:
                lifecycle_prefix = lifecycle_prefix_map[lifecycle_name]
                has_rider_tab = plan_type != "saving plan"
                if has_rider_tab:
                    base_tab, rider_tab = st.tabs(["Base Plan Epics", "Rider Epics"])
                else:
                    base_tab, = st.tabs(["Plan Epics"])


                lifecycle_module_name = resolve_plan_lifecycle_module(
                    plan_type, lifecycle_name
                )
                lifecycle_module_path = os.path.join(
                    LOGIC_MODULE_DIR, f"{lifecycle_module_name}.py"
                )
                if not os.path.exists(lifecycle_module_path):
                    st.error(
                        f"Missing logic module '{lifecycle_module_name}.py' for {plan_type} - {lifecycle_name}."
                    )
                    continue

                logic_module = load_logic_module(
                    lifecycle_module_name,
                    override_display_name=st.session_state.get(
                        "product_display_name_input"
                    ),
                    override_product_code=st.session_state.get("product_code_input"),
                )

                if lifecycle_name == "post issuance":
                    with base_tab:
                        selected_header, selected_epics, epic_counts = (
                            render_post_issuance_epics(
                                plan_type,
                                lifecycle_prefix,
                                count_mode,
                                num_positive_global,
                                shared_lifecycle_prefix=lifecycle_prefix,
                            )
                        )
                    if has_rider_tab:
                        with rider_tab:
                            _, selected_epics_rider, epic_counts_rider = (
                                render_post_issuance_epics(
                                    plan_type,
                                    f"{lifecycle_prefix}_rider",
                                    count_mode,
                                    num_positive_global,
                                    shared_lifecycle_prefix=lifecycle_prefix,
                                )
                            )
                    else:
                        selected_epics_rider, epic_counts_rider = [], {}
                else:
                    selected_header = None
                    with base_tab:
                        selected_epics, epic_counts = render_base_plan_epics(
                            logic_module,
                            lifecycle_prefix,
                            count_mode,
                            num_positive_global,
                            num_negative_global,
                        )
                    if has_rider_tab:
                        with rider_tab:
                            selected_epics_rider, epic_counts_rider = render_rider_epics(
                                logic_module,
                                lifecycle_prefix,
                                count_mode,
                                num_positive_global,
                                num_negative_global,
                            )
                    else:
                        selected_epics_rider, epic_counts_rider = [], {}

                phase_configs[lifecycle_name]["selected_epics"] = selected_epics
                phase_configs[lifecycle_name]["epic_counts"] = epic_counts
                phase_configs[lifecycle_name][
                    "selected_epics_rider"
                ] = selected_epics_rider
                phase_configs[lifecycle_name][
                    "epic_counts_rider"
                ] = epic_counts_rider
                phase_configs[lifecycle_name]["selected_header"] = selected_header
                phase_configs[lifecycle_name][
                    "module_name_py"
                ] = lifecycle_module_name

    # --- Sidebar buttons for actions ---
    with st.sidebar:
        st.header("Generate")
        st.radio(
            "Lifecycle Stage",
            options=lifecycle_options,
            key="lifecycle_to_generate",
        )
        if plan_type == "ulip plan":
            selected_lifecycle = st.session_state.get(
                "lifecycle_to_generate", "pre issuance"
            )
            lifecycle_prefix = LIFECYCLE_PREFIX_MAP.get(
                selected_lifecycle, "pre_issuance"
            )
            portfolio_key = lifecycle_key(lifecycle_prefix, "portfolio_type")
            st.selectbox(
                "Portfolio Type",
                options=["LIFESTYLE", "SELFMANAGED"],
                key=portfolio_key,
            )

        if st.button(
            "\U0001F680 Generate Test Cases",
            type="primary",
            disabled=st.session_state.processing,
            use_container_width=True,
        ):
            selected_lifecycle = st.session_state.get(
                "lifecycle_to_generate", "pre issuance"
            )
            selected_phase_config = phase_configs.get(selected_lifecycle, {})
            selected_epics = selected_phase_config.get("selected_epics", [])
            selected_epics_rider = selected_phase_config.get(
                "selected_epics_rider", []
            )
            selected_header = selected_phase_config.get("selected_header")

            if not st.session_state.selected_module_name_py:
                st.warning("Please select a product.")
            elif not (selected_epics or selected_epics_rider):
                st.warning(
                    "Please select at least one epic to generate from the main screen."
                )
            else:
                selected_module_name = selected_phase_config.get(
                    "module_name_py",
                    resolve_plan_lifecycle_module(plan_type, selected_lifecycle),
                )
                st.session_state.processing = True
                st.session_state.selected_lifecycle_for_output = selected_lifecycle
                st.session_state.selected_module_name_py = selected_module_name
                st.session_state.epic_counts_to_generate = selected_phase_config.get(
                    "epic_counts", {}
                )
                st.session_state.epic_counts_to_generate_rider = selected_phase_config.get(
                    "epic_counts_rider", {}
                )
                st.session_state.post_issuance_selected_header = selected_header
                st.rerun()

        if st.session_state.generated_df is not None:
            if st.button(
                "\U0001F9F9 Clear Results & Start Over",
                use_container_width=True,
                disabled=st.session_state.processing,
            ):
                st.session_state.generated_df = None
                st.session_state.processing = False
                st.rerun()

    # --- Main Canvas Logic ---
    if st.session_state.processing and st.session_state.selected_module_name_py:
        with st.spinner("Generating test cases... Please wait."):
            logic_module = load_logic_module(
                st.session_state.selected_module_name_py,
                override_display_name=st.session_state.get("product_display_name_input"),
                override_product_code=st.session_state.get("product_code_input"),
            )
            if logic_module:
                if hasattr(logic_module, "generate_test_cases") and callable(
                    logic_module.generate_test_cases
                ):
                    try:
                        generate_kwargs = {
                            "epic_counts": st.session_state.epic_counts_to_generate,
                            "selected_epics": list(
                                st.session_state.epic_counts_to_generate.keys()
                            ),
                            "epic_counts_rider": st.session_state.epic_counts_to_generate_rider,
                            "selected_epics_rider": list(
                                st.session_state.epic_counts_to_generate_rider.keys()
                            ),
                        }
                        if (
                            st.session_state.get("selected_lifecycle_for_output")
                            == "post issuance"
                        ):
                            generate_kwargs["selected_header"] = st.session_state.get(
                                "post_issuance_selected_header"
                            )
                        if plan_type == "ulip plan":
                            lifecycle_prefix = LIFECYCLE_PREFIX_MAP.get(
                                selected_lifecycle, "pre_issuance"
                            )
                            portfolio_key = lifecycle_key(lifecycle_prefix, "portfolio_type")
                            generate_kwargs["portfolio_type"] = st.session_state.get(
                                portfolio_key, "LIFESTYLE"
                            )

                        df = logic_module.generate_test_cases(**generate_kwargs)
                        st.session_state.generated_df = df
                        st.success(
                            f"Successfully generated {len(df)} test cases!"
                        )
                    except Exception as e:
                        st.error("Error during test case generation:")
                        st.exception(e)
                        st.session_state.generated_df = None
                else:
                    st.error("Module does not have a 'generate_test_cases' function.")
                    st.session_state.generated_df = None
            else:
                st.error("Failed to load the logic module.")
                st.session_state.generated_df = None
        st.session_state.processing = False
        st.rerun()

    elif st.session_state.generated_df is not None:
        _render_generation_output(st.session_state.generated_df)

    elif not st.session_state.selected_module_name_py:
        st.info("\U0001F44B Welcome! Please select a product from the sidebar to begin.")

    else:
        st.info("\u2139\ufe0f Configure your test run, then click 'Generate Test Cases' in the sidebar.")
