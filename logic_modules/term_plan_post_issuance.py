import calendar
import random
from datetime import date, datetime, timedelta

import pandas as pd

from logic_modules import term_plan_issuance as issuance

# Constants
FLC_PERIOD_DAYS = 30
GRACE_PERIOD_MONTHLY = 15
GRACE_PERIOD_OTHER = 30
LAPSE_DELAY_DAYS = 1
RCD_MIN_MONTHS_BACK = 13
RCD_MAX_MONTHS_BACK = 36
POST_REVIVAL_LAPSE_MONTHS_BACK = 61
NULL_VOID_DATE_MAX_DAYS_BEFORE_PTD = 10

HEADER_ORDER = ["FLC", "Grace", "Lapse", "Reinstatement", "Null and Void", "Renewal"]

POST_ISSUANCE_EPICS_BY_PLAN = {
    "term plan": {
        "FLC": [
            "Freelook Cancellation Beyond 30 day period",
            "Freelook Cancellation Comms",
            # "Freelook Cancellation for AD rider",
            "Freelook Cancellation GL Reports",
            "Freelook Cancellation iAssist quotation",
            "Freelook Cancellation iAssist Refund",
            "Freelook Cancellation with Medical Charges",
            "Freelook Cancellation within 30 days",
        ],
        "Grace": [
            "Grace Communication",
            "Grace for Annual Scenarios",
            "Grace for Half Yearly",
            "Grace for Quarterly",
            "Grace for Monthly",
        ],
        "Lapse": [
            "Check for policy Lapsation - Annual",
            "Check for policy Lapsation - Half Yearly",
            "Check for policy Lapsation - Quarterly",
            "Check for policy Lapsation - Monthly",
            "Check for policy Lapsation - Communication",
            "Check for policy Lapsation in Ops Console - Annual",
            "Check for policy Lapsation in Ops Console - Half Yearly",
            "Check for policy Lapsation in Ops Console - Quarterly",
            "Check for policy Lapsation in Ops Console - Monthly",
            "Check for policy Lapsation on iAssist",
        ],
        "Reinstatement": [
            "Reinstatement within Revival period for RPU",
            "Reinstatement within Revival period",
            "Reinstatement post Revival period",
            "Reinstatement/Revival via iAssist"
        ],
        "Null and Void": [
            "Null & Void Full refund",
            "Null & Void No refund",   
        ],
        "Renewal": [
            "Renewal premium calculation and acceptence - Annual",
            "Renewal premium calculation and acceptence - Half Yearly",
            "Renewal premium calculation and acceptence - Quarterly",
            "Renewal premium calculation and acceptence - Monthly",
        ],
    }
}

EPIC_TEST_SCENARIO_MAP = {
    # FLC scenarios
    "Freelook Cancellation Beyond 30 day period": "To verify whether freelook cancellation request is rejected beyond 30 days of policy issuance.",
    "Freelook Cancellation Comms": "To check if communication is triggered to customer after freelook cancellation as per existing logic.",
    "Freelook Cancellation GL Reports": "To check if correct activity, Breakdown file generated for policy where Freelook cancellation is processed.",
    "Freelook Cancellation iAssist quotation": "To check if customer is able to view quotation on iAssist while giving request for Freelook cancellation",
    "Freelook Cancellation iAssist Refund": "To verify whether system allows Freelook Cancellation iAssist Refund based on Policy Acknowledgement timelines.",
    "Freelook Cancellation with Medical Charges": "To check if medical charges are fetched from datalake before processing freelook cancellation.",
    "Freelook Cancellation within 30 days": "To check if system allows to process Freelook cancellation within 30 days from Policy issuance.",
    # Grace scenarios
    "Grace for Annual Scenarios": "To check that policy move to grace period post 30 days from premium due date for non- monthly policy",
    "Grace for Half Yearly": "To check that policy move to grace period post 30 days from premium due date for non- monthly policy",
    "Grace for Quarterly": "To check that policy move to grace period post 30 days from premium due date for non- monthly policy",
    "Grace for Monthly": "To check that policy move to grace period post 15 days from premium due date for monthly policy",
    "Grace Communication": "To check the communication part once policy moved to Inforce grace period",
    # Lapse scenarios
    "Check for policy Lapsation - Annual": "To verify whether policy gets lapsed  when premium is not paid when its due.(Annual mode).",
    "Check for policy Lapsation - Half Yearly": "To verify whether policy gets lapsed  when premium is not paid when its due.(Half Yearly mode).",
    "Check for policy Lapsation - Quarterly": "To verify whether policy gets lapsed  when premium is not paid when its due.(Quarterly mode).",
    "Check for policy Lapsation - Monthly": "To verify whether policy gets lapsed  when premium is not paid when its due.(Monthly mode).",
    "Check for policy Lapsation - Communication": "To check the communication part once policy moved to Terminated Lapsed ({frequency} mode).",
    "Check for policy Lapsation in Ops Console - Annual": "To check the communication part once policy moved to Terminated Lapsed (Yearly mode).",
    "Check for policy Lapsation in Ops Console - Half Yearly": "To check the communication part once policy moved to Terminated Lapsed (Half Yearly mode).",
    "Check for policy Lapsation in Ops Console - Quarterly": "To check the communication part once policy moved to Terminated Lapsed (Quarterly mode).",
    "Check for policy Lapsation in Ops Console - Monthly": "To check if policy move to lapsed on non payment of premium once grace period over (Monthly mode).",
    "Check for policy Lapsation on iAssist": "To verify whether policy gets lapsed when premium is not paid when its due ({frequency} mode).",
    # Reinstatement scenarios
    "Reinstatement within Revival period for RPU": "Verify that the policy can be revived if it is in Terminated-RPU  status within 5 years from the last PTD.",
    "Reinstatement within Revival period": "Verify that the policy can be revived if it is in Terminated-Lapsed  status within 5 years from the last PTD.",
    "Reinstatement post Revival period": "To verify, \nReinstatement post 5 years of Revival period completion.",
    "Reinstatement/Revival via iAssist": "Verify that the policy status is set to \"Active\" on the iAssist platform post-revival",
    # Null and Void scenarios
    "Null & Void Full refund": "To verify whether policy is Null & Void full refund.",
    "Null & Void No refund": "To verify whether policy is Null & Void no refund.",
    # Renewal scenarios
    "Renewal premium calculation and acceptence - Annual": "To check Policy can be renewed with correct renewal premium for Annual mode.",
    "Renewal premium calculation and acceptence - Half Yearly": "To check Policy can be renewed with correct renewal premium for Half Yearly mode.",
    "Renewal premium calculation and acceptence - Quarterly": "To check Policy can be renewed with correct renewal premium for Quarterly mode.",
    "Renewal premium calculation and acceptence - Monthly": "To check Policy can be renewed with correct renewal premium for Monthly mode.",
}

