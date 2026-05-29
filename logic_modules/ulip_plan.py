# logic_module.py
import sys
import logging
import pandas as pd
import random 
import math
import numpy as np
from datetime import date
import copy
import traceback

# import logging
# logging.basicConfig(level=logging.DEBUG)
# logging.debug("Debugging is enabled")

# Global declarations
MIN_ENTRY_AGE = 0.25
MAX_ENTRY_AGE = 65
PRODUCT_CODE = 'ARMP0000150'
MIN_MATURITY_AGE = 18
MAX_MATURITY_AGE = 75
MAX_POLICY_TERM = 40
POLICY_TERM_STEP = 5
SUM_ASSURED_MULTIPLE_RANGE = (10, 20)

GENDER = ['Male', 'Female']
SMOKING = ['Smoker', 'Non Smoker']
policy_holder_location = ['MH', 'KA'] 
insurer_location = ['MH', 'KA']

ONLINE_DISCOUNT = [2, 15]
EXISTING_CUSTOMER_DISCOUNT = [0, 2]
LUMPSUM_PERCENT = [0, 100, 50]
MONTHLY_PERCENTAGE = [100, 0, 50]
DB_PAY_OPTION = ['Monthly', 'Lumpsum', 'Lumpsum + Monthly']
DB_PAY_OPTION_C = ['Monthly Income Payout', 'Lumpsum Payment', 'Lumpsum Payment + Monthly Income Payout']
INSTALLMENT_PERIOD = ['NA', '60', '120']
SUM_ASSURED = [1000000, 5000000, 10000000, 20000000]
PAYMENT_FREQUENCY = [1, 2, 3, 4, 5] # Annual, Half-Yearly, Quarterly, Monthly, Single
PAYMENT_FREQUENCY_STR = {1: 'Annual', 2: 'Half-Yearly', 3: 'Quarterly', 4: 'Monthly', 5: 'Single'}

PORTFOLIO_TYPES = ["LIFESTYLE", "SELFMANAGED"]
PORTFOLIO_STRATEGY_MAP = {
    "LIFESTYLE": "Lifestyle Based Portfolio Strategy",
    "SELFMANAGED": "Self Managed Portfolio Strategy",
}
PLAN_OPTION_DEFAULT = "Option A"
PAYOUT_FREQUENCY_DEFAULT = "YEARLY"
PROBIRTHDATE_DEFAULT = "No"
ADRIDER_CODE_DEFAULT = "BLLADBV1"
AGENT_CODE_DEFAULT = 10051410
RISK_CLASS_DEFAULT = "Standard"
REMARKS_DEFAULT = ""
TOTAL_FUND_ALLOCATED_DEFAULT = 100
FUND_STEP = 5
CURRENT_PORTFOLIO_TYPE = "LIFESTYLE"

FUND_COLUMNS = [
    "DebtFundPercentage",
    "AcceleratorFundPercentage",
    "OpportunityFundPercentage",
    "StableFundPercentage",
    "SecureFundPercentage",
    "BlueChipFundPercentage",
    "FlexiCapFundPercentage",
    "LiquidFundPercentage",
    "Nifty50CappedIndexFund",
    "MidCapFundPercentage",
]

MODULE_NAME = "ULIP Plan" 
API_MODE_VALUE = "Base plan" 
API_MODE_VALUE_RIDER = "Base Plan + AD"

INCEPTION_DATE_VALUE = "1/Sept/2025" #can be changed to current date
EXECUTE_VALUE = "N"
MEDICAL_INDI = "Medical"
CHECKING_NOTE_CREATE_VALUE = "Create"
CHECKING_NOTE_UPDATE_VALUE = "Create , Update"

TENANT_ID = ["SALES-APP", "POLICYBAZAAR"]
AD_RIDER_VARIANT = ["Classic", "Premium"]
AD_RIDER_VARIANT_C = ["Classic Option", "Premium Option"]

EXPECTED_RESULT_MAP = {
    'Positive': 'System should allow to generate Premium and all fields should match to the offline BI',
    'Negative': 'System should throw error message and should not generate Premium'
}

PPT_NAME = [
    "Single Pay",
    "Limited Pay (5 pay)",
    "Limited Pay (7 pay)",
    "Limited Pay (10 pay)",
    "Limited Pay (15 pay)",
    "Limited Pay (20 pay)",
    "Regular Pay",
]

EPIC_MAP = {
    'EntryAge': 'Check for Minimum - Maximum entry age',
    'PolicyTerm': 'Check for Policy Term',
    'MaturityAge': 'Check for Minimum - Maximum maturity age',
    'PaymentFrequency': 'Check for Premium Frequency validation',
    'PremiumPayingTerm': 'Check for Premium Paying Term',
    'SumAssuredValidation': 'Check for Sum Assured Validation',
    # 'ExistingCustomerDiscount': 'Check for Existing Customer Discount validation',
    # 'OnlinePlatformDiscountRP': 'Check for Online Platform Discount validation for Regular Pay',
    # 'OnlinePlatformDiscountLP': 'Check for Online Platform Discount validation for Limited Pay',
    # 'TotalDiscountValidation': 'Check for Total Discount validation',
}

EPIC_MAP_RIDER = {
    'EntryAge': 'Check for Minimum - Maximum entry age',
    'PolicyTerm': 'Check for Policy Term',
    'MaturityAge': 'Check for Minimum - Maximum maturity age',
    'PaymentFrequency': 'Check for Premium Frequency validation',
    'PremiumPayingTerm': 'Check for Premium Paying Term',
    'SumAssuredValidation': 'Check for Sum Assured Validation',
}


def get_api_operation(key):
    """Return the human readable API operation name for an epic key.

    Falls back to the rider map or the key itself if not found to avoid KeyError
    when code references EPIC_MAP entries that were intentionally omitted.
    """
    return EPIC_MAP.get(key) or EPIC_MAP_RIDER.get(key) or key

POLICY_TERM_NAMES = {
    "Single Pay": "SP",
    "Limited Pay (5 pay)": "LP5",
    "Limited Pay (7 pay)": "LP7",
    "Limited Pay (10 pay)": "LP10",
    "Limited Pay (15 pay)": "LP15",
    "Limited Pay (20 pay)": "LP20",
    "Regular Pay": "RP",
}

def premium_paying_term_message(ppt, min_ppt=None, max_ppt=None, ppt_limit=None):
    if ppt_limit is not None:
        return f"Premium Paying Term should be {ppt_limit} years for {ppt}."
    elif min_ppt is not None and max_ppt is not None:
        return f"Premium Paying Term chosen should be between {min_ppt} and {max_ppt} years for {ppt}."

def sum_assured_validation_message(ppt, min_sum=None, max_sum=None):
    if min_sum is not None and max_sum is not None and ppt == "SP_neg_max":
        return f"Max Base SA should not be greater than {max_sum} for Single pay"
    elif min_sum is not None and max_sum is not None:
        return f"Min Base SA should not be less than {min_sum} for Single pay"
    else:
        return f"Min Base SA should not be less than {min_sum} for Regular & Limited pay"

SCENARIO_MAP = {
        'EntryAge': lambda ppt, min_entry_age, max_entry_age: f"The age of Life Assured should be between {min_entry_age} to {max_entry_age} years for {ppt}",
        'PolicyTerm': lambda ppt, min_policy_term, max_policy_term: f"Policy term chosen should be between {min_policy_term} years to {max_policy_term} years for {ppt}",
        'MaturityAge': lambda ppt, min_maturity_age, max_maturity_age: f"The maturity age of Life Assured should be between {min_maturity_age} to {max_maturity_age} years for {ppt}",
        'PaymentFrequency': f"To check for premium Frequency chosen should be Single, Yearly, Half-Yearly, Quarterly & Monthly",
        'PremiumPayingTerm': premium_paying_term_message,
        'SumAssuredValidation': sum_assured_validation_message,
        'ExistingCustomerDiscount': f"To check for Existing Customer Discount should be 0% or 2%",
        'OnlinePlatformDiscountRP': f"To check for Online Platform Discount should be 0%, 2% or 10% for Regular Pay",
        'OnlinePlatformDiscountLP': f"To check for Online Platform Discount should be 0%, 2% or 15% for Limited Pay",
        'TotalDiscountValidation': f"To check for Total Discount should not be more than 17%",
        'SumAssuredValidation_Rider_min': lambda ppt, min_sum=None: f"Min Rider SA should not be less than {min_sum} for Rider AD",
        'SumAssuredValidation_Rider_max': lambda ppt, max_sum=None: f"Max Rider SA should not be greater than {max_sum} for Rider AD",
    }

