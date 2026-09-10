from ui_common import render_plan_ui, get_selected_ulip_variant


def render_ulip_plan_ui():
    render_plan_ui("ulip plan", display_name_default=get_selected_ulip_variant())
