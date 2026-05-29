import streamlit as st
from ui_common import configure_app_shell, PLAN_LIFECYCLE_MODULE_MAP
from term_plan_ui import render_term_plan_ui
from saving_plan_ui import render_saving_plan_ui
from ulip_plan_ui import render_ulip_plan_ui

configure_app_shell()

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
