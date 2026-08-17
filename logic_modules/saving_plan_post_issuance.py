import random
from datetime import date, timedelta

import pandas as pd

from logic_modules import saving_plan_issuance as issuance

# ============================================================================
# Constants
# ============================================================================

MODULE_NAME = "Saving Plan"
LIFECYCLE_STAGE = "post issuance"
PRODUCT_CODE = getattr(issuance, "PRODUCT_CODE", "")

HEADER_ORDER = ["Death Claim"]

DEATH_CLAIM_SUBSECTIONS = [
    "Claim Accept cases",
    "Claim Reject/Repudiate cases",
    "Suicide cases",
]

POST_ISSUANCE_EPICS_BY_PLAN = {
    "saving plan": {
        "Death Claim": list(DEATH_CLAIM_SUBSECTIONS),
    }
}

EPIC_MAP = {epic_name: epic_name for epic_name in DEATH_CLAIM_SUBSECTIONS}
EPIC_MAP_RIDER = {}

# policyReasonOnEvent -> matching Policy Status
POLICY_REASON_STATUS_MAP = {
    "NEW_ISSUE": "Inforce",
    "GRACE": "Grace Period",
    "LAPSED": "Lapse",
    "REINSTATMENT": "Inforce",
    "REDUCED_PAID_UP": "Reduced Paid Up",
}
POLICY_REASONS = list(POLICY_REASON_STATUS_MAP.keys())

CAUSE_OF_DEATH_OPTIONS = ["ACCIDENTAL", "NON_ACCIDENTAL"]

INCOME_SHIELD_PLAN_OPTIONS = {"CAREERSTART_SECURE_INCOME", "CAREERSTART_LIFE_SHIELD_INCOME"}

FIXED_VALUES = {
    "type": "DEATH",
    "timeOfClaimIntimation": "BEFORE_3_PM",
    "incomeBenefit": 0,
    "lumpSumBenefit": 100,
    "coverageCode": "ARMP0000149",
    "name": "kabir aneja",
    "payoutPercent": 100,
    "schemeCode": "ARMP0000149",
    "productCode": "IGCHILDASSURE_01",
    "productCategory": "ENDOWMENT",
    "policyStatusOnEvent": "INFORCE",
    "isPartiallyWithdrawn": False,
    "lob": "RETAIL",
    "paymentType": "LIMITED_PAY",
    "loanPayoutRequired": False,
    "loanAmount": 0,
    "Oustanding Policy Loan Amount inclusive of Loan Interest as on date of death (INR)": 0,
    "sumAssured": "",
    "effectiveSumAssured": "",
    "accidentalDeathBenefit": "",
    "currentPolicyStatus": "INFORCE",
    "totalSuspense": 0,
    "adRiderSumAssured": 0,
    "allRidersUrpvAmount": 0,
    "option": "INCOME",
    "additionalSumAssured": "",
    "Surrender Value as on Date of Death (INR)": 0,
    "Distribution Channel": "Other than Direct / Online",
    "Policy Loan Opted (if any)": "No",
    "Interest rate for calculating monthly income shield instalment": "6%",
}

CLAIM_DECISION_BY_SUBSECTION = {
    "Claim Accept cases": "Accept",
    "Claim Reject/Repudiate cases": "Reject",
    "Suicide cases": None,  # resolved per-row (Accept / Reject)
}

REASON_FOR_DEATH_BY_CAUSE = {
    "ACCIDENTAL": "Accident",
    "NON_ACCIDENTAL": "Natural",
    "SUICIDE": "Suicide",
}

column_order = [
    "TUID", "API_Operation", "Test Scenario",
    "policyNumber", "type", "dateOfIntimation", "timeOfClaimIntimation", "causeOfDeath",
    "Date of Revival", "rcd",
    "Date of Birth of Life Assured", "Gender of Life Assured",
    "Date of Birth of Child", "Gender of Child",
    "Is the Life Assured same as Policyholder?",
    "dueDate", "Date of Death",
    "incomeBenefit", "lumpSumBenefit", "coverageCode", "name", "payoutPercent",
    "schemeCode", "productCode", "productCategory",
    "policyStatusOnEvent", "policyReasonOnEvent", "Policy Status",
    "isPartiallyWithdrawn", "lob",
    "Claim Status", "decision", "paymentType", "Plan Option",
    "loanPayoutRequired", "loanAmount",
    "Oustanding Policy Loan Amount inclusive of Loan Interest as on date of death (INR)",
    "Base Installment Premium inclusive of EMR Premium, Per Mille, NSAP loading and Service Tax (Rs.)",
    "sumAssured", "effectiveSumAssured", "accidentalDeathBenefit",
    "Total Premiums Paid inclusive of First Year Discount and modal loadings till Date of Death (INR)",
    "totalBasePremiumPaidToDate",
    "currentPolicyStatus", "currentPolicyReason",
    "premiumOnDateOfEvent", "outstandingPremium", "excessPremiumOnEventDate",
    "totalSuspense", "adRiderSumAssured", "allRidersUrpvAmount", "option", "additionalSumAssured",
    "Annualised Premium (INR)", "Date of Claim Acceptance",
    "Surrender Value as on Date of Death (INR)",
    "Premium Payment Term (in years)", "Deferment period", "Policy Term (in years)",
    "Premium Frequency", "Income Period", "Advance Option",
    "Distribution Channel", "Existing Customer/Employee Discount",
    "Policy Loan Opted (if any)", "Reason For Death",
    "Income Shield Monthly Income Instalment (in years)",
    "Interest rate for calculating monthly income shield instalment",
    "Date of last Premium Paid", "No. Of premium paid", "Premium Refund",
    "Total Premiums Paid inclusive of Modal Loading, First Year Premium Discount, EMR Premium, Per Mille, NSAP loading & Rider premiums exclusive of Taxes till Date of Death (INR)",
]