column_order = [
    "Execute",
    "Remarks",
    "TUID",
    "API_Mode",
    "API_Name",
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
    "LAMaturity Age",
    "PH Maturity Age",
    "LAGender",
    "PHGender",
    "Probirthdate",
    "Channel",
    "Plan Option",
    "portfolio",
    "PortfolioStrategy",
    "coverageYear",
    "chargeYear",
    "ADRider Opted",
    "ADCoverageyear",
    "chargePeriod",
    "paymentFreqW",
    "paymentFreq",
    "payoutFrequency",
    "annualizedPremium",
    "installmentPremium",
    "SAMultiple",
    "SA",
    "ADsumAssured",
    "ADRiderVariantC",
    "ADRiderCode",
    "Years to Maturity",
    "DebtFundPercentage",
    "AcceleratorFundPercentage",
    "OpportunityFundPercentage",
    "StableFundPercentage",
    "SecureFundPercentage",
    "BlueChipFundPercentage",
    "FlexiCapFundPercentage",
    "LiquidFundPercentage",
    "Nifty50CappedIndexFund",
    "MidCapFundPercentage",
    "Total Fund Allocated",
    "ProductCode",
    "Premium Allocation Charge",
    "Commission",
    "Proposer_insured",
    "AgentCode",
    "PartySerialId",
    "RiskClass",
    "PerMile",
    "EMRPeriod",
    "RiderEMR_extraPara",
    "RiderPerMille_extraPara",
    "LAGenderC",
    "PHGenderC",
    "paymentFreqC",
    "relationToInsured",
    "relationToHolder",
    "Is the Life Assured same as Policyholder?",
    'policyHolderLocation',
    "Difference_Value",
    # "ADRiderChargeYear",
    # "Rider Coverage upto Age",
    # "DBpayOptionC",
]

# Discount and sum assured calculation based on PPT type
PPT_RULES_TT2 = {
        "Single Pay": (2500000, 5000000),
        "Limited Pay (5 pay)": (5000000, 20000000),
        "Limited Pay (7 pay)": (5000000, 20000000),
        "Limited Pay (10 pay)": (5000000, 20000000),
        "Limited Pay (15 pay)": (5000000, 20000000),
        "Limited Pay (20 pay)": (5000000, 20000000),
        "Regular Pay": (5000000, 20000000)
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
    if ppt_name == "Single Pay":
        return "Single Pay"
    if ppt_name == "Regular Pay":
        return "Regular Pay"
    return "Limited Pay"


def normalize_age_value(age):
    if age is None:
        return age
    if 0 < age < 1:
        return 0.25
    if age >= 1:
        return int(round(age))
    return int(math.floor(age))


def build_birthdate_for_age(age, reference_date=None):
    ref_date = reference_date or date.today()
    if isinstance(age, float) and age % 1 != 0:
        return build_birthdate(age, reference_date=ref_date)
    return f"01/Jan/{ref_date.year - int(age)}"


def build_person_context(age, gender, reference_date=None):
    ref_date = reference_date or date.today()
    la_age = normalize_age_value(age)
    la_gender = gender
    if la_age < 18:
        same_person = False
        ph_age_min = max(18, int(math.ceil(la_age + 25)))
        ph_age_max = max(ph_age_min, MAX_ENTRY_AGE)
        if ph_age_min >= ph_age_max:
            ph_age = ph_age_min
        else:
            ph_age = random.randint(ph_age_min, ph_age_max)
        ph_gender = random.choice(GENDER)
    else:
        same_person = True
        ph_age = la_age
        ph_gender = la_gender
    la_birthdate = build_birthdate_for_age(la_age, reference_date=ref_date)
    ph_birthdate = build_birthdate_for_age(ph_age, reference_date=ref_date)
    la_gender_c = "M" if la_gender == "Male" else "F"
    ph_gender_c = "M" if ph_gender == "Male" else "F"
    proposer_insured = "Same" if same_person else "Different"
    relation_to_holder = "SELF" if same_person else "PARENT"
    relation_to_insured = "SELF" if same_person else "CHILD"
    same_as_ph = "Yes" if same_person else "No"
    return {
        "la_age": la_age,
        "ph_age": ph_age,
        "la_gender": la_gender,
        "ph_gender": ph_gender,
        "la_birthdate": la_birthdate,
        "ph_birthdate": ph_birthdate,
        "la_gender_c": la_gender_c,
        "ph_gender_c": ph_gender_c,
        "proposer_insured": proposer_insured,
        "relation_to_holder": relation_to_holder,
        "relation_to_insured": relation_to_insured,
        "same_as_ph": same_as_ph,
    }


def build_fund_allocation(portfolio_type):
    portfolio_type = normalize_portfolio_type(portfolio_type)
    allocation = {fund: 0 for fund in FUND_COLUMNS}
    if portfolio_type == "LIFESTYLE":
        allocation["BlueChipFundPercentage"] = TOTAL_FUND_ALLOCATED_DEFAULT
        return allocation
    selected_count = random.randint(1, len(FUND_COLUMNS))
    selected_funds = random.sample(FUND_COLUMNS, selected_count)
    units_total = TOTAL_FUND_ALLOCATED_DEFAULT // FUND_STEP
    units = [0] * selected_count
    for _ in range(units_total):
        units[random.randrange(selected_count)] += 1
    for fund, fund_units in zip(selected_funds, units):
        allocation[fund] = fund_units * FUND_STEP
    return allocation


def build_ad_sum_assured(base_sum_assured, max_multiplier=3, min_value=25000, cap=30000000):
    max_value = min(cap, int(max_multiplier * base_sum_assured))
    return pick_sum_assured_value(min_value, max_value)
def calculate_discounts(ppt_type):

    min_sa, max_sa = PPT_RULES_TT2[ppt_type]
    sum_assured = pick_sum_assured_value(min_sa, max_sa)
    if(ppt_type == "Regular Pay"):
        if(sum_assured < 7500000):
            online_discount = random.choice([4])
        else:
            online_discount = random.choice([10])
    elif(ppt_type == "Single Pay"):
        online_discount = random.choice([2])
    else:
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
        "sumAssured": sum_assured
    }


CURRENT_SUM_ASSURED_MULTIPLE = None
MONTH_ABBR = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def pick_sum_assured_multiple():
    return random.randint(SUM_ASSURED_MULTIPLE_RANGE[0], SUM_ASSURED_MULTIPLE_RANGE[1])


def policy_term_min_for_multiple(sum_assured_multiple):
    if sum_assured_multiple <= 14:
        return 10
    return 15


