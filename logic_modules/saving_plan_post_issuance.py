import calendar
import math
import random
from datetime import date, timedelta
import string

import pandas as pd

from logic_modules import saving_plan_issuance as issuance

# ============================================================================
# Constants
# ============================================================================

MODULE_NAME = "Saving Plan"
LIFECYCLE_STAGE = "post issuance"
PRODUCT_CODE = getattr(issuance, "PRODUCT_CODE", "")

HEADER_ORDER = ["Death Claim"]

# Status progression used to build dod (date-of-death) / doi (date-of-intimation)
# combinations: policy status can only move forward along this chain between
# the death event and the intimation event (revival is handled separately).
STATUS_ORDER = ["inforce", "grace", "lapse", "RPU"]

STATUS_LABELS = {
    "inforce": "Inforce",
    "grace": "Grace Period",
    "lapse": "Lapse",
    "RPU": "Reduced Paid Up",
}

STATUS_REASON = {
    "inforce": "NEW_ISSUE",
    "grace": "GRACE",
    "lapse": "LAPSED",
    "RPU": "REDUCED_PAID_UP",
}

FREQUENCY_INTERVAL_MONTHS = {
    "Annual": 12,
    "Half-Yearly": 6,
    "Quarterly": 3,
    "Monthly": 1,
}
PAYMENT_FREQUENCY_CODE = {"Annual": 1, "Half-Yearly": 2, "Quarterly": 3, "Monthly": 4}

CAUSE_OF_DEATH_OPTIONS = ["ACCIDENTAL", "NON_ACCIDENTAL"]

INCOME_SHIELD_PLAN_OPTIONS = {"CAREERSTART_SECURE_INCOME", "CAREERSTART_LIFE_SHIELD_INCOME"}


def _dod_doi_cases(dod_status, doi_statuses):
    """Build (dod, doi) case tuples for one dod status against several doi statuses."""
    return [(dod_status, doi_status) for doi_status in doi_statuses]


# ----------------------------------------------------------------------------
# Case catalogues per sub-section. Each case is:
#   (checkbox_label, dod_status, doi_status, extra) where extra carries
#   flags: is_extra_prem / is_post_revival / suicide_window ("within"/"after"/None).
# A checkbox label may expand into several (dod, doi) rows (kept together so the
# UI shows one checkbox but generation still walks every dod/doi combination).
# ----------------------------------------------------------------------------

def _death_matrix_cases():
    """The base dod/doi death matrix shared by Claim Accept and Reject/Repudiate."""
    return [
        ("Death in-force + extra prem paids", [("inforce", "inforce")], {"extra_prem": True}),
        ("Death in-force", _dod_doi_cases("inforce", ["inforce", "grace", "lapse", "RPU"]), {}),
        ("Death post revival", [("inforce", "inforce")], {"post_revival": True}),
        ("Death in grace", _dod_doi_cases("grace", ["grace", "lapse"]), {}),
        ("Death in lapse", _dod_doi_cases("lapse", ["lapse"]), {}),
        ("Death in reduced paid up", _dod_doi_cases("RPU", ["RPU"]), {}),
    ]


def _suicide_matrix_cases():
    """The suicide dod/doi x within/after-1yr matrix shared by Suicide cases and
    the suicide-flavored rows inside Reject/Repudiate."""
    cases = [
        ("Suicide in-force + extra prem paids (after 1yr)", [("inforce", "inforce")],
         {"extra_prem": True, "suicide_window": "after"}),
        ("Suicide in-force + extra prem paids (within 1yr)", [("inforce", "inforce")],
         {"extra_prem": True, "suicide_window": "within"}),
        ("Suicide in-force (within 1yr)", _dod_doi_cases("inforce", ["inforce", "grace", "lapse", "RPU"]),
         {"suicide_window": "within"}),
        ("Suicide in-force (after 1yr)", _dod_doi_cases("inforce", ["inforce", "grace", "lapse", "RPU"]),
         {"suicide_window": "after"}),
        ("Suicide in grace (within 1yr)", _dod_doi_cases("grace", ["grace", "lapse"]),
         {"suicide_window": "within"}),
        ("Suicide in lapse (within 1yr)", _dod_doi_cases("lapse", ["lapse"]),
         {"suicide_window": "within"}),
        # No "Suicide in grace (after 1yr)" / "Suicide in lapse (after 1yr)"
        # cases: grace and lapse only occur within policy year 1 (see
        # dod_status in ("grace", "lapse") handling above), so a suicide more
        # than 1yr after RCD while dod_status is grace/lapse is not a valid
        # combination.
    ]
    return cases


CLAIM_ACCEPT_CASES = _death_matrix_cases()
REJECT_REPUDIATE_CASES = _death_matrix_cases() + _suicide_matrix_cases()
SUICIDE_CASES = _suicide_matrix_cases()

DEATH_CLAIM_SUBSECTIONS = [
    "Claim Accept cases",
    "Claim Reject/Repudiate cases",
    "Suicide cases",
]

SUBSECTION_CASE_CATALOGUE = {
    "Claim Accept cases": CLAIM_ACCEPT_CASES,
    "Claim Reject/Repudiate cases": REJECT_REPUDIATE_CASES,
    "Suicide cases": SUICIDE_CASES,
}

# decision fixed per sub-section; None means it's resolved per-row.
SUBSECTION_DECISION = {
    "Claim Accept cases": "Accept",
    "Claim Reject/Repudiate cases": None,  # Reject / Repudiate (with/without refund)
    "Suicide cases": "Accept",
}

REJECT_REPUDIATE_FLAVORS = [
    "Reject (no refund)",
    "Repudiate (with refund)",
    "Repudiate (without refund)",
]

POST_ISSUANCE_EPICS_BY_PLAN = {
    "saving plan": {
        "Death Claim": list(DEATH_CLAIM_SUBSECTIONS),
    }
}

EPIC_MAP = {epic_name: epic_name for epic_name in DEATH_CLAIM_SUBSECTIONS}
EPIC_MAP_RIDER = {}