def get_post_issuance_epics_for_plan(plan_type):
    """Retrieve post-issuance epic configuration for a given plan type."""
    return POST_ISSUANCE_EPICS_BY_PLAN.get(plan_type, {})


# ============================================================================
# Scenario text
# ============================================================================

SCENARIO_TEXT_MAP = {
    "Claim Accept cases": "To verify Death Claim is Accepted for cause of death: {cause}, policy status/reason on event: {reason} ({status})",
    "Claim Reject/Repudiate cases": "To verify Death Claim is {decision} for cause of death: {cause}, policy status/reason on event: {reason} ({status})",
    "Suicide cases": "To verify Death Claim ({decision}) for Suicide, policy status/reason on event: {reason} ({status})",
}

EXPECTED_RESULT_MAP = {
    "Claim Accept cases": "Death Claim should be Accepted. Claim amount should be correctly computed and payable benefits, premiums paid and outstanding amounts should reflect correctly against the policy.",
    "Claim Reject/Repudiate cases": "Death Claim should be Rejected/Repudiated as per policy status/reason on event. No claim payout should be processed.",
    "Suicide cases": "Death Claim (Suicide) decision should be correctly evaluated (Accept/Reject) as per policy terms and policy status/reason on event.",
}


def _format_date(value):
    """Format date object to DD/MM/YYYY string."""
    return value.strftime("%d/%m/%Y")


def _random_policy_number():
    """Generate a random policy-number-like identifier, e.g. ALI0QAC92579805."""
    letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
    mid = "0" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    digits = "".join(random.choices("0123456789", k=8))
    return f"{letters}{mid}{digits}"


def _frequency_interval_months(payment_freq_label):
    mapping = {
        "Annual": 12,
        "Half-Yearly": 6,
        "Quarterly": 3,
        "Monthly": 1,
    }
    return mapping.get(payment_freq_label, 12)