def round_up_to_step(value, step):
    return int(((value + step - 1) // step) * step)


def build_policy_term_range(age, sum_assured_multiple, min_term_override=None):
    min_term = policy_term_min_for_multiple(sum_assured_multiple)
    if min_term_override is not None:
        min_term = max(min_term, min_term_override)
    max_term = min(MAX_POLICY_TERM, MAX_MATURITY_AGE - age)
    return min_term, max_term


def pick_policy_term(min_term, max_term):
    min_term = round_up_to_step(min_term, POLICY_TERM_STEP)
    if max_term < min_term:
        return min_term
    valid_terms = list(range(min_term, int(max_term) + 1, POLICY_TERM_STEP))
    return random.choice(valid_terms) if valid_terms else min_term


def build_birthdate(age, reference_date=None):
    ref_date = reference_date or date.today()
    total_months = int(round(age * 12))
    years_back, months_back = divmod(total_months, 12)
    year = ref_date.year - years_back
    month = ref_date.month - months_back
    if month <= 0:
        year -= 1
        month += 12
    return f"01/{MONTH_ABBR[month - 1]}/{year}"

PPT_RULES = {
    "Single Pay": {
        "entry_age_range": (MIN_ENTRY_AGE, 65),
        "charge_year": lambda age: 1,
        "coverage_year_range": lambda age, charge_year=None, sum_assured_multiple=None: build_policy_term_range(
            age,
            sum_assured_multiple,
            min_term_override=None,
        ),
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (MIN_MATURITY_AGE, MAX_MATURITY_AGE),
    },
    "Limited Pay (5 pay)": {
        "entry_age_range": (MIN_ENTRY_AGE, 60),
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
        "entry_age_range": (MIN_ENTRY_AGE, 60),
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
        "entry_age_range": (MIN_ENTRY_AGE, 60),
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
        "entry_age_range": (MIN_ENTRY_AGE, 60),
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
        "entry_age_range": (MIN_ENTRY_AGE, 60),
        "charge_year": lambda age: 20,
        "coverage_year_range": lambda age, charge_year=None, sum_assured_multiple=None: build_policy_term_range(
            age,
            sum_assured_multiple,
            min_term_override=charge_year,
        ),
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (MIN_MATURITY_AGE, MAX_MATURITY_AGE),
    },
    "Regular Pay": {
        "entry_age_range": (MIN_ENTRY_AGE, 60),
        "charge_year": lambda age: 0,
        "coverage_year_range": lambda age, charge_year=None, sum_assured_multiple=None: build_policy_term_range(
            age,
            sum_assured_multiple,
            min_term_override=None,
        ),
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (MIN_MATURITY_AGE, MAX_MATURITY_AGE),
    },
}

PPT_RULES_RIDER = {
    "Rider AD": {
        "entry_age_range": (18, 65),
        "charge_year": lambda age: random.randint(5, 57),
        "coverage_year_range": lambda age: (5, 57),
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (23, 75),
        "sum_assured_range": (25000, 10000000)
    },
}

def get_rider_years(ppt_name, age, PPT_RULES=PPT_RULES_RIDER):
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule.get('charge_year_override', rule['charge_year'](age))
    # Determine coverage year range
    coverage_min, coverage_max = rule['coverage_year_range'](age)
    # Ensure valid range
    if coverage_min > coverage_max:
        coverage_year = coverage_min
    else:
        coverage_year = random.randint(coverage_min, coverage_max)
    maturity_year = rule['maturity_year'](age, coverage_year)
    return charge_year, coverage_year, maturity_year

def get_years(ppt_name, age, PPT_RULES=PPT_RULES, sum_assured_multiple=None):
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule.get('charge_year_override', rule['charge_year'](age))
    if sum_assured_multiple is None:
        sum_assured_multiple = pick_sum_assured_multiple()
    coverage_min, coverage_max = rule['coverage_year_range'](age, charge_year, sum_assured_multiple)
    coverage_year = pick_policy_term(coverage_min, coverage_max)
    if ppt_name == "Regular Pay":
        charge_year = coverage_year
    maturity_year = rule['maturity_year'](age, coverage_year)
    global CURRENT_SUM_ASSURED_MULTIPLE
    CURRENT_SUM_ASSURED_MULTIPLE = sum_assured_multiple
    return charge_year, coverage_year, maturity_year

def get_out_of_range_coverage(ppt_name, age, PPT_RULES=PPT_RULES, sum_assured_multiple=None):
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule['charge_year'](age)
    if sum_assured_multiple is None:
        sum_assured_multiple = pick_sum_assured_multiple()
    coverage_min, coverage_max = rule['coverage_year_range'](age, charge_year, sum_assured_multiple)
    coverage_min = round_up_to_step(coverage_min, POLICY_TERM_STEP)
    coverage_max = round_up_to_step(coverage_max, POLICY_TERM_STEP)
    coverage_year = coverage_max + POLICY_TERM_STEP if not random.choice([True, False]) else coverage_min - POLICY_TERM_STEP
    maturity_year = rule['maturity_year'](age, coverage_year)
    global CURRENT_SUM_ASSURED_MULTIPLE
    CURRENT_SUM_ASSURED_MULTIPLE = sum_assured_multiple
    return charge_year, coverage_year, maturity_year, coverage_min, coverage_max

def get_out_of_range_maturity_year(ppt_name, age, PPT_RULES=PPT_RULES, sum_assured_multiple=None):
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule['charge_year'](age)
    maturity_min, maturity_max = rule['maturity_age_range']
    if sum_assured_multiple is None:
        sum_assured_multiple = pick_sum_assured_multiple()
    coverage_min, coverage_max = rule['coverage_year_range'](age, charge_year, sum_assured_multiple)
    coverage_year = maturity_max - age + random.randint(1, 5)
    maturity_year = rule['maturity_year'](age, coverage_year)
    global CURRENT_SUM_ASSURED_MULTIPLE
    CURRENT_SUM_ASSURED_MULTIPLE = sum_assured_multiple
    return charge_year, coverage_year, maturity_year, maturity_min, maturity_max

def get_out_of_range_charge_year(ppt_name, age, PPT_RULES=PPT_RULES, sum_assured_multiple=None):
    age = normalize_age_value(age)
    rule = PPT_RULES.get(ppt_name)
    charge_year = rule.get('charge_year_override', rule['charge_year'](age))
    charge_year_out = charge_year - 1 if random.choice([True, False]) else charge_year + 1
    if ppt_name == "Single Pay":
        charge_year_out = 2
    if sum_assured_multiple is None:
        sum_assured_multiple = pick_sum_assured_multiple()
    coverage_min, coverage_max = rule['coverage_year_range'](age, charge_year_out, sum_assured_multiple)
    coverage_year = pick_policy_term(coverage_min, coverage_max)
    if ppt_name == "Regular Pay":
        coverage_year = pick_policy_term(coverage_min, coverage_max)
    maturity_year = rule['maturity_year'](age, coverage_year)
    global CURRENT_SUM_ASSURED_MULTIPLE
    CURRENT_SUM_ASSURED_MULTIPLE = sum_assured_multiple
    return charge_year_out, coverage_year, maturity_year


def make_constant_coverage_func(range_tuple):
    return lambda age, charge_year=None, sum_assured_multiple=None, _range_tuple=range_tuple: (_range_tuple[0], _range_tuple[1])


def apply_entry_age_overrides(epic_counts_local):
    entry_conf = epic_counts_local.get('EntryAge', {})
    for ppt_name, (min_age, max_age) in entry_conf.get('ppt_age_ranges', {}).items():
        if ppt_name in PPT_RULES:
            PPT_RULES[ppt_name]['entry_age_range'] = (min_age, max_age)


def apply_policy_term_overrides(epic_counts_local):
    policy_conf = epic_counts_local.get('PolicyTerm', {})
    for ppt_name, (min_cov, max_cov) in policy_conf.get('ppt_age_ranges', {}).items():
        if ppt_name in PPT_RULES:
            PPT_RULES[ppt_name]['coverage_year_range'] = make_constant_coverage_func((min_cov, max_cov))


def apply_maturity_age_overrides(epic_counts_local):
    maturity_conf = epic_counts_local.get('MaturityAge', {})
    for ppt_name, (min_mat, max_mat) in maturity_conf.get('ppt_age_ranges', {}).items():
        if ppt_name in PPT_RULES:
            PPT_RULES[ppt_name]['maturity_age_range'] = (min_mat, max_mat)


def apply_premium_paying_term_overrides(epic_counts_local):
    ppt_conf = epic_counts_local.get('PremiumPayingTerm', {})
    for ppt_name, value in ppt_conf.get('ppt_age_ranges', {}).items():
        if ppt_name not in PPT_RULES:
            continue
        try:
            min_value, max_value = value
        except Exception:
            continue
        if min_value == max_value:
            PPT_RULES[ppt_name]['charge_year_override'] = min_value
        else:
            PPT_RULES[ppt_name]['charge_year_range'] = (min_value, max_value)
            PPT_RULES[ppt_name]['charge_year'] = lambda age, value_range=(min_value, max_value): random.randint(value_range[0], value_range[1])


def apply_sum_assured_overrides(epic_counts_local):
    sum_assured_conf = epic_counts_local.get('SumAssuredValidation', {})
    # print("SumAssuredValidation overrides:", sum_assured_conf)

    min_sa = sum_assured_conf.get("Single Pay", {}).get('min_val')
    max_sa = sum_assured_conf.get("Single Pay", {}).get('max_val')
    if max_sa is not None or min_sa is not None:
        PPT_RULES_TT2["Single Pay"] = (min_sa, max_sa)

    min_sa = sum_assured_conf.get("Others", {}).get('min_val')
    max_sa = sum_assured_conf.get("Others", {}).get('max_val')
    if max_sa is not None or min_sa is not None:
        PPT_RULES_TT2["Limited Pay (5 pay)"] = (min_sa, max_sa)
        PPT_RULES_TT2["Limited Pay (7 pay)"] = (min_sa, max_sa)
        PPT_RULES_TT2["Limited Pay (10 pay)"] = (min_sa, max_sa)
        PPT_RULES_TT2["Limited Pay (15 pay)"] = (min_sa, max_sa)
        PPT_RULES_TT2["Limited Pay (20 pay)"] = (min_sa, max_sa)
        PPT_RULES_TT2["Regular Pay"] = (min_sa, max_sa)


def apply_rider_overrides(epic_counts_rider_local):
    if not epic_counts_rider_local:
        return

    entry_conf_rider = epic_counts_rider_local.get('EntryAge', {})
    for ppt_name, (min_age, max_age) in entry_conf_rider.get('ppt_age_ranges', {}).items():
        if ppt_name in PPT_RULES_RIDER:
            PPT_RULES_RIDER[ppt_name]['entry_age_range'] = (min_age, max_age)

    maturity_conf_rider = epic_counts_rider_local.get('MaturityAge', {})
    for ppt_name, (min_mat, max_mat) in maturity_conf_rider.get('ppt_age_ranges', {}).items():
        if ppt_name in PPT_RULES_RIDER:
            PPT_RULES_RIDER[ppt_name]['maturity_age_range'] = (min_mat, max_mat)


def update_ppt_rules_with_epic_counts(epic_counts_local, epic_counts_rider_local=None):
    if not epic_counts_local:
        return

    apply_entry_age_overrides(epic_counts_local)
    apply_policy_term_overrides(epic_counts_local)
    apply_maturity_age_overrides(epic_counts_local)
    apply_premium_paying_term_overrides(epic_counts_local)
    apply_sum_assured_overrides(epic_counts_local)
    apply_rider_overrides(epic_counts_rider_local)


def resolve_ppt_case_counts(target_rule, epic_config, epic_count_source, ppt_name):
    ppt_pos_counts = epic_config.get('ppt_pos_counts', {})
    ppt_neg_counts = epic_config.get('ppt_neg_counts', {})
    per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME)
    ppt_enabled = epic_config.get('ppt_enabled', {})

    if per_ppt_mode:
        return int(ppt_pos_counts.get(ppt_name, 0)), int(ppt_neg_counts.get(ppt_name, 0)), per_ppt_mode, ppt_enabled
    if ppt_enabled.get(ppt_name, False):
        shared_counts = epic_count_source.get(target_rule, {})
        return shared_counts.get('positive', 0), shared_counts.get('negative', 0), per_ppt_mode, ppt_enabled
    return None, None, per_ppt_mode, ppt_enabled


def normalize_payment_frequency(ppt_name, payment_freq):
    if ppt_name == "Single Pay":
        return 5
    if payment_freq == 5:
        return 1
    return payment_freq


def build_case_age(min_age, max_age, iteration_index):
    if iteration_index % 2 == 0:
        age = max(min_age, min(max_age - iteration_index, max_age))
    else:
        age = min(max_age, min_age + iteration_index)
    return normalize_age_value(age)


def build_random_age(min_age, max_age):
    if isinstance(min_age, float) or isinstance(max_age, float) or min_age < 1:
        age = random.uniform(min_age, max_age)
    else:
        age = random.randint(int(min_age), int(max_age))
    return normalize_age_value(age)


def build_entry_age_negative(min_age, max_age, iteration_index, ppt_name):
    if iteration_index % 2 == 0:
        negative_age = random.uniform(max_age + 1, max_age + 10)
    else:
        if min_age <= 0.25:
            negative_age = max_age + 1
        else:
            lower_bound = 0.01
            upper_bound = min_age - 0.01 if min_age > 0.02 else min_age
            negative_age = random.uniform(lower_bound, upper_bound)
    return normalize_age_value(negative_age)


def build_rider_years(charge_year, coverage_year, maturity_year, apply_min_charge_floor=True):
    rider_charge_year = max(5, charge_year) if apply_min_charge_floor else charge_year
    rider_coverage_year = min(coverage_year, 57)
    rider_maturity_year = min(maturity_year, 75)
    return rider_charge_year, rider_coverage_year, rider_maturity_year


def build_rider_fields(ad_sum_assured, rider_variant_index, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=None, payment_freq=None):
    ad_sum_assured = ensure_thousand_multiple(ad_sum_assured)
    rider_fields = {
        'API_Mode': API_MODE_VALUE_RIDER,
        'ADRider Opted': 'Yes',
        'ADsumAssured': ad_sum_assured,
        'ADCoverageyear': coverage_year_rider,
        'ADRiderChargeYear': charge_year_rider,
        'Rider Coverage upto Age': maturity_year_rider,
        'ADRiderCode': ADRIDER_CODE_DEFAULT,
        'ADRiderVariantC': AD_RIDER_VARIANT_C[rider_variant_index],
    }
    if idx is not None:
        rider_fields['DBpayOptionC'] = DB_PAY_OPTION_C[idx]
    if payment_freq is not None and idx is not None:
        rider_fields['paymentFreqC'] = PAYMENT_FREQUENCY_STR[payment_freq]
    return rider_fields


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
):
    """Return the common base row dict used across many test scenarios."""
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

    if ppt_name == "Single Pay":
        annualized_premium = sum_assured
        installment_premium = sum_assured
    else:
        annualized_premium = (
            sum_assured / sum_assured_multiple if sum_assured_multiple else 0
        )
        installment_premium = (
            annualized_premium / payment_freq if payment_freq else 0
        )
    annualized_premium = round(annualized_premium, 2)
    installment_premium = round(installment_premium, 2)

    la_maturity_age = round(person_ctx["la_age"] + coverage_year, 2)
    ph_maturity_age = round(person_ctx["ph_age"] + coverage_year, 2)
    premium_allocation_charge = round(sum_assured * 0.001, 2)
    commission = round(sum_assured * 0.001, 2)

    row = {
        'Execute': EXECUTE_VALUE,
        'Remarks': REMARKS_DEFAULT,
        'TUID': f'TC_{module_name}_{tuid_counter:03d}',
        'API_Mode': API_MODE_VALUE,
        'API_Name': resolve_api_name(ppt_name),
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
        'LAMaturity Age': la_maturity_age,
        'PH Maturity Age': ph_maturity_age,
        'LAGender': person_ctx["la_gender"],
        'PHGender': person_ctx["ph_gender"],
        'Probirthdate': PROBIRTHDATE_DEFAULT,
        'Channel': 'Direct' if(discount_info.get('tenantID') == 'SALES-APP') else 'Non-Direct',
        'Plan Option': PLAN_OPTION_DEFAULT,
        'portfolio': portfolio_type,
        'PortfolioStrategy': portfolio_strategy,
        'coverageYear': coverage_year,
        'chargeYear': charge_year,
        'ADRider Opted': 'No',
        'ADCoverageyear': 0,
        'ADRiderChargeYear': 0,
        'Rider Coverage upto Age': 0,
        'chargePeriod': 2,
        'paymentFreqW': PAYMENT_FREQUENCY_STR.get(payment_freq, ''),
        'paymentFreqC': PAYMENT_FREQUENCY_STR.get(payment_freq, ''),
        'payoutFrequency': PAYOUT_FREQUENCY_DEFAULT,
        'annualizedPremium': annualized_premium,
        'installmentPremium': installment_premium,
        'SAMultiple': sum_assured_multiple,
        'SA': sum_assured,
        'ADsumAssured': 0,
        'ADRiderCode': '',
        'Years to Maturity': '',
        'ProductCode': product_code,
        'paymentFreq': payment_freq,
        'PerMile': 0,
        'EMRPeriod': 0,
        'RiderEMR_extraPara': 0,
        'RiderPerMille_extraPara': 0,
        'LAGenderC': person_ctx["la_gender_c"],
        'PHGenderC': person_ctx["ph_gender_c"],
        'relationToHolder': person_ctx["relation_to_holder"],
        'relationToInsured': person_ctx["relation_to_insured"],
        'Proposer_insured': person_ctx["proposer_insured"],
        'Is the Life Assured same as Policyholder?': person_ctx["same_as_ph"],
        'Difference_Value': '',
        'DBpayOptionC': DB_PAY_OPTION_C[idx],
        'ADRiderVariantC': 'Classic Option',
        'Total Fund Allocated': TOTAL_FUND_ALLOCATED_DEFAULT,
        'Premium Allocation Charge': premium_allocation_charge,
        'Commission': commission,
        'AgentCode': AGENT_CODE_DEFAULT,
        'PartySerialId': '',
        'RiskClass': RISK_CLASS_DEFAULT,
        'policyHolderLocation': policy_loc,
    }
    row.update(fund_allocation)
    return row


