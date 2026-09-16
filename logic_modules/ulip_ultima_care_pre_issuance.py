# logic_module.py
import logging
import math
import random
import pandas as pd
from datetime import date

# Global declarations
MIN_ENTRY_AGE = 18
MAX_ENTRY_AGE = 45
PRODUCT_CODE = 'CMB15015101'
MIN_MATURITY_AGE = 23
MAX_MATURITY_AGE = 75
MAX_POLICY_TERM = 30
POLICY_TERM_STEP = 5
SUM_ASSURED_MULTIPLE_RANGE = (10, 20)

# Ultima Care is a ULIP + iTerm Care combo, so it carries both a base (ULIP)
# sum assured and an iTerm Care sum assured that is bounded by the base plan.
ITERM_CARE_SA_RANGE = (300000, 3500000)
TOTAL_SA_PREMIUM_MULTIPLE_CAP = 30
MIN_ANNUALIZED_PREMIUM = 50000

GENDER = ['Male', 'Female']
SMOKING = ['Smoker', 'Non Smoker']
# insuredLocation / policyHolderLocation are MH per the Ultima Care conditions.
policy_holder_location = ['MH']
insurer_location = ['MH']

EXISTING_CUSTOMER_DISCOUNT = [0, 2]

# Ultima Care is yearly only.
PAYMENT_FREQUENCY = [1]
PAYMENT_FREQUENCY_STR = {1: 'Annual', 2: 'Half-Yearly', 3: 'Quarterly', 4: 'Monthly', 5: 'Single'}
INVALID_PAYMENT_FREQUENCY = [2, 3, 4, 5]

# Fixed field values from the Ultima Care conditions.
CHANNEL_DEFAULT = "Other than Online"
SUB_CHANNEL_DEFAULT = "Other than Direct"
AUTO_DEBIT_DEFAULT = "N"
DISCOUNT_TYPE_DEFAULT = 0
OCCUPATION_DEFAULT = "SALARIED"
BONUS_ACCRUAL_DEFAULT = "FALSE"
INCOME_ACCRUAL_DEFAULT = "FALSE"
PAYOUT_FREQUENCY_DEFAULT = "Monthly"
PREMIUM_FREQUENCY_DEFAULT = "YEAR"
PAYMENT_FREQUENCY_DEFAULT = "Yearly"
EXISTING_POLICY_DEFAULT = "No"
EXISTING_POLICY_COUNT_DEFAULT = 0
STANDARD_AGE_PROOF_DEFAULT = "Yes"
AUTO_FUND_OPTIONS = ["TRUE", "FALSE"]
TENANT_ID = ["MANNAPURAM", "BANDHANBANK"]
# installmentPremium must be a minimum of 50K and in multiples of this step.
INSTALLMENT_PREMIUM_STEP = 1000

PORTFOLIO_TYPES = ["LIFESTYLE", "SELFMANAGED"]
PORTFOLIO_STRATEGY_MAP = {
    "LIFESTYLE": "Lifestyle Based Portfolio Strategy",
    "SELFMANAGED": "Self Managed Portfolio Strategy",
}
RISK_CLASS_DEFAULT = 0
TOTAL_FUND_ALLOCATED_DEFAULT = 100
FUND_STEP = 5
CURRENT_PORTFOLIO_TYPE = "LIFESTYLE"

FUND_COLUMNS = [
    "SecureFundPercentage",
    "DebtFundPercentage",
    "StableFundPercentage",
    "BlueChipFundPercentage",
    "AcceleratorFundPercentage",
    "OpportunityFundPercentage",
    "FlexiCapFundPercentage",
    "LiquidFundPercentage",
    "MidCapFundPercentage",
    "MulticapFundPercentage",
]

MODULE_NAME = "Ultima Care"
LIFECYCLE_STAGE = "pre issuance"
API_MODE_VALUE = "Base plan"

INCEPTION_DATE_VALUE = "2026-09-09"
EXECUTE_VALUE = "N"
MEDICAL_INDI = "Medical"
CHECKING_NOTE_CREATE_VALUE = "Create"
CHECKING_NOTE_UPDATE_VALUE = "Create , Update"

EXPECTED_RESULT_MAP = {
    'Positive': 'System should allow to generate Premium and all fields should match to the offline BI',
    'Negative': 'System should throw error message and should not generate Premium'
}

# Ultima Care is Limited Pay only.
PPT_NAME = [
    "Limited Pay (5 pay)",
    "Limited Pay (7 pay)",
    "Limited Pay (10 pay)",
    "Limited Pay (15 pay)",
    "Limited Pay (20 pay)",
]

EPIC_MAP = {
    'EntryAge': 'Check for Minimum - Maximum Entry Age',
    'MaturityAge': 'Check for Minimum - Maximum Maturity Age',
    'PolicyTerm': 'Check for Policy Term',
    'PremiumPayingTerm': 'Check for Premium Paying Term',
    'PaymentFrequency': 'Check for Premium payment frequencies',
    'FundAllocation': 'Check for fund percentage - selfmanaged',
    'FundAllocationLifestyle': 'Check for fund percentage - lifestyle',
    'PremiumValidation': 'Check for Annual Premium Validation',
    'ITermCareSumAssured': 'Check iTerm Care Sum Assured is within 3 lakh - 35 lakh',
    'ComboSumAssured': "Check combo iTerm Care Sum Assured is <= Ultima Plus (base) Sum Assured",
    'TotalSumAssured': 'Check Total Sum Assured (Ultima Plus + iTerm Care) is <= 30x Annualized Premium',
}

EPIC_MAP_RIDER = {}


def get_api_operation(key):
    """Return the human readable API operation name for an epic key."""
    return EPIC_MAP.get(key) or EPIC_MAP_RIDER.get(key) or key


POLICY_TERM_NAMES = {
    "Limited Pay (5 pay)": "LP5",
    "Limited Pay (7 pay)": "LP7",
    "Limited Pay (10 pay)": "LP10",
    "Limited Pay (15 pay)": "LP15",
    "Limited Pay (20 pay)": "LP20",
}

# SAM band -> minimum policy term / minimum PPT, per the Ultima Care conditions.
SAM_BAND_RULES = {
    "SAM 10-14": {
        "sam_range": (10, 14),
        "min_policy_term": 10,
        "min_ppt": 5,
        "allowed_policy_terms": [10, 15, 20, 25, 30],
    },
    "SAM 15-20": {
        "sam_range": (15, 20),
        "min_policy_term": 15,
        "min_ppt": 15,
        "allowed_policy_terms": [15, 20, 25, 30],
    },
}


def sam_band_for_multiple(sum_assured_multiple):
    for band, rule in SAM_BAND_RULES.items():
        low, high = rule["sam_range"]
        if low <= sum_assured_multiple <= high:
            return band
    return "SAM 15-20"


def premium_paying_term_message(ppt, min_ppt=None, max_ppt=None, ppt_limit=None):
    if ppt_limit is not None:
        return f"Premium Paying Term should be {ppt_limit} years for {ppt}."
    elif min_ppt is not None and max_ppt is not None:
        return f"Premium Paying Term chosen should be between {min_ppt} and {max_ppt} years for {ppt}."


def sam_bands_for_ppt(ppt_name):
    """SAM bands whose minimum PPT the given premium paying term satisfies."""
    charge_year = PPT_RULES[ppt_name]['charge_year'](MIN_ENTRY_AGE)
    bands = [
        band
        for band, rule in SAM_BAND_RULES.items()
        if charge_year >= rule["min_ppt"]
    ]
    return bands or [next(iter(SAM_BAND_RULES))]


def policy_term_message(ppt_name):
    """Policy term rule stated for a PPT, covering every SAM band it can use."""
    bands = sam_bands_for_ppt(ppt_name)
    min_term = min(SAM_BAND_RULES[b]["min_policy_term"] for b in bands)
    allowed = sorted(
        {t for b in bands for t in SAM_BAND_RULES[b]["allowed_policy_terms"]}
    )
    band_text = " / ".join(bands)
    return (
        f"Minimum Policy term should be {min_term} for {ppt_name} ({band_text}). "
        f"Allowed PT values: {','.join(str(t) for t in allowed)}"
    )


def min_ppt_message(ppt_name):
    """Premium paying term rule stated for a specific PPT."""
    charge_year = PPT_RULES[ppt_name]['charge_year'](MIN_ENTRY_AGE)
    bands = sam_bands_for_ppt(ppt_name)
    band_text = " / ".join(bands)
    return (
        f"Premium Paying Term should be {charge_year} years for {ppt_name}, "
        f"valid for {band_text}"
    )