EPIC_EXPECTED_RESULT_MAP = {
    # FLC scenarios
    "Freelook Cancellation Beyond 30 day period": "If customer applies for freelook on 31st Day from the date of policy issuance (date on which customer receives physical or digital policy)Policy should not be applicable for freelook",
    "Freelook Cancellation Comms": "Communication should be sent as per current flow.",
    "Freelook Cancellation GL Reports": "Correct activity,Breakdown file should get generated for policy where Freelook cancellation is processed.",
    "Freelook Cancellation iAssist quotation": "Customer should be able to view quotation on iAssist while giving request for Freelook cancellation",
    "Freelook Cancellation iAssist Refund": "Refund amount should be correctly calculated and payout should be triggered to customer.",
    "Freelook Cancellation with Medical Charges": "Medical charges should be deducted from freelook cancellation amount\n- Test actuarial extract\n\nActuarial extract:\nStatus name: RESCINDED\nStatus code: 42",
    "Freelook Cancellation within 30 days": "System should allow to process Freelook cancellation within 30 days from Policy Acknowledgement date.\n- The Company shall refund premiums paid after deducting the proportionate risk Premium for the period on cover, and the expenses incurred by the Company for medical expenses (if any) and stamp duty (if any).\n- Also please check finance requirements:\nCorrect accounting lines for freelook charges, premium reversal, commission reversal should be generated\nActuarial extract:\nStatus name: RESCINDED\nStatus code: 42",
    # Grace scenarios
    "Grace for Annual Scenarios": "Policy should be moved to grace period post due date and grace period of 30 days for non monthly. \nThe policy will remain Inforce during the Grace Period",
    "Grace for Half Yearly": "Policy should be moved to grace period post due date and grace period of 30 days for non monthly. \nThe policy will remain Inforce during the Grace Period",
    "Grace for Quarterly": "Policy should be moved to grace period post due date and grace period of 30 days for non monthly. \nThe policy will remain Inforce during the Grace Period",
    "Grace for Monthly": "Policy should be moved to grace period post due date and grace period of 15 days for non monthly. \nThe policy will remain Inforce during the Grace Period",
    "Grace Communication": "Communication (SMS,Email & Whatsapp) should send to customer to  intimate that policy is in grace period and need  to pay premium",
    # Lapse scenarios
    "Check for policy Lapsation - Annual": "If any premium remains unpaid after the expiry of the grace period, the policy shall lapse and the cover will cease to exist. No benefit shall be payable under a lapsed policy.\nPolicy status should change\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation - Half Yearly": "If any premium remains unpaid after the expiry of the grace period, the policy shall lapse and the cover will cease to exist. No benefit shall be payable under a lapsed policy.\nPolicy status should change\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation - Quarterly": "If any premium remains unpaid after the expiry of the grace period, the policy shall lapse and the cover will cease to exist. No benefit shall be payable under a lapsed policy.\nPolicy status should change\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation - Monthly": "If any premium remains unpaid after the expiry of the grace period, the policy shall lapse and the cover will cease to exist. No benefit shall be payable under a lapsed policy.\nPolicy status should change\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation - Communication": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation in Ops Console - Annual": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation in Ops Console - Quarterly": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation in Ops Console - Monthly": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation on iAssist": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    # Reinstatement scenarios
    "Reinstatement within Revival period for RPU": "Then, \n1. Revival period should be available for Base premium. \n2.Revival period is 5 yrs from the last unpaid premiums. \n3. Policy status changed to Inforce reinstatment \n4. Interest is applicable along with premium \nStatus name : REINSTATE \nStatus code : 36",
    "Reinstatement within Revival period": "Then, \n1. Revival period should be available for Base premium. \n2.Revival period is 5 yrs from the last unpaid premiums. \n3. Policy status changed to Inforce reinstatment \n4. Interest is applicable along with premium \nStatus name : REINSTATE \nStatus code : 36",
    "Reinstatement post Revival period": "Then, \nReinstatement post 5 years of Revival period completion,system should not allow.",
    "Reinstatement/Revival via iAssist": "Then, \n1. Revival period should be available for Base premium. \n2.Revival period is 5 yrs from the last unpaid premiums. \n3. Policy status changed to Inforce reinstatment \n4. Interest is applicable along with premium \nStatus name : REINSTATE \nStatus code : 36",
    # Null and Void scenarios
    "Null & Void Full refund": "When Null & Void full refund  is processed \nThen Policy status change to Terminated Null & Void full refund. \nCorrect amount should be refunded. Commission should be clawed back, Test Commission lines, Test OFI lines \nTest actuarial extract",
    "Null & Void No refund": "When Null & Void no refund is processed \nThen Policy status change to Terminated Null & Void no refund. \nNo amount should be refunded. Commission should be retained, Test Commission lines, Test OFI lines \nTest actuarial extract",
    # Renewal scenarios
    "Renewal premium calculation and acceptence - Annual": "The policy should be renewed with correct renewal premium. Renewal premium should be calculated based on the business rules defined for Annual mode.",
    "Renewal premium calculation and acceptence - Half Yearly": "The policy should be renewed with correct renewal premium. Renewal premium should be calculated based on the business rules defined for Half Yearly mode.",
    "Renewal premium calculation and acceptence - Quarterly": "The policy should be renewed with correct renewal premium. Renewal premium should be calculated based on the business rules defined for Quarterly mode.",
    "Renewal premium calculation and acceptence - Monthly": "The policy should be renewed with correct renewal premium. Renewal premium should be calculated based on the business rules defined for Monthly mode.",
}