def _build_death_claim_dates(today_value, policy_reason, interval_months):
    """Build the RCD -> last premium paid -> due date -> death -> intimation ->
    (revival) -> claim acceptance date chain, all strictly before today."""

    rcd_years_back = random.randint(2, 10)
    rcd_date = today_value.replace(year=today_value.year - rcd_years_back)

    # Number of premiums already paid before the event, spaced by frequency.
    max_installments = max(1, ((today_value - rcd_date).days // 30) // max(interval_months, 1))
    installments_paid = random.randint(1, max(1, min(max_installments, 20)))

    last_premium_paid_date = rcd_date
    for _ in range(installments_paid):
        last_premium_paid_date = _add_months(last_premium_paid_date, interval_months)

    due_date = _add_months(last_premium_paid_date, interval_months)

    if policy_reason == "GRACE":
        # Death occurs within the grace window, before the next due date.
        death_date = due_date + timedelta(days=random.randint(1, 25))
    elif policy_reason in ("LAPSED", "REDUCED_PAID_UP"):
        # Death occurs well after the due date, policy already lapsed/RPU.
        death_date = due_date + timedelta(days=random.randint(35, 120))
    elif policy_reason == "REINSTATMENT":
        # Policy lapsed, was revived, then death occurred post revival.
        death_date = due_date + timedelta(days=random.randint(35, 90))
    else:  # NEW_ISSUE
        # Death occurs on or shortly after the due date while policy is Inforce.
        death_date = due_date + timedelta(days=random.choice([0, 1, 2, 3]))

    death_date = min(death_date, today_value - timedelta(days=3))
    if death_date <= due_date:
        due_date = death_date - timedelta(days=1)

    intimation_date = death_date + timedelta(days=random.randint(1, 10))
    intimation_date = min(intimation_date, today_value - timedelta(days=2))
    if intimation_date <= death_date:
        intimation_date = death_date + timedelta(days=1)

    revival_date = None
    if policy_reason == "REINSTATMENT":
        earliest_revival = due_date + timedelta(days=random.randint(31, 60))
        revival_date = min(earliest_revival, intimation_date - timedelta(days=1))
        if revival_date <= due_date:
            revival_date = due_date + timedelta(days=1)

    acceptance_date = intimation_date + timedelta(days=random.randint(5, 20))
    acceptance_date = min(acceptance_date, today_value - timedelta(days=1))
    if acceptance_date <= intimation_date:
        acceptance_date = intimation_date + timedelta(days=1)

    return {
        "rcd_date": rcd_date,
        "last_premium_paid_date": last_premium_paid_date,
        "due_date": due_date,
        "death_date": death_date,
        "intimation_date": intimation_date,
        "revival_date": revival_date,
        "acceptance_date": acceptance_date,
        "installments_paid": installments_paid,
    }


def _add_months(base_date, month_delta):
    """Add months to a date, clamping day to the target month's length."""
    import calendar

    target_month_index = (base_date.month - 1) + month_delta
    target_year = base_date.year + target_month_index // 12
    target_month = (target_month_index % 12) + 1
    target_day = min(base_date.day, calendar.monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


# ============================================================================
# Row construction
# ============================================================================

def _resolve_claim_decision(subsection, is_suicide_row):
    if subsection == "Suicide cases":
        return random.choice(["Accept", "Reject"])
    return CLAIM_DECISION_BY_SUBSECTION[subsection]


def _resolve_cause_of_death(subsection):
    if subsection == "Suicide cases":
        return "SUICIDE"
    return random.choice(CAUSE_OF_DEATH_OPTIONS)


def _build_death_claim_row(tuid_counter, subsection, policy_reason, today_value):
    plan_option = random.choice(issuance.PLAN_OPTIONS)
    entry_age_min, entry_age_max = issuance.get_entry_age_range_for_plan_option(plan_option)
    age = random.randint(entry_age_min, entry_age_max)

    payment_freq_label = random.choice(["Annual", "Half-Yearly", "Quarterly", "Monthly"])
    interval_months = _frequency_interval_months(payment_freq_label)

    dates = _build_death_claim_dates(today_value, policy_reason, interval_months)

    birth_year = today_value.year - age
    la_birthdate = f"{birth_year}-05-25"
    la_gender = random.choice(issuance.GENDER)

    child_birthdate, _child_age, child_gender = issuance.build_child_fields()

    deferment_period = issuance.build_deferment_period(valid=True)
    charge_year, coverage_year, _maturity_year = issuance.get_years(
        "Regular Pay", age, deferment_period=deferment_period
    )

    if charge_year == 8:
        income_period = random.choice(issuance.INCOME_PERIOD_PPT8_VALID)
    else:
        income_period = random.choice(issuance.INCOME_PERIOD_PPT10_12_VALID)

    payment_freq_code = {"Annual": 1, "Half-Yearly": 2, "Quarterly": 3, "Monthly": 4}[payment_freq_label]
    discount_info = issuance.calculate_discounts("Regular Pay")
    annualized_premium = discount_info.get("annualized_premium")
    install_premium = issuance.compute_install_premium(annualized_premium, payment_freq_code)

    total_premiums_paid = install_premium * dates["installments_paid"]

    cause_of_death = _resolve_cause_of_death(subsection)
    decision = _resolve_claim_decision(subsection, cause_of_death == "SUICIDE")
    claim_status = decision if decision != "Reject" else "Reject/Repudiate"

    policy_status = POLICY_REASON_STATUS_MAP[policy_reason]

    # Premium due-date interplay with death/intimation, per business rule.
    premium_on_event_date = install_premium if dates["death_date"] == dates["due_date"] else 0
    excess_premium_on_event_date = (
        install_premium
        if dates["due_date"] < dates["death_date"] <= dates["intimation_date"]
        else 0
    )
    outstanding_premium = 0 if policy_status in ("Inforce",) else install_premium

    income_shield_period = (
        random.choice(issuance.INCOME_SHIELD_VALID_PERIODS)
        if plan_option in INCOME_SHIELD_PLAN_OPTIONS
        else "NA"
    )

    reason_for_death = REASON_FOR_DEATH_BY_CAUSE[cause_of_death]

    scenario_template = SCENARIO_TEXT_MAP[subsection]
    scenario_text = scenario_template.format(
        cause=cause_of_death,
        reason=policy_reason,
        status=policy_status,
        decision=decision,
    )
    scenario_text = "\n".join([
        scenario_text,
        f"RCD: {_format_date(dates['rcd_date'])}",
        f"Date of last Premium Paid: {_format_date(dates['last_premium_paid_date'])}",
        f"Due date: {_format_date(dates['due_date'])}",
        f"Date of Death: {_format_date(dates['death_date'])}",
        f"Date of Intimation: {_format_date(dates['intimation_date'])}",
    ] + (
        [f"Date of Revival: {_format_date(dates['revival_date'])}"] if dates["revival_date"] else []
    ) + [
        f"Date of Claim Acceptance: {_format_date(dates['acceptance_date'])}",
    ])

    row = {
        "TUID": f"TC_{MODULE_NAME.replace(' ', '')}_POST_{tuid_counter:03d}",
        "API_Operation": subsection,
        "Test Scenario": scenario_text,
        "Expected_Result": EXPECTED_RESULT_MAP[subsection],
        "policyNumber": _random_policy_number(),
        "dateOfIntimation": _format_date(dates["intimation_date"]),
        "causeOfDeath": cause_of_death,
        "Date of Revival": _format_date(dates["revival_date"]) if dates["revival_date"] else "",
        "rcd": _format_date(dates["rcd_date"]),
        "Date of Birth of Life Assured": la_birthdate,
        "Gender of Life Assured": la_gender,
        "Date of Birth of Child": child_birthdate,
        "Gender of Child": child_gender,
        "Is the Life Assured same as Policyholder?": "Yes",
        "dueDate": _format_date(dates["due_date"]),
        "Date of Death": _format_date(dates["death_date"]),
        "policyReasonOnEvent": policy_reason,
        "Policy Status": policy_status,
        "Claim Status": claim_status,
        "decision": decision,
        "Plan Option": plan_option,
        "Base Installment Premium inclusive of EMR Premium, Per Mille, NSAP loading and Service Tax (Rs.)": install_premium,
        "Total Premiums Paid inclusive of First Year Discount and modal loadings till Date of Death (INR)": total_premiums_paid,
        "totalBasePremiumPaidToDate": total_premiums_paid,
        "currentPolicyReason": policy_reason,
        "premiumOnDateOfEvent": premium_on_event_date,
        "outstandingPremium": outstanding_premium,
        "excessPremiumOnEventDate": excess_premium_on_event_date,
        "Annualised Premium (INR)": annualized_premium,
        "Date of Claim Acceptance": _format_date(dates["acceptance_date"]) if decision == "Accept" else "",
        "Premium Payment Term (in years)": charge_year,
        "Deferment period": deferment_period,
        "Policy Term (in years)": coverage_year,
        "Premium Frequency": payment_freq_label,
        "Income Period": income_period,
        "Advance Option": random.choice(["Yes", "No"]),
        "Existing Customer/Employee Discount": "Yes" if discount_info.get("Existing Customer Discount (%)") else "No",
        "Reason For Death": reason_for_death,
        "Income Shield Monthly Income Instalment (in years)": income_shield_period,
        "Date of last Premium Paid": _format_date(dates["last_premium_paid_date"]),
        "No. Of premium paid": dates["installments_paid"],
        "Premium Refund": "NA" if decision == "Accept" else install_premium,
        "Total Premiums Paid inclusive of Modal Loading, First Year Premium Discount, EMR Premium, Per Mille, NSAP loading & Rider premiums exclusive of Taxes till Date of Death (INR)": total_premiums_paid,
    }
    row.update(FIXED_VALUES)
    return row


# ============================================================================
# Main Test Case Generation
# ============================================================================

def generate_test_cases(epic_counts, selected_epics=None, epic_counts_rider=None,
                        selected_epics_rider=None, selected_header=None, **_kwargs):
    """Generate post-issuance Death Claim test cases for the saving plan."""
    selected_epics = selected_epics or list((epic_counts or {}).keys())

    if not selected_epics:
        return pd.DataFrame(columns=column_order)

    today_value = date.today()
    scenarios = []
    tuid_counter = 0

    for subsection in DEATH_CLAIM_SUBSECTIONS:
        if subsection not in selected_epics:
            continue
        counts = (epic_counts or {}).get(subsection, {})
        positive_count = int(counts.get("positive", 0) or 0)
        if positive_count <= 0:
            continue

        for i in range(positive_count):
            policy_reason = POLICY_REASONS[i % len(POLICY_REASONS)]
            tuid_counter += 1
            row = _build_death_claim_row(tuid_counter, subsection, policy_reason, today_value)
            scenarios.append(row)

    if not scenarios:
        return pd.DataFrame(columns=column_order)

    result_df = pd.DataFrame(scenarios)
    for col in column_order:
        if col not in result_df.columns:
            result_df[col] = ""

    return result_df[column_order]