def iterm_care_sum_assured_message(min_sum=None, max_sum=None):
    return (
        f"Sum assured for iTerm Care should be between {min_sum:,} to {max_sum:,}."
    )


def combo_sum_assured_message():
    return (
        "For combo, iTerm Care's Sum Assured should be less than or equal to "
        "Sum Assured of the base plan (ULIP)."
    )


def total_sum_assured_message():
    return (
        f"Total Sum Assured (Base Plan + iTerm Care) to be less than or equal to "
        f"{TOTAL_SA_PREMIUM_MULTIPLE_CAP}x base plan's Annualized Premium."
    )


def lifestyle_fund_allocation_message(coverage_year=None):
    """Lifestyle allocation rule stated for a policy term."""
    if coverage_year is None:
        return (
            "User allocates investment in lifestyle based portfolio strategy; "
            "allocation across Secure, Debt and Blue Chip Equity funds should "
            "follow the years to maturity"
        )
    secure, debt, blue_chip = lifestyle_allocation_for_term(coverage_year)
    return (
        f"For a policy term of {int(coverage_year)} years, the lifestyle based "
        f"portfolio strategy should allocate Secure Fund {secure:.2f}%, "
        f"Debt Fund {debt:.2f}% and Blue Chip Equity Fund {blue_chip:.2f}%"
    )


def premium_validation_message():
    return (
        f"Min annual/annualized premium for the base plan (ULIP/Savings) to be "
        f"INR {MIN_ANNUALIZED_PREMIUM:,}."
    )


SCENARIO_MAP = {
    'EntryAge': lambda ppt, min_entry_age, max_entry_age: f"The age of Life Assured should be between {min_entry_age} years to {max_entry_age} years",
    'PolicyTerm': policy_term_message,
    'MaturityAge': lambda ppt, min_maturity_age, max_maturity_age: f"The maturity age of Life Assured should be between {min_maturity_age} to {max_maturity_age} years",
    'PaymentFrequency': "To check for premium Frequency chosen should be yearly only (Other frequencies not allowed)",
    'PremiumPayingTerm': min_ppt_message,
    'FundAllocation': "User allocates investment in self-managed strategy",
    'FundAllocationLifestyle': lifestyle_fund_allocation_message,
    'PremiumValidation': premium_validation_message,
    'ITermCareSumAssured': iterm_care_sum_assured_message,
    'ComboSumAssured': combo_sum_assured_message,
    'TotalSumAssured': total_sum_assured_message,
}

# Column order follows the Ultima Care conditions sheet.
column_order = [
    "Execute",
    "TUID",
    "API_Name",
    "API_Mode",
    "API_Operation",
    "Checking_Note",
    "Test_Scenario",
    "Test_Type",
    "Expected_Result",
    "InceptionDate",
    "LABirthdate",
    "PHBirthdate",
    "LAAge",
    "PHAge",
    "LA Maturity Age",
    "PH Maturity Age",
    "Is the Life Assured same as Policyholder?",
    "relationToInsured",
    "relationToHolder",
    "LAGender",
    "PHGender",
    "SmokerStatus",
    "insuredLocation",
    "policyHolderLocation",
    "Channel",
    "Sub Channel",
    "portfolio",
    "PortfolioStrategy",
    "coverageYear",
    "chargeYear",
    "chargePeriod",
    "premiumPayOption",
    "paymentFreq",
    "autoDebit",
    "discountType",
    "LAOccupation",
    "PHOccupation",
    "bonusAccrual",
    "incomeAccrual",
    "payoutFrequency",
    "installmentPremium",
    "Annualized premium",
    "SAMultiple",
    "Base Sum Assured - iTerm Care (INR)",
    "Base Sum Assured - Ultima Plus(INR)",
    "existingPosPolicy",
    "existingPosSumAssured",
    "SecureFundPercentage",
    "DebtFundPercentage",
    "StableFundPercentage",
    "BlueChipFundPercentage",
    "AcceleratorFundPercentage",
    "OpportunityFundPercentage",
    "FlexiCapFundPercentage",
    "LiquidFundPercentage",
    "MidCapFundPercentage",
    "MulticapFundPercentage",
    "Total Fund Allocated",
    "ProductCode",
    "tenantId",
    "Premium Payment Option",
    "autoFundSwitchConsent",
    "Standard Age Proof",
    "BaseEMR_extraType",
    "Risk Class",
    "BaseEMR_extraArith",
    "BaseEMR_extraPara",
    "BasePerMille_extraType",
    "BasePerMille_extraArith",
    "BasePerMille_extraPara",
]

# Base (ULIP) sum assured band per PPT.
PPT_RULES_TT2 = {
    "Limited Pay (5 pay)": (5000000, 20000000),
    "Limited Pay (7 pay)": (5000000, 20000000),
    "Limited Pay (10 pay)": (5000000, 20000000),
    "Limited Pay (15 pay)": (5000000, 20000000),
    "Limited Pay (20 pay)": (5000000, 20000000),
}


def normalize_portfolio_type(portfolio_type):
    if not portfolio_type:
        return "LIFESTYLE"
    normalized = str(portfolio_type).upper()
    return normalized if normalized in PORTFOLIO_TYPES else "LIFESTYLE"


def set_current_portfolio_type(portfolio_type):
    global CURRENT_PORTFOLIO_TYPE
    CURRENT_PORTFOLIO_TYPE = normalize_portfolio_type(portfolio_type)


def ensure_thousand_multiple(value):
    if value is None:
        return None
    return int(round(float(value) / 1000.0) * 1000)


def pick_sum_assured_value(min_sa, max_sa):
    if min_sa is None or max_sa is None:
        return ensure_thousand_multiple(min_sa or 0)
    min_sa = int(math.ceil(float(min_sa) / 1000.0) * 1000)
    max_sa = int(math.floor(float(max_sa) / 1000.0) * 1000)
    if max_sa < min_sa:
        return min_sa
    return random.randrange(min_sa, max_sa + 1000, 1000)


def resolve_api_name(ppt_name):
    # Ultima Care is Limited Pay only.
    return "Limited Pay"


def normalize_age_value(age):
    if age is None:
        return age
    # An (years, months, days) age is already exact; keep only the completed
    # years, which is the age the system reads off the birthdate.
    if isinstance(age, AgeYMD):
        return age.years
    if age >= 1:
        return int(round(age))
    return int(math.floor(age))


class AgeYMD:
    """An exact entry age expressed as completed years, months and days.

    Whole-year ages are enough for most epics, but the entry age boundaries have
    to distinguish "45 years, 11 months, 30 days" (the last eligible day) from
    "46 years exactly" (the first ineligible one). Those differ by a single day
    of birthdate, so they cannot be expressed as a plain integer age.
    """

    __slots__ = ("years", "months", "days")

    def __init__(self, years, months=0, days=0):
        self.years = int(years)
        self.months = int(months)
        self.days = int(days)

    def __int__(self):
        return self.years

    def __index__(self):
        return self.years

    def __repr__(self):
        return f"AgeYMD({self.years}, {self.months}, {self.days})"


def subtract_months(reference_date, months):
    """Shift a date back by whole months, clamping to the month's last day."""
    month_index = (reference_date.year * 12 + (reference_date.month - 1)) - months
    year, month = divmod(month_index, 12)
    month += 1
    # Feb 30 does not exist, so clamp to the last valid day of the target month.
    if month == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)
    last_day = (next_month_start - pd.Timedelta(days=1)).day
    return date(year, month, min(reference_date.day, last_day))


def build_birthdate_for_age(age, reference_date=None):
    """Birthdate of someone who is exactly `age` old on the reference date."""
    ref_date = reference_date or date.today()
    if isinstance(age, AgeYMD):
        if age.months or age.days:
            # "N years, 11 months, 30 days" means the person turns N+1 tomorrow,
            # so anchor on the birthdate that lands the next birthday one day
            # after the reference date and step back the N+1 years from there.
            # Deriving it this way keeps the result strictly inside the year,
            # which naive month-then-day subtraction does not guarantee.
            next_birthday = (pd.Timestamp(ref_date) + pd.Timedelta(days=1)).date()
            birth = subtract_months(next_birthday, (age.years + 1) * 12)
            return birth.isoformat()
        birth = subtract_months(ref_date, age.years * 12)
        return birth.isoformat()
    return f"{ref_date.year - int(age)}-01-01"