EPIC_TEST_SCENARIO_MAP_RIDER = {
    # FLC scenarios
    "Freelook Cancellation Beyond 30 day period": "To verify whether freelook cancellation request is rejected beyond 30 days of policy issuance.",
    "Freelook Cancellation Comms": "To check if communication is triggered to customer after freelook cancellation as per existing logic.",
    "Freelook Cancellation GL Reports": "To check if correct activity,Breakdown  file generated for policy where Freelook cancellation is processed.",
    "Freelook Cancellation iAssist quotation": "To check if customer is able to view quotation on iAssist while giving request for Freelook cancellation",
    "Freelook Cancellation iAssist Refund": "To verify whether system allows Freelook Cancellation iAssist Refund based on Policy Acknowledgement timelines.",
    "Freelook Cancellation with Medical Charges": "To check if medical charges are fetched from datalake before processing freelook cancellation.",
    "Freelook Cancellation within 30 days": "To check if system allows to process Freelook cancellation within 30 days from Policy issuance.",
    # Grace scenarios
    "Grace for Annual Scenarios": "To check that policy move to grace period post 30 days from premium due date for non- monthly policy",
    "Grace for Half Yearly": "To check that policy move to grace period post 30 days from premium due date for non- monthly policy",
    "Grace for Quarterly": "To check that policy move to grace period post 30 days from premium due date for non- monthly policy",
    "Grace for Monthly": "To check that policy move to grace period post 15 days from premium due date for monthly policy",
    "Grace Communication": "To check the communication part once policy moved to Inforce grace period",
    # Lapse scenarios
    "Check for policy Lapsation - Annual": "To verify whether policy gets lapsed  when premium is not paid when its due.(Annual mode).",
    "Check for policy Lapsation - Half Yearly": "To verify whether policy gets lapsed  when premium is not paid when its due.(Half Yearly mode).",
    "Check for policy Lapsation - Quarterly": "To verify whether policy gets lapsed  when premium is not paid when its due.(Quarterly mode).",
    "Check for policy Lapsation - Monthly": "To verify whether policy gets lapsed  when premium is not paid when its due.(Monthly mode).",
    "Check for policy Lapsation - Communication": "To check the communication part once policy moved to Terminated Lapsed ({frequency} mode).",
    "Check for policy Lapsation in Ops Console - Annual": "To check the communication part once policy moved to Terminated Lapsed (Yearly mode).",
    "Check for policy Lapsation in Ops Console - Half Yearly": "To check the communication part once policy moved to Terminated Lapsed (Half Yearly mode).",
    "Check for policy Lapsation in Ops Console - Quarterly": "To check the communication part once policy moved to Terminated Lapsed (Quarterly mode).",
    "Check for policy Lapsation in Ops Console - Monthly": "To check if policy move to lapsed on non payment of premium once grace period over (Monthly mode).",
    "Check for policy Lapsation on iAssist": "To verify whether policy gets lapsed when premium is not paid when its due ({frequency} mode).",
    # Reinstatement scenarios
    "Reinstatement within Revival period for RPU": "Verify that the policy can be revived if it is in Terminated-RPU  status within 5 years from the last PTD.",
    "Reinstatement within Revival period": "Verify that the policy can be revived if it is in Terminated-Lapsed  status within 5 years from the last PTD.",
    "Reinstatement post Revival period": "To verify, \nReinstatement post 5 years of Revival period completion.",
    "Reinstatement/Revival via iAssist": "Verify that the policy status is set to \"Active\" on the iAssist platform post-revival",
    # Null and Void scenarios
    "Null & Void Full refund": "To verify whether policy is Null & Void full refund.",
    "Null & Void No refund": "To verify whether policy is Null & Void no refund.",
    # Renewal scenarios
    "Renewal premium calculation and acceptence - Annual": "To check Policy can be renewed with correct renewal premium for Annual mode.",
    "Renewal premium calculation and acceptence - Half Yearly": "To check Policy can be renewed with correct renewal premium for Half Yearly mode.",
    "Renewal premium calculation and acceptence - Quarterly": "To check Policy can be renewed with correct renewal premium for Quarterly mode.",
    "Renewal premium calculation and acceptence - Monthly": "To check Policy can be renewed with correct renewal premium for Monthly mode.",
}

