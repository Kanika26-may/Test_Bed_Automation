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
RISK_CLASS_DEFAULT = "Standard"
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
    'EntryAge': 'Check Min Entry Age',
    'MaturityAge': 'Check Max Maturity Age is 75 Years',
    'PolicyTerm': 'Allowed PT values',
    'PremiumPayingTerm': 'Check for Premium Paying Term',
    'PaymentFrequency': 'Premium payment frequencies',
    'FundAllocation': 'Fund Percentage',
    'PremiumValidation': 'Check for Premium Validation',
    'ITermCareSumAssured': 'Check for iTerm Care Sum Assured',
    'ComboSumAssured': 'Check for combo Sum Assured validation',
    'TotalSumAssured': 'Check for Total Sum Assured validation',
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


def policy_term_message(sam_band):
    rule = SAM_BAND_RULES[sam_band]
    allowed = ",".join(str(term) for term in rule["allowed_policy_terms"])
    return (
        f"Minimum Policy term should be {rule['min_policy_term']} for {sam_band}. "
        f"Allowed PT values: {allowed}"
    )


def min_ppt_message(sam_band):
    rule = SAM_BAND_RULES[sam_band]
    return f"Minimum PPT should be {rule['min_ppt']} for {sam_band}"


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
    if age >= 1:
        return int(round(age))
    return int(math.floor(age))


def build_birthdate_for_age(age, reference_date=None):
    ref_date = reference_date or date.today()
    return f"{ref_date.year - int(age)}-01-01"


def build_person_context(age, gender, reference_date=None):
    """Ultima Care entry age starts at 18, so LA and PH are always the same person."""
    ref_date = reference_date or date.today()
    la_age = normalize_age_value(age)
    la_gender = gender
    ph_age = la_age
    ph_gender = la_gender
    la_birthdate = build_birthdate_for_age(la_age, reference_date=ref_date)
    ph_birthdate = build_birthdate_for_age(ph_age, reference_date=ref_date)
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


def build_fund_allocation(portfolio_type):
    portfolio_type = normalize_portfolio_type(portfolio_type)
    allocation = {fund: 0 for fund in FUND_COLUMNS}
    if portfolio_type == "LIFESTYLE":
        allocation["BlueChipFundPercentage"] = TOTAL_FUND_ALLOCATED_DEFAULT
        return allocation
    selected_count = random.randint(1, len(FUND_COLUMNS))
    selected_funds = random.sample(FUND_COLUMNS, selected_count)
    remaining = TOTAL_FUND_ALLOCATED_DEFAULT
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


def ppt_names_for_sam_band(sam_band):
    """PPTs whose premium paying term satisfies the band's minimum PPT."""
    min_ppt = SAM_BAND_RULES[sam_band]["min_ppt"]
    valid = [
        ppt for ppt in PPT_NAME
        if PPT_RULES[ppt]['charge_year'](MIN_ENTRY_AGE) >= min_ppt
    ]
    return valid or list(PPT_NAME)


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


def get_out_of_range_coverage(ppt_name, age, PPT_RULES=PPT_RULES, sum_assured_multiple=None):
    """Return a policy term below the SAM band's minimum (negative case)."""
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule.get('charge_year_override', rule['charge_year'](age))
    if sum_assured_multiple is None:
        sum_assured_multiple = pick_sum_assured_multiple_for_ppt(ppt_name)
    min_term = policy_term_min_for_multiple(sum_assured_multiple)
    coverage_year = max(1, min_term - 1)
    maturity_year = rule['maturity_year'](age, coverage_year)
    return charge_year, coverage_year, maturity_year


def get_out_of_range_maturity_year(ppt_name, age, PPT_RULES=PPT_RULES, sum_assured_multiple=None):
    """Return a policy term that pushes maturity age beyond the allowed maximum."""
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule.get('charge_year_override', rule['charge_year'](age))
    coverage_year = int(MAX_MATURITY_AGE - age) + 1
    maturity_year = rule['maturity_year'](age, coverage_year)
    return charge_year, coverage_year, maturity_year


def build_case_age(min_age, max_age, iteration_index):
    if iteration_index % 2 == 0:
        return max(min_age, min(max_age - iteration_index, max_age))
    return min(max_age, min_age + iteration_index)


def build_random_age(min_age, max_age):
    min_age = normalize_age_value(min_age)
    max_age = normalize_age_value(max_age)
    if min_age >= max_age:
        return min_age
    return random.randint(int(min_age), int(max_age))


def build_entry_age_negative(min_age, max_age, iteration_index, ppt_name):
    """Below minimum on even iterations, above maximum on odd ones."""
    if iteration_index % 2 == 0:
        return max(0, int(min_age) - 1)
    return int(max_age) + 1


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