def resolve_reference_date(value=None):
    """The inception date the ages are measured against."""
    try:
        return date.fromisoformat(str(value or INCEPTION_DATE_VALUE))
    except (TypeError, ValueError):
        return date.today()


def build_person_context(age, gender, reference_date=None):
    """Ultima Care entry age starts at 18, so LA and PH are always the same person."""
    ref_date = reference_date or resolve_reference_date()
    la_age = normalize_age_value(age)
    la_gender = gender
    ph_age = la_age
    ph_gender = la_gender
    # Pass the original age through so an exact (y, m, d) boundary keeps its
    # day-level precision in the birthdate.
    la_birthdate = build_birthdate_for_age(age, reference_date=ref_date)
    ph_birthdate = build_birthdate_for_age(age, reference_date=ref_date)
    la_gender_c = "M" if la_gender == "Male" else "F"
    ph_gender_c = "M" if ph_gender == "Male" else "F"
    return {
        "la_age": la_age,
        "ph_age": ph_age,
        "la_gender": la_gender,
        "ph_gender": ph_gender,
        "la_birthdate": la_birthdate,
        "ph_birthdate": ph_birthdate,
        "la_gender_c": la_gender_c,
        "ph_gender_c": ph_gender_c,
        "proposer_insured": "Same",
        # Per the Ultima Care conditions: relations are SELF and the
        # "same as Policyholder" flag is No.
        "relation_to_holder": "SELF",
        "relation_to_insured": "SELF",
        "same_as_ph": "No",
    }


# Lifestyle Based Portfolio Strategy allocates by years to maturity (the policy
# term). Terms of 12 and above sit entirely in Blue Chip Equity; from 11 years
# down the mix shifts progressively into Debt.
# (Secure Fund %, Debt Fund %, Blue Chip Equity Fund %)
# Only policy terms of 10, 15, 20, 25 and 30 are orderable, so the allocation
# has just two outcomes: PT 10 keeps 10% in Debt, and every longer term sits
# entirely in Blue Chip Equity.
LIFESTYLE_ALLOCATION_BY_TERM = {
    10: (0, 10, 90),
}
LIFESTYLE_LONG_TERM_ALLOCATION = (0, 0, 100)


def lifestyle_allocation_for_term(coverage_year):
    """The prescribed (Secure, Debt, Blue Chip) split for a policy term."""
    if coverage_year is None:
        return LIFESTYLE_LONG_TERM_ALLOCATION
    return LIFESTYLE_ALLOCATION_BY_TERM.get(
        int(coverage_year), LIFESTYLE_LONG_TERM_ALLOCATION
    )


def build_lifestyle_fund_allocation(coverage_year):
    """Fund columns filled in with the lifestyle split for this policy term."""
    secure, debt, blue_chip = lifestyle_allocation_for_term(coverage_year)
    allocation = {fund: 0 for fund in FUND_COLUMNS}
    allocation["SecureFundPercentage"] = secure
    allocation["DebtFundPercentage"] = debt
    allocation["BlueChipFundPercentage"] = blue_chip
    return allocation


# Totals that are not 100, mirroring the self-managed negative cases.
INVALID_FUND_TOTALS = [90, 95, 105, 110]


def build_invalid_lifestyle_fund_allocation(coverage_year, iteration_index):
    """A lifestyle allocation the strategy should reject.

    Two ways it can be wrong, alternating so both are covered. Odd iterations
    keep the total at 100 but split it differently from the mix prescribed for
    the policy term; even iterations use the prescribed split but scale it to a
    total other than 100, the same failure the self-managed epic exercises.

    Returns the fund columns and the total to report, which is not always 100.
    """
    prescribed = lifestyle_allocation_for_term(coverage_year)
    wrong_split_variants = [
        # The split prescribed for the *other* policy term, which is wrong for
        # this one: PT 10 gets the long-term 0/0/100, longer terms get 0/10/90.
        (0, 0, 100) if prescribed == (0, 10, 90) else (0, 10, 90),
        # Secure Fund is never used by the lifestyle strategy.
        (10, 0, 90),
        # Everything in Debt.
        (0, 100, 0),
        # Everything in Secure.
        (100, 0, 0),
        # Debt overweighted well past any prescribed split.
        (0, 50, 50),
    ]
    pair_index = iteration_index // 2
    if iteration_index % 2:
        secure_v, debt_v, blue_v = wrong_split_variants[
            pair_index % len(wrong_split_variants)
        ]
        total = 100
    else:
        # Right shape, wrong total: the surplus or shortfall lands on Blue Chip,
        # the fund the lifestyle strategy leans on, so only the total is off.
        total = INVALID_FUND_TOTALS[pair_index % len(INVALID_FUND_TOTALS)]
        secure_v, debt_v, blue_v = prescribed
        blue_v += total - 100
    allocation = {fund: 0 for fund in FUND_COLUMNS}
    allocation["SecureFundPercentage"] = secure_v
    allocation["DebtFundPercentage"] = debt_v
    allocation["BlueChipFundPercentage"] = blue_v
    return allocation, total