EPIC_EXPECTED_RESULT_MAP_RIDER = {
    # FLC scenarios
    "Freelook Cancellation Beyond 30 day period": "If customer applies for freelook on 31st Day from the date of policy issuance (date on which customer receives physical or digital policy)Policy should not be applicable for freelook",
    "Freelook Cancellation Comms": "Communication should be sent as per current flow.",
    "Freelook Cancellation GL Reports": "Correct activity,Breakdown file should get generated for policy where Freelook cancellation is processed.",
    "Freelook Cancellation iAssist quotation": "Customer should be able to view quotation on iAssist while giving request for Freelook cancellation",
    "Freelook Cancellation iAssist Refund": "Refund amount should be correctly calculated and payout should be triggered to customer.",
    "Freelook Cancellation with Medical Charges": "Medical charges should be deducted from freelook cancellation amount\n- Test actuarial extract\n\nActuarial extract:\nStatus name: RESCINDED\nStatus code: 42",
    "Freelook Cancellation within 30 days": "System should allow to process Freelook cancellation within 30 days from Policy Acknowledgement date.\n- The Company shall refund premiums paid after deducting the proportionate risk Premium for the period on cover, and the expenses incurred by the Company for medical expenses (if any) and stamp duty (if any).\n- Also please check finance requirements:\nCorrect accounting lines for freelook charges, premium reversal, commission reversal should be generated\nActuarial extract:\nStatus name: RESCINDED\nStatus code: 42",
    # Grace scenarios
    "Grace for Annual Scenarios": "Policy should be moved to grace period post due date and grace period of 30 days for non monthly. \nThe policy will remain Inforce during the Grace Period",
    "Grace for Half Yearly": "Policy should be moved to grace period post due date and grace period of 30 days for non monthly. \nThe policy will remain Inforce during the Grace Period",
    "Grace for Quarterly": "Policy should be moved to grace period post due date and grace period of 30 days for non monthly. \nThe policy will remain Inforce during the Grace Period",
    "Grace for Monthly": "Policy should be moved to grace period post due date and grace period of 15 days for non monthly. \nThe policy will remain Inforce during the Grace Period",
    "Grace Communication": "Communication (SMS,Email & Whatsapp) should send to customer to  intimate that policy is in grace period and need  to pay premium",
    # Lapse scenarios
    "Check for policy Lapsation - Annual": "If any premium remains unpaid after the expiry of the grace period, the policy shall lapse and the cover will cease to exist. No benefit shall be payable under a lapsed policy.\nPolicy status should change\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation - Half Yearly": "If any premium remains unpaid after the expiry of the grace period, the policy shall lapse and the cover will cease to exist. No benefit shall be payable under a lapsed policy.\nPolicy status should change\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation - Quarterly": "If any premium remains unpaid after the expiry of the grace period, the policy shall lapse and the cover will cease to exist. No benefit shall be payable under a lapsed policy.\nPolicy status should change\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation - Monthly": "If any premium remains unpaid after the expiry of the grace period, the policy shall lapse and the cover will cease to exist. No benefit shall be payable under a lapsed policy.\nPolicy status should change\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation - Communication": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation in Ops Console - Annual": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation in Ops Console - Quarterly": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation in Ops Console - Monthly": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    "Check for policy Lapsation on iAssist": "In Ops-console, Policy status should be changed post due as Inforce grace period on the completion of grace period as Terminated Lapsed\n\nTest OFI lines\nTest actuarial extract\nStatus name: LAPSED and Status code: 40",
    # Reinstatement scenarios
    "Reinstatement within Revival period for RPU": "Then, \n1. Revival period should be available for Base premium. \n2.Revival period is 5 yrs from the last unpaid premiums. \n3. Policy status changed to Inforce reinstatment \n4. Interest is applicable along with premium \nStatus name : REINSTATE \nStatus code : 36",
    "Reinstatement within Revival period": "Then, \n1. Revival period should be available for Base premium. \n2.Revival period is 5 yrs from the last unpaid premiums. \n3. Policy status changed to Inforce reinstatment \n4. Interest is applicable along with premium \nStatus name : REINSTATE \nStatus code : 36",
    "Reinstatement post Revival period": "Then, \nReinstatement post 5 years of Revival period completion,system should not allow.",
    "Reinstatement/Revival via iAssist": "Then, \n1. Revival period should be available for Base premium. \n2.Revival period is 5 yrs from the last unpaid premiums. \n3. Policy status changed to Inforce reinstatment \n4. Interest is applicable along with premium \nStatus name : REINSTATE \nStatus code : 36",
    # Null and Void scenarios
    "Null & Void Full refund": "When Null & Void full refund  is processed \nThen Policy status change to Terminated Null & Void full refund. \nCorrect amount should be refunded. Commission should be clawed back, Test Commission lines, Test OFI lines \nTest actuarial extract",
    "Null & Void No refund": "When Null & Void no refund is processed \nThen Policy status change to Terminated Null & Void no refund. \nNo amount should be refunded. Commission should be retained, Test Commission lines, Test OFI lines \nTest actuarial extract",
    # Renewal scenarios
    "Renewal premium calculation and acceptence - Annual": "The policy should be renewed with correct renewal premium. Renewal premium should be calculated based on the business rules defined for Annual mode.",
    "Renewal premium calculation and acceptence - Half Yearly": "The policy should be renewed with correct renewal premium. Renewal premium should be calculated based on the business rules defined for Half Yearly mode.",
    "Renewal premium calculation and acceptence - Quarterly": "The policy should be renewed with correct renewal premium. Renewal premium should be calculated based on the business rules defined for Quarterly mode.",
    "Renewal premium calculation and acceptence - Monthly": "The policy should be renewed with correct renewal premium. Renewal premium should be calculated based on the business rules defined for Monthly mode.",
}

FREQUENCY_INTERVAL_MONTHS = {
    1: 12,
    2: 6,
    3: 3,
    4: 1,
    5: 0,
    "annual": 12,
    "yearly": 12,
    "half yearly": 6,
    "half-yearly": 6,
    "quarterly": 3,
    "monthly": 1,
    "single": 0,
}

# Module metadata
MODULE_NAME = "Term Plan"
LIFECYCLE_STAGE = "post issuance"
PRODUCT_CODE = getattr(issuance, "PRODUCT_CODE", "")

# EPIC_HEADERS = get_post_issuance_epics_for_plan("term plan")
EPIC_HEADERS = POST_ISSUANCE_EPICS_BY_PLAN.get("term plan", {})

EPIC_MAP = {
    epic_name: epic_name
    for header_data in EPIC_HEADERS.values()
    for epic_name in header_data
}
EPIC_MAP_RIDER = {
    epic_name: epic_name
    for header_data in EPIC_HEADERS.values()
    for epic_name in header_data
}


def get_post_issuance_epics_for_plan(plan_type):
    """Retrieve post-issuance epic configuration for a given plan type."""
    return POST_ISSUANCE_EPICS_BY_PLAN.get(plan_type, {})


# ============================================================================
# Date Utility Functions
# ============================================================================

def _format_date(value):
    """Format date object to DD/MM/YYYY string."""
    return value.strftime("%d/%m/%Y")


def _format_birthdate(value):
    """Format birthdate as DD/Mon/YYYY to match issuance style."""
    return value.strftime("%d/%b/%Y")


def _parse_date_value(value):
    """Parse a date value from date objects or known string formats."""
    if isinstance(value, date):
        return value

    text_value = str(value or "").strip()
    if not text_value:
        return None

    for fmt in ("%d/%m/%Y", "%d/%b/%Y", "%d/%B/%Y"):
        try:
            return datetime.strptime(text_value, fmt).date()
        except (TypeError, ValueError):
            continue

    try:
        return date.fromisoformat(text_value)
    except (TypeError, ValueError):
        return None


def _derive_birthdate_from_age_and_inception(age_value, inception_value):
    """Derive birthdate so the customer age aligns with inception/RCD date."""
    inception_date = _parse_date_value(inception_value)
    if inception_date is None:
        return None

    try:
        age_years = int(float(age_value))
    except (TypeError, ValueError):
        return None

    if age_years < 0:
        return None

    return _add_months(inception_date, -(age_years * 12))