def resolve_sam_band_counts(epic_config, sam_band):
    """Counts for a SAM band.

    Supports the SAM-band shape ({'SAM 10-14': {'positive': n, 'negative': n}})
    and the shared UI's per-PPT shape, where the band inherits the epic-level
    counts and each band is generated once per enabled PPT.
    """
    band_config = epic_config.get(sam_band)
    if isinstance(band_config, dict) and (
        'positive' in band_config or 'negative' in band_config
    ):
        return int(band_config.get('positive', 0)), int(band_config.get('negative', 0))

    ppt_pos_counts = epic_config.get('ppt_pos_counts', {})
    ppt_neg_counts = epic_config.get('ppt_neg_counts', {})
    ppt_enabled = epic_config.get('ppt_enabled', {})
    per_ppt_mode = any(
        int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0
        for ppt in PPT_NAME
    )
    if per_ppt_mode:
        pos = sum(int(ppt_pos_counts.get(ppt, 0)) for ppt in PPT_NAME if ppt_enabled.get(ppt, True))
        neg = sum(int(ppt_neg_counts.get(ppt, 0)) for ppt in PPT_NAME if ppt_enabled.get(ppt, True))
        return pos, neg
    if ppt_enabled and not any(ppt_enabled.values()):
        return 0, 0
    return int(epic_config.get('positive', 0)), int(epic_config.get('negative', 0))


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

    age = normalize_age_value(age)
    person_ctx = build_person_context(age, gender)
    sum_assured = ensure_thousand_multiple(discount_info.get("sumAssured") or 0)
    portfolio_type = normalize_portfolio_type(portfolio_type or CURRENT_PORTFOLIO_TYPE)
    portfolio_strategy = PORTFOLIO_STRATEGY_MAP.get(portfolio_type, "")
    fund_allocation = build_fund_allocation(portfolio_type)

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
                charge_year, coverage_year, maturity_year = get_out_of_range_maturity_year(
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
    # Min PT 10 for SAM 10-14 (allowed 10,15,20,25,30);
    # Min PT 15 for SAM 15-20 (allowed 15,20,25,30).
    if 'PolicyTerm' in selected_epics:
        target_rule = 'PolicyTerm'
        policy_term_config = epic_counts.get(target_rule, {})

        for sam_band, band_rule in SAM_BAND_RULES.items():
            pos_count, neg_count = resolve_sam_band_counts(policy_term_config, sam_band)
            sam_low, sam_high = band_rule["sam_range"]

            band_ppt_names = ppt_names_for_sam_band(sam_band)

            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                ppt_name = band_ppt_names[(idx + i) % len(band_ppt_names)]
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = random.randint(sam_low, sam_high)
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
                    SCENARIO_MAP[target_rule](sam_band),
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
                ppt_name = band_ppt_names[(idx + i) % len(band_ppt_names)]
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = random.randint(sam_low, sam_high)
                charge_year, coverage_year, maturity_year = get_out_of_range_coverage(
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
                    SCENARIO_MAP[target_rule](sam_band),
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
    # Min PPT 5 for SAM 10-14; Min PPT 15 for SAM 15-20.
    if 'PremiumPayingTerm' in selected_epics:
        target_rule = 'PremiumPayingTerm'
        ppt_config = epic_counts.get(target_rule, {})

        for sam_band, band_rule in SAM_BAND_RULES.items():
            pos_count, neg_count = resolve_sam_band_counts(ppt_config, sam_band)
            sam_low, sam_high = band_rule["sam_range"]
            min_ppt = band_rule["min_ppt"]

            valid_ppts = [
                ppt for ppt in PPT_NAME if PPT_RULES[ppt]['charge_year'](30) >= min_ppt
            ]
            invalid_ppts = [
                ppt for ppt in PPT_NAME if PPT_RULES[ppt]['charge_year'](30) < min_ppt
            ]

            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                ppt_name = valid_ppts[(idx + i) % len(valid_ppts)] if valid_ppts else PPT_NAME[0]
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = random.randint(sam_low, sam_high)
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
                    SCENARIO_MAP[target_rule](sam_band),
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
                # A PPT below the band minimum is the negative condition; when every
                # PPT is valid for the band, force the charge year below the minimum.
                if invalid_ppts:
                    ppt_name = invalid_ppts[(idx + i) % len(invalid_ppts)]
                    force_charge_year = None
                else:
                    ppt_name = PPT_NAME[(idx + i) % len(PPT_NAME)]
                    force_charge_year = max(1, min_ppt - 1)
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = build_case_age(min_entry_age, max_entry_age, i)
                sum_assured_multiple = random.randint(sam_low, sam_high)
                charge_year, coverage_year, maturity_year = get_years(
                    ppt_name, positive_age, sum_assured_multiple=sum_assured_multiple
                )
                if force_charge_year is not None:
                    charge_year = force_charge_year
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](sam_band),
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
            # Fund allocation that does not add up to 100 is the negative condition.
            invalid_total = random.choice([90, 95, 105, 110])
            for fund in FUND_COLUMNS:
                common_row[fund] = 0
            common_row["DebtFundPercentage"] = invalid_total
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
                iterm_care_sum_assured=pick_sum_assured_value(min_sum, max_sum),
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
            # Just below min on even iterations, just above max on odd ones.
            neg_iterm_sa = (
                ensure_thousand_multiple(min_sum - 1000)
                if i % 2 == 0
                else ensure_thousand_multiple(max_sum + 1000)
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
            # iTerm Care SA at or below the Ultima Plus SA.
            iterm_sa = pick_sum_assured_value(
                ITERM_CARE_SA_RANGE[0], min(ITERM_CARE_SA_RANGE[1], ultima_plus_sa)
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
            iterm_sa = pick_sum_assured_value(
                ITERM_CARE_SA_RANGE[0],
                min(ITERM_CARE_SA_RANGE[1], ultima_plus_sa, headroom)
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