def build_fund_allocation(portfolio_type, total=None, coverage_year=None):
    """Spread `total` across the fund columns for the given portfolio type.

    Lifestyle follows the prescribed split for the policy term; self-managed
    splits the total across several funds, which is what the user is choosing
    when they self-manage.
    """
    portfolio_type = normalize_portfolio_type(portfolio_type)
    if total is None:
        total = TOTAL_FUND_ALLOCATED_DEFAULT
    allocation = {fund: 0 for fund in FUND_COLUMNS}
    if portfolio_type == "LIFESTYLE":
        if total == TOTAL_FUND_ALLOCATED_DEFAULT:
            return build_lifestyle_fund_allocation(coverage_year)
        # A deliberately invalid total still goes to the fund the lifestyle
        # strategy leans on, so the row differs only in the total.
        allocation["BlueChipFundPercentage"] = total
        return allocation
    # Self-managed means a real spread, so always use at least two funds.
    max_funds = min(len(FUND_COLUMNS), max(2, total // FUND_STEP))
    selected_count = random.randint(2, max_funds)
    selected_funds = random.sample(FUND_COLUMNS, selected_count)
    remaining = total
    for index, fund in enumerate(selected_funds):
        if index == len(selected_funds) - 1:
            allocation[fund] = remaining
            break
        max_units = (remaining - (len(selected_funds) - index - 1) * FUND_STEP) // FUND_STEP
        if max_units < 1:
            allocation[fund] = FUND_STEP
            remaining -= FUND_STEP
            continue
        units = random.randint(1, int(max_units))
        value = units * FUND_STEP
        allocation[fund] = value
        remaining -= value
    return allocation


def calculate_discounts(ppt_type):
    min_sa, max_sa = PPT_RULES_TT2[ppt_type]
    sum_assured = pick_sum_assured_value(min_sa, max_sa)
    online_discount = random.choice([15])
    existing_discount = random.choice(EXISTING_CUSTOMER_DISCOUNT)
    total_discount = online_discount + existing_discount

    discount_type = 20 if existing_discount and online_discount else 0
    digital_platform = "Digital Platform" if online_discount > 0 else "Non Digital Platform"
    existing_customer_discount_calc = "Yes" if existing_discount > 0 else "No"
    if online_discount:
        tenantID = random.choice(TENANT_ID)
    else:
        tenantID = "None"
    return {
        "Online Discount (%)": online_discount,
        "Existing Customer Discount (%)": existing_discount,
        "Total Discount": total_discount,
        "Discount Type": discount_type,
        "Digital Platform": digital_platform,
        "Existing Customer Discount Calculated": existing_customer_discount_calc,
        "tenantID": tenantID,
        "sumAssured": sum_assured,
    }


CURRENT_SUM_ASSURED_MULTIPLE = None


def pick_sum_assured_multiple():
    return random.randint(SUM_ASSURED_MULTIPLE_RANGE[0], SUM_ASSURED_MULTIPLE_RANGE[1])


def pick_sum_assured_multiple_for_ppt(ppt_name):
    """Pick a SAM multiple whose band the given PPT satisfies.

    Min PPT is 5 for SAM 10-14 and 15 for SAM 15-20, so a 5/7/10 pay policy can
    only sit in the SAM 10-14 band. Epics that choose a PPT freely use this so
    their positive rows stay consistent with the SAM band rules.
    """
    charge_year = PPT_RULES[ppt_name]['charge_year'](MIN_ENTRY_AGE)
    valid = [
        multiple
        for multiple in range(SUM_ASSURED_MULTIPLE_RANGE[0], SUM_ASSURED_MULTIPLE_RANGE[1] + 1)
        if charge_year >= min_ppt_for_multiple(multiple)
    ]
    return random.choice(valid) if valid else pick_sum_assured_multiple()


def policy_term_min_for_multiple(sum_assured_multiple):
    """Min PT is 10 for SAM 10-14 and 15 for SAM 15-20."""
    return SAM_BAND_RULES[sam_band_for_multiple(sum_assured_multiple)]["min_policy_term"]


def min_ppt_for_multiple(sum_assured_multiple):
    """Min PPT is 5 for SAM 10-14 and 15 for SAM 15-20."""
    return SAM_BAND_RULES[sam_band_for_multiple(sum_assured_multiple)]["min_ppt"]


def allowed_policy_terms(sum_assured_multiple, age=None):
    """Allowed PT values for the SAM band, capped by the max maturity age."""
    terms = SAM_BAND_RULES[sam_band_for_multiple(sum_assured_multiple)]["allowed_policy_terms"]
    if age is None:
        return list(terms)
    capped = [term for term in terms if age + term <= MAX_MATURITY_AGE]
    return capped or [terms[0]]


def round_up_to_step(value, step):
    return int(((value + step - 1) // step) * step)


def build_policy_term_range(age, sum_assured_multiple, min_term_override=None):
    min_term = policy_term_min_for_multiple(sum_assured_multiple)
    if min_term_override is not None:
        min_term = max(min_term, min_term_override)
    max_term = min(MAX_POLICY_TERM, MAX_MATURITY_AGE - age)
    return min_term, max_term


def pick_policy_term(min_term, max_term, sum_assured_multiple=None, age=None):
    if sum_assured_multiple is not None:
        valid_terms = [
            term
            for term in allowed_policy_terms(sum_assured_multiple, age)
            if min_term <= term <= max_term
        ]
        if valid_terms:
            return random.choice(valid_terms)
    min_term = round_up_to_step(min_term, POLICY_TERM_STEP)
    if max_term < min_term:
        return min_term
    valid_terms = list(range(min_term, int(max_term) + 1, POLICY_TERM_STEP))
    return random.choice(valid_terms) if valid_terms else min_term


PPT_RULES = {
    "Limited Pay (5 pay)": {
        "entry_age_range": (MIN_ENTRY_AGE, MAX_ENTRY_AGE),
        "charge_year": lambda age: 5,
        "coverage_year_range": lambda age, charge_year=None, sum_assured_multiple=None: build_policy_term_range(
            age,
            sum_assured_multiple,
            min_term_override=charge_year,
        ),
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (MIN_MATURITY_AGE, MAX_MATURITY_AGE),
    },
    "Limited Pay (7 pay)": {
        "entry_age_range": (MIN_ENTRY_AGE, MAX_ENTRY_AGE),
        "charge_year": lambda age: 7,
        "coverage_year_range": lambda age, charge_year=None, sum_assured_multiple=None: build_policy_term_range(
            age,
            sum_assured_multiple,
            min_term_override=charge_year,
        ),
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (MIN_MATURITY_AGE, MAX_MATURITY_AGE),
    },
    "Limited Pay (10 pay)": {
        "entry_age_range": (MIN_ENTRY_AGE, MAX_ENTRY_AGE),
        "charge_year": lambda age: 10,
        "coverage_year_range": lambda age, charge_year=None, sum_assured_multiple=None: build_policy_term_range(
            age,
            sum_assured_multiple,
            min_term_override=charge_year,
        ),
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (MIN_MATURITY_AGE, MAX_MATURITY_AGE),
    },
    "Limited Pay (15 pay)": {
        "entry_age_range": (MIN_ENTRY_AGE, MAX_ENTRY_AGE),
        "charge_year": lambda age: 15,
        "coverage_year_range": lambda age, charge_year=None, sum_assured_multiple=None: build_policy_term_range(
            age,
            sum_assured_multiple,
            min_term_override=charge_year,
        ),
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (MIN_MATURITY_AGE, MAX_MATURITY_AGE),
    },
    "Limited Pay (20 pay)": {
        "entry_age_range": (MIN_ENTRY_AGE, MAX_ENTRY_AGE),
        "charge_year": lambda age: 20,
        "coverage_year_range": lambda age, charge_year=None, sum_assured_multiple=None: build_policy_term_range(
            age,
            sum_assured_multiple,
            min_term_override=charge_year,
        ),
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (MIN_MATURITY_AGE, MAX_MATURITY_AGE),
    },
}


def get_years(ppt_name, age, PPT_RULES=PPT_RULES, sum_assured_multiple=None):
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule.get('charge_year_override', rule['charge_year'](age))

    if sum_assured_multiple is None:
        sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)

    coverage_min, coverage_max = rule['coverage_year_range'](
        age, charge_year=charge_year, sum_assured_multiple=sum_assured_multiple
    )
    min_maturity_age, max_maturity_age = rule['maturity_age_range']
    coverage_min = max(coverage_min, min_maturity_age - age)
    coverage_max = min(coverage_max, max_maturity_age - age)
    coverage_year = pick_policy_term(
        coverage_min, coverage_max, sum_assured_multiple=sum_assured_multiple, age=age
    )
    maturity_year = rule['maturity_year'](age, coverage_year)
    return charge_year, coverage_year, maturity_year


def get_out_of_range_coverage(
    ppt_name,
    age,
    PPT_RULES=PPT_RULES,
    sum_assured_multiple=None,
    iteration_index=0,
):
    """Return a policy term outside the allowed range (negative case).

    Even iterations fall below the SAM band's minimum term, odd iterations rise
    above the maximum policy term, each pair stepping one year further out. For
    SAM 10-14 that yields terms in the 5-9 and 31-35 regions.
    """
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule.get('charge_year_override', rule['charge_year'](age))
    if sum_assured_multiple is None:
        sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
    min_term = policy_term_min_for_multiple(sum_assured_multiple)
    step = iteration_index // 2
    if iteration_index % 2 == 0:
        coverage_year = max(1, min_term - 1 - step)
    else:
        coverage_year = MAX_POLICY_TERM + 1 + step
    maturity_year = rule['maturity_year'](age, coverage_year)
    return charge_year, coverage_year, maturity_year


def get_maturity_boundary_years(
    ppt_name, age, sum_assured_multiple=None, iteration_index=0
):
    """Valid policy term chosen to exercise the maturity age boundaries.

    Even iterations aim at the lowest reachable maturity age, odd iterations at
    the highest, each pair stepping one allowed policy term further inward, so
    both the minimum and maximum maturity boundaries are covered.
    """
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule.get('charge_year_override', rule['charge_year'](age))
    if sum_assured_multiple is None:
        sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
    min_maturity_age, max_maturity_age = rule['maturity_age_range']
    # Allowed terms that keep both the PPT and the maturity window satisfied.
    terms = sorted(
        term
        for term in allowed_policy_terms(sum_assured_multiple, age)
        if term >= charge_year
        and min_maturity_age <= age + term <= max_maturity_age
    )
    if not terms:
        return get_years(ppt_name, age, sum_assured_multiple=sum_assured_multiple)
    step = iteration_index // 2
    if iteration_index % 2 == 0:
        coverage_year = terms[min(step, len(terms) - 1)]
    else:
        coverage_year = terms[max(0, len(terms) - 1 - step)]
    return charge_year, coverage_year, rule['maturity_year'](age, coverage_year)


def get_out_of_range_maturity_year(
    ppt_name,
    age,
    PPT_RULES=PPT_RULES,
    sum_assured_multiple=None,
    iteration_index=0,
):
    """Return a policy term whose maturity age falls outside the allowed range.

    Even iterations push the maturity age above the maximum, odd iterations pull
    it below the minimum, so both boundaries are covered. Each pair steps one
    year further outside the range.
    """
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    step = iteration_index // 2
    if iteration_index % 2 == 0:
        coverage_year = int(MAX_MATURITY_AGE - age) + 1 + step
    else:
        # Below the minimum maturity age. That is only reachable when the entry
        # age leaves room for a policy term of at least one year, so pull the
        # age down if the caller's age is already too high.
        max_usable_age = MIN_MATURITY_AGE - 2 - step
        if age > max_usable_age:
            age = max(MIN_ENTRY_AGE, max_usable_age)
        coverage_year = max(1, int(MIN_MATURITY_AGE - age) - 1 - step)
    charge_year = rule.get('charge_year_override', rule['charge_year'](age))
    maturity_year = rule['maturity_year'](age, coverage_year)
    # The age is returned because the below-minimum case may have lowered it.
    return charge_year, coverage_year, maturity_year, age


def build_case_age(min_age, max_age, iteration_index):
    """Positive ages: boundary values first, then spread across the range.

    Index 0 and 1 are the exact minimum and maximum entry ages. Index 2 is the
    last eligible day before the maximum age is exceeded (max age, 11 months and
    30 days), which is the tightest valid boundary. Index 3 and 4 sit one step
    inside each boundary. From index 5 the values are spread evenly through the
    interior of the range so mid-range ages are covered too.
    """
    min_age = int(min_age)
    max_age = int(max_age)
    if max_age <= min_age:
        return min_age
    edges = [
        # Minimum entry age: exactly 18 years.
        AgeYMD(min_age, 0, 0),
        # Maximum entry age: exactly 45 years.
        AgeYMD(max_age, 0, 0),
        # Last valid day before turning max_age + 1.
        AgeYMD(max_age, 11, 30),
        min(min_age + 1, max_age),
        max(max_age - 1, min_age),
    ]
    if iteration_index < len(edges):
        return edges[iteration_index]
    # Walk the interior in evenly spaced steps, wrapping as the count grows.
    interior_min = min(min_age + 2, max_age)
    interior_max = max(max_age - 2, min_age)
    span = interior_max - interior_min
    if span <= 0:
        return interior_min
    offset = iteration_index - len(edges)
    steps = span + 1
    # Golden-ratio style stride keeps successive values spread out rather than
    # marching in from one end.
    stride = max(1, round(steps * 0.382)) or 1
    return interior_min + ((offset * stride) % steps)


def build_random_age(min_age, max_age):
    min_age = normalize_age_value(min_age)
    max_age = normalize_age_value(max_age)
    if min_age >= max_age:
        return min_age
    return random.randint(int(min_age), int(max_age))


def build_entry_age_negative(min_age, max_age, iteration_index, ppt_name):
    """Invalid ages, just-outside boundaries first.

    Index 0 is the last invalid day before the minimum entry age is reached (17
    years, 11 months, 30 days) and index 1 is the first age past the maximum (46
    years exactly) - the two tightest invalid boundaries. Index 2 and 3 are a
    whole year outside each boundary; later indexes move further out.
    """
    min_age = int(min_age)
    max_age = int(max_age)
    edges = [
        # Last invalid day before reaching the minimum entry age.
        AgeYMD(max(0, min_age - 1), 11, 30),
        # First age that exceeds the maximum entry age.
        AgeYMD(max_age + 1, 0, 0),
        max(0, min_age - 1),
        max_age + 2,
    ]
    if iteration_index < len(edges):
        return edges[iteration_index]
    offset = (iteration_index - len(edges)) // 2 + 3
    if iteration_index % 2 == 0:
        return max(0, min_age - offset)
    return max_age + offset


# Ultima Care allows only 5, 7, 10, 15 and 20 pay, so any other premium paying
# term is invalid. The values that sit *between* the allowed ones are the
# interesting negatives: they are inside the overall 5-20 span, so a rule that
# only range-checks the term would wrongly accept them.
VALID_PREMIUM_PAYING_TERMS = [5, 7, 10, 15, 20]
INVALID_PREMIUM_PAYING_TERMS = [6, 8, 9, 11, 14, 16, 19, 21]


def build_invalid_premium_paying_term(iteration_index, min_ppt=None):
    """An invalid premium paying term, in-between values first.

    The in-between values (6, 8, 9, 11, 14, 16, 19, 21) are cycled through first.
    Once they are exhausted the terms move below the SAM band's minimum, which is
    the other way a premium paying term can be invalid.
    """
    if iteration_index < len(INVALID_PREMIUM_PAYING_TERMS):
        return INVALID_PREMIUM_PAYING_TERMS[iteration_index]
    floor = min_ppt if min_ppt is not None else min(VALID_PREMIUM_PAYING_TERMS)
    step = iteration_index - len(INVALID_PREMIUM_PAYING_TERMS)
    return max(1, floor - 1 - step)


def build_case_sum_assured(min_sum, max_sum, iteration_index):
    """Valid sum assured values, boundary values first.

    Index 0 and 1 are the exact minimum and maximum (the edge cases), 2 and 3 sit
    one step inside each boundary, and later indexes are random within the band.
    """
    min_sum = ensure_thousand_multiple(min_sum)
    max_sum = ensure_thousand_multiple(max_sum)
    if max_sum <= min_sum:
        return min_sum
    edges = [
        min_sum,
        max_sum,
        min(min_sum + 1000, max_sum),
        max(max_sum - 1000, min_sum),
    ]
    if iteration_index < len(edges):
        return edges[iteration_index]
    return pick_sum_assured_value(min_sum, max_sum)


def build_out_of_band_sum_assured(min_sum, max_sum, iteration_index):
    """Invalid sum assured values, just-outside boundaries first."""
    min_sum = ensure_thousand_multiple(min_sum)
    max_sum = ensure_thousand_multiple(max_sum)
    edges = [
        max(0, min_sum - 1000),
        max_sum + 1000,
        max(0, min_sum - 2000),
        max_sum + 2000,
    ]
    if iteration_index < len(edges):
        return edges[iteration_index]
    step = ((iteration_index - len(edges)) // 2 + 3) * 1000
    if iteration_index % 2 == 0:
        return max(0, min_sum - step)
    return max_sum + step


def resolve_annualized_premium(discount_info, sum_assured_multiple):
    """Annualised premium as build_common_row derives it.

    The seed sum assured divided by the SA multiple, floored at the minimum
    annualised premium and rounded up to a whole installment step.
    """
    sum_assured = ensure_thousand_multiple(discount_info.get("sumAssured") or 0)
    premium = sum_assured / sum_assured_multiple if sum_assured_multiple else 0
    return max(
        MIN_ANNUALIZED_PREMIUM,
        round_up_to_step(int(premium), INSTALLMENT_PREMIUM_STEP),
    )


def build_iterm_care_sum_assured(base_sum_assured, annualized_premium):
    """iTerm Care SA: within its own band, <= base SA, and total <= 30x annualized premium."""
    min_sa, max_sa = ITERM_CARE_SA_RANGE
    upper = min(max_sa, base_sum_assured)
    total_cap = TOTAL_SA_PREMIUM_MULTIPLE_CAP * annualized_premium
    upper = min(upper, max(0, total_cap - base_sum_assured))
    if upper < min_sa:
        return min_sa
    return pick_sum_assured_value(min_sa, upper)


def resolve_ppt_case_counts(target_rule, epic_config, epic_count_source, ppt_name):
    ppt_pos_counts = epic_config.get('ppt_pos_counts', {})
    ppt_neg_counts = epic_config.get('ppt_neg_counts', {})
    per_ppt_mode = any(
        int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0
        for ppt in PPT_NAME
    )
    ppt_enabled = epic_config.get('ppt_enabled', {})
    if per_ppt_mode:
        return int(ppt_pos_counts.get(ppt_name, 0)), int(ppt_neg_counts.get(ppt_name, 0))
    if ppt_enabled.get(ppt_name, False):
        counts = epic_count_source.get(target_rule, {})
        return int(counts.get('positive', 0)), int(counts.get('negative', 0))
    return 0, 0


def apply_entry_age_overrides(epic_counts_local):
    entry_cfg = epic_counts_local.get('EntryAge', {}) or {}
    ppt_age_ranges = entry_cfg.get('ppt_age_ranges', {})
    for ppt_name, age_range in ppt_age_ranges.items():
        if ppt_name in PPT_RULES and age_range:
            PPT_RULES[ppt_name]['entry_age_range'] = tuple(age_range)


def apply_maturity_age_overrides(epic_counts_local):
    maturity_cfg = epic_counts_local.get('MaturityAge', {}) or {}
    ppt_maturity_ranges = maturity_cfg.get('ppt_maturity_ranges', {})
    for ppt_name, maturity_range in ppt_maturity_ranges.items():
        if ppt_name in PPT_RULES and maturity_range:
            PPT_RULES[ppt_name]['maturity_age_range'] = tuple(maturity_range)


def apply_premium_paying_term_overrides(epic_counts_local):
    ppt_cfg = epic_counts_local.get('PremiumPayingTerm', {}) or {}
    ppt_values = ppt_cfg.get('ppt_values', {})
    for ppt_name, value in ppt_values.items():
        if ppt_name in PPT_RULES and value:
            PPT_RULES[ppt_name]['charge_year_override'] = int(value)


def update_ppt_rules_with_epic_counts(epic_counts_local, epic_counts_rider_local=None):
    apply_entry_age_overrides(epic_counts_local)
    apply_maturity_age_overrides(epic_counts_local)
    apply_premium_paying_term_overrides(epic_counts_local)


def build_common_row(
    tuid_counter,
    module_name,
    api_operation,
    checking_note,
    ppt_name,
    scenario_text,
    test_type,
    expected_result,
    inception_date,
    policy_loc,
    insurer_loc,
    birth_year,
    age,
    gender,
    smoking,
    medical_indi,
    product_code,
    coverage_year,
    charge_year,
    maturity_year,
    payment_freq,
    discount_info,
    idx,
    sum_assured_multiple=None,
    portfolio_type=None,
    iterm_care_sum_assured=None,
    annualized_premium_override=None,
):
    """Return the common base row dict used across all Ultima Care scenarios."""
    if sum_assured_multiple is None:
        sum_assured_multiple = CURRENT_SUM_ASSURED_MULTIPLE
    if sum_assured_multiple is None:
        sum_assured_multiple = pick_sum_assured_multiple()

    # Keep the exact age for the person context so an (y, m, d) boundary keeps
    # its day-level precision in the birthdate; everything else uses the
    # completed years.
    exact_age = age
    age = normalize_age_value(age)
    person_ctx = build_person_context(exact_age, gender)
    sum_assured = ensure_thousand_multiple(discount_info.get("sumAssured") or 0)
    portfolio_type = normalize_portfolio_type(portfolio_type or CURRENT_PORTFOLIO_TYPE)
    portfolio_strategy = PORTFOLIO_STRATEGY_MAP.get(portfolio_type, "")
    fund_allocation = build_fund_allocation(portfolio_type, coverage_year=coverage_year)

    # Yearly only, so the installment premium equals the annualized premium.
    # It must be a minimum of 50,000 and in multiples of INSTALLMENT_PREMIUM_STEP,
    # except where an epic deliberately drives the premium below the minimum.
    if annualized_premium_override is not None:
        annualized_premium = annualized_premium_override
    else:
        annualized_premium = resolve_annualized_premium(
            discount_info, sum_assured_multiple
        )
    installment_premium = annualized_premium / payment_freq if payment_freq else 0
    annualized_premium = round(annualized_premium, 2)
    installment_premium = round(installment_premium, 2)

    if iterm_care_sum_assured is None:
        iterm_care_sum_assured = build_iterm_care_sum_assured(
            sum_assured, annualized_premium
        )

    # Ultima Plus (ULIP) base sum assured = annualised premium x SA multiple.
    ultima_plus_sum_assured = round(annualized_premium * sum_assured_multiple, 2)

    la_maturity_age = round(person_ctx["la_age"] + coverage_year, 2)
    ph_maturity_age = round(person_ctx["ph_age"] + coverage_year, 2)

    row = {
        'Execute': EXECUTE_VALUE,
        'TUID': f'TC_{module_name}_{tuid_counter:03d}',
        'API_Name': resolve_api_name(ppt_name),
        'API_Mode': API_MODE_VALUE,
        'API_Operation': api_operation,
        'Checking_Note': checking_note,
        'Test_Scenario': scenario_text,
        'Test_Type': test_type,
        'Expected_Result': expected_result,
        'InceptionDate': inception_date,
        'LABirthdate': person_ctx["la_birthdate"],
        'PHBirthdate': person_ctx["ph_birthdate"],
        'LAAge': person_ctx["la_age"],
        'PHAge': person_ctx["ph_age"],
        'LA Maturity Age': la_maturity_age,
        'PH Maturity Age': ph_maturity_age,
        'Is the Life Assured same as Policyholder?': person_ctx["same_as_ph"],
        'relationToInsured': person_ctx["relation_to_insured"],
        'relationToHolder': person_ctx["relation_to_holder"],
        'LAGender': person_ctx["la_gender"],
        'PHGender': person_ctx["ph_gender"],
        'SmokerStatus': smoking,
        'insuredLocation': insurer_loc,
        'policyHolderLocation': policy_loc,
        'Channel': CHANNEL_DEFAULT,
        'Sub Channel': SUB_CHANNEL_DEFAULT,
        'portfolio': portfolio_type,
        'PortfolioStrategy': portfolio_strategy,
        'coverageYear': coverage_year,
        'chargeYear': charge_year,
        'chargePeriod': 2,
        'premiumPayOption': PREMIUM_FREQUENCY_DEFAULT,
        'paymentFreq': PAYMENT_FREQUENCY_STR.get(payment_freq, ''),
        'autoDebit': AUTO_DEBIT_DEFAULT,
        'discountType': DISCOUNT_TYPE_DEFAULT,
        'LAOccupation': OCCUPATION_DEFAULT,
        'PHOccupation': OCCUPATION_DEFAULT,
        'bonusAccrual': BONUS_ACCRUAL_DEFAULT,
        'incomeAccrual': INCOME_ACCRUAL_DEFAULT,
        'payoutFrequency': PAYOUT_FREQUENCY_DEFAULT,
        'installmentPremium': installment_premium,
        'Annualized premium': annualized_premium,
        'SAMultiple': sum_assured_multiple,
        # iTerm Care SA: between 3 lakh and 35 lakh, and <= the Ultima Plus SA.
        'Base Sum Assured - iTerm Care (INR)': iterm_care_sum_assured,
        'Base Sum Assured - Ultima Plus(INR)': ultima_plus_sum_assured,
        'existingPosPolicy': EXISTING_POLICY_DEFAULT,
        'existingPosSumAssured': EXISTING_POLICY_COUNT_DEFAULT,
        'Total Fund Allocated': TOTAL_FUND_ALLOCATED_DEFAULT,
        'ProductCode': product_code,
        'tenantId': discount_info.get('tenantID', ''),
        'Premium Payment Option': PREMIUM_FREQUENCY_DEFAULT,
        'autoFundSwitchConsent': random.choice(AUTO_FUND_OPTIONS),
        'Standard Age Proof': STANDARD_AGE_PROOF_DEFAULT,
        'Risk Class': RISK_CLASS_DEFAULT,
    }
    row.update(fund_allocation)
    return row


def generate_test_cases(
    epic_counts,
    selected_epics=None,
    epic_counts_rider=None,
    selected_epics_rider=None,
    portfolio_type=None,
    skip_testbed_load=False,
):
    if selected_epics is None:
        selected_epics = []
    if selected_epics_rider is None:
        selected_epics_rider = []
    if epic_counts_rider is None:
        epic_counts_rider = {}

    scenarios = []
    tuid_counter = 0
    current_year = date.today().year

    set_current_portfolio_type(portfolio_type)

    try:
        update_ppt_rules_with_epic_counts(epic_counts or {}, epic_counts_rider or {})
    except Exception:
        logging.exception('Failed to apply PPT_RULES overrides from epic_counts')

    def make_emr_fields():
        """Condition onloading fields, mirroring the saving plan pre-issuance module."""
        return {
            'BaseEMR_extraType': 'EMR' if skip_testbed_load else 'EMR',
            'BaseEMR_extraArith': 0 if skip_testbed_load else 8,
            'BaseEMR_extraPara': 0 if skip_testbed_load else random.choice([round(i * 0.25, 2) for i in range(1, 17)]),
            'BasePerMille_extraType': 'PER_MILE' if skip_testbed_load else 'PER_MILE',
            'BasePerMille_extraArith': 0 if skip_testbed_load else 1,
            'BasePerMille_extraPara': 0 if skip_testbed_load else random.choice([1, 2]),
        }

    common_data = {
        'PerMile': 0,
        'EMRPeriod': 0,
        'Standard Age Proof': 'Yes',
        'Difference_Value': '',
    }

    def append_scenario(common_row):
        scenarios.append({**common_data, **make_emr_fields(), **common_row})

    # --- EPIC: EntryAge ---
    # The age of Life Assured should be between 18 years to 45 years.
    if 'EntryAge' in selected_epics:
        target_rule = 'EntryAge'
        entry_age_config = epic_counts.get(target_rule, {})
        ppt_age_ranges = entry_age_config.get('ppt_age_ranges', {})

        for ppt_name in PPT_NAME:
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, rule['entry_age_range'])
            pos_count, neg_count = resolve_ppt_case_counts(
                target_rule, entry_age_config, epic_counts, ppt_name
            )

            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
                charge_year, coverage_year, maturity_year = get_years(
                    ppt_name, positive_age, sum_assured_multiple=sum_assured_multiple
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_entry_age, max_entry_age),
                    'Positive',
                    EXPECTED_RESULT_MAP['Positive'],
                    INCEPTION_DATE_VALUE,
                    random.choice(policy_holder_location),
                    random.choice(insurer_location),
                    current_year - int(positive_age),
                    positive_age,
                    random.choice(GENDER),
                    random.choice(SMOKING),
                    MEDICAL_INDI,
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    sum_assured_multiple=sum_assured_multiple,
                )
                append_scenario(common_row)

            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                negative_age = build_entry_age_negative(
                    min_entry_age, max_entry_age, i, ppt_name
                )
                sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
                charge_year, coverage_year, maturity_year = get_years(
                    ppt_name, negative_age, sum_assured_multiple=sum_assured_multiple
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_entry_age, max_entry_age),
                    'Negative',
                    EXPECTED_RESULT_MAP['Negative'],
                    INCEPTION_DATE_VALUE,
                    random.choice(policy_holder_location),
                    random.choice(insurer_location),
                    current_year - int(negative_age),
                    negative_age,
                    random.choice(GENDER),
                    random.choice(SMOKING),
                    MEDICAL_INDI,
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    sum_assured_multiple=sum_assured_multiple,
                )
                append_scenario(common_row)

    # --- EPIC: MaturityAge ---
    # The maturity age of Life Assured should be between 23 to 75 years.
    if 'MaturityAge' in selected_epics:
        target_rule = 'MaturityAge'
        maturity_age_config = epic_counts.get(target_rule, {})
        ppt_maturity_ranges = maturity_age_config.get('ppt_maturity_ranges', {})

        for ppt_name in PPT_NAME:
            rule = PPT_RULES.get(ppt_name)
            min_maturity_age, max_maturity_age = ppt_maturity_ranges.get(
                ppt_name, rule['maturity_age_range']
            )
            pos_count, neg_count = resolve_ppt_case_counts(
                target_rule, maturity_age_config, epic_counts, ppt_name
            )
            min_entry_age, max_entry_age = rule['entry_age_range']

            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
                charge_year, coverage_year, maturity_year = get_maturity_boundary_years(
                    ppt_name,
                    positive_age,
                    sum_assured_multiple=sum_assured_multiple,
                    iteration_index=i,
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_maturity_age, max_maturity_age),
                    'Positive',
                    EXPECTED_RESULT_MAP['Positive'],
                    INCEPTION_DATE_VALUE,
                    random.choice(policy_holder_location),
                    random.choice(insurer_location),
                    current_year - int(positive_age),
                    positive_age,
                    random.choice(GENDER),
                    random.choice(SMOKING),
                    MEDICAL_INDI,
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    sum_assured_multiple=sum_assured_multiple,
                )
                append_scenario(common_row)

            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
                (
                    charge_year,
                    coverage_year,
                    maturity_year,
                    positive_age,
                ) = get_out_of_range_maturity_year(
                    ppt_name,
                    positive_age,
                    sum_assured_multiple=sum_assured_multiple,
                    iteration_index=i,
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_maturity_age, max_maturity_age),
                    'Negative',
                    EXPECTED_RESULT_MAP['Negative'],
                    INCEPTION_DATE_VALUE,
                    random.choice(policy_holder_location),
                    random.choice(insurer_location),
                    current_year - int(positive_age),
                    positive_age,
                    random.choice(GENDER),
                    random.choice(SMOKING),
                    MEDICAL_INDI,
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    sum_assured_multiple=sum_assured_multiple,
                )
                append_scenario(common_row)

    # --- EPIC: PolicyTerm ---
    # Cases are generated per PPT (5/7/10/15/20 pay); the scenario states the
    # policy term rule for that PPT's SAM band(s).
    # Min PT 10 for SAM 10-14 (allowed 10,15,20,25,30);
    # Min PT 15 for SAM 15-20 (allowed 15,20,25,30).
    if 'PolicyTerm' in selected_epics:
        target_rule = 'PolicyTerm'
        policy_term_config = epic_counts.get(target_rule, {})

        for ppt_name in PPT_NAME:
            pos_count, neg_count = resolve_ppt_case_counts(
                target_rule, policy_term_config, epic_counts, ppt_name
            )

            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
                charge_year, coverage_year, maturity_year = get_years(
                    ppt_name, positive_age, sum_assured_multiple=sum_assured_multiple
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name),
                    'Positive',
                    EXPECTED_RESULT_MAP['Positive'],
                    INCEPTION_DATE_VALUE,
                    random.choice(policy_holder_location),
                    random.choice(insurer_location),
                    current_year - int(positive_age),
                    positive_age,
                    random.choice(GENDER),
                    random.choice(SMOKING),
                    MEDICAL_INDI,
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    sum_assured_multiple=sum_assured_multiple,
                )
                append_scenario(common_row)

            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
                charge_year, coverage_year, maturity_year = get_out_of_range_coverage(
                    ppt_name,
                    positive_age,
                    sum_assured_multiple=sum_assured_multiple,
                    iteration_index=i,
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name),
                    'Negative',
                    EXPECTED_RESULT_MAP['Negative'],
                    INCEPTION_DATE_VALUE,
                    random.choice(policy_holder_location),
                    random.choice(insurer_location),
                    current_year - int(positive_age),
                    positive_age,
                    random.choice(GENDER),
                    random.choice(SMOKING),
                    MEDICAL_INDI,
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    sum_assured_multiple=sum_assured_multiple,
                )
                append_scenario(common_row)

    # --- EPIC: PremiumPayingTerm ---
    # Cases are generated per PPT (5/7/10/15/20 pay); the scenario states the
    # premium paying term for that PPT.
    # Min PPT 5 for SAM 10-14; Min PPT 15 for SAM 15-20.
    if 'PremiumPayingTerm' in selected_epics:
        target_rule = 'PremiumPayingTerm'
        ppt_config = epic_counts.get(target_rule, {})

        for ppt_name in PPT_NAME:
            pos_count, neg_count = resolve_ppt_case_counts(
                target_rule, ppt_config, epic_counts, ppt_name
            )
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
                charge_year, coverage_year, maturity_year = get_years(
                    ppt_name, positive_age, sum_assured_multiple=sum_assured_multiple
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name),
                    'Positive',
                    EXPECTED_RESULT_MAP['Positive'],
                    INCEPTION_DATE_VALUE,
                    random.choice(policy_holder_location),
                    random.choice(insurer_location),
                    current_year - int(positive_age),
                    positive_age,
                    random.choice(GENDER),
                    random.choice(SMOKING),
                    MEDICAL_INDI,
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    sum_assured_multiple=sum_assured_multiple,
                )
                append_scenario(common_row)

            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
                charge_year, coverage_year, maturity_year = get_years(
                    ppt_name, positive_age, sum_assured_multiple=sum_assured_multiple
                )
                # The negative condition is a premium paying term that Ultima
                # Care does not offer: first the values between the allowed
                # 5/7/10/15/20 pay terms, then terms below the minimum allowed
                # for this row's own SA multiple.
                row_min_ppt = min_ppt_for_multiple(sum_assured_multiple)
                charge_year = build_invalid_premium_paying_term(i, row_min_ppt)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name),
                    'Negative',
                    EXPECTED_RESULT_MAP['Negative'],
                    INCEPTION_DATE_VALUE,
                    random.choice(policy_holder_location),
                    random.choice(insurer_location),
                    current_year - int(positive_age),
                    positive_age,
                    random.choice(GENDER),
                    random.choice(SMOKING),
                    MEDICAL_INDI,
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    sum_assured_multiple=sum_assured_multiple,
                )
                append_scenario(common_row)

    # --- EPIC: PaymentFrequency ---
    # Premium frequency chosen should be yearly only.
    if 'PaymentFrequency' in selected_epics:
        target_rule = 'PaymentFrequency'
        counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})

        for i in range(int(counts.get('positive', 0))):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                SCENARIO_MAP[target_rule],
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                1,  # Yearly
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
            )
            append_scenario(common_row)

        for i in range(int(counts.get('negative', 0))):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            payment_freq = INVALID_PAYMENT_FREQUENCY[i % len(INVALID_PAYMENT_FREQUENCY)]
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                SCENARIO_MAP[target_rule],
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
            )
            append_scenario(common_row)

    # --- EPIC: FundAllocationLifestyle ---
    # Lifestyle Based Portfolio Strategy allocates by years to maturity. Only
    # policy terms of 10/15/20/25/30 are orderable, so PT 10 puts 10% in Debt
    # and 90% in Blue Chip Equity, and every longer term is fully Blue Chip.
    if 'FundAllocationLifestyle' in selected_epics:
        target_rule = 'FundAllocationLifestyle'
        counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})

        for i in range(int(counts.get('positive', 0))):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                SCENARIO_MAP[target_rule](coverage_year),
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                portfolio_type="LIFESTYLE",
            )
            append_scenario(common_row)

        for i in range(int(counts.get('negative', 0))):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                SCENARIO_MAP[target_rule](coverage_year),
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                portfolio_type="LIFESTYLE",
            )
            # The negative condition is either a split that does not match the
            # one prescribed for this policy term, or a total other than 100.
            invalid_allocation, invalid_total = build_invalid_lifestyle_fund_allocation(
                coverage_year, i
            )
            common_row.update(invalid_allocation)
            common_row["Total Fund Allocated"] = invalid_total
            append_scenario(common_row)

    # --- EPIC: FundAllocation ---
    # User allocates investment in self-managed strategy; fund percentage totals 100.
    if 'FundAllocation' in selected_epics:
        target_rule = 'FundAllocation'
        counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})

        for i in range(int(counts.get('positive', 0))):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                SCENARIO_MAP[target_rule],
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                portfolio_type="SELFMANAGED",
            )
            append_scenario(common_row)

        for i in range(int(counts.get('negative', 0))):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                SCENARIO_MAP[target_rule],
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                portfolio_type="SELFMANAGED",
            )
            # Fund allocation that does not add up to 100 is the negative
            # condition. Self-managed spreads across several funds, so the
            # invalid total is distributed the same way a valid one would be.
            invalid_total = random.choice([90, 95, 105, 110])
            common_row.update(build_fund_allocation("SELFMANAGED", invalid_total))
            common_row["Total Fund Allocated"] = invalid_total
            append_scenario(common_row)

    # --- EPIC: PremiumValidation ---
    # Min annual/annualized premium for the base plan to be INR 50,000.
    if 'PremiumValidation' in selected_epics:
        target_rule = 'PremiumValidation'
        premium_config = epic_counts.get(target_rule, {})
        min_premium = int(premium_config.get('min_val', MIN_ANNUALIZED_PREMIUM))
        pos_count = int(premium_config.get('positive', 0))
        neg_count = int(premium_config.get('negative', 0))

        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_case_age(min_entry_age, max_entry_age, i)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            # At or above the minimum annualized premium.
            annualized_premium = min_premium + (i * 5000)
            discount_info = {
                **discount_info,
                "sumAssured": ensure_thousand_multiple(annualized_premium * sum_assured_multiple),
            }
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                SCENARIO_MAP[target_rule](),
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                annualized_premium_override=annualized_premium,
            )
            append_scenario(common_row)

        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_case_age(min_entry_age, max_entry_age, i)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            # Just below the minimum annualized premium.
            annualized_premium = max(0, min_premium - 1000 * (i + 1))
            discount_info = {
                **discount_info,
                "sumAssured": ensure_thousand_multiple(annualized_premium * sum_assured_multiple),
            }
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                SCENARIO_MAP[target_rule](),
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                annualized_premium_override=annualized_premium,
            )
            append_scenario(common_row)

    # --- EPIC: ITermCareSumAssured ---
    # Sum assured for iTerm Care should be between 3,00,000-35,00,000.
    if 'ITermCareSumAssured' in selected_epics:
        target_rule = 'ITermCareSumAssured'
        iterm_config = epic_counts.get(target_rule, {})
        min_sum = int(iterm_config.get('min_val', ITERM_CARE_SA_RANGE[0]))
        max_sum = int(iterm_config.get('max_val', ITERM_CARE_SA_RANGE[1]))
        pos_count = int(iterm_config.get('positive', 0))
        neg_count = int(iterm_config.get('negative', 0))
        message = SCENARIO_MAP[target_rule](min_sum=min_sum, max_sum=max_sum)

        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_case_age(min_entry_age, max_entry_age, i)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                message,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                iterm_care_sum_assured=build_case_sum_assured(min_sum, max_sum, i),
            )
            append_scenario(common_row)

        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_case_age(min_entry_age, max_entry_age, i)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            # Just outside each boundary first, then further outside the band.
            neg_iterm_sa = build_out_of_band_sum_assured(min_sum, max_sum, i)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                message,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                iterm_care_sum_assured=neg_iterm_sa,
            )
            append_scenario(common_row)

    # --- EPIC: ComboSumAssured ---
    # iTerm Care's SA should be <= SA of the base plan (ULIP).
    if 'ComboSumAssured' in selected_epics:
        target_rule = 'ComboSumAssured'
        combo_config = epic_counts.get(target_rule, {})
        pos_count = int(combo_config.get('positive', 0))
        neg_count = int(combo_config.get('negative', 0))
        message = SCENARIO_MAP[target_rule]()

        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_case_age(min_entry_age, max_entry_age, i)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            ultima_plus_sa = resolve_annualized_premium(
                discount_info, sum_assured_multiple
            ) * sum_assured_multiple
            # iTerm Care SA at or below the Ultima Plus SA. The boundary case is
            # exactly equal to it, capped by the iTerm Care band.
            iterm_sa = build_case_sum_assured(
                ITERM_CARE_SA_RANGE[0], min(ITERM_CARE_SA_RANGE[1], ultima_plus_sa), i
            )
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                message,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                iterm_care_sum_assured=iterm_sa,
            )
            append_scenario(common_row)

        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_case_age(min_entry_age, max_entry_age, i)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            # The Ultima Plus SA is driven to its floor (the minimum annualised
            # premium x SA multiple) and the iTerm Care SA is set just above it,
            # breaching the combo rule.
            discount_info = {**discount_info, "sumAssured": 0}
            ultima_plus_sa = MIN_ANNUALIZED_PREMIUM * sum_assured_multiple
            iterm_sa = ensure_thousand_multiple(ultima_plus_sa + 1000)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                message,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                iterm_care_sum_assured=iterm_sa,
            )
            append_scenario(common_row)

    # --- EPIC: TotalSumAssured ---
    # Total SA (Base Plan + iTerm Care) <= 30x base plan's Annualized Premium.
    if 'TotalSumAssured' in selected_epics:
        target_rule = 'TotalSumAssured'
        total_config = epic_counts.get(target_rule, {})
        multiple_cap = int(total_config.get('max_multiple', TOTAL_SA_PREMIUM_MULTIPLE_CAP))
        pos_count = int(total_config.get('positive', 0))
        neg_count = int(total_config.get('negative', 0))
        message = SCENARIO_MAP[target_rule]()

        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_case_age(min_entry_age, max_entry_age, i)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            annualized_premium = resolve_annualized_premium(
                discount_info, sum_assured_multiple
            )
            ultima_plus_sa = annualized_premium * sum_assured_multiple
            headroom = max(0, (multiple_cap * annualized_premium) - ultima_plus_sa)
            # The boundary case puts the total exactly on the 30x premium cap.
            iterm_sa = build_case_sum_assured(
                ITERM_CARE_SA_RANGE[0],
                min(ITERM_CARE_SA_RANGE[1], ultima_plus_sa, headroom),
                i,
            )
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                message,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                iterm_care_sum_assured=iterm_sa,
            )
            append_scenario(common_row)

        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_case_age(min_entry_age, max_entry_age, i)
            sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
            charge_year, coverage_year, maturity_year = get_years(
                ppt_name, age, sum_assured_multiple=sum_assured_multiple
            )
            discount_info = calculate_discounts(ppt_name)
            # Mirror how build_common_row derives the premium and the Ultima Plus
            # SA, so the breach is measured against the values actually reported.
            annualized_premium = resolve_annualized_premium(
                discount_info, sum_assured_multiple
            )
            ultima_plus_sa = annualized_premium * sum_assured_multiple
            # Total SA is pushed just past the 30x annualized premium cap.
            iterm_sa = ensure_thousand_multiple(
                max(0, (multiple_cap * annualized_premium) - ultima_plus_sa) + 1000
            )
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                message,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                MEDICAL_INDI,
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                random.choice(PAYMENT_FREQUENCY),
                discount_info,
                idx,
                sum_assured_multiple=sum_assured_multiple,
                iterm_care_sum_assured=iterm_sa,
            )
            append_scenario(common_row)

    # Convert to DataFrame
    df = pd.DataFrame(scenarios)
    if not df.empty:
        df = df.reindex(columns=column_order)

    return df