def _add_months(base_date, month_delta):
    """Add or subtract months from a date, handling month-end edge cases."""
    target_month_index = (base_date.month - 1) + month_delta
    target_year = base_date.year + target_month_index // 12
    target_month = (target_month_index % 12) + 1
    target_day = min(base_date.day, calendar.monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


def _months_between(start_date, end_date):
    """Calculate the number of complete months between two dates."""
    total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if end_date.day < start_date.day:
        total_months -= 1
    return max(total_months, 0)


# ============================================================================
# Seed Data Generation
# ============================================================================

def _resolve_payment_frequency_options(counts):
    """Resolve payment frequency options from epic counts."""
    options = (counts or {}).get("payment_frequency_options")
    if options:
        return list(options)
    return [1, 2, 3, 4, 5]


def _normalize_frequency_options(options):
    """Normalize payment frequency options to unique integer values."""
    normalized = []
    for option in options or []:
        try:
            option_value = int(option)
        except (TypeError, ValueError):
            continue
        if option_value in {1, 2, 3, 4, 5} and option_value not in normalized:
            normalized.append(option_value)
    return normalized


def _to_int(value, default=None):
    """Safely convert values to int, preserving default on conversion failure."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _normalize_range(range_value):
    """Normalize a range tuple/list into ordered integer bounds."""
    if not isinstance(range_value, (list, tuple)) or len(range_value) != 2:
        return None

    min_value = _to_int(range_value[0])
    max_value = _to_int(range_value[1])
    if min_value is None or max_value is None:
        return None

    if min_value > max_value:
        min_value, max_value = max_value, min_value

    return min_value, max_value


def _resolve_ppt_range(range_map, ppt_name):
    """Resolve configured range for a premium payment option."""
    if not isinstance(range_map, dict):
        return None
    return _normalize_range(range_map.get(ppt_name))


def _apply_seed_value_constraints(seed_df, counts):
    """Apply configured entry/term/sum-assured constraints on seed rows."""
    if seed_df is None or seed_df.empty:
        return seed_df

    counts = counts or {}
    entry_age_ranges = counts.get("entry_age_ranges") or {}
    policy_term_ranges = counts.get("policy_term_ranges") or {}
    maturity_age_ranges = counts.get("maturity_age_ranges") or {}
    premium_paying_term_ranges = counts.get("premium_paying_term_ranges") or {}
    sum_assured_ranges = counts.get("sum_assured_ranges") or {}

    def _apply_row_constraints(row):
        ppt_name = str(row.get("Premium Payment Option", "")).strip()

        age = _to_int(row.get("Age"), 30)
        coverage_year = _to_int(row.get("coverageYear"), 10)
        charge_year = _to_int(row.get("chargeYear"), 1)

        entry_age_range = _resolve_ppt_range(entry_age_ranges, ppt_name)
        if entry_age_range:
            age = random.randint(entry_age_range[0], entry_age_range[1])

        policy_term_range = _resolve_ppt_range(policy_term_ranges, ppt_name)
        if policy_term_range:
            coverage_year = random.randint(policy_term_range[0], policy_term_range[1])

        premium_paying_range = _resolve_ppt_range(premium_paying_term_ranges, ppt_name)
        if premium_paying_range:
            charge_year = random.randint(premium_paying_range[0], premium_paying_range[1])

        maturity_age_range = _resolve_ppt_range(maturity_age_ranges, ppt_name)
        if maturity_age_range:
            min_maturity_age, max_maturity_age = maturity_age_range
            min_coverage_year = max(1, min_maturity_age - age)
            max_coverage_year = max(min_coverage_year, max_maturity_age - age)

            if policy_term_range:
                min_coverage_year = max(min_coverage_year, policy_term_range[0])
                max_coverage_year = min(max_coverage_year, policy_term_range[1])

            if max_coverage_year < min_coverage_year:
                max_coverage_year = min_coverage_year

            coverage_year = random.randint(min_coverage_year, max_coverage_year)

        if ppt_name == "Single Pay":
            charge_year = 1
            row["paymentFreq"] = 5
            row["paymentFreqW"] = "Single"
            row["paymentFreqC"] = "Single"
        elif coverage_year > 0:
            charge_year = min(charge_year, coverage_year)

        row["Age"] = age
        row["coverageYear"] = coverage_year
        row["chargeYear"] = charge_year
        row["Coverage upto Age"] = age + coverage_year

        sum_assured_key = "Single Pay" if ppt_name.lower() == "single pay" else "Others"
        sum_assured_config = sum_assured_ranges.get(sum_assured_key, {})
        min_sum_assured = _to_int(sum_assured_config.get("min_val"))
        max_sum_assured = _to_int(sum_assured_config.get("max_val"))
        if (
            min_sum_assured is not None
            and max_sum_assured is not None
            and min_sum_assured <= max_sum_assured
        ):
            row["sumAssured"] = random.randint(min_sum_assured, max_sum_assured)

        return row

    return seed_df.apply(_apply_row_constraints, axis=1)


def _frequency_options_from_epic_name(epic_name):
    """Extract payment frequency options from epic name text."""
    normalized = (epic_name or "").lower()
    if "half yearly" in normalized or "half-yearly" in normalized:
        return [2]
    if "quarterly" in normalized:
        return [3]
    if "monthly" in normalized:
        return [4]
    if "annual" in normalized or "yearly" in normalized:
        return [1]
    return None


def _resolve_frequency_options_for_epic(header_name, epic_name, counts):
    """Resolve frequency options for a post-issuance epic."""
    counts = counts or {}

    if header_name == "FLC":
        epic_frequency_options = [1, 2, 3, 4, 5]
    elif header_name in {"Grace", "Lapse", "Reinstatement", "Null and Void", "Renewal"}:
        matched = _frequency_options_from_epic_name(epic_name)
        if matched:
            epic_frequency_options = matched
        else:
            epic_frequency_options = [1, 2, 3, 4]
    else:
        epic_frequency_options = _resolve_payment_frequency_options(counts)

    if "payment_frequency_options" not in counts:
        return epic_frequency_options

    configured_options = _normalize_frequency_options(counts.get("payment_frequency_options"))
    configured_option_set = set(configured_options)
    return [
        option for option in epic_frequency_options
        if option in configured_option_set
    ]


def _resolve_frequency_label_for_scenario(epic_name, row):
    """Resolve frequency label for scenario templates with {frequency} placeholder."""
    frequency_values = _frequency_options_from_epic_name(epic_name)
    frequency_value = frequency_values[0] if frequency_values else row.get("paymentFreq")

    if pd.isna(frequency_value):
        frequency_value = row.get("paymentFreqW")

    try:
        frequency_value = int(frequency_value)
    except (TypeError, ValueError):
        pass

    # Keep mapping inline as lambda as requested.
    frequency_to_label = lambda value: {
        1: "Annual",
        2: "Half Yearly",
        3: "Quarterly",
        4: "Monthly",
        5: "Single",
    }.get(value, str(value or ""))

    return frequency_to_label(frequency_value)


def _enforce_single_pay_frequency(row):
    """Align payment frequency with Single Pay premium payment option."""
    if str(row.get("Premium Payment Option", "")).strip().lower() != "single pay":
        return row

    row["paymentFreq"] = 5
    row["paymentFreqW"] = "Single"
    row["paymentFreqC"] = "Single"
    return row




def _filter_positive_cases(df, case_count=None, inception_date=None, exclude_single_pay=False):
    """Return only positive cases with optional inception date override."""
    if df is None or df.empty:
        return pd.DataFrame(columns=issuance.column_order)

    positive_df = df[df["Test_Type"] == "Positive"].copy()
    if inception_date:
        positive_df["inceptionDate"] = inception_date
    if exclude_single_pay:
        positive_df = positive_df[
            positive_df["Premium Payment Option"].str.strip().str.lower() != "single pay"
        ]
    positive_df = positive_df.apply(_enforce_single_pay_frequency, axis=1)
    if case_count is not None:
        positive_df = positive_df.head(case_count)
    return positive_df


def generate_positive_payment_frequency_cases_base(frequency_options=None, inception_date=None,
                                                   case_count=None, exclude_single_pay=False,
                                                   constraint_config=None):
    """Generate positive-only base PaymentFrequency cases."""
    frequency_options = list(frequency_options or [1, 2, 3, 4, 5])
    positive_count = case_count if case_count is not None else max(len(frequency_options), 1)
    seed_epic_counts = {
        "PaymentFrequency": {
            "positive": positive_count,
            "negative": 0,
            "payment_frequency_options": frequency_options,
        }
    }
    seed_df = issuance.generate_test_cases(
        epic_counts=seed_epic_counts,
        selected_epics=["PaymentFrequency"],
        epic_counts_rider={},
        selected_epics_rider=[],
    )
    positive_df = _filter_positive_cases(
        seed_df,
        case_count=positive_count,
        inception_date=inception_date,
        exclude_single_pay=exclude_single_pay,
    )
    return _apply_seed_value_constraints(positive_df, constraint_config)


def generate_positive_payment_frequency_cases_rider(frequency_options=None, inception_date=None,
                                                    case_count=None, exclude_single_pay=False,
                                                    constraint_config=None):
    """Generate positive-only rider PaymentFrequency cases."""
    frequency_options = list(frequency_options or [1, 2, 3, 4, 5])
    positive_count = case_count if case_count is not None else max(len(frequency_options), 1)
    seed_epic_counts_rider = {
        "PaymentFrequency": {
            "positive": positive_count,
            "negative": 0,
            "payment_frequency_options": frequency_options,
        }
    }
    seed_df = issuance.generate_test_cases(
        epic_counts={},
        selected_epics=[],
        epic_counts_rider=seed_epic_counts_rider,
        selected_epics_rider=["PaymentFrequency"],
    )
    positive_df = _filter_positive_cases(
        seed_df,
        case_count=positive_count,
        inception_date=inception_date,
        exclude_single_pay=exclude_single_pay,
    )
    return _apply_seed_value_constraints(positive_df, constraint_config)


def _get_positive_count(counts):
    """Extract positive count from epic counts configuration."""
    counts = counts or {}
    
    if "positive" in counts:
        return int(counts.get("positive", 0) or 0)

    ppt_pos_counts = counts.get("ppt_pos_counts", {})
    if isinstance(ppt_pos_counts, dict):
        return sum(int(value or 0) for value in ppt_pos_counts.values())

    return 0


# ============================================================================
# Frequency and Date Calculation
# ============================================================================

def _frequency_interval_in_months(row):
    """Extract payment frequency interval in months from row data."""
    freq_candidates = [
        row.get("paymentFreqW"),
        row.get("paymentFreq"),
        row.get("paymentFreqC")
    ]

    for value in freq_candidates:
        if pd.isna(value):
            continue

        # Try integer lookup
        try:
            int_value = int(value)
            if int_value in FREQUENCY_INTERVAL_MONTHS:
                return FREQUENCY_INTERVAL_MONTHS[int_value]
        except (TypeError, ValueError):
            pass

        # Try string lookup
        normalized = str(value).strip().lower().replace("_", " ")
        if normalized in FREQUENCY_INTERVAL_MONTHS:
            return FREQUENCY_INTERVAL_MONTHS[normalized]

    return 12  # Default to annual


def _generate_rcd(today_value):
    """Generate a random Risk Commencement Date (RCD) in the past."""
    months_back = random.randint(RCD_MIN_MONTHS_BACK, RCD_MAX_MONTHS_BACK)
    return _add_months(today_value, -months_back)


def _generate_ptd_and_renewal_count(rcd_date, interval_months, today_value):
    """Calculate Premium Till Date (PTD) and renewal count based on RCD and frequency."""
    if interval_months <= 0:
        return rcd_date, 0

    max_interval_steps = _months_between(rcd_date, today_value) // interval_months
    if max_interval_steps <= 0:
        return rcd_date, 0

    renewal_count = random.randint(1, max_interval_steps)
    ptd_date = _add_months(rcd_date, renewal_count * interval_months)

    # Ensure PTD is not in the future
    if ptd_date >= today_value and renewal_count > 0:
        renewal_count -= 1
        ptd_date = _add_months(rcd_date, renewal_count * interval_months)

    return ptd_date, max(renewal_count-1, 0)


def _calculate_grace_days(interval_months):
    """Determine grace period days based on payment frequency."""
    return GRACE_PERIOD_MONTHLY if interval_months == 1 else GRACE_PERIOD_OTHER


def _build_post_issuance_dates(row):
    """Build all relevant post-issuance dates for a policy."""
    today_value = date.today()
    interval_months = _frequency_interval_in_months(row)

    rcd_date = _generate_rcd(today_value)
    ptd_date, renewal_count = _generate_ptd_and_renewal_count(rcd_date, interval_months, today_value)

    flc_date = rcd_date + timedelta(days=FLC_PERIOD_DAYS)
    grace_days = _calculate_grace_days(interval_months)
    grace_date = ptd_date + timedelta(days=grace_days)
    lapse_date = grace_date + timedelta(days=LAPSE_DELAY_DAYS)

    return {
        "rcd_date": rcd_date,
        "ptd_date": ptd_date,
        "flc_date": flc_date,
        "grace_date": grace_date,
        "lapse_date": lapse_date,
        "reinstatement_date": None,
        "nvfr_date": None,
        "nvnr_date": None,
        "renewal_count": renewal_count,
    }


def _build_reinstatement_dates(row, epic_name):
    """Build date context for reinstatement epics."""
    today_value = date.today()
    interval_months = _frequency_interval_in_months(row)
    grace_days = _calculate_grace_days(interval_months)

    if epic_name == "Reinstatement post Revival period":
        # Keep lapse safely beyond revival window (5 years + 1 month).
        lapse_date = _add_months(today_value, -POST_REVIVAL_LAPSE_MONTHS_BACK)
        reinstatement_date = _add_months(lapse_date, 60)
        reinstatement_date = reinstatement_date + timedelta(days=1)  # Ensure it's just beyond the revival period
    else:
        lapse_months_back = random.randint(2, 48)
        lapse_date = _add_months(today_value, -lapse_months_back)
        days_since_lapse = max((today_value - lapse_date).days, 0)
        reinstatement_offset = random.randint(0, days_since_lapse) if days_since_lapse else 0
        reinstatement_date = lapse_date + timedelta(days=reinstatement_offset)

    ptd_date = lapse_date - timedelta(days=grace_days + LAPSE_DELAY_DAYS)
    rcd_months_back = random.randint(RCD_MIN_MONTHS_BACK, RCD_MAX_MONTHS_BACK)
    rcd_date = _add_months(ptd_date, -rcd_months_back)

    if interval_months <= 0:
        renewal_count = 0
    else:
        renewal_count = max(_months_between(rcd_date, ptd_date) // interval_months - 1, 0)

    flc_date = rcd_date + timedelta(days=FLC_PERIOD_DAYS)
    grace_date = ptd_date + timedelta(days=grace_days)

    return {
        "rcd_date": rcd_date,
        "ptd_date": ptd_date,
        "flc_date": flc_date,
        "grace_date": grace_date,
        "lapse_date": lapse_date,
        "reinstatement_date": reinstatement_date,
        "nvfr_date": None,
        "nvnr_date": None,
        "renewal_count": renewal_count,
    }


def _build_null_void_dates(row, epic_name):
    """Build date context for Null and Void epics with NVFR/NVNR date."""
    date_context = _build_post_issuance_dates(row)
    ptd_date = date_context["ptd_date"]
    days_before_ptd = random.randint(1, NULL_VOID_DATE_MAX_DAYS_BEFORE_PTD)
    null_void_date = ptd_date - timedelta(days=days_before_ptd)

    if "full refund" in str(epic_name or "").strip().lower():
        date_context["nvfr_date"] = null_void_date
    elif "no refund" in str(epic_name or "").strip().lower():
        date_context["nvnr_date"] = null_void_date

    return date_context


# ============================================================================
# Epic Metadata and Scenario Building
# ============================================================================

def _resolve_header(selected_header, epic_name):
    """Resolve the header category for a given epic."""
    if selected_header in EPIC_HEADERS:
        return selected_header

    for header_name, epic_names in EPIC_HEADERS.items():
        if epic_name in epic_names:
            return header_name

    return "Post Issuance"


def _resolve_epic_metadata(header_name, epic_name, row, isrider=False):
    """Get test scenario and expected result metadata for an epic."""
    test_scenario_map = EPIC_TEST_SCENARIO_MAP_RIDER if isrider else EPIC_TEST_SCENARIO_MAP
    expected_result_map = EPIC_EXPECTED_RESULT_MAP_RIDER if isrider else EPIC_EXPECTED_RESULT_MAP
    
    scenario_text = test_scenario_map.get(epic_name)
    if isinstance(scenario_text, str) and "{frequency}" in scenario_text:
        scenario_text = scenario_text.format(
            frequency=_resolve_frequency_label_for_scenario(epic_name, row)
        )

    return {
        "API_Operation": epic_name,
        "Test_Scenario": scenario_text,
        "Expected_Result": expected_result_map.get(
            epic_name),
    }


def _build_scenario_with_dates(base_scenario, date_context, selected_header, epic_name=None):
    """Augment base scenario text with date information, based on selected_header."""
    
    # Always include the first three dates
    scenario_lines = [
        base_scenario,
        f"RCD date: {_format_date(date_context['rcd_date'])}",
        f"PTD date: {_format_date(date_context['ptd_date'])}",
        f"Renewal: {date_context['renewal_count']}",
    ]
    
    # Add header-specific dates in the scenario payload.
    if selected_header in ['FLC', 'Grace', 'Lapse']:
        scenario_lines.append(f"{selected_header} date: {_format_date(date_context[f'{selected_header.lower()}_date'])}")
    elif selected_header == 'Reinstatement':
        scenario_lines.append(f"Lapse date: {_format_date(date_context['lapse_date'])}")
        if date_context.get('reinstatement_date'):
            scenario_lines.append(
                f"Reinstatement date: {_format_date(date_context['reinstatement_date'])}"
            )
    elif selected_header == 'Null and Void':
        epic_name_normalized = str(epic_name or '').strip().lower()
        if "full refund" in epic_name_normalized and date_context.get('nvfr_date'):
            scenario_lines.append(f"NVFR date: {_format_date(date_context['nvfr_date'])}")
        elif "no refund" in epic_name_normalized and date_context.get('nvnr_date'):
            scenario_lines.append(f"NVNR date: {_format_date(date_context['nvnr_date'])}")
    
    return "\n".join(scenario_lines)


def _apply_post_issuance_overrides(row, epic_name, selected_header, tuid_counter, isrider=False):
    """Apply post-issuance specific overrides to a test case row."""
    header_name = _resolve_header(selected_header, epic_name)
    metadata = _resolve_epic_metadata(header_name, epic_name, row, isrider=isrider)
    if header_name == "Reinstatement":
        date_context = _build_reinstatement_dates(row, epic_name)
    elif header_name == "Null and Void":
        date_context = _build_null_void_dates(row, epic_name)
    else:
        date_context = _build_post_issuance_dates(row)

    row["TUID"] = f"TC_{MODULE_NAME.replace(' ', '')}_POST_{tuid_counter:03d}"
    row["API_Mode"] = "Base plan + AD" if isrider else "Base plan"
    row["API_Operation"] = metadata["API_Operation"]
    row["Test Scenario"] = _build_scenario_with_dates(
        metadata["Test_Scenario"],
        date_context, selected_header,
        epic_name=epic_name,
    )
    negative_epics = {
        "Freelook Cancellation Beyond 30 day period",
        "Reinstatement post Revival period",
    }
    row["Test_Type"] = "Negative" if epic_name in negative_epics else "Positive"
    row["Expected_Result"] = metadata.get(
        "Expected_Result")
    row["inceptionDate"] = _format_date(date_context["rcd_date"])

    updated_birthdate = _derive_birthdate_from_age_and_inception(
        row.get("Age"),
        date_context["rcd_date"],
    )
    if updated_birthdate is not None:
        row["birthdate"] = _format_birthdate(updated_birthdate)

    row["FLC date"] = _format_date(date_context["flc_date"])
    row["Grace date"] = _format_date(date_context["grace_date"])
    row["Lapse date"] = _format_date(date_context["lapse_date"])
    if date_context.get("nvfr_date") is not None:
        row["NVFR date"] = _format_date(date_context["nvfr_date"])
    if date_context.get("nvnr_date") is not None:
        row["NVNR date"] = _format_date(date_context["nvnr_date"])

    return row


# ============================================================================
# Epic Grouping and Case Generation
# ============================================================================

def _group_epics_by_header(epics, counts_dict, selected_header):
    """Group epics into their respective header categories (FLC, Grace, Lapse, Reinstatement, Null and Void, Renewal)."""
    grouped = {header: [] for header in HEADER_ORDER}
    
    for epic_name in epics:
        counts = (counts_dict or {}).get(epic_name, {})
        header_name = counts.get("header") or selected_header or _resolve_header(None, epic_name)
        resolved_header = _resolve_header(header_name, epic_name)
        
        if resolved_header in grouped:
            grouped[resolved_header].append(epic_name)
    
    return grouped


def _append_cases_for_header(epic_names, header_name, epic_counts, selected_header,
                             scenarios, tuid_counter, isrider=False):
    """
    Append test cases for a given header category.
    Unified function that handles both base and rider cases.
    """
    for epic_name in epic_names:
        counts = (epic_counts or {}).get(epic_name, {})
        
        # Generate appropriate seed rows based on rider flag
        positive_count = _get_positive_count(counts)
        if positive_count <= 0:
            continue
        frequency_options = _resolve_frequency_options_for_epic(header_name, epic_name, counts)
        if not frequency_options:
            continue
        exclude_single_pay = header_name in {"Grace", "Lapse"}
        if isrider:
            seed_rows = generate_positive_payment_frequency_cases_rider(
                frequency_options=frequency_options,
                inception_date=None,
                case_count=positive_count,
                exclude_single_pay=exclude_single_pay,
                constraint_config=counts,
            )
        else:
            seed_rows = generate_positive_payment_frequency_cases_base(
                frequency_options=frequency_options,
                inception_date=None,
                case_count=positive_count,
                exclude_single_pay=exclude_single_pay,
                constraint_config=counts,
            )
        
        if seed_rows.empty:
            continue
        
        header_label = counts.get("header") or selected_header or header_name
        
        for _, seed_row in seed_rows.iterrows():
            tuid_counter += 1
            row = seed_row.to_dict()
            row = _apply_post_issuance_overrides(
                row, epic_name, header_label, tuid_counter, isrider=isrider
            )
            scenarios.append(row)

    return tuid_counter
    


# ============================================================================
# Main Test Case Generation
# ============================================================================

def generate_test_cases(epic_counts, selected_epics=None, epic_counts_rider=None, 
                       selected_epics_rider=None, selected_header=None):
    """
    Generate post-issuance test cases for base plan and rider epics.
    
    Args:
        epic_counts: Dict of epic configurations for base plan
        selected_epics: List of selected epic names for base plan
        epic_counts_rider: Dict of epic configurations for riders
        selected_epics_rider: List of selected epic names for riders
        selected_header: Optional header category override
        
    Returns:
        DataFrame with generated test cases
    """
    selected_epics = selected_epics or list((epic_counts or {}).keys())
    selected_epics_rider = selected_epics_rider or list((epic_counts_rider or {}).keys())
    
    if not selected_epics and not selected_epics_rider:
        return pd.DataFrame(columns=issuance.column_order)

    scenarios = []
    tuid_counter = 0

    # Group epics by header category
    base_grouped_epics = _group_epics_by_header(selected_epics, epic_counts, selected_header)
    rider_grouped_epics = _group_epics_by_header(selected_epics_rider, epic_counts_rider, selected_header)

    # Process all headers in order: first base cases, then rider cases
    # Base plan cases
    for header_name in HEADER_ORDER:
        if header_name=="FLC":
            tuid_counter = _append_cases_for_header(
                base_grouped_epics[header_name],
                header_name,
                epic_counts,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=False,
            )
        
        if header_name=="Grace":
            tuid_counter = _append_cases_for_header(
                base_grouped_epics[header_name],
                header_name,
                epic_counts,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=False,
            )
        
        if header_name=="Lapse":
            tuid_counter = _append_cases_for_header(
                base_grouped_epics[header_name],
                header_name,
                epic_counts,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=False,
            )

        if header_name=="Reinstatement":
            tuid_counter = _append_cases_for_header(
                base_grouped_epics[header_name],
                header_name,
                epic_counts,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=False,
            )

        if header_name=="Null and Void":
            tuid_counter = _append_cases_for_header(
                base_grouped_epics[header_name],
                header_name,
                epic_counts,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=False,
            )

        if header_name=="Renewal":
            tuid_counter = _append_cases_for_header(
                base_grouped_epics[header_name],
                header_name,
                epic_counts,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=False,
            )

    # Rider cases
    for header_name in HEADER_ORDER:
        if header_name=="FLC":
            tuid_counter = _append_cases_for_header(
                rider_grouped_epics[header_name],
                header_name,
                epic_counts_rider,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=True,
            )

        if header_name=="Grace":
            tuid_counter = _append_cases_for_header(
                rider_grouped_epics[header_name],
                header_name,
                epic_counts_rider,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=True,
            )
        
        if header_name=="Lapse":
            tuid_counter = _append_cases_for_header(
                rider_grouped_epics[header_name],
                header_name,
                epic_counts_rider,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=True,
            )

        if header_name=="Reinstatement":
            tuid_counter = _append_cases_for_header(
                rider_grouped_epics[header_name],
                header_name,
                epic_counts_rider,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=True,
            )
        
        if header_name=="Null and Void":
            tuid_counter = _append_cases_for_header(
                rider_grouped_epics[header_name],
                header_name,
                epic_counts_rider,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=True,
            )

        if header_name=="Renewal":
            tuid_counter = _append_cases_for_header(
                rider_grouped_epics[header_name],
                header_name,
                epic_counts_rider,
                selected_header,
                scenarios,
                tuid_counter,
                isrider=True,
            )

    if not scenarios:
        return pd.DataFrame(columns=issuance.column_order)

    # Build result DataFrame with proper column order
    result_df = pd.DataFrame(scenarios)
    for col in issuance.column_order:
        if col not in result_df.columns:
            result_df[col] = ""

    return result_df[issuance.column_order]