REASON_FOR_DEATH_BY_CAUSE = {
    "ACCIDENTAL": "Accident",
    "NON_ACCIDENTAL": "Natural",
    "SUICIDE": "Suicide",
}

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

column_order = [
    "TUID", "API_Operation", "Test Scenario", "Expected_Result",
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


def get_case_catalogue(subsection):
    """Return the list of (checkbox_label, dod_doi_pairs, extra) cases for a sub-section."""
    return SUBSECTION_CASE_CATALOGUE.get(subsection, [])


# ============================================================================
# Date utilities
# ============================================================================

def _format_date(value):
    """Format date object to DD/MM/YYYY string."""
    return value.strftime("%d/%m/%Y")


def _add_months(base_date, month_delta):
    """Add months to a date, clamping day to the target month's length."""
    target_month_index = (base_date.month - 1) + month_delta
    target_year = base_date.year + target_month_index // 12
    target_month = (target_month_index % 12) + 1
    target_day = min(base_date.day, calendar.monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


def _random_policy_number():
    prefix_letters = "ALI0QA0"
    random_letters = "".join(random.choices(string.ascii_uppercase, k=2))
    digits = "".join(random.choices("0123456789", k=4))
    return f"{prefix_letters}{random_letters}{digits}"


# ============================================================================
# Date engine
# ============================================================================
# All date placement is done in integer day-offsets from RCD first (so every
# ordering/window constraint is checked with exact arithmetic), and only
# converted to real calendar dates -- via _add_months for premium-installment
# dates -- at the very end. The chain is built from a provisional RCD pinned
# comfortably far in the past (RCD_MAX_YEARS_BACK), then re-anchored to a
# genuinely random RCD between RCD_MIN_YEARS_BACK and RCD_MAX_YEARS_BACK back
# (see _place_chain_in_time) so the resulting chain always lands before
# "today" with margin to spare; nothing is clamped against "today" after the
# fact.
#
# Chain: RCD -> (lapse -> Reinstatement, if applicable) -> last premium paid
# -> due date -> date of death (dod) -> date of intimation (doi) -> date of
# claim acceptance. doi status is always >= dod status along STATUS_ORDER;
# the only status change between dod and doi is the grace/lapse/RPU clock
# running out while the intimation is delayed.
#
# For suicide cases, "within/after 1 year" is measured against whichever
# reference point applies: RCD for a policy that never lapsed, or the
# Reinstatement date for a policy that lapsed and was later revived. RPU
# requires >=12 months of premiums paid overall, which conflicts with "within
# 1 year of RCD" for a policy that never lapsed -- so rows that need both RPU
# eligibility and a "within 1yr" suicide window are built against a
# Reinstatement reference: the policy had already paid 12+ months before its
# original lapse, then reinstated, and the suicide window is re-measured from
# that reinstatement.

SUICIDE_WINDOW_DAYS = 365
INTERVAL_DAY_APPROX = 30.44  # average calendar month length, for bounds math

# RCD must never be more than 5 years before today, and is randomized between
# 2 and 5 years back. A chain is first built from a provisional RCD pinned at
# RCD_MAX_YEARS_BACK (always feasible), then its real measured span is used
# to place a genuinely random final RCD within the full 2-5 year window (see
# _place_chain_in_time), leaving CHAIN_SAFETY_MARGIN_DAYS of slack before
# today.
RCD_MAX_YEARS_BACK = 5
RCD_MIN_YEARS_BACK = 2
CHAIN_SAFETY_MARGIN_DAYS = 30

DOD_OFFSET_RANGE = {
    # (min, max) days added on top of due_date so the policy is in this dod_status.
    # "inforce" is negative: DOD must fall *before* the premium due date.
    "inforce": (-5, -1),
    "grace": (5, 15),
    "lapse": (35, 90),
    "RPU": (35, 90),
}

# Grace period length by payment frequency: 15 days for Monthly, 30 days otherwise.
GRACE_PERIOD_DAYS = {
    "Annual": 30,
    "Half-Yearly": 30,
    "Quarterly": 30,
    "Monthly": 15,
}


def _grace_period_days(interval_months):
    for label, months in FREQUENCY_INTERVAL_MONTHS.items():
        if months == interval_months:
            return GRACE_PERIOD_DAYS[label]
    return 30


def _lapse_dod_offset_cap(rcd_date, due_date, interval_months):
    """Largest dod_offset (days past due_date) that keeps death_date on the
    "lapse" side of the lapse/RPU cutover used by _intimation_date_for_status
    -- mirrors that function's own cutover logic exactly so a dod_status of
    "lapse" never produces a death_date for which no "lapse" doi window
    exists."""
    grace_days = _grace_period_days(interval_months)
    grace_end = due_date + timedelta(days=grace_days)
    months_paid_by_due_days = (due_date - rcd_date).days
    lapse_end = grace_end if months_paid_by_due_days >= 360 else max(grace_end, rcd_date + timedelta(days=365))
    return (lapse_end - due_date).days


def _installments_for_days(min_days, interval_months):
    interval_days = interval_months * INTERVAL_DAY_APPROX
    return max(1, math.ceil(min_days / interval_days))


def _add_installments(base_date, count, interval_months):
    """Advance base_date by `count` premium intervals. Computed as a single
    _add_months call (not a sequential loop) so every installment date is
    independently anchored to base_date's day-of-month: a clamp in a short
    month (e.g. 31st -> 28th in Feb) never carries over to later
    installments that land in months long enough for the original day."""
    return _add_months(base_date, count * interval_months)


def _due_date_for_installments(reference_date, installments, interval_months):
    """due_date is one interval past the last paid installment (the next
    premium that would fall due), computed as a single hop from
    reference_date (not via last_paid) so it is independently anchored to
    reference_date's day-of-month."""
    return _add_months(reference_date, (installments + 1) * interval_months)


def _max_installments_within_window(reference_date, interval_months, dod_min, min_installments,
                                    window_days, safety_margin):
    """Walk real (calendar-correct) due_date positions forward from
    `reference_date` and return the largest installment count N >=
    min_installments for which due_date (the premium due after N paid
    installments) plus the smallest possible dod_status offset still lands
    within `window_days` of `reference_date` (minus safety_margin). Returns
    None if even min_installments doesn't fit."""
    limit = timedelta(days=window_days - safety_margin - dod_min)
    best = None
    count = min_installments
    # Cap the walk generously; real chains never need anywhere near this many.
    while count <= min_installments + 60:
        candidate_due_date = _due_date_for_installments(reference_date, count, interval_months)
        if candidate_due_date - reference_date > limit:
            break
        best = count
        count += 1
    return best


def _max_installments_before_rpu(interval_months):
    """Largest installment count N (paid after RCD) for which the due_date
    that follows still falls before 12 months of premiums have been paid --
    i.e. the policy is still grace/lapse-eligible rather than having already
    crossed into RPU territory. For sub-annual frequencies this is > 0, so
    several installments can legitimately be paid before the due date that
    finally gets missed (not just the very first one)."""
    return max(0, math.ceil(12 / interval_months) - 2)


def _choose_payment_frequency(dod_status, suicide_window, doi_status=None, reference_date=None, freq_group_idx=0):
    """Pick a payment frequency label, excluding frequencies for which a
    "within 1yr" suicide window is mathematically infeasible against this
    dod_status (the post-reinstatement leg always starts from 1 installment,
    since RPU eligibility there is satisfied by the pre-lapse phase).

    Annual is also excluded whenever dod_status or doi_status is "lapse", or
    dod_status is "grace": with a 12-month interval, the first due date after
    RCD already falls at the year 1 / year 2 boundary, so a missed premium
    can never put the policy in grace or lapse within policy year 1 (dod), or
    let the policy reach lapse -- rather than RPU -- with fewer than 12
    months paid (doi) -- lapse (and the grace period that precedes it, when
    it is dod_status) is only possible for sub-annual frequencies."""
    all_frequencies = ["Annual", "Half-Yearly", "Quarterly", "Monthly"]
    if dod_status in ("grace", "lapse") or doi_status == "lapse":
        all_frequencies = [label for label in all_frequencies if label != "Annual"]

    if suicide_window != "within":
        return all_frequencies[freq_group_idx % len(all_frequencies)]

    dod_min, _dod_max = DOD_OFFSET_RANGE[dod_status]
    reference_date = reference_date or date.today()
    feasible = [
        label for label in all_frequencies
        if _max_installments_within_window(
            reference_date, FREQUENCY_INTERVAL_MONTHS[label], dod_min, 1, SUICIDE_WINDOW_DAYS, 5
        ) is not None
    ]
    pool = feasible or all_frequencies
    return pool[freq_group_idx % len(pool)]


def _pick_installments_for_suicide_window(reference_date, interval_months, dod_status, suicide_window,
                                          min_installments):
    """Pick an installment count N (measured from `reference_date`, the RCD or
    Reinstatement point the suicide window applies to) such that due_date (N
    intervals out) plus the dod_status offset satisfies the suicide
    within/after-1yr window. Returns (installments, dod_offset_days).

    dod_status "grace"/"lapse" must stay under the 12-months-paid RPU
    threshold (_max_installments_before_rpu), otherwise the policy would go
    to RPU instead of lapsing -- but for sub-annual frequencies several
    installments can still legitimately be paid before the due date that
    finally gets missed, so N is randomized up to that cap rather than
    always pinned to min_installments (which only ever produced the very
    first due date)."""
    dod_min, dod_max = DOD_OFFSET_RANGE[dod_status]
    pinned_to_min = dod_status in ("grace", "lapse")
    rpu_cap = _max_installments_before_rpu(interval_months) if pinned_to_min else None

    if suicide_window == "within":
        max_installments = _max_installments_within_window(
            reference_date, interval_months, dod_min, min_installments, SUICIDE_WINDOW_DAYS, 5
        )
        if max_installments is None:
            # Caller should have avoided this via _choose_payment_frequency;
            # fall back to the smallest possible chain as a safe default.
            max_installments = min_installments
        if pinned_to_min:
            max_installments = min(max_installments, max(min_installments, rpu_cap))
        installments = random.randint(min_installments, max_installments)
        due_date = _due_date_for_installments(reference_date, installments, interval_months)
        remaining_days = (SUICIDE_WINDOW_DAYS - 5) - (due_date - reference_date).days
        dod_offset = random.randint(dod_min, max(dod_min, min(dod_max, remaining_days)))
        return installments, dod_offset

    if suicide_window == "after":
        safety_margin = 30
        min_installments_for_window = _installments_for_days(SUICIDE_WINDOW_DAYS + safety_margin, interval_months)
        installments = max(min_installments, min_installments_for_window) + random.randint(0, 1)
        dod_offset = random.randint(dod_min, dod_max)
        return installments, dod_offset

    if pinned_to_min:
        installments = random.randint(min_installments, max(min_installments, rpu_cap))
    else:
        installments = min_installments + random.randint(0, 2)
    dod_offset = random.randint(dod_min, dod_max)
    return installments, dod_offset


def _trial_rcd_date(today_value):
    """Earliest allowed RCD (RCD_MAX_YEARS_BACK before today), used as a
    provisional anchor to build a chain and measure its real length before
    placing it randomly in time (see _place_chain_in_time)."""
    return today_value.replace(year=today_value.year - RCD_MAX_YEARS_BACK)


def _place_chain_in_time(today_value, chain_result, trial_rcd_date):
    """Re-anchor a chain built from `trial_rcd_date` to a genuinely random
    RCD between RCD_MIN_YEARS_BACK and RCD_MAX_YEARS_BACK before today.

    The chain was built forward from trial_rcd_date (the earliest allowed
    RCD), so its real end-to-end span is now known exactly (no more relying
    on a conservative, worst-case per-shape budget that often left no slack
    to randomize within).

    A flat day-count shift preserves every day-based gap/window/ordering
    constraint exactly, but installment-anchored dates (last premium paid,
    due date, lapsed due date) were originally placed via month-based
    _add_months off trial_rcd_date, not a day count -- shifting them by a
    flat day delta instead of re-materializing them via _add_months off the
    final RCD lets their day-of-month drift away from the final RCD's
    whenever the two anchors cross a different mix of month lengths (e.g.
    Feb vs. 31-day months) over the (often multi-year) gap between them.
    So those three are re-materialized via _add_months off the final RCD
    using their already-known total months-from-rcd, and every other date
    (which is a pure day offset from one of those three, or from another
    day-offset date) is shifted by that same anchor's correction -- the
    difference between its re-materialized and naively-shifted position --
    so its exact day-gap from its anchor is preserved."""
    total_span_days = (chain_result["acceptance_date"] - trial_rcd_date).days

    earliest_rcd = trial_rcd_date
    latest_rcd = today_value.replace(year=today_value.year - RCD_MIN_YEARS_BACK) - timedelta(
        days=total_span_days + CHAIN_SAFETY_MARGIN_DAYS
    )
    if latest_rcd < earliest_rcd:
        latest_rcd = earliest_rcd

    days_of_slack = (latest_rcd - earliest_rcd).days
    shift_days = random.randint(0, max(0, days_of_slack))
    if shift_days == 0:
        return chain_result

    delta = timedelta(days=shift_days)
    final_rcd_date = trial_rcd_date + delta

    shifted = dict(chain_result)
    shifted["rcd_date"] = final_rcd_date
    shifted["due_date"] = _add_months(final_rcd_date, chain_result["due_date_months"])
    shifted["last_premium_paid_date"] = _add_months(final_rcd_date, chain_result["last_premium_paid_months"])

    if chain_result.get("lapsed_due_date") is not None:
        shifted["lapsed_due_date"] = _add_months(final_rcd_date, chain_result["lapsed_due_date_months"])
        lapsed_correction = shifted["lapsed_due_date"] - (chain_result["lapsed_due_date"] + delta)
        shifted["revival_date"] = chain_result["revival_date"] + delta + lapsed_correction

    # death_date is a pure day offset from due_date (dod_offset), with no
    # separate dependency on rcd_date, so it can be corrected the same way --
    # except for dod_status "lapse", whose offset was originally capped
    # against the trial position's lapse/RPU cutover (_lapse_dod_offset_cap);
    # since that cutover depends on (due_date - rcd_date) in days, which can
    # itself shift by a day or two once due_date is re-materialized here,
    # the cap must be re-applied at the final position too.
    dod_offset_days = (chain_result["death_date"] - chain_result["due_date"]).days
    if chain_result.get("dod_status") == "lapse":
        dod_offset_days = min(
            dod_offset_days,
            _lapse_dod_offset_cap(final_rcd_date, shifted["due_date"], chain_result["interval_months"]),
        )
    shifted["death_date"] = shifted["due_date"] + timedelta(days=dod_offset_days)

    # intimation_date's window boundaries depend on rcd_date and due_date
    # independently (see _intimation_date_for_status), so a single flat
    # correction can't always preserve both relationships -- recompute it
    # (and the dates that chain off it) fresh against the final structural
    # dates instead of reshifting the trial run's values.
    extra_premium_debit_date, intimation_date, acceptance_date = _add_dependent_dates(
        final_rcd_date, shifted["due_date"], shifted["death_date"],
        chain_result["doi_status"], chain_result["interval_months"], chain_result["extra_prem"],
    )
    shifted["extra_premium_debit_date"] = extra_premium_debit_date
    shifted["intimation_date"] = intimation_date
    shifted["acceptance_date"] = acceptance_date
    return shifted


def _build_date_chain(today_value, dod_status, doi_status,
                       extra_prem=False, post_revival=False,
                       suicide_window=None, needs_rpu_1yr=False, freq_group_idx=0):
    """Build the full date chain, choosing the payment frequency and RCD
    internally.

    The chain is first built forward from a provisional RCD pinned at
    RCD_MAX_YEARS_BACK before today (the earliest allowed point), which is
    always feasible regardless of frequency/installment counts. Its real
    end-to-end span is then measured exactly and used to place a genuinely
    random final RCD anywhere between RCD_MIN_YEARS_BACK and
    RCD_MAX_YEARS_BACK back (see _place_chain_in_time), rather than relying
    on a conservative worst-case budget picked before the chain's actual
    shape was known.

    Frequency feasibility for a "within 1yr" suicide window depends on the
    exact calendar dates involved (leap years shift the real day-count by 1),
    so it must be checked against the actual (provisional) RCD that will be
    used to build the chain, not an approximation.
    """
    is_suicide = suicide_window is not None
    # A "within 1yr" suicide row that also needs RPU eligibility (12+ months
    # paid) can only be satisfied by measuring the 1yr window from a
    # Reinstatement, not from the original RCD.
    uses_reinstatement_reference = post_revival or (
        is_suicide and needs_rpu_1yr and suicide_window == "within"
    )

    trial_rcd_date = _trial_rcd_date(today_value)

    payment_freq_label = _choose_payment_frequency(
        dod_status, suicide_window, doi_status=doi_status, reference_date=trial_rcd_date,
        freq_group_idx=freq_group_idx,
    )
    interval_months = FREQUENCY_INTERVAL_MONTHS[payment_freq_label]

    if uses_reinstatement_reference:
        result = _build_date_chain_via_reinstatement(
            trial_rcd_date, dod_status, doi_status, interval_months,
            extra_prem=extra_prem, post_revival=post_revival,
            suicide_window=suicide_window, needs_rpu_1yr=needs_rpu_1yr,
        )
    else:
        result = _build_date_chain_via_rcd(
            trial_rcd_date, dod_status, doi_status, interval_months,
            extra_prem=extra_prem, suicide_window=suicide_window, needs_rpu_1yr=needs_rpu_1yr,
        )

    result["dod_status"] = dod_status
    result = _place_chain_in_time(today_value, result, trial_rcd_date)
    result["payment_freq_label"] = payment_freq_label
    return result


def _build_date_chain_via_rcd(rcd_date, dod_status, doi_status, interval_months,
                               extra_prem=False, suicide_window=None, needs_rpu_1yr=False):
    """Build the chain forward from RCD, measuring the suicide window (if any)
    against RCD directly."""
    if dod_status in ("grace", "lapse"):
        # Grace/lapse must stay under the 12-months-paid RPU threshold; 0 is
        # just the floor (the very first premium after RCD could be the one
        # that's missed) -- _pick_installments_for_suicide_window randomizes
        # up to _max_installments_before_rpu from here.
        min_installments = 0
    else:
        min_installments = _installments_for_days(360, interval_months) if needs_rpu_1yr else 1

    installments_before_dod, dod_offset = _pick_installments_for_suicide_window(
        rcd_date, interval_months, dod_status, suicide_window, min_installments
    )

    if extra_prem and dod_status == "inforce":
        # extra_prem cases are always paired with doi_status "inforce" too, so
        # both the extra auto-pay debit and the intimation date (in that
        # order) must still land before due_date. The plain inforce window
        # (-5,-1) is too tight at its near end (-1/-2 days) to fit both --
        # widen the gap so _finish_date_chain has room to place them.
        dod_offset = min(dod_offset, -3)

    if doi_status == "lapse" and dod_status != "lapse":
        # Lapse (as opposed to RPU) is only reached if fewer than 12 months
        # of premiums were paid as of the missed due_date; otherwise the
        # policy goes straight to RPU instead of lapsing. Cap the installment
        # count so (installments_before_dod + 1) * interval_months < 12,
        # overriding min_installments if needed (Annual is excluded earlier
        # via _choose_payment_frequency, so this cap is always >= 0 here).
        installments_before_dod = min(installments_before_dod, _max_installments_before_rpu(interval_months))

    last_premium_paid_date = _add_installments(rcd_date, installments_before_dod, interval_months)
    due_date = _due_date_for_installments(rcd_date, installments_before_dod, interval_months)

    if dod_status == "lapse":
        # Mirror _intimation_date_for_status's lapse/RPU cutover: if due_date
        # already sits close to the 12-months-paid mark, the (35,90)-day
        # DOD_OFFSET_RANGE for lapse can push death_date past that cutover,
        # leaving no valid "lapse" window for the intimation date afterward.
        # Cap the offset so death_date never crosses it.
        dod_offset = min(dod_offset, _lapse_dod_offset_cap(rcd_date, due_date, interval_months))

    death_date = due_date + timedelta(days=dod_offset)

    return _finish_date_chain(
        rcd_date, last_premium_paid_date, due_date, death_date,
        doi_status, installments_before_dod, interval_months,
        due_date_months=(installments_before_dod + 1) * interval_months,
        last_premium_paid_months=installments_before_dod * interval_months,
        extra_prem=extra_prem, revival_date=None,
    )


def _first_rcd_aligned_due_at_or_after(lapse_due_date, target_date, interval_months):
    """Return the first due_date on the lapse_due_date-anchored RCD-aligned
    premium cycle that falls strictly after `target_date` (e.g. the
    Reinstatement date), plus how many intervals past lapse_due_date it is.
    Each candidate is computed as a single hop from lapse_due_date (not
    chained through prior candidates) so a month-end clamp never carries
    over to a later, longer month."""
    intervals = 1
    candidate = _add_months(lapse_due_date, intervals * interval_months)
    while candidate <= target_date:
        intervals += 1
        candidate = _add_months(lapse_due_date, intervals * interval_months)
    return candidate, intervals


def _build_date_chain_via_reinstatement(rcd_date, dod_status, doi_status, interval_months,
                                        extra_prem=False, post_revival=False,
                                        suicide_window=None, needs_rpu_1yr=False):
    """Build the chain forward from RCD -> lapse -> Reinstatement, with the
    suicide window (if any) measured from the Reinstatement date. Every
    installment-anchored date (last premium paid, due date) stays aligned to
    RCD's day-of-month throughout -- premiums resume on the same RCD-aligned
    cycle after reinstatement rather than restarting from Reinstatement's own
    (arbitrary) day."""
    # Pre-lapse phase: enough installments paid before the original lapse so
    # RPU eligibility (12+ months total paid) holds if required. Kept to
    # exactly 1 installment for the plain post_revival case (due_date is
    # always one interval past the last paid installment, so each leg here
    # effectively costs (installments+1) intervals) so the full chain fits
    # within the 5-year RCD budget even at Annual frequency.
    pre_lapse_installments = _installments_for_days(360, interval_months) if needs_rpu_1yr else 1

    lapse_due_date = _due_date_for_installments(rcd_date, pre_lapse_installments, interval_months)

    grace_days = _grace_period_days(interval_months)
    reinstatement_date = lapse_due_date + timedelta(days=grace_days + random.randint(15, 60))

    # How many RCD-aligned intervals past lapse_due_date are needed to reach
    # the first due_date after reinstatement (premiums resume on this
    # RCD-aligned cycle, not on a new one anchored to reinstatement_date's
    # own arbitrary day-of-month).
    _, intervals_to_first_due = _first_rcd_aligned_due_at_or_after(
        lapse_due_date, reinstatement_date, interval_months
    )

    if post_revival:
        post_reinstatement_installments = 1
        dod_min, dod_max = DOD_OFFSET_RANGE[dod_status]
        dod_offset = random.randint(dod_min, dod_max)
    else:
        # Installment count is chosen against the real Reinstatement date (the
        # suicide within/after-1yr window is measured from there), but the
        # resulting due_date is then materialized on the RCD-aligned cycle
        # below, not restarted from reinstatement_date's own day-of-month.
        post_reinstatement_installments, dod_offset = _pick_installments_for_suicide_window(
            reinstatement_date, interval_months, dod_status, suicide_window, 1
        )

    # last_premium_paid_date is `post_reinstatement_installments` intervals
    # past lapse_due_date's cycle, starting at intervals_to_first_due (the
    # first RCD-aligned due date at/after reinstatement -- that installment
    # is the reinstatement payment itself, paid on/after reinstatement_date,
    # never on lapse_due_date, which is the due date that was missed and
    # triggered the lapse). due_date (the next, still-unpaid premium) is one
    # interval further. Both are computed as a single hop from lapse_due_date
    # (not chained through intermediate candidates) so month-end clamping
    # never compounds.
    last_paid_intervals_from_lapse_due = intervals_to_first_due + post_reinstatement_installments - 1
    due_intervals_from_lapse_due = last_paid_intervals_from_lapse_due + 1
    due_date = _add_months(lapse_due_date, due_intervals_from_lapse_due * interval_months)
    last_premium_paid_date = _add_months(lapse_due_date, last_paid_intervals_from_lapse_due * interval_months)
    death_date = due_date + timedelta(days=dod_offset)

    # +1 for the arrears premium that reinstatement clears (the original
    # lapse_due_date installment): it has no calendar date of its own --
    # last_premium_paid_date above only marks the first *regular* installment
    # paid after reinstatement -- but it was still a real premium paid to
    # revive the policy, so it must be counted even though it isn't dated.
    total_installments = pre_lapse_installments + last_paid_intervals_from_lapse_due + 1

    lapsed_due_date_months = (pre_lapse_installments + 1) * interval_months
    return _finish_date_chain(
        rcd_date, last_premium_paid_date, due_date, death_date,
        doi_status, total_installments, interval_months,
        due_date_months=lapsed_due_date_months + due_intervals_from_lapse_due * interval_months,
        last_premium_paid_months=lapsed_due_date_months + last_paid_intervals_from_lapse_due * interval_months,
        extra_prem=extra_prem, revival_date=reinstatement_date, lapsed_due_date=lapse_due_date,
        lapsed_due_date_months=lapsed_due_date_months,
    )


def _add_dependent_dates(rcd_date, due_date, death_date, doi_status, interval_months, extra_prem):
    """Compute the dates that are randomized *from* the structural chain
    (extra-premium debit, intimation, acceptance) but never feed back into
    it. Kept as a standalone function of only (rcd_date, due_date,
    death_date) -- not the intermediate values used to derive them -- so
    _place_chain_in_time can call it a second time against the final,
    RCD-realigned structural dates to get genuinely correct results there,
    rather than trying to reshift the trial run's values (whose windows
    depend on rcd_date and due_date independently, so a single flat
    correction can't always preserve both relationships at once)."""
    # Extra-premium scenario: an autopay premium is debited *after* the date of
    # death but on/before the date of intimation (rare, explicit case).
    # extra_prem cases are always paired with doi_status "inforce", so the
    # debit (and the intimation_date override below) must still land before
    # due_date -- cap the 1-5 day offset to whatever room actually remains
    # (the caller widens dod_offset for extra_prem so there's at least 3
    # days of gap here).
    extra_premium_debit_date = None
    if extra_prem:
        gap_to_due = (due_date - death_date).days
        max_extra_offset = max(1, min(5, gap_to_due - 2))
        extra_premium_debit_date = death_date + timedelta(days=random.randint(1, max_extra_offset))

    intimation_date = _intimation_date_for_status(
        death_date, due_date, rcd_date, doi_status, interval_months
    )
    if extra_premium_debit_date is not None:
        intimation_date = max(intimation_date, extra_premium_debit_date + timedelta(days=1))

    acceptance_date = intimation_date + timedelta(days=random.randint(5, 20))
    return extra_premium_debit_date, intimation_date, acceptance_date


def _finish_date_chain(rcd_date, last_premium_paid_date, due_date, death_date,
                       doi_status, installments_paid, interval_months,
                       due_date_months, last_premium_paid_months,
                       extra_prem=False, revival_date=None, lapsed_due_date=None,
                       lapsed_due_date_months=None):
    extra_premium_debit_date, intimation_date, acceptance_date = _add_dependent_dates(
        rcd_date, due_date, death_date, doi_status, interval_months, extra_prem
    )

    # installments_paid counts installments *after* RCD (count=0 means only
    # the RCD premium was paid); the real "number of premiums paid" also
    # includes the RCD installment itself.
    total_premiums_paid_count = installments_paid + 1

    return {
        "rcd_date": rcd_date,
        "last_premium_paid_date": last_premium_paid_date,
        "due_date": due_date,
        "death_date": death_date,
        "intimation_date": intimation_date,
        "revival_date": revival_date,
        "lapsed_due_date": lapsed_due_date,
        "acceptance_date": acceptance_date,
        "extra_premium_debit_date": extra_premium_debit_date,
        "installments_paid": total_premiums_paid_count,
        # Total whole-interval months from rcd_date to each installment-
        # anchored date, so _place_chain_in_time can re-materialize them via
        # _add_months off the final RCD (keeping day-of-month aligned)
        # instead of a flat day shift.
        "due_date_months": due_date_months,
        "last_premium_paid_months": last_premium_paid_months,
        "lapsed_due_date_months": lapsed_due_date_months,
        # Carried through so _place_chain_in_time can recompute the
        # dependent dates (extra premium debit / intimation / acceptance)
        # against the final, RCD-realigned structural dates.
        "doi_status": doi_status,
        "interval_months": interval_months,
        "extra_prem": extra_prem,
    }


def _intimation_date_for_status(death_date, due_date, rcd_date, doi_status, interval_months):
    """Place the date of intimation after death_date so the policy has reached
    `doi_status`, using the real calendar boundaries around `due_date` (the
    due date dod_status was measured against) rather than a flat day-delay:
      - inforce: strictly before due_date.
      - grace:   (due_date, due_date + grace_days].
      - lapse:   (due_date + grace_days, rcd_date + 365 days] -- i.e. before
                 the policy would reach 12 months paid (from RCD) and become
                 RPU instead of remaining lapsed.
      - RPU:     after the lapse window closes (or, for a direct
                 inforce/grace -> RPU jump, comfortably after due_date).
    Every window is intersected with "on/after death_date" and falls back to
    a fixed small delay if death_date itself is already past the window
    (e.g. dod_status == doi_status, where death_date is already inside it).

    The 12-months-paid mark is normally rcd_date + 365 days, but a dod_status
    that itself requires 12+ months paid before the missed due_date (RPU
    eligibility on the dod side) can push due_date -- and so grace_end --
    past that fixed mark. In that case there is no lapse state to pass
    through at all (grace transitions straight to RPU), so lapse_end is
    pulled up to grace_end rather than left behind it, which would otherwise
    invert the lapse/RPU window order.
    """
    grace_days = _grace_period_days(interval_months)
    grace_end = due_date + timedelta(days=grace_days)
    months_paid_by_due_days = (due_date - rcd_date).days
    lapse_end = grace_end if months_paid_by_due_days >= 360 else max(grace_end, rcd_date + timedelta(days=365))

    windows = {
        "inforce": (None, due_date - timedelta(days=1)),
        "grace": (due_date, grace_end),
        "lapse": (grace_end + timedelta(days=1), lapse_end),
        "RPU": (lapse_end + timedelta(days=1), None),
    }

    window_start, window_end = windows[doi_status]
    earliest = death_date if window_start is None else max(death_date, window_start)
    if window_end is not None and earliest > window_end:
        # death_date already sits past this doi_status's window (typical
        # when dod_status == doi_status and death_date is already inside
        # it) -- fall back to a short delay from death_date.
        return death_date + timedelta(days=random.randint(1, 5))

    latest = window_end if window_end is not None else earliest + timedelta(days=60)
    span_days = max(0, (latest - earliest).days)
    return earliest + timedelta(days=random.randint(0, span_days))


# ============================================================================
# Row construction
# ============================================================================

def _resolve_reject_repudiate_flavor():
    return random.choice(REJECT_REPUDIATE_FLAVORS)


def _decision_and_status_from_flavor(flavor):
    if flavor.startswith("Reject"):
        return "Reject", "Reject"
    return "Repudiate", "Repudiate"


def _premium_refund(flavor, total_premiums_paid):
    if flavor == "Repudiate (with refund)":
        return str(total_premiums_paid)
    return "NA"


def _build_death_claim_row(tuid_counter, subsection, case_label, dod_status, doi_status, extra, combo_idx=0):
    today_value = date.today()

    # Deterministic Plan Option x PPT x Premium Frequency coverage: combo_idx
    # walks a full (plan option x frequency) grid (plan option fast-changing,
    # frequency slow-changing via freq_group_idx), while ppt_idx is offset by
    # both indices so PPT doesn't move in lockstep with either axis. See the
    # plan doc for the pairwise-coverage proof.
    plan_options = issuance.PLAN_OPTIONS
    plan_option_idx = combo_idx % len(plan_options)
    freq_group_idx = combo_idx // len(plan_options)
    plan_option = plan_options[plan_option_idx]
    entry_age_min, entry_age_max = issuance.get_entry_age_range_for_plan_option(plan_option)
    age = random.randint(entry_age_min, entry_age_max)

    extra_prem = bool(extra.get("extra_prem"))
    post_revival = bool(extra.get("post_revival"))
    suicide_window = extra.get("suicide_window")
    needs_rpu_1yr = "RPU" in (dod_status, doi_status)

    dates = _build_date_chain(
        today_value, dod_status, doi_status,
        extra_prem=extra_prem, post_revival=post_revival,
        suicide_window=suicide_window, needs_rpu_1yr=needs_rpu_1yr,
        freq_group_idx=freq_group_idx,
    )
    payment_freq_label = dates["payment_freq_label"]

    # Anchor to RCD (not today's date): `age` is the entry age as of RCD, and
    # RCD is itself backdated by RCD_MIN_YEARS_BACK..RCD_MAX_YEARS_BACK years,
    # so computing the birth year off today's date would understate the
    # assured's real age at RCD and could put it below MIN_ENTRY_AGE (18).
    # Birthdate is fixed at MM-DD 05-25, so if RCD falls before May 25 of its
    # own year, that year's birthday hasn't happened yet as of RCD -- back the
    # birth year up one further to keep the completed age at RCD equal to age.
    rcd_date = dates["rcd_date"]
    birthday_not_yet_reached = (rcd_date.month, rcd_date.day) < (5, 25)
    birth_year = rcd_date.year - age - (1 if birthday_not_yet_reached else 0)
    la_birthdate = f"{birth_year}-05-25"
    la_gender = random.choice(issuance.GENDER)

    # Anchor the child's DOB to the death event's year (not the real today,
    # which build_child_fields defaults to) so a young child_age can't land
    # a birthdate after Date of Death/Intimation. build_child_fields fixes
    # the birthdate at MM-DD 05-25, so when death_date falls before May 25
    # of its own year, back the anchor up a further year to guarantee the
    # birthdate still precedes it even at child_age=0.
    death_date = dates["death_date"]
    child_ref_year = death_date.year if (death_date.month, death_date.day) >= (5, 25) else death_date.year - 1
    child_birthdate, _child_age, child_gender = issuance.build_child_fields(current_year=child_ref_year)

    deferment_period = issuance.build_deferment_period(valid=True)
    ppt_values = issuance.PPT_RULES["Regular Pay"]["valid_charge_years"]
    ppt_idx = (plan_option_idx + freq_group_idx) % len(ppt_values)
    charge_year, coverage_year, _maturity_year = issuance.get_years(
        "Regular Pay", age, deferment_period=deferment_period,
        forced_charge_year=ppt_values[ppt_idx],
    )

    if charge_year == 8:
        income_period = random.choice(issuance.INCOME_PERIOD_PPT8_VALID)
    else:
        income_period = random.choice(issuance.INCOME_PERIOD_PPT10_12_VALID)

    payment_freq_code = PAYMENT_FREQUENCY_CODE[payment_freq_label]
    discount_info = issuance.calculate_discounts("Regular Pay")
    annualized_premium = discount_info.get("annualized_premium")
    install_premium = issuance.compute_install_premium(annualized_premium, payment_freq_code)

    total_premiums_paid = install_premium * dates["installments_paid"]

    is_suicide_case = subsection == "Suicide cases" or suicide_window is not None
    cause_of_death = "SUICIDE" if is_suicide_case else random.choice(CAUSE_OF_DEATH_OPTIONS)
    reason_for_death = REASON_FOR_DEATH_BY_CAUSE[cause_of_death]

    fixed_decision = SUBSECTION_DECISION[subsection]
    if fixed_decision is not None:
        decision = fixed_decision
        claim_status = decision
        premium_refund = "NA"
    else:
        flavor = _resolve_reject_repudiate_flavor()
        decision, claim_status = _decision_and_status_from_flavor(flavor)
        premium_refund = _premium_refund(flavor, total_premiums_paid)

    # dod is used for policyReasonOnEvent/Policy Status (status as of the event).
    policy_reason = STATUS_REASON["inforce"] if post_revival else STATUS_REASON[dod_status]
    policy_status = STATUS_LABELS["inforce"] if post_revival else STATUS_LABELS[dod_status]

    premium_on_event_date = install_premium if dates["death_date"] == dates["due_date"] else 0
    excess_premium_on_event_date = (
        install_premium if dates.get("extra_premium_debit_date") is not None else 0
    )
    outstanding_premium = 0 if policy_status == "Inforce" else install_premium

    income_shield_period = (
        str(random.choice(issuance.INCOME_SHIELD_VALID_PERIODS))
        if plan_option in INCOME_SHIELD_PLAN_OPTIONS
        else "NA"
    )

    suicide_window_reference = None
    if suicide_window is not None:
        uses_reinstatement_reference = post_revival or (needs_rpu_1yr and suicide_window == "within")
        suicide_window_reference = "Reinstatement" if uses_reinstatement_reference else "RCD"

    is_revival_case = bool(dates.get("revival_date"))

    scenario_lines = [
        f"To verify Death Claim [{case_label}] - dod:{dod_status}, doi:{doi_status}"
        + (
            f", suicide window: {suicide_window} 1yr of {suicide_window_reference}"
            if suicide_window
            else ""
        )
        + f" -> decision: {decision}",
        f"RCD: {_format_date(dates['rcd_date'])}",
    ]
    if is_revival_case and dates.get("lapsed_due_date"):
        scenario_lines.append(f"Due date before revival (lapsed): {_format_date(dates['lapsed_due_date'])}")
    if is_revival_case:
        scenario_lines.append(f"Date of Revival: {_format_date(dates['revival_date'])}")
    scenario_lines.append(f"Date of last Premium Paid: {_format_date(dates['last_premium_paid_date'])}")
    scenario_lines.append(
        f"Due date{' after revival' if is_revival_case else ''}: {_format_date(dates['due_date'])}"
    )
    scenario_lines.append(f"Date of Death: {_format_date(dates['death_date'])}")
    scenario_lines.append(f"Date of Intimation: {_format_date(dates['intimation_date'])}")
    if dates.get("extra_premium_debit_date"):
        scenario_lines.append(
            f"Auto-pay premium debited after death, on: {_format_date(dates['extra_premium_debit_date'])}"
        )
    if decision == "Accept":
        scenario_lines.append(f"Date of Claim Acceptance: {_format_date(dates['acceptance_date'])}")

    scenario_text = "\n".join(scenario_lines)

    expected_result = {
        "Accept": "Death Claim should be Accepted. Claim amount should be correctly computed and payable benefits, premiums paid and outstanding amounts should reflect correctly against the policy.",
        "Reject": "Death Claim should be Rejected as per policy status/reason on event. No claim payout or premium refund should be processed.",
        "Repudiate": "Death Claim should be Repudiated as per policy status/reason on event/suicide clause. Premium refund should be processed only where applicable.",
    }[decision]

    row = {
        "TUID": f"TC_{MODULE_NAME.replace(' ', '')}_POST_{tuid_counter:03d}",
        "API_Operation": f"{subsection} - {case_label}",
        "Test Scenario": scenario_text,
        "Expected_Result": expected_result,
        "policyNumber": _random_policy_number(),
        "dateOfIntimation": _format_date(dates["intimation_date"]),
        "causeOfDeath": cause_of_death,
        "Date of Revival": _format_date(dates["revival_date"]) if dates.get("revival_date") else "",
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
        "Premium Refund": premium_refund,
        "Total Premiums Paid inclusive of Modal Loading, First Year Premium Discount, EMR Premium, Per Mille, NSAP loading & Rider premiums exclusive of Taxes till Date of Death (INR)": total_premiums_paid,
    }
    row.update(FIXED_VALUES)
    return row


# ============================================================================
# Main Test Case Generation
# ============================================================================

def generate_test_cases(epic_counts, selected_epics=None, epic_counts_rider=None,
                        selected_epics_rider=None, selected_header=None, **_kwargs):
    """Generate post-issuance Death Claim test cases for the saving plan.

    epic_counts keys are "<subsection>::<case_label>" for the specific dod/doi
    case checkboxes selected under a sub-section; each selected case contributes
    its configured positive count, generating one row per dod/doi pair in that
    case (so e.g. "Death in-force" with count=1 yields 4 rows: one per doi
    status). selected_epics lists the same composite keys.
    """
    selected_epics = selected_epics or list((epic_counts or {}).keys())

    if not selected_epics:
        return pd.DataFrame(columns=column_order)

    scenarios = []
    tuid_counter = 0

    for subsection in DEATH_CLAIM_SUBSECTIONS:
        catalogue = {label: (pairs, extra) for label, pairs, extra in get_case_catalogue(subsection)}
        for epic_key in selected_epics:
            if not epic_key.startswith(f"{subsection}::"):
                continue
            case_label = epic_key.split("::", 1)[1]
            if case_label not in catalogue:
                continue
            pairs, extra = catalogue[case_label]
            counts = (epic_counts or {}).get(epic_key, {})
            positive_count = int(counts.get("positive", 0) or 0)
            if positive_count <= 0:
                continue

            combo_idx = 0
            for _ in range(positive_count):
                for dod_status, doi_status in pairs:
                    tuid_counter += 1
                    row = _build_death_claim_row(
                        tuid_counter, subsection, case_label, dod_status, doi_status, extra,
                        combo_idx=combo_idx,
                    )
                    combo_idx += 1
                    scenarios.append(row)

    if not scenarios:
        return pd.DataFrame(columns=column_order)

    result_df = pd.DataFrame(scenarios)
    for col in column_order:
        if col not in result_df.columns:
            result_df[col] = ""

    return result_df[column_order]