def generate_test_cases(
    epic_counts,
    selected_epics=None,
    epic_counts_rider=None,
    selected_epics_rider=None,
    portfolio_type=None,
):
    scenarios = []
    tuid_counter = 0
    current_year = date.today().year

    set_current_portfolio_type(portfolio_type)

    # print("#"*50,"\n\niTerm Elite N logic module")
    # apply overrides in-place before generation
    try:
        update_ppt_rules_with_epic_counts(epic_counts or {}, epic_counts_rider or {})
    except Exception:
        # if anything goes wrong during applying user overrides, ensure generation continues with original rules
        logging.exception('Failed to apply PPT_RULES overrides from epic_counts')

    common_data = {
                'PerMile': 0,
                'EMRPeriod': 0,
                'RiderEMR_extraPara': 0,
                'RiderPerMille_extraPara': 0,
                'Difference_Value': ''}
    
    # --- EPIC: EntryAge ---
    if 'EntryAge' in selected_epics:
        target_rule = 'EntryAge'
        entry_age_config = epic_counts.get(target_rule, {})
        ppt_age_ranges = entry_age_config.get('ppt_age_ranges', {})
        ppt_pos_counts = entry_age_config.get('ppt_pos_counts', {})
        ppt_neg_counts = entry_age_config.get('ppt_neg_counts', {})

        entryage_ppt_rules = PPT_RULES
        # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
        per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
        ppt_enabled = entry_age_config.get('ppt_enabled', {}) # for same count mode
        # if ppt_age_ranges and per_ppt_mode:
        for ppt_name in PPT_NAME:
            rule = entryage_ppt_rules.get(ppt_name)
            min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, rule['entry_age_range'])
            if per_ppt_mode:
                pos_count = int(ppt_pos_counts.get(ppt_name, 0))
                neg_count = int(ppt_neg_counts.get(ppt_name, 0))
            elif ppt_enabled.get(ppt_name, False):
                pos_count = epic_counts.get(target_rule, {}).get('positive', 0)
                neg_count = epic_counts.get(target_rule, {}).get('negative', 0)
            else:
                continue
            # Positive cases for this PPT
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)

                charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, entryage_ppt_rules)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                    payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
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
                    idx
                )
                scenarios.append({**common_data, **common_row})
            # Negative cases for this PPT
            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                negative_age = build_entry_age_negative(min_entry_age, max_entry_age, i, ppt_name)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, negative_age, entryage_ppt_rules)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                    payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
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
                    idx
                )
                scenarios.append({**common_data, **common_row})

    # --- EPIC: PolicyTerm ---
    if 'PolicyTerm' in selected_epics:
        target_rule = 'PolicyTerm'
        # counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        policy_term_config = epic_counts.get(target_rule, {})
        ppt_age_ranges = policy_term_config.get('ppt_age_ranges', {})
        ppt_pos_counts = policy_term_config.get('ppt_pos_counts', {})
        ppt_neg_counts = policy_term_config.get('ppt_neg_counts', {})

        policy_term_ppt_rules = PPT_RULES
        # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
        per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
        ppt_enabled = policy_term_config.get('ppt_enabled', {}) # for same count mode
        # if ppt_age_ranges and per_ppt_mode:
        for ppt_name in PPT_NAME:
            if per_ppt_mode:
                pos_count = int(ppt_pos_counts.get(ppt_name, 0))
                neg_count = int(ppt_neg_counts.get(ppt_name, 0))
            elif ppt_enabled.get(ppt_name, False):
                pos_count = epic_counts.get(target_rule, {}).get('positive', 0)
                neg_count = epic_counts.get(target_rule, {}).get('negative', 0)
            else:
                continue
            # Positive Cases
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
                rule = policy_term_ppt_rules.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                age = build_random_age(min_entry_age, max_entry_age)
                sum_assured_multiple = pick_sum_assured_multiple()
                min_policy_term, max_policy_term = ppt_age_ranges.get(ppt_name, (5, 85))
                charge_year, coverage_year, maturity_year = get_years(
                    ppt_name,
                    age,
                    policy_term_ppt_rules,
                    sum_assured_multiple=sum_assured_multiple,
                )
                # if(ppt_name != "Limited Pay (Pay till age 60)"):
                #     policy_term_ppt_rules[ppt_name]["coverage_year_range"] = lambda age: (min(min_policy_term, charge_year+5), min(max_policy_term, 85-age))
                # else:
                #     policy_term_ppt_rules[ppt_name]["coverage_year_range"] = lambda age, charge_year: (max(charge_year+5, min_policy_term), min(max_policy_term, 85-age))
                # Use coverage_year_range from PPT_RULES
                min_policy_term, max_policy_term = rule['coverage_year_range'](
                    age,
                    charge_year,
                    sum_assured_multiple,
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                        payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule) + " - " + POLICY_TERM_NAMES[ppt_name],
                    CHECKING_NOTE_UPDATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_policy_term, max_policy_term),
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
                    payment_freq,
                    discount_info,
                    idx,
                    sum_assured_multiple=sum_assured_multiple
                )
                scenarios.append({**common_data, **common_row})
            # Negative Cases
            for i in range(neg_count):
                tuid_counter += 1
                # age = build_random_age(min_entry_age, max_entry_age)
                idx = random.randint(0, 2)
                # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
                rule = policy_term_ppt_rules.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                age = build_random_age(min_entry_age, max_entry_age)
                sum_assured_multiple = pick_sum_assured_multiple()
                charge_year, coverage_year, maturity_year, coverage_min, coverage_max = get_out_of_range_coverage(
                    ppt_name,
                    age,
                    policy_term_ppt_rules,
                    sum_assured_multiple=sum_assured_multiple,
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                        payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule] + " - " + POLICY_TERM_NAMES[ppt_name],
                    CHECKING_NOTE_UPDATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, coverage_min, coverage_max),
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
                    sum_assured_multiple=sum_assured_multiple
                )
                scenarios.append({**common_data, **common_row})

    # --- EPIC: MaturityAge ---
    if 'MaturityAge' in selected_epics:
        target_rule = 'MaturityAge'
        # counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        maturity_age_config = epic_counts.get(target_rule, {})
        ppt_age_ranges = maturity_age_config.get('ppt_age_ranges', {})
        ppt_pos_counts = maturity_age_config.get('ppt_pos_counts', {})
        ppt_neg_counts = maturity_age_config.get('ppt_neg_counts', {})

        # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
        per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
        ppt_enabled = maturity_age_config.get('ppt_enabled', {}) # for same count mode
        # if ppt_age_ranges and per_ppt_mode:
        for ppt_name in PPT_NAME:
            # min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
            if per_ppt_mode:
                pos_count = int(ppt_pos_counts.get(ppt_name, 0))
                neg_count = int(ppt_neg_counts.get(ppt_name, 0))
            elif ppt_enabled.get(ppt_name, False):
                pos_count = epic_counts.get(target_rule, {}).get('positive', 0)
                neg_count = epic_counts.get(target_rule, {}).get('negative', 0)
            else:
                continue
            # Positive Cases
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                age = build_random_age(min_entry_age, max_entry_age)
                min_maturity_age, max_maturity_age = rule['maturity_age_range']
                charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                        payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
                
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
                    idx
                )
                scenarios.append({**common_data, **common_row})
            # Negative Cases
            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                age = build_random_age(min_entry_age, max_entry_age)
                charge_year, coverage_year, maturity_year, min_maturity_age, max_maturity_age = get_out_of_range_maturity_year(ppt_name, age)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                        payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_maturity_age, max_maturity_age),
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
                    idx
                )
                scenarios.append({**common_data, **common_row})

    # --- EPIC: PaymentFrequency ---
    if 'PaymentFrequency' in selected_epics:
        target_rule = 'PaymentFrequency'
        counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        PAYMENT_FREQUENCY_U = epic_counts.get('PaymentFrequency', {}).get('payment_frequency_options')
        # Positive Cases
        for i in range(counts.get('positive', 0)):
            tuid_counter += 1
            idx = random.randint(0, 2)
            # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            if 5 not in PAYMENT_FREQUENCY_U:
                filtered_PPT_NAME = [ppt for ppt in PPT_NAME if ppt != "Single Pay"]
            else:
                filtered_PPT_NAME = PPT_NAME.copy()
            ppt_name = filtered_PPT_NAME[(idx+i) % len(filtered_PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY_U)
            if(ppt_name == "Single Pay"):
                    payment_freq = 5
            if(payment_freq == 5 and ppt_name != "Single Pay"):
                payment_freq = 1
            
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
                payment_freq,
                discount_info,
                idx
            )
            scenarios.append({**common_data, **common_row})
        # Negative Cases
        for i in range(counts.get('negative', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            # payment_freq = random.choice(PAYMENT_FREQUENCY)
            # invalid_freq = random.choice([6, 7]) # Invalid frequencies
            # paymentFreqStr = "invalid_freq"
            if(ppt_name == "Single Pay"):
                payment_freq = random.choice([1, 2, 3, 4]) # Invalid frequencies for Single Pay
            else:
                payment_freq = 5 # Invalid frequency for others
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
                idx
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: PremiumPayingTerm ---
    if 'PremiumPayingTerm' in selected_epics:
        target_rule = 'PremiumPayingTerm'
        premium_paying_term_config = epic_counts.get(target_rule, {})
        ppt_age_ranges = premium_paying_term_config.get('ppt_age_ranges', {})
        ppt_pos_counts = premium_paying_term_config.get('ppt_pos_counts', {})
        ppt_neg_counts = premium_paying_term_config.get('ppt_neg_counts', {})

        premium_paying_ppt_rules = PPT_RULES
        per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # check for 'different count' mode
        ppt_enabled = premium_paying_term_config.get('ppt_enabled', {}) # check for 'same count' mode

        for ppt_name in PPT_NAME:
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            if per_ppt_mode:
                pos_count = int(ppt_pos_counts.get(ppt_name, 0))
                neg_count = int(ppt_neg_counts.get(ppt_name, 0))
            elif ppt_enabled.get(ppt_name, False):
                pos_count = epic_counts.get(target_rule, {}).get('positive', 0)
                neg_count = epic_counts.get(target_rule, {}).get('negative', 0)
            else:
                continue
            
            # Prepare scenario message based on PPT type
            if ppt_name == "Regular Pay":
                min_ppt, max_ppt = premium_paying_ppt_rules[ppt_name]['coverage_year_range'](0, 0, 10)
                message = SCENARIO_MAP['PremiumPayingTerm'](ppt_name, min_ppt=min_ppt, max_ppt=max_ppt)
            elif pos_count > 0 or neg_count > 0:
                ppt_limit = premium_paying_ppt_rules[ppt_name]['charge_year'](0)
                message = SCENARIO_MAP['PremiumPayingTerm'](ppt_name, ppt_limit=ppt_limit)
            # Positive cases for this PPT
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
                # if ppt_name == "Limited Pay (Pay till age 60)" and positive_age >= 55:
                #     positive_age = 54
                charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, premium_paying_ppt_rules)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                    payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    message,
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
                    idx
                )
                scenarios.append({**common_data, **common_row})
            # Negative cases for this PPT
            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
                charge_year, coverage_year, maturity_year = get_out_of_range_charge_year(ppt_name, positive_age, premium_paying_ppt_rules)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                    payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    message,
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
                    idx
                )
                scenarios.append({**common_data, **common_row})

    # --- EPIC: SumAssuredValidation ---
    if 'SumAssuredValidation' in selected_epics:
        target_rule = 'SumAssuredValidation'
        sum_assured_validation_config = epic_counts.get(target_rule, {})

        PPTS_NAME = {"Single Pay", "Others"}
        for ppt_name in PPTS_NAME:
            pos_count = sum_assured_validation_config.get(ppt_name, {}).get('positive', 0)
            neg_count = sum_assured_validation_config.get(ppt_name, {}).get('negative', 0)
            if(ppt_name == "Single Pay"):
                # min_sum = sum_assured_validation_config.get(ppt_name, {}).get('min_val', 2500000)
                # max_sum = sum_assured_validation_config.get(ppt_name, {}).get('max_val', 5000000)
                min_sum, max_sum = PPT_RULES_TT2.get(ppt_name)
                message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum, max_sum=max_sum)

            # Positive cases for this PPT
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                if(ppt_name != "Single Pay"):
                    # min_sum = sum_assured_validation_config.get(ppt_name, {}).get('min_val', 5000000)
                    # max_sum = 50000000 # assuming an upper limit for positive cases
                    ppt_name = random.choice([
                        "Regular Pay",
                        "Limited Pay (5 pay)",
                        "Limited Pay (7 pay)",
                        "Limited Pay (10 pay)",
                        "Limited Pay (15 pay)",
                        "Limited Pay (20 pay)",
                    ])
                    min_sum, max_sum = PPT_RULES_TT2.get(ppt_name)
                    message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum)
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
                # if ppt_name == "Limited Pay (Pay till age 60)" and positive_age >= 55:
                #     positive_age = 54
                charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age)
                discount_info = calculate_discounts(ppt_name)
                override_sum_assured = pick_sum_assured_value(min_sum, max_sum)
                discount_info = {**discount_info, "sumAssured": override_sum_assured}
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                    payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
                    CHECKING_NOTE_UPDATE_VALUE,
                    ppt_name,
                    message,
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
                    idx
                )
                scenarios.append({**common_data, **common_row})
            # Negative cases for this PPT
            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                if(ppt_name != "Single Pay"):
                    ppt_name = random.choice([
                        "Regular Pay",
                        "Limited Pay (5 pay)",
                        "Limited Pay (7 pay)",
                        "Limited Pay (10 pay)",
                        "Limited Pay (15 pay)",
                        "Limited Pay (20 pay)",
                    ])
                    # min_sum = sum_assured_validation_config.get(ppt_name, {}).get('min_val', 500000)
                    min_sum, max_sum = PPT_RULES_TT2.get(ppt_name)
                    message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum)
                    neg_assured_sum = ensure_thousand_multiple(min_sum - 1000) # just below min
                else:
                    neg_assured_sum = (
                        ensure_thousand_multiple(min_sum - 1000)
                        if (i % 2 == 0)
                        else ensure_thousand_multiple(max_sum + 1000)
                    ) # just below min or just above max
                    message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum, max_sum=max_sum) if(i % 2 == 0) else SCENARIO_MAP['SumAssuredValidation']("SP_neg_max", min_sum=min_sum, max_sum=max_sum)
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age)
                discount_info = calculate_discounts(ppt_name)
                discount_info = {**discount_info, "sumAssured": neg_assured_sum}
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                if(ppt_name == "Single Pay"):
                    payment_freq = 5
                if(payment_freq == 5 and ppt_name != "Single Pay"):
                    payment_freq = 1
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
                    CHECKING_NOTE_UPDATE_VALUE,
                    ppt_name,
                    message,
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
                    idx
                )
                scenarios.append({**common_data, **common_row})

    # --- EPIC: ExistingCustomerDiscount ---
    if 'ExistingCustomerDiscount' in selected_epics:
        target_rule = 'ExistingCustomerDiscount'
        counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        # Positive Cases
        for i in range(counts.get('positive', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            # min_maturity_age, max_maturity_age = rule['maturity_age_range']
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                EPIC_MAP[target_rule],
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
                payment_freq,
                discount_info,
                idx
            )
            scenarios.append({**common_data, **common_row})
        # Negative Cases
        for i in range(counts.get('negative', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            invalid_discount = random.choice([1, 3]) # Invalid frequencies
            discount_info["Total Discount"] = discount_info["Online Discount (%)"] + invalid_discount
            discount_info["Existing Customer Discount (%)"] = invalid_discount
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                EPIC_MAP[target_rule],
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
                idx
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: OnlinePlatformDiscountRP ---
    if 'OnlinePlatformDiscountRP' in selected_epics:
        target_rule = 'OnlinePlatformDiscountRP'
        counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        # Positive Cases
        for i in range(counts.get('positive', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            # min_maturity_age, max_maturity_age = rule['maturity_age_range']
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            
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
                payment_freq,
                discount_info,
                idx
            )
            scenarios.append({**common_data, **common_row})
        # Negative Cases
        for i in range(counts.get('negative', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = "Regular Pay"
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            invalid_discount = random.choice([11, 12]) # Invalid discounts
            discount_info["Total Discount"] = discount_info["Existing Customer Discount (%)"] + invalid_discount
            discount_info["Online Discount (%)"] = invalid_discount
            payment_freq = random.choice(PAYMENT_FREQUENCY)
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
                idx
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: OnlinePlatformDiscountLP ---
    if 'OnlinePlatformDiscountLP' in selected_epics:
        target_rule = 'OnlinePlatformDiscountLP'
        counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        # Positive Cases
        for i in range(counts.get('positive', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = random.choice([
                "Limited Pay (5 pay)",
                "Limited Pay (7 pay)",
                "Limited Pay (10 pay)",
                "Limited Pay (15 pay)",
                "Limited Pay (20 pay)",
            ])
            rule = PPT_RULES.get(ppt_name)
            # min_maturity_age, max_maturity_age = rule['maturity_age_range']
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            
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
                payment_freq,
                discount_info,
                idx
            )
            scenarios.append({**common_data, **common_row})
        # Negative Cases
        for i in range(counts.get('negative', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = random.choice([
                "Limited Pay (5 pay)",
                "Limited Pay (7 pay)",
                "Limited Pay (10 pay)",
                "Limited Pay (15 pay)",
                "Limited Pay (20 pay)",
            ])
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            invalid_discount = random.choice([11, 12]) # Invalid discounts
            discount_info["Total Discount"] = discount_info["Existing Customer Discount (%)"] + invalid_discount
            discount_info["Online Discount (%)"] = invalid_discount
            payment_freq = random.choice(PAYMENT_FREQUENCY)
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
                idx
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: TotalDiscountValidation ---
    if 'TotalDiscountValidation' in selected_epics:
        target_rule = 'TotalDiscountValidation'
        counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        # Positive Cases
        for i in range(counts.get('positive', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            # min_maturity_age, max_maturity_age = rule['maturity_age_range']
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            
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
                payment_freq,
                discount_info,
                idx
            )
            scenarios.append({**common_data, **common_row})
        # Negative Cases
        for i in range(counts.get('negative', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = "Regular Pay"
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            discount_info = calculate_discounts(ppt_name)
            discount_info["Total Discount"] = random.choice([18, 19, 20]) # Invalid total discount
            payment_freq = random.choice(PAYMENT_FREQUENCY)
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
                idx
            )
            scenarios.append({**common_data, **common_row})

    ########################
    # Rider Epics
    ########################
    # --- EPIC: EntryAge ---
    if 'EntryAge' in selected_epics_rider: # rider
        target_rule = 'EntryAge'
        entry_age_config = epic_counts_rider.get(target_rule, {}) #rider
        ppt_age_ranges = entry_age_config.get('ppt_age_ranges', {})
        ppt_pos_counts = entry_age_config.get('ppt_pos_counts', {})
        ppt_neg_counts = entry_age_config.get('ppt_neg_counts', {})
        # Update PPT_RULES entry_age_range for each PPT if provided
        entryage_ppt_rules = PPT_RULES

        # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
        per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
        ppt_enabled = entry_age_config.get('ppt_enabled', {}) # for same count mode
        # if ppt_age_ranges and per_ppt_mode:
        for ppt_name in PPT_NAME:
            min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
            if per_ppt_mode:
                pos_count = int(ppt_pos_counts.get(ppt_name, 0))
                neg_count = int(ppt_neg_counts.get(ppt_name, 0))
            elif ppt_enabled.get(ppt_name, False):
                pos_count = epic_counts_rider.get(target_rule, {}).get('positive', 0)
                neg_count = epic_counts_rider.get(target_rule, {}).get('negative', 0)
            else:
                continue
            # Positive cases for this PPT
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                idy = random.randint(0, 1) # rider
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
                # if ppt_name == "Limited Pay (Pay till age 60)" and positive_age >= 55:
                #     positive_age = 54
                charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, entryage_ppt_rules)
                # charge_year_rider, coverage_year_rider, maturity_year_rider = get_years("Rider AD", positive_age, PPT_RULES_RIDER) # rider, no positive_age
                # charge_year_rider = min(charge_year_rider, charge_year) # rider
                # maturity_year_rider = min(maturity_year_rider, maturity_year) # rider
                charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
                discount_info = calculate_discounts(ppt_name)
                ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"]) # rider
                payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
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
                    idx
                )
                rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider)
                scenarios.append({**common_data, **common_row, **rider_fields})
            # Negative cases for this PPT
            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                idy = random.randint(0, 1)
                negative_age = build_entry_age_negative(min_entry_age, max_entry_age, i, ppt_name)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, negative_age, entryage_ppt_rules)
                charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
                discount_info = calculate_discounts(ppt_name)
                ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"])
                payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
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
                    idx
                )
                rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider)
                scenarios.append({**common_data, **common_row, **rider_fields})

    # --- EPIC: PolicyTerm ---
    if 'PolicyTerm' in selected_epics_rider:
        target_rule = 'PolicyTerm'
        # counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        policy_term_config = epic_counts_rider.get(target_rule, {})
        ppt_age_ranges = policy_term_config.get('ppt_age_ranges', {})
        ppt_pos_counts = policy_term_config.get('ppt_pos_counts', {})
        ppt_neg_counts = policy_term_config.get('ppt_neg_counts', {})
        # Update PPT_RULES entry_age_range for each PPT if provided
        policy_term_ppt_rules = PPT_RULES
        # for ppt_name, (min_age, max_age) in ppt_age_ranges.items():
        #     if ppt_name in policy_term_ppt_rules:
        #         policy_term_ppt_rules[ppt_name]['coverage_year_range'] = (min_age, max_age)

        # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
        per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
        ppt_enabled = policy_term_config.get('ppt_enabled', {}) # for same count mode
        # if ppt_age_ranges and per_ppt_mode:
        for ppt_name in PPT_NAME:
            # min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
            if per_ppt_mode:
                pos_count = int(ppt_pos_counts.get(ppt_name, 0))
                neg_count = int(ppt_neg_counts.get(ppt_name, 0))
            elif ppt_enabled.get(ppt_name, False):
                pos_count = policy_term_config.get('positive', 0)
                neg_count = policy_term_config.get('negative', 0)
            else:
                continue
            # Positive Cases
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                idy = random.randint(0, 1) 
                # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
                rule = policy_term_ppt_rules.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                age = build_random_age(min_entry_age, max_entry_age)
                min_policy_term, max_policy_term = ppt_age_ranges.get(ppt_name)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, age, policy_term_ppt_rules)
                min_coverage_year_rider, max_coverage_year_rider = PPT_RULES_RIDER["Rider AD"]["coverage_year_range"](age)
                charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
                discount_info = calculate_discounts(ppt_name)
                ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"])
                payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule) + " - " + POLICY_TERM_NAMES[ppt_name],
                    CHECKING_NOTE_UPDATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_coverage_year_rider, max_coverage_year_rider),
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
                    payment_freq,
                    discount_info,
                    idx
                )
                rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
                scenarios.append({**common_data, **common_row, **rider_fields})
            # Negative Cases
            for i in range(neg_count):
                tuid_counter += 1
                # age = build_random_age(min_entry_age, max_entry_age)
                idx = random.randint(0, 2)
                idy = random.randint(0, 1)
                # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
                rule = policy_term_ppt_rules.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                age = build_random_age(min_entry_age, max_entry_age)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, age, policy_term_ppt_rules)
                charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
                coverage_year_rider = random.choice([4, 58]) # Invalid policy term
                maturity_year_rider = age + coverage_year_rider
                min_coverage_year_rider, max_coverage_year_rider = PPT_RULES_RIDER["Rider AD"]["coverage_year_range"](age)
                discount_info = calculate_discounts(ppt_name)
                ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"])
                payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule) + " - " + POLICY_TERM_NAMES[ppt_name],
                    CHECKING_NOTE_UPDATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_coverage_year_rider, max_coverage_year_rider),
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
                    idx
                )
                rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
                scenarios.append({**common_data, **common_row, **rider_fields})

    # --- EPIC: MaturityAge ---
    if 'MaturityAge' in selected_epics_rider:
        target_rule = 'MaturityAge'
        # counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        maturity_age_config = epic_counts_rider.get(target_rule, {})
        ppt_age_ranges = maturity_age_config.get('ppt_age_ranges', {})
        ppt_pos_counts = maturity_age_config.get('ppt_pos_counts', {})
        ppt_neg_counts = maturity_age_config.get('ppt_neg_counts', {})
        maturity_age_ppt_rules = PPT_RULES

        for ppt in PPT_NAME:
            rule = PPT_RULES
            rule[ppt]['maturity_age_range'] = ppt_age_ranges.get(ppt, rule[ppt]['maturity_age_range'])

        # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
        per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
        ppt_enabled = maturity_age_config.get('ppt_enabled', {}) # for same count mode
        # if ppt_age_ranges and per_ppt_mode:
        for ppt_name in PPT_NAME:
            # min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
            if per_ppt_mode:
                pos_count = int(ppt_pos_counts.get(ppt_name, 0))
                neg_count = int(ppt_neg_counts.get(ppt_name, 0))
            elif ppt_enabled.get(ppt_name, False):
                pos_count = epic_counts_rider.get(target_rule, {}).get('positive', 0)
                neg_count = epic_counts_rider.get(target_rule, {}).get('negative', 0)
            else:
                continue
            # Positive Cases
            for i in range(pos_count):
                tuid_counter += 1
                # age = build_random_age(min_entry_age, max_entry_age)
                idx = random.randint(0, 2)
                idy = random.randint(0, 1)
                ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                age = build_random_age(min_entry_age, max_entry_age)
                min_maturity_age_rider, max_maturity_age_rider = PPT_RULES_RIDER["Rider AD"]["maturity_age_range"]
                charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
                charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
                discount_info = calculate_discounts(ppt_name)
                ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"])
                payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
                
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_maturity_age_rider, max_maturity_age_rider),
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
                    payment_freq,
                    discount_info,
                    idx
                )
                rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
                scenarios.append({**common_data, **common_row, **rider_fields})
            # Negative Cases
            for i in range(neg_count):
                tuid_counter += 1
                # age = build_random_age(min_entry_age, max_entry_age)
                idx = random.randint(0, 2)
                idy = random.randint(0, 1)
                ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
                rule = PPT_RULES.get(ppt_name)
                min_entry_age, max_entry_age = rule['entry_age_range']
                age = build_random_age(min_entry_age, max_entry_age)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
                min_maturity_age_rider, max_maturity_age_rider = PPT_RULES_RIDER["Rider AD"]["maturity_age_range"]
                charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
                maturity_year_rider = 76
                coverage_year_rider = maturity_year_rider - age
                discount_info = calculate_discounts(ppt_name)
                ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"])
                payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    SCENARIO_MAP[target_rule](ppt_name, min_maturity_age_rider, max_maturity_age_rider),
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
                    idx
                )
                rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
                scenarios.append({**common_data, **common_row, **rider_fields})

    # --- EPIC: PaymentFrequency ---
    if 'PaymentFrequency' in selected_epics_rider:
        target_rule = 'PaymentFrequency'
        counts = epic_counts_rider.get(target_rule, {'positive': 0, 'negative': 0})
        # Positive Cases
        for i in range(counts.get('positive', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            idy = random.randint(0, 1)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            # min_maturity_age, max_maturity_age = rule['maturity_age_range']
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            # charge_year_rider, coverage_year_rider, maturity_year_rider = get_years("Rider AD", age, PPT_RULES_RIDER)
            # charge_year_rider = min(charge_year_rider, charge_year)
            # maturity_year_rider = min(maturity_year_rider, maturity_year)
            charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
            discount_info = calculate_discounts(ppt_name)
            ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"])
            payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
            
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
                payment_freq,
                discount_info,
                idx
            )
            rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
            scenarios.append({**common_data, **common_row, **rider_fields})
        # Negative Cases
        for i in range(counts.get('negative', 0)):
            tuid_counter += 1
            # age = build_random_age(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            idy = random.randint(0, 1)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            age = build_random_age(min_entry_age, max_entry_age)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
            # charge_year_rider, coverage_year_rider, maturity_year_rider = get_years("Rider AD", age, PPT_RULES_RIDER)
            # charge_year_rider = min(charge_year_rider, charge_year)
            # maturity_year_rider = min(maturity_year_rider, maturity_year)
            charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
            discount_info = calculate_discounts(ppt_name)
            ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"])
            # payment_freq = random.choice(PAYMENT_FREQUENCY)
            # invalid_freq = random.choice([6, 7]) # Invalid frequencies
            # paymentFreqStr = "invalid_freq"
            if(ppt_name == "Single Pay"):
                payment_freq = random.choice([1, 2, 3, 4]) # Invalid frequencies for Single Pay
            else:
                payment_freq = 5 # Invalid frequency for others
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
                idx
            )
            rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
            scenarios.append({**common_data, **common_row, **rider_fields})

    # --- EPIC: PremiumPayingTerm ---
    if 'PremiumPayingTerm' in selected_epics_rider:
        target_rule = 'PremiumPayingTerm'
        premium_paying_term_config = epic_counts_rider.get(target_rule, {})
        ppt_age_ranges = premium_paying_term_config.get('ppt_age_ranges', {})
        ppt_pos_counts = premium_paying_term_config.get('ppt_pos_counts', {})
        ppt_neg_counts = premium_paying_term_config.get('ppt_neg_counts', {})
        # Premium paying term adjustments are applied globally; use the module-level rules
        premium_paying_ppt_rules = PPT_RULES

        per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # check for 'different count' mode
        ppt_enabled = premium_paying_term_config.get('ppt_enabled', {}) # check for 'same count' mode
        # print(premium_paying_term_config)
        for ppt_name in PPT_NAME:
            
            # min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            if per_ppt_mode:
                pos_count = int(ppt_pos_counts.get(ppt_name, 0))
                neg_count = int(ppt_neg_counts.get(ppt_name, 0))
            elif ppt_enabled.get(ppt_name, False):
                pos_count = premium_paying_term_config.get('positive', 0)
                neg_count = premium_paying_term_config.get('negative', 0)
            else:
                continue
            # Prepare scenario message based on PPT type
            if ppt_name == "Regular Pay":
                min_ppt, max_ppt = premium_paying_ppt_rules[ppt_name]['coverage_year_range'](0, 0, 10)
                message = SCENARIO_MAP['PremiumPayingTerm'](ppt_name, min_ppt=min_ppt, max_ppt=max_ppt)
            elif pos_count > 0 or neg_count > 0:
                ppt_limit = premium_paying_ppt_rules[ppt_name]['charge_year'](0)
                message = SCENARIO_MAP['PremiumPayingTerm'](ppt_name, ppt_limit=ppt_limit)
            # Positive cases for this PPT
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                idy = random.randint(0, 1)
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
                # if ppt_name == "Limited Pay (Pay till age 60)" and positive_age >= 55:
                #     positive_age = 54
                charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, premium_paying_ppt_rules)
                charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year, apply_min_charge_floor=False)
                discount_info = calculate_discounts(ppt_name)
                ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"])
                payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    message,
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
                    idx
                )
                # Merge rider-specific fields
                rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider)
                scenarios.append({**common_data, **common_row, **rider_fields})
            # Negative cases for this PPT
            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                idy = random.randint(0, 1)
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
                charge_year, coverage_year, maturity_year = get_out_of_range_charge_year(ppt_name, positive_age, premium_paying_ppt_rules)
                charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year, apply_min_charge_floor=False)
                discount_info = calculate_discounts(ppt_name)
                ad_sum_assured = build_ad_sum_assured(discount_info["sumAssured"])
                payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
                    CHECKING_NOTE_CREATE_VALUE,
                    ppt_name,
                    message,
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
                    idx
                )
                rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
                scenarios.append({**common_data, **common_row, **rider_fields})

    # --- EPIC: SumAssuredValidation ---
    if 'SumAssuredValidation' in selected_epics_rider:
        target_rule = 'SumAssuredValidation'
        sum_assured_validation_config = epic_counts_rider.get(target_rule, {})
        counts = epic_counts_rider.get(target_rule, {'positive': 0, 'negative': 0})
        for i in range(counts.get('positive', 0)):
            tuid_counter += 1
            min_sum_assured, max_sum_assured = PPT_RULES_RIDER["Rider AD"]["sum_assured_range"]
            idx = random.randint(0, 2)
            idy = random.randint(0, 1)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age)
            charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
            # Adjust max_sum_assured for variant
            min_sum_assured, max_sum_assured = PPT_RULES_RIDER["Rider AD"]["sum_assured_range"]
            max_sum_assured = max_sum_assured * 3 if idy == 1 else max_sum_assured
            discount_info = calculate_discounts(ppt_name)
            max_multiplier = 3 if idy == 1 else 1
            ad_sum_assured = min(
                max_sum_assured,
                build_ad_sum_assured(discount_info["sumAssured"], max_multiplier=max_multiplier, min_value=min_sum_assured),
            )
            message = SCENARIO_MAP['SumAssuredValidation_Rider_max'](ppt_name, max_sum_assured) if (i % 2 == 0) else SCENARIO_MAP['SumAssuredValidation_Rider_min'](ppt_name, min_sum_assured)
            payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                EPIC_MAP[target_rule],
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                message,
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
                idx
            )
            rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
            scenarios.append({**common_data, **common_row, **rider_fields})
        # Negative cases for this PPT
        for i in range(counts.get('negative', 0)):
            tuid_counter += 1
            idx = random.randint(0, 2)
            idy = random.randint(0, 1)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            rule = PPT_RULES.get(ppt_name)
            min_entry_age, max_entry_age = rule['entry_age_range']
            positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age)
            charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
            min_sum_assured, max_sum_assured = PPT_RULES_RIDER["Rider AD"]["sum_assured_range"]
            max_sum_assured = max_sum_assured * 3 if idy == 1 else max_sum_assured
            # x = 3 if idy == 1 else 1
            # ad_sum_assured = min(max_sum_assured, random.randint(min_sum_assured, x * calculate_discounts(ppt_name)["sumAssured"]))
            neg_ad_sum_assured = (
                ensure_thousand_multiple(max_sum_assured + 1000)
                if (i % 2 == 0)
                else ensure_thousand_multiple(min_sum_assured - 1000)
            )
            message = SCENARIO_MAP['SumAssuredValidation_Rider_max'](ppt_name, max_sum_assured) if (i % 2 == 0) else SCENARIO_MAP['SumAssuredValidation_Rider_min'](ppt_name, min_sum_assured)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                EPIC_MAP[target_rule],
                CHECKING_NOTE_UPDATE_VALUE,
                ppt_name,
                message,
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
                idx
            )
            rider_fields = build_rider_fields(neg_ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
            scenarios.append({**common_data, **common_row, **rider_fields})

    # Convert to DataFrame
    df = pd.DataFrame(scenarios)
    if not df.empty:
        df = df.reindex(columns=column_order)
            
    return df

