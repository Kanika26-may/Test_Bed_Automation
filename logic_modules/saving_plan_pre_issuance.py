from logic_modules.lifecycle_plan_base import build_lifecycle_module_exports

globals().update(
    build_lifecycle_module_exports(
        base_module_name="saving_plan",
        module_name="Saving Plan",
        lifecycle_stage="pre issuance",
    )
)

# logic_module.py

import sys
import logging
import pandas as pd
import random 
import numpy as np
from datetime import date, datetime
import copy
import traceback

# import logging
# logging.basicConfig(level=logging.DEBUG)
# logging.debug("Debugging is enabled")

#Global declarations 
MIN_ENTRY_AGE = 18
MAX_ENTRY_AGE = 65
PRODUCT_CODE = '138N122V01'

GENDER = ['Male', 'Female']
SMOKING = ['Smoker', 'Non Smoker']
policy_holder_location = ['MH', 'KA'] 
insurer_location = ['MH', 'KA']

EXISTING_CUSTOMER_DISCOUNT = [0, 20]
SUM_ASSURED = [1000000, 5000000, 10000000, 20000000]
PAYMENT_FREQUENCY = [1, 2, 3, 4] # Annual, Half-Yearly, Quarterly, Monthly
PAYMENT_FREQUENCY_STR = {1: 'Annual', 2: 'Half-Yearly', 3: 'Quarterly', 4: 'Monthly'}

YES_NO_OPTIONS = ['Yes', 'No']
PLAN_OPTIONS = ['CS_I', 'CS_HSI', 'CS_SI', 'CS_LSI']
PLAN_OPTION_MAX_ENTRY_AGE = {
    'CS_I': 50,
    'CS_HSI': 45,
    'CS_SI': 45,
    'CS_LSI': 45,
}

PLAN_OPTION_MAX_MATURITY_AGE = {
    'CS_I': 67,
    'CS_HSI': 62,
    'CS_SI': 62,
    'CS_LSI': 62,
}

def get_entry_age_range_for_plan_option(plan_option, ppt_name="Regular Pay"):
    # Prefer values defined inside PPT_RULES under plan_options if present
    ppt = PPT_RULES.get(ppt_name, {})
    plan_opts = ppt.get('plan_options', {}) if isinstance(ppt, dict) else {}
    if plan_option in plan_opts and isinstance(plan_opts[plan_option], dict):
        return tuple(plan_opts[plan_option].get('entry_age_range', (MIN_ENTRY_AGE, MAX_ENTRY_AGE)))
    # Fallback to legacy constant mapping
    return MIN_ENTRY_AGE, PLAN_OPTION_MAX_ENTRY_AGE.get(plan_option, MAX_ENTRY_AGE)


def get_maturity_age_range_for_plan_option(plan_option, ppt_name="Regular Pay"):
    ppt = PPT_RULES.get(ppt_name, {})
    plan_opts = ppt.get('plan_options', {}) if isinstance(ppt, dict) else {}
    if plan_option in plan_opts and isinstance(plan_opts[plan_option], dict):
        return tuple(plan_opts[plan_option].get('maturity_age_range', (27, 62)))
    return 27, PLAN_OPTION_MAX_MATURITY_AGE.get(plan_option, 62)

CHILD_AGE_RANGE = (0, 21)
DEFERMENT_PERIOD_RANGE = (1, 5)
INCOME_PERIOD_DEFAULT = 10
INCOME_SHIELD_PERIOD_DEFAULT = 10
PAYOUT_FREQUENCY_DEFAULT = 'YEARLY'
AUTO_DEBIT_DEFAULT = ['Y', 'N']
INSTALL_PREMIUM_DEFAULT = 10000

PPT_VALID_CHARGE_YEARS = [8, 10, 12]         # PPT must be exactly 8, 10, or 12
INCOME_PERIOD_PPT8_VALID = [4, 5, 6]          # valid income periods for PPT 8
INCOME_PERIOD_PPT10_12_VALID = [4, 5, 6, 7]   # valid income periods for PPT 10 and 12
INCOME_SHIELD_VALID_PERIODS = [5, 10]          # valid income shield payout durations
BANDHAN_EMPLOYEE_OPTIONS = ['Yes', 'No']

MODULE_NAME = "Saving Plan" 
API_MODE_VALUE = "Base plan" 

INCEPTION_DATE_VALUE = "25/May/2026" #can be changed to current date
EXECUTE_VALUE = "N"
MEDICAL_INDI = ['Y', 'N']
CHECKING_NOTE_CREATE_VALUE = "Create"
CHECKING_NOTE_UPDATE_VALUE = "Create , Update"


EXPECTED_RESULT_MAP = {
    'Positive': 'System should allow to generate Premium and all fields should match to the offline BI',
    'Negative': 'System should throw error message and should not generate Premium'
}

PPT_NAME = ["Regular Pay"]

EPIC_MAP = {
    'PolicyTerm': 'Check for Policy Term',
    # 'EntryAge': 'Check for Minimum entry age for Life assured',
    'MinimumEntryAge': 'Check for Minimum entry age for Life assured for all plan options',
    'MaximumEntryAgePlanOption1': 'Check for Maximum entry age for Life assured for plan option 1',
    'MaximumEntryAgePlanOption2': 'Check for Maximum entry age for Life assured for plan option 2',
    'MaximumEntryAgePlanOption3': 'Check for Maximum entry age for Life assured for plan option 3',
    'MaximumEntryAgePlanOption4': 'Check for Maximum entry age for Life assured for plan option 4',
    'ChildEntryAge': 'Check for Minimum - Maximum entry age for Child',
    'MinimumMaturityAge': 'Check for Minimum Maturity age for Life assured',
    'MaximumMaturityAgePlanOption1': 'Check for Maximum Maturity age for Life assured for plan option 1',
    'MaximumMaturityAgePlanOption2': 'Check for Maximum Maturity age for Life assured for plan option 2',
    'MaximumMaturityAgePlanOption3': 'Check for Maximum Maturity age for Life assured for plan option 3',
    'MaximumMaturityAgePlanOption4': 'Check for Maximum Maturity age for Life assured for plan option 4',
    'PaymentFrequency': 'Check for Premium Frequency validation',
    'PremiumPayingTerm': 'Check for Premium Paying Term',
    'PremiumValidation': 'Check for Premium Validation',
    'IncomePeriodPPT8': 'Check for Income Period for PPT 8',
    'IncomePeriodPPT10And12': 'Check for Income Period for PPT 10 and 12',
    'DefermentPeriod': 'Check for Deferment Period',
    'SumAssuredValidation': 'Check for Sum Assured Validation',
    'IncomeShieldPayoutDuration': 'Check for Income shield payout duration',
    'IncomePayoutFrequency': 'Check for Income Payout Frequency',
    'AdvanceFeatureOption': 'Check for Advance feature option',
    'PlanOptions': 'Check for Plan options',
    'ExistingCustomer': 'Check for existing customer',
    'BandhanLifeEmployee': 'Check for bandhan life employee',
}
 


def get_api_operation(key):
    """Return the human readable API operation name for an epic key.
    """
    return EPIC_MAP.get(key) or key

POLICY_TERM_NAMES = {"Regular Pay": "RP"}

def premium_paying_term_message(ppt, min_ppt=None, max_ppt=None, ppt_limit=None, valid_ppTs=None):
    if valid_ppTs:
        return f"Premium Paying Term should be {', '.join(map(str, valid_ppTs))} years for {ppt}."
    # if ppt_limit is not None:
    #     return f"Premium Paying Term should be {ppt_limit} years for {ppt}."
    # elif min_ppt is not None and max_ppt is not None:
    #     return f"Premium Paying Term chosen should be between {min_ppt} and {max_ppt} years for {ppt}."

def sum_assured_validation_message(ppt, min_sum=None, max_sum=None):
    if min_sum is not None and max_sum is not None:
        return f"Base SA should be between {min_sum} and {max_sum} for {ppt}"
    return f"Min Base SA should not be less than {min_sum} for {ppt}"

SCENARIO_MAP = {
        'MinimumEntryAge': lambda ppt, min_entry_age, max_entry_age: f"The age of Life Assured should be greater than or equal to {min_entry_age} years for {ppt}",
        'PolicyTerm': lambda ppt, min_policy_term, max_policy_term: f"Policy term chosen should be between {min_policy_term} years to {max_policy_term} years for {ppt}",
        'MinimumMaturityAge': lambda ppt, min_maturity_age, max_maturity_age: f"The minimum maturity age of Life Assured should be greater than or equal to {min_maturity_age} years for {ppt}",
        'PaymentFrequency': f"To check for premium Frequency chosen should be Yearly, Half-Yearly, Quarterly & Monthly",
        'PremiumPayingTerm': premium_paying_term_message,
        'SumAssuredValidation': sum_assured_validation_message,
        'IncomePeriodPPT8': "Income period should be 4, 5 or 6 years for PPT 8",
        'IncomePeriodPPT10And12': "Income period should be 4, 5, 6 or 7 years for PPT 10 and 12",
        'IncomeShieldPayoutDuration': "Income shield payout duration should be 5 or 10 years",
    }

column_order = [
    "Execute", "TUID", "API_Mode", "API_Operation", "Checking_Note", "Test_Type", "Test Scenario", "Expected_Result",
    "inceptionDate","current_date", "InceptionBackdays", "policyHolderLocation", "insurerLocation",
    "LABirthdate","Child Birthdate", "LAAge","ChildAge", "LAGender",  "ChildGender","smoking", "Medicalindi",
    "planOption","productCode", "coverageYear",  "chargeYear","Coverage upto Age","DefermentPeriod", "incomePeriod",
    "advanceIncomeOption","chargePeriod","paymentFreq","payoutFrequency", "ddaMandateIndi", "Distribution Channel", "discountType", "Existing Customer", "IncomeShieldMonthlyInstalmentPeriod", "sumAssured", "autoDebit", "installPremium","BaseEMR_extraType", "BaseEMR_extraArith", "BaseEMR_extraPara", "BasePerMille_extraType", "BasePerMille_extraArith", "BasePerMille_extraPara",  "Maturity age","Standard Age Proof"
]



def calculate_discounts(ppt_type):
    # annualized_premium_range and sum_assured_range are stored in PPT_RULES and updated from UI
    ppt = PPT_RULES.get(ppt_type, {})
    ann_min, ann_max = ppt.get('annualized_premium_range', (36001, 500000))
    annualized_premium = random.randint(ann_min, ann_max)
    sum_assured = int(10.5 * annualized_premium)
    discount_type = random.choice(EXISTING_CUSTOMER_DISCOUNT)
    existing_customer_discount_calc = "Yes" if discount_type > 0 else "No"
    # if online_discount:
    #     tenantID = random.choice(TENANT_ID)
    # else:
    #     tenantID = "None"
    return {
        "Existing Customer Discount (%)": discount_type,
        "Discount Type": discount_type,
        "Existing Customer Discount Calculated": existing_customer_discount_calc,
        "sumAssured": sum_assured,
        "annualized_premium": annualized_premium,
    }

def compute_install_premium(annualized_premium, payment_freq):
    """installPremium = annualized_premium × frequency factor."""
    factors = {1: 1.0, 2: 0.512, 3: 0.259, 4: 0.087}
    return round(annualized_premium * factors.get(payment_freq, 1.0))

PPT_RULES = {
    "Regular Pay": {
        "entry_age_range": (18, 65),
        "charge_year": lambda age: random.choice([8, 10, 12]),   # PPT must be 8, 10, or 12
        "charge_year_range": (8, 12),                            # kept for out-of-range detection
        "valid_charge_years": [8, 10, 12],                       # discrete valid PPT values
        "coverage_year_range": lambda age: (9, max(9, 67 - age)),  # plan max maturity age = 67
        "maturity_year": lambda age, coverage_year: age + coverage_year,
        "maturity_age_range": (27, 67),
        "annualized_premium_range": (36000, 500000),  # valid annualized premium (>= 36000)
        "sum_assured_range": (378000, 5000000),        # valid sum assured (>= 378000 = 10.5 × 36000)
        "plan_options": {
            'CS_I': {
                'entry_age_range': (MIN_ENTRY_AGE, PLAN_OPTION_MAX_ENTRY_AGE['CS_I']),
                'maturity_age_range': (27, PLAN_OPTION_MAX_MATURITY_AGE['CS_I'])
            },
            'CS_HSI': {
                'entry_age_range': (MIN_ENTRY_AGE, PLAN_OPTION_MAX_ENTRY_AGE['CS_HSI']),
                'maturity_age_range': (27, PLAN_OPTION_MAX_MATURITY_AGE['CS_HSI'])
            },
            'CS_SI': {
                'entry_age_range': (MIN_ENTRY_AGE, PLAN_OPTION_MAX_ENTRY_AGE['CS_SI']),
                'maturity_age_range': (27, PLAN_OPTION_MAX_MATURITY_AGE['CS_SI'])
            },
            'CS_LSI': {
                'entry_age_range': (MIN_ENTRY_AGE, PLAN_OPTION_MAX_ENTRY_AGE['CS_LSI']),
                'maturity_age_range': (27, PLAN_OPTION_MAX_MATURITY_AGE['CS_LSI'])
            },
        },
    },
}




def resolve_charge_year(age, rule, deferment_period=None):
    # Discrete valid charge years take priority over range logic
    valid_years = rule.get('valid_charge_years')
    if valid_years:
        return random.choice(valid_years)
    charge_year_range = rule.get('charge_year_range')
    if not charge_year_range:
        return rule.get('charge_year_override', rule['charge_year'](age))
    min_charge, max_charge = charge_year_range
    if deferment_period is not None:
        maturity_age_max = rule.get('maturity_age_range', (27, 85))[1]
        max_charge = min(max_charge, maturity_age_max - age - deferment_period)
        if max_charge < min_charge:
            max_charge = min_charge
    return random.randint(min_charge, max_charge)


def get_years(ppt_name, age, deferment_period=None, PPT_RULES=PPT_RULES):
    rule = PPT_RULES.get(ppt_name)
    charge_year = resolve_charge_year(age, rule, deferment_period)
    # Determine coverage year range
    coverage_min, coverage_max = rule['coverage_year_range'](age)
    maturity_age_max = rule.get('maturity_age_range', (27, 85))[1]
    coverage_max = min(coverage_max, maturity_age_max - age)
    if deferment_period is not None:
        coverage_year = charge_year + deferment_period
    elif coverage_min > coverage_max:
        coverage_year = coverage_min
    else:
        coverage_year = random.randint(coverage_min, coverage_max)
    maturity_year = rule['maturity_year'](age, coverage_year)
    return charge_year, coverage_year, maturity_year

def get_out_of_range_coverage(ppt_name, age, deferment_period=None, PPT_RULES=PPT_RULES):
    rule = PPT_RULES.get(ppt_name)
    charge_year = resolve_charge_year(age, rule, deferment_period)
    coverage_min, coverage_max = rule['coverage_year_range'](age)
    # Force an out-of-range coverage year
    coverage_year = coverage_max + 1 if not random.choice([True, False]) else coverage_min - 1
    if deferment_period is not None:
        charge_year = coverage_year - deferment_period
    maturity_year = rule['maturity_year'](age, coverage_year)
    return charge_year, coverage_year, maturity_year, coverage_min, coverage_max

def get_out_of_range_maturity_year(ppt_name, age, deferment_period=None, PPT_RULES=PPT_RULES):
    rule = PPT_RULES.get(ppt_name)
    charge_year = resolve_charge_year(age, rule, deferment_period)
    maturity_min, maturity_max = rule['maturity_age_range']
    coverage_year = maturity_max - age + random.randint(1, 5)
    if deferment_period is not None:
        charge_year = coverage_year - deferment_period
    maturity_year = rule['maturity_year'](age, coverage_year)
    return  charge_year, coverage_year, maturity_year, maturity_min, maturity_max

def get_out_of_range_charge_year(ppt_name, age, deferment_period=None, PPT_RULES=PPT_RULES):
    rule = PPT_RULES.get(ppt_name)
    valid_years = rule.get('valid_charge_years')
    if valid_years:
        # Generate a value outside the discrete valid set (below min or above max)
        charge_year_out = min(valid_years) - 1 if random.choice([True, False]) else max(valid_years) + 1
    else:
        charge_year_range = rule.get('charge_year_range')
        if not charge_year_range:
            charge_year = rule.get('charge_year_override', rule['charge_year'](age))
            charge_year_out = charge_year - 1 if random.choice([True, False]) else charge_year + 1
        else:
            min_charge, max_charge = charge_year_range
            charge_year_out = min_charge - 1 if random.choice([True, False]) else max_charge + 1
    coverage_min, coverage_max = rule['coverage_year_range'](age)
    if deferment_period is not None:
        coverage_year = charge_year_out + deferment_period
    else:
        coverage_year = coverage_min if coverage_min <= coverage_max else coverage_max
    maturity_year = rule['maturity_year'](age, coverage_year)
    return charge_year_out, coverage_year, maturity_year

def get_out_of_range_maturity_year_for_range(ppt_name, age, maturity_min, maturity_max, deferment_period=None, max=None,    PPT_RULES=PPT_RULES):
    """Generate out-of-range maturity year for a specific maturity age range (outside maturity_min-maturity_max)."""
    rule = PPT_RULES.get(ppt_name)
    
    # Randomly choose to go below minimum or above maximum
    if max:
        # Generate maturity year above maximum
        coverage_year = maturity_max - age + random.randint(1, 5)
    else:
        # Generate maturity year below minimum
        coverage_year = maturity_min - age - random.randint(1, 5)
        if coverage_year < 0:
            coverage_year = 0
    
    if deferment_period is not None and deferment_period > 0:
        charge_year = coverage_year - deferment_period
        if charge_year < 0:
            charge_year = 0
    else:
        charge_year = resolve_charge_year(age, rule, deferment_period) if deferment_period is not None else rule.get('charge_year_override', rule['charge_year'](age))
    
    maturity_year = rule['maturity_year'](age, coverage_year)
    return charge_year, coverage_year, maturity_year, maturity_min, maturity_max

def make_constant_coverage_func(range_tuple):
    return lambda age, charge_year=None, _range_tuple=range_tuple: (_range_tuple[0], _range_tuple[1])


def apply_entry_age_overrides(epic_counts_local):
    entry_conf = epic_counts_local.get('EntryAge', {})
    plan_option = entry_conf.get('plan_option')
    for ppt_name, (min_age, max_age) in entry_conf.get('ppt_age_ranges', {}).items():
        if ppt_name not in PPT_RULES:
            continue
        if plan_option:
            ppt = PPT_RULES[ppt_name]
            ppt.setdefault('plan_options', {})
            ppt['plan_options'].setdefault(plan_option, {})
            ppt['plan_options'][plan_option]['entry_age_range'] = (min_age, max_age)
        else:
            PPT_RULES[ppt_name]['entry_age_range'] = (min_age, max_age)


def apply_policy_term_overrides(epic_counts_local):
    policy_conf = epic_counts_local.get('PolicyTerm', {})
    for ppt_name, (min_cov, max_cov) in policy_conf.get('ppt_age_ranges', {}).items():
        if ppt_name in PPT_RULES:
            PPT_RULES[ppt_name]['coverage_year_range'] = make_constant_coverage_func((min_cov, max_cov))


def apply_maturity_age_overrides(epic_counts_local):
    maturity_conf = epic_counts_local.get('MaturityAge', {})
    plan_option = maturity_conf.get('plan_option')
    for ppt_name, (min_mat, max_mat) in maturity_conf.get('ppt_age_ranges', {}).items():
        if ppt_name not in PPT_RULES:
            continue
        if plan_option:
            ppt = PPT_RULES[ppt_name]
            ppt.setdefault('plan_options', {})
            ppt['plan_options'].setdefault(plan_option, {})
            ppt['plan_options'][plan_option]['maturity_age_range'] = (min_mat, max_mat)
        else:
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
    """Sync SumAssuredValidation UI min/max → PPT_RULES sum_assured_range."""
    conf = epic_counts_local.get('SumAssuredValidation', {})
    min_sa = conf.get('min_val')
    max_sa = conf.get('max_val')
    if min_sa is not None or max_sa is not None:
        ppt = PPT_RULES.get('Regular Pay', {})
        cur_min, cur_max = ppt.get('sum_assured_range', (378001, 5000000))
        PPT_RULES['Regular Pay']['sum_assured_range'] = (
            int(min_sa) if min_sa is not None else cur_min,
            int(max_sa) if max_sa is not None else cur_max,
        )


def apply_premium_validation_overrides(epic_counts_local):
    """Sync PremiumValidation UI min/max → PPT_RULES annualized_premium_range."""
    conf = epic_counts_local.get('PremiumValidation', {})
    min_pv = conf.get('min_val')
    max_pv = conf.get('max_val')
    if min_pv is not None or max_pv is not None:
        ppt = PPT_RULES.get('Regular Pay', {})
        cur_min, cur_max = ppt.get('annualized_premium_range', (36001, 500000))
        # min must be strictly above the threshold (annualized premium > min_val)
        PPT_RULES['Regular Pay']['annualized_premium_range'] = (
            int(min_pv) + 1 if min_pv is not None else cur_min,
            int(max_pv) if max_pv is not None else cur_max,
        )


def _read_single_val(raw):
    """Extract an int from a single value or the min/max of a range tuple."""
    if isinstance(raw, (int, float)):
        return int(raw)
    if isinstance(raw, (list, tuple)) and len(raw) >= 1:
        return int(raw[0])
    return None


def apply_min_entry_age_overrides(epic_counts_local):
    """Sync MinimumEntryAge UI value → PPT_RULES plan_options entry_age_range min."""
    raw = epic_counts_local.get('MinimumEntryAge', {}).get('ppt_age_ranges', {}).get('Regular Pay')
    min_age = _read_single_val(raw)
    if min_age is None:
        return
    ppt = PPT_RULES.get('Regular Pay', {})
    # Update global entry_age_range min
    cur_min, cur_max = ppt.get('entry_age_range', (MIN_ENTRY_AGE, MAX_ENTRY_AGE))
    PPT_RULES['Regular Pay']['entry_age_range'] = (min_age, cur_max)
    # Update each plan option's entry_age_range min
    for opt_name, opt_data in ppt.get('plan_options', {}).items():
        o_min, o_max = opt_data.get('entry_age_range', (MIN_ENTRY_AGE, PLAN_OPTION_MAX_ENTRY_AGE.get(opt_name, MAX_ENTRY_AGE)))
        opt_data['entry_age_range'] = (min_age, o_max)


def apply_max_entry_age_overrides(epic_counts_local):
    """Sync MaximumEntryAgePlanOptionX UI values → PPT_RULES plan_options entry_age_range max."""
    plan_epic_map = {
        'MaximumEntryAgePlanOption1': 'CS_I',
        'MaximumEntryAgePlanOption2': 'CS_HSI',
        'MaximumEntryAgePlanOption3': 'CS_SI',
        'MaximumEntryAgePlanOption4': 'CS_LSI',
    }
    ppt = PPT_RULES.get('Regular Pay', {})
    plan_opts = ppt.setdefault('plan_options', {})
    for epic_key, plan_name in plan_epic_map.items():
        raw = epic_counts_local.get(epic_key, {}).get('ppt_age_ranges', {}).get('Regular Pay')
        if raw is None:
            continue
        max_age = int(raw) if isinstance(raw, (int, float)) else (int(raw[1]) if isinstance(raw, (list, tuple)) and len(raw) >= 2 else None)
        if max_age is None:
            continue
        plan_opts.setdefault(plan_name, {})
        o_min, _ = plan_opts[plan_name].get('entry_age_range', (MIN_ENTRY_AGE, PLAN_OPTION_MAX_ENTRY_AGE.get(plan_name, MAX_ENTRY_AGE)))
        plan_opts[plan_name]['entry_age_range'] = (o_min, max_age)
        PLAN_OPTION_MAX_ENTRY_AGE[plan_name] = max_age


def apply_min_maturity_age_overrides(epic_counts_local):
    """Sync MinimumMaturityAge UI value → PPT_RULES plan_options maturity_age_range min."""
    raw = epic_counts_local.get('MinimumMaturityAge', {}).get('ppt_age_ranges', {}).get('Regular Pay')
    min_mat = _read_single_val(raw)
    if min_mat is None:
        return
    ppt = PPT_RULES.get('Regular Pay', {})
    cur_min, cur_max = ppt.get('maturity_age_range', (27, 67))
    PPT_RULES['Regular Pay']['maturity_age_range'] = (min_mat, cur_max)
    for opt_name, opt_data in ppt.get('plan_options', {}).items():
        o_min, o_max = opt_data.get('maturity_age_range', (27, PLAN_OPTION_MAX_MATURITY_AGE.get(opt_name, 67)))
        opt_data['maturity_age_range'] = (min_mat, o_max)


def apply_max_maturity_age_overrides(epic_counts_local):
    """Sync MaximumMaturityAgePlanOptionX UI values → PPT_RULES plan_options maturity_age_range max."""
    plan_epic_map = {
        'MaximumMaturityAgePlanOption1': 'CS_I',
        'MaximumMaturityAgePlanOption2': 'CS_HSI',
        'MaximumMaturityAgePlanOption3': 'CS_SI',
        'MaximumMaturityAgePlanOption4': 'CS_LSI',
    }
    ppt = PPT_RULES.get('Regular Pay', {})
    plan_opts = ppt.setdefault('plan_options', {})
    for epic_key, plan_name in plan_epic_map.items():
        raw = epic_counts_local.get(epic_key, {}).get('ppt_age_ranges', {}).get('Regular Pay')
        if raw is None:
            continue
        max_mat = int(raw) if isinstance(raw, (int, float)) else (int(raw[1]) if isinstance(raw, (list, tuple)) and len(raw) >= 2 else None)
        if max_mat is None:
            continue
        plan_opts.setdefault(plan_name, {})
        o_min, _ = plan_opts[plan_name].get('maturity_age_range', (27, PLAN_OPTION_MAX_MATURITY_AGE.get(plan_name, 67)))
        plan_opts[plan_name]['maturity_age_range'] = (o_min, max_mat)
        PLAN_OPTION_MAX_MATURITY_AGE[plan_name] = max_mat


def apply_deferment_period_overrides(epic_counts_local):
    """Sync DefermentPeriod UI range → global DEFERMENT_PERIOD_RANGE."""
    global DEFERMENT_PERIOD_RANGE
    raw = epic_counts_local.get('DefermentPeriod', {}).get('ppt_age_ranges', {}).get('Regular Pay')
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        DEFERMENT_PERIOD_RANGE = (int(raw[0]), int(raw[1]))


def apply_child_entry_age_overrides(epic_counts_local):
    """Sync ChildEntryAge UI range → global CHILD_AGE_RANGE."""
    global CHILD_AGE_RANGE
    raw = epic_counts_local.get('ChildEntryAge', {}).get('ppt_age_ranges', {}).get('Regular Pay')
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        inner = raw[0]
        if isinstance(inner, (list, tuple)) and len(inner) == 2:
            CHILD_AGE_RANGE = (int(inner[0]), int(inner[1]))
        else:
            CHILD_AGE_RANGE = (int(raw[0]), int(raw[1]))
    elif isinstance(raw, (int, float)):
        CHILD_AGE_RANGE = (0, int(raw))


def update_ppt_rules_with_epic_counts(epic_counts_local, epic_counts_rider_local=None):
    if not epic_counts_local:
        return

    apply_entry_age_overrides(epic_counts_local)
    apply_min_entry_age_overrides(epic_counts_local)
    apply_max_entry_age_overrides(epic_counts_local)
    apply_policy_term_overrides(epic_counts_local)
    apply_min_maturity_age_overrides(epic_counts_local)
    apply_max_maturity_age_overrides(epic_counts_local)
    apply_maturity_age_overrides(epic_counts_local)
    apply_premium_paying_term_overrides(epic_counts_local)
    apply_sum_assured_overrides(epic_counts_local)
    apply_premium_validation_overrides(epic_counts_local)
    apply_deferment_period_overrides(epic_counts_local)
    apply_child_entry_age_overrides(epic_counts_local)


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
    return payment_freq


def build_case_age(min_age, max_age, iteration_index):
    if iteration_index % 2 == 0:
        return max(min_age, min(max_age - iteration_index, max_age))
    return min(max_age, min_age + iteration_index)


def build_entry_age_negative(min_age, max_age, iteration_index, ppt_name):
    # if iteration_index % 2 == 0:
    negative_age = round(random.uniform(max_age + 1, max_age + 10))
    # else:
    #     negative_age = round(random.uniform(1, min_age - 1))
    return negative_age

def build_child_fields(child_age=None, child_gender=None, current_year=None):
    if current_year is None:
        current_year = date.today().year
    if child_age is None:
        child_age = random.randint(CHILD_AGE_RANGE[0], CHILD_AGE_RANGE[1])
    if child_gender is None:
        child_gender = random.choice(GENDER)
    child_birthdate = f"01/Jan/{current_year - int(child_age)}"
    return child_birthdate, child_age, child_gender


def build_deferment_period(valid=True):
    if valid:
        return random.randint(DEFERMENT_PERIOD_RANGE[0], DEFERMENT_PERIOD_RANGE[1])
    return random.choice([DEFERMENT_PERIOD_RANGE[0] - 1, DEFERMENT_PERIOD_RANGE[1] + 1])


def resolve_simple_counts(epic_counts_local, target_rule):
    counts = epic_counts_local.get(target_rule, {})
    return int(counts.get('positive', 0) or 0), int(counts.get('negative', 0) or 0)


def build_common_row(tuid_counter, module_name, api_operation, checking_note, ppt_name, scenario_text, test_type,
                     expected_result, inception_date, policy_loc, insurer_loc, birth_year,
                     age, gender, smoking, medical_indi, product_code,
                     coverage_year, charge_year, maturity_year, payment_freq, discount_info,
                     idx, deferment_period=None, plan_option=None, child_age=None,
                     child_gender=None, income_period=None, advance_income_option=None,
                     payout_frequency=None, income_shield_period=None, auto_debit=None,
                     install_premium=None, existing_customer=None, bandhan_employee=None,
                     current_date_value=None, inception_backdays=None, pro_difference_value=None):
    """Return the common base row dict used across many test scenarios."""
    if current_date_value is None:
        current_date_value = date.today().strftime("%d/%b/%Y")
    if inception_backdays is None:
        try:
            current_date_obj = datetime.strptime(current_date_value, "%d/%b/%Y")
            inception_date_obj = datetime.strptime(inception_date, "%d/%b/%Y")
            inception_backdays = (current_date_obj - inception_date_obj).days
        except Exception:
            inception_backdays = 0
    if deferment_period is None:
        deferment_period = build_deferment_period(valid=True)
    if plan_option is None:
        plan_option = random.choice(PLAN_OPTIONS)
    child_birthdate, child_age, child_gender = build_child_fields(
        child_age=child_age,
        child_gender=child_gender,
    )
    if income_period is None:
        # Choose income period based on the PPT (charge_year)
        if charge_year == 8:
            income_period = random.choice(INCOME_PERIOD_PPT8_VALID)
        else:  # charge_year in [10, 12]
            income_period = random.choice(INCOME_PERIOD_PPT10_12_VALID)
    if advance_income_option is None:
        advance_income_option = random.choice(["True", "False"])
    if payout_frequency is None:
        payout_frequency = PAYOUT_FREQUENCY_DEFAULT
    if income_shield_period is None:
        income_shield_period = INCOME_SHIELD_PERIOD_DEFAULT
    if auto_debit is None:
        auto_debit = random.choice(AUTO_DEBIT_DEFAULT)
    if install_premium is None:
        ann_prem = discount_info.get('annualized_premium', INSTALL_PREMIUM_DEFAULT)
        install_premium = compute_install_premium(ann_prem, payment_freq)
    if isinstance(medical_indi, (list, tuple)):
        medical_indi = random.choice(medical_indi)
    elif medical_indi is None:
        medical_indi = random.choice(MEDICAL_INDI)
    if existing_customer is None:
        existing_customer = discount_info.get("Existing Customer Discount Calculated")
    if bandhan_employee is None:
        bandhan_employee = random.choice(BANDHAN_EMPLOYEE_OPTIONS)
    if pro_difference_value is None:
        pro_difference_value = ''
    

    return {
        'Execute': EXECUTE_VALUE,
        'TUID': f'TC_{module_name}_{tuid_counter:03d}',
        'API_Mode': API_MODE_VALUE,
        'API_Operation': api_operation,
        'Checking_Note': checking_note,
        'Test Scenario': scenario_text,
        'Test_Type': test_type,
        'Expected_Result': expected_result,
        'current_date': current_date_value,
        'inceptionDate': inception_date,
        'InceptionBackdays': inception_backdays,
        'policyHolderLocation': policy_loc,
        'insurerLocation': insurer_loc,
        'LABirthdate': f"01/Jan/{birth_year}",
        'LAAge': age,
        'LAGender': gender,
        'smoking': smoking,
        'Medicalindi': medical_indi,
        'Child Birthdate': child_birthdate,
        'ChildAge': child_age,
        'ChildGender': child_gender,
        'planOption': plan_option,
        'DefermentPeriod': deferment_period,
        'incomePeriod': income_period,
        'advanceIncomeOption': advance_income_option,
        'Advance Income': advance_income_option,
        'IncomeShieldMonthlyInstalmentPeriod': income_shield_period,
        'payoutFrequency': payout_frequency,
        'productCode': product_code,
        'coverageYear': coverage_year,
        'Coverage upto Age': maturity_year,
        'chargeYear': charge_year,
        'Maturity age': maturity_year,
        'chargePeriod': 2,
        'paymentFreq': PAYMENT_FREQUENCY_STR.get(payment_freq, str(payment_freq)) if payment_freq!=5 else "Single Pay",
        'autoDebit': auto_debit,
        'installPremium': install_premium,
        'Distribution Channel': 'Other than Direct/Online',
        'ddaMandateIndi': 'N',
        'discountType': discount_info.get("Existing Customer Discount (%)"),
        'Existing Customer': existing_customer,
        #'Bandhan Life Employee': bandhan_employee,
        'sumAssured': discount_info.get("sumAssured"),
        'proDifference_Value': pro_difference_value,   
    }


def generate_test_cases(epic_counts, selected_epics=None, epic_counts_rider=None, selected_epics_rider=None):
    if selected_epics is None:
        selected_epics = []
    scenarios = []
    tuid_counter = 0
    current_year = date.today().year
    current_date_value = date.today().strftime("%d/%b/%Y")

    # print("#"*50,"\n\niTerm Elite N logic module")
    # apply overrides in-place before generation
    try:
        update_ppt_rules_with_epic_counts(epic_counts or {}, epic_counts_rider or {})
    except Exception:
        # if anything goes wrong during applying user overrides, ensure generation continues with original rules
        logging.exception('Failed to apply PPT_RULES overrides from epic_counts')

    common_data = {
                'BaseEMR_extraType': 'Yes',
                'BaseEMR_extraArith': 8,
                'BaseEMR_extraPara': 0,
                'BasePerMille_extraType': 'Yes',
                'BasePerMille_extraArith': 1,
                'BasePerMille_extraPara': 0,
                'Standard Age Proof': 'Yes',
                'proDifference_Value': ''}
    
    # --- EPIC: EntryAge ---
    if 'MinimumEntryAge' in selected_epics:
        target_rule = 'MinimumEntryAge'
        entry_age_config = epic_counts.get(target_rule, {})
        ppt_age_ranges = entry_age_config.get('ppt_age_ranges', {})
        ppt_pos_counts = entry_age_config.get('ppt_pos_counts', {})
        ppt_neg_counts = entry_age_config.get('ppt_neg_counts', {})

        plan_option = entry_age_config.get('plan_option') or PLAN_OPTIONS[0]
        # min from MinimumEntryAge epic UI (single value in same-count mode)
        min_raw = ppt_age_ranges.get("Regular Pay")
        if isinstance(min_raw, (int, float)):
            plan_min_age = int(min_raw)
        elif isinstance(min_raw, (list, tuple)) and len(min_raw) == 2:
            plan_min_age = int(min_raw[0])
        else:
            plan_min_age = MIN_ENTRY_AGE
        # max from corresponding MaximumEntryAgePlanOption epic UI (single value)
        plan_opt_idx = PLAN_OPTIONS.index(plan_option) + 1
        max_epic_key = f'MaximumEntryAgePlanOption{plan_opt_idx}'
        max_raw = epic_counts.get(max_epic_key, {}).get('ppt_age_ranges', {}).get("Regular Pay")
        if isinstance(max_raw, (int, float)):
            plan_max_age = int(max_raw)
        elif isinstance(max_raw, (list, tuple)) and len(max_raw) == 2:
            plan_max_age = int(max_raw[1])
        else:
            plan_max_age = PLAN_OPTION_MAX_ENTRY_AGE.get(plan_option, MAX_ENTRY_AGE)

        entryage_ppt_rules = PPT_RULES
        # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
        per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
        ppt_enabled = entry_age_config.get('ppt_enabled', {}) # for same count mode
        # if ppt_age_ranges and per_ppt_mode:
        for ppt_name in PPT_NAME:
            min_entry_age, max_entry_age = plan_min_age, plan_max_age
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
                deferment_period = build_deferment_period(valid=True)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, deferment_period=deferment_period, PPT_RULES=entryage_ppt_rules)
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
                    random.choice(MEDICAL_INDI),
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    deferment_period=deferment_period,
                    plan_option=plan_option,
                    current_date_value=current_date_value
                )
                scenarios.append({**common_data, **common_row})
            # Negative cases for this PPT
            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                # if i % 2 == 0:
                #     negative_age = round(random.uniform(max_entry_age + 1, max_entry_age + 10))
                # else:
                negative_age = round(random.uniform(1, min_entry_age - 1))
                deferment_period = build_deferment_period(valid=True)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, negative_age, deferment_period=deferment_period, PPT_RULES=entryage_ppt_rules)
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
                    random.choice(MEDICAL_INDI),
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    deferment_period=deferment_period,
                    plan_option=plan_option,
                    current_date_value=current_date_value
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
                plan_option = random.choice(PLAN_OPTIONS)
                min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
                age = random.randint(min_entry_age, max_entry_age)
                min_policy_term, max_policy_term = ppt_age_ranges.get(ppt_name, (5, 85))
                deferment_period = build_deferment_period(valid=True)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period, PPT_RULES=policy_term_ppt_rules)
                # if(ppt_name != "Limited Pay (Pay till age 60)"):
                #     policy_term_ppt_rules[ppt_name]["coverage_year_range"] = lambda age: (min(min_policy_term, charge_year+5), min(max_policy_term, 85-age))
                # else:
                #     policy_term_ppt_rules[ppt_name]["coverage_year_range"] = lambda age, charge_year: (max(charge_year+5, min_policy_term), min(max_policy_term, 85-age))
                # Use coverage_year_range from PPT_RULES
                min_policy_term, max_policy_term = policy_term_ppt_rules[ppt_name]['coverage_year_range'](age)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    get_api_operation(target_rule),
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
                    random.choice(MEDICAL_INDI),
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    deferment_period=deferment_period,
                    plan_option=plan_option,
                    current_date_value=current_date_value
                )
                scenarios.append({**common_data, **common_row})
            # Negative Cases
            for i in range(neg_count):
                tuid_counter += 1
                # age = random.randint(min_entry_age, max_entry_age)
                idx = random.randint(0, 2)
                # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
                plan_option = random.choice(PLAN_OPTIONS)
                min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
                age = random.randint(min_entry_age, max_entry_age)
                deferment_period = build_deferment_period(valid=True)
                charge_year, coverage_year, maturity_year, coverage_min, coverage_max = get_out_of_range_coverage(ppt_name, age, deferment_period=deferment_period, PPT_RULES=policy_term_ppt_rules)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
                common_row = build_common_row(
                    tuid_counter,
                    MODULE_NAME,
                    EPIC_MAP[target_rule],
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
                    random.choice(MEDICAL_INDI),
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    deferment_period=deferment_period,
                    plan_option=plan_option,
                    current_date_value=current_date_value
                )
                scenarios.append({**common_data, **common_row})

    # --- EPIC: MaturityAge ---
    if 'MinimumMaturityAge' in selected_epics:
        target_rule = 'MinimumMaturityAge'
        # counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        maturity_age_config = epic_counts.get(target_rule, {})
        ppt_age_ranges = maturity_age_config.get('ppt_age_ranges', {})
        ppt_pos_counts = maturity_age_config.get('ppt_pos_counts', {})
        ppt_neg_counts = maturity_age_config.get('ppt_neg_counts', {})

        plan_option = maturity_age_config.get('plan_option') or PLAN_OPTIONS[0]
        plan_min_entry_age, plan_max_entry_age = get_entry_age_range_for_plan_option(plan_option)
        # min maturity from MinimumMaturityAge epic UI (single value in same-count mode)
        _mat_min_raw = ppt_age_ranges.get("Regular Pay")
        if isinstance(_mat_min_raw, (int, float)):
            plan_min_maturity_age = int(_mat_min_raw)
        elif isinstance(_mat_min_raw, (list, tuple)) and len(_mat_min_raw) == 2:
            plan_min_maturity_age = int(_mat_min_raw[0])
        else:
            plan_min_maturity_age = 27
        # max maturity from corresponding MaximumMaturityAgePlanOption epic UI
        plan_opt_idx = PLAN_OPTIONS.index(plan_option) + 1
        _max_mat_epic = f'MaximumMaturityAgePlanOption{plan_opt_idx}'
        _mat_max_raw = epic_counts.get(_max_mat_epic, {}).get('ppt_age_ranges', {}).get("Regular Pay")
        if isinstance(_mat_max_raw, (int, float)):
            plan_max_maturity_age = int(_mat_max_raw)
        else:
            plan_max_maturity_age = PLAN_OPTION_MAX_MATURITY_AGE.get(plan_option, 67)

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
                age = random.randint(plan_min_entry_age, plan_max_entry_age)
                min_maturity_age, max_maturity_age = plan_min_maturity_age, plan_max_maturity_age
                deferment_period = build_deferment_period(valid=True)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
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
                    current_year - int(age),
                    age,
                    random.choice(GENDER),
                    random.choice(SMOKING),
                    random.choice(MEDICAL_INDI),
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    deferment_period=deferment_period,
                    plan_option=plan_option,
                    current_date_value=current_date_value
                )
                scenarios.append({**common_data, **common_row})
            # Negative Cases
            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                age = random.randint(plan_min_entry_age, plan_max_entry_age)
                deferment_period = build_deferment_period(valid=True)
                charge_year, coverage_year, maturity_year, min_maturity_age, max_maturity_age = get_out_of_range_maturity_year_for_range(
                    ppt_name,
                    age,
                    plan_min_maturity_age,
                    plan_max_maturity_age,
                    deferment_period=deferment_period,
                    max=False
                )
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
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
                    random.choice(MEDICAL_INDI),
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    deferment_period=deferment_period,
                    plan_option=plan_option,
                    current_date_value=current_date_value
                )
                scenarios.append({**common_data, **common_row})

    # --- EPIC: MaximumEntryAgePlanOption1 ---
    if 'MaximumEntryAgePlanOption1' in selected_epics:
        target_rule = 'MaximumEntryAgePlanOption1'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        plan_option = PLAN_OPTIONS[0]
        # max from this epic's ppt_age_ranges (single value in same-count mode)
        _max_raw = epic_counts.get(target_rule, {}).get('ppt_age_ranges', {}).get(ppt_name)
        max_entry_age = int(_max_raw) if isinstance(_max_raw, (int, float)) else (int(_max_raw[1]) if isinstance(_max_raw, (list, tuple)) else PLAN_OPTION_MAX_ENTRY_AGE.get(plan_option, MAX_ENTRY_AGE))
        # min from MinimumEntryAge epic
        _min_raw = epic_counts.get('MinimumEntryAge', {}).get('ppt_age_ranges', {}).get(ppt_name)
        min_entry_age = int(_min_raw) if isinstance(_min_raw, (int, float)) else MIN_ENTRY_AGE
        scenario_text = f"The age of Life Assured should be less than or equal to {max_entry_age} years for {plan_option}"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            age = build_case_age(min_entry_age, max_entry_age, i)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            age = build_entry_age_negative(min_entry_age, max_entry_age, i, ppt_name)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: MaximumEntryAgePlanOption2 ---
    if 'MaximumEntryAgePlanOption2' in selected_epics:
        target_rule = 'MaximumEntryAgePlanOption2'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        plan_option = PLAN_OPTIONS[1]
        _max_raw = epic_counts.get(target_rule, {}).get('ppt_age_ranges', {}).get(ppt_name)
        max_entry_age = int(_max_raw) if isinstance(_max_raw, (int, float)) else (int(_max_raw[1]) if isinstance(_max_raw, (list, tuple)) else PLAN_OPTION_MAX_ENTRY_AGE.get(plan_option, MAX_ENTRY_AGE))
        _min_raw = epic_counts.get('MinimumEntryAge', {}).get('ppt_age_ranges', {}).get(ppt_name)
        min_entry_age = int(_min_raw) if isinstance(_min_raw, (int, float)) else MIN_ENTRY_AGE
        scenario_text = f"The age of Life Assured should be less than or equal to {max_entry_age} years for {plan_option}"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            age = build_case_age(min_entry_age, max_entry_age, i)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            age = build_entry_age_negative(min_entry_age, max_entry_age, i, ppt_name)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: MaximumEntryAgePlanOption3 ---
    if 'MaximumEntryAgePlanOption3' in selected_epics:
        target_rule = 'MaximumEntryAgePlanOption3'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        plan_option = PLAN_OPTIONS[2]
        _max_raw = epic_counts.get(target_rule, {}).get('ppt_age_ranges', {}).get(ppt_name)
        max_entry_age = int(_max_raw) if isinstance(_max_raw, (int, float)) else (int(_max_raw[1]) if isinstance(_max_raw, (list, tuple)) else PLAN_OPTION_MAX_ENTRY_AGE.get(plan_option, MAX_ENTRY_AGE))
        _min_raw = epic_counts.get('MinimumEntryAge', {}).get('ppt_age_ranges', {}).get(ppt_name)
        min_entry_age = int(_min_raw) if isinstance(_min_raw, (int, float)) else MIN_ENTRY_AGE
        scenario_text = f"The age of Life Assured should be less than or equal to {max_entry_age} years for {plan_option}"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            age = build_case_age(min_entry_age, max_entry_age, i)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            age = build_entry_age_negative(min_entry_age, max_entry_age, i, ppt_name)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: MaximumEntryAgePlanOption4 ---
    if 'MaximumEntryAgePlanOption4' in selected_epics:
        target_rule = 'MaximumEntryAgePlanOption4'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        plan_option = PLAN_OPTIONS[3]
        _max_raw = epic_counts.get(target_rule, {}).get('ppt_age_ranges', {}).get(ppt_name)
        max_entry_age = int(_max_raw) if isinstance(_max_raw, (int, float)) else (int(_max_raw[1]) if isinstance(_max_raw, (list, tuple)) else PLAN_OPTION_MAX_ENTRY_AGE.get(plan_option, MAX_ENTRY_AGE))
        _min_raw = epic_counts.get('MinimumEntryAge', {}).get('ppt_age_ranges', {}).get(ppt_name)
        min_entry_age = int(_min_raw) if isinstance(_min_raw, (int, float)) else MIN_ENTRY_AGE
        scenario_text = f"The age of Life Assured should be less than or equal to {max_entry_age} years for {plan_option}"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            age = build_case_age(min_entry_age, max_entry_age, i)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            age = build_entry_age_negative(min_entry_age, max_entry_age, i, ppt_name)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: ChildEntryAge ---
    if 'ChildEntryAge' in selected_epics:
        target_rule = 'ChildEntryAge'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        child_min, child_max = CHILD_AGE_RANGE
        scenario_text = f"Child age should be between {child_min} to {child_max} years"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            child_age = random.randint(child_min, child_max)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                child_age=child_age,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            child_age = child_min - 1 if i % 2 == 0 else child_max + random.randint(1, 5)
            if child_age < 0:
                child_age = child_max + random.randint(1, 5)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                child_age=child_age,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: MaximumMaturityAgePlanOption1 ---
    if 'MaximumMaturityAgePlanOption1' in selected_epics:
        target_rule = 'MaximumMaturityAgePlanOption1'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        plan_option = PLAN_OPTIONS[0]
        # max from this epic's ppt_age_ranges (single value in same-count mode)
        _mmax_raw = epic_counts.get(target_rule, {}).get('ppt_age_ranges', {}).get(ppt_name)
        maturity_max = int(_mmax_raw) if isinstance(_mmax_raw, (int, float)) else PLAN_OPTION_MAX_MATURITY_AGE.get(plan_option, 67)
        # min from MinimumMaturityAge epic UI
        _mmin_raw = epic_counts.get('MinimumMaturityAge', {}).get('ppt_age_ranges', {}).get(ppt_name)
        maturity_min = int(_mmin_raw) if isinstance(_mmin_raw, (int, float)) else 27
        scenario_text = f"The maturity age of Life Assured should be less than or equal to {maturity_max} years for {plan_option}"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year, maturity_min, maturity_max = get_out_of_range_maturity_year_for_range(
                ppt_name,
                age,
                maturity_min,
                maturity_max,
                deferment_period=deferment_period,
                max=True
            )
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: MaximumMaturityAgePlanOption2 ---
    if 'MaximumMaturityAgePlanOption2' in selected_epics:
        target_rule = 'MaximumMaturityAgePlanOption2'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        plan_option = PLAN_OPTIONS[1]
        _mmax_raw = epic_counts.get(target_rule, {}).get('ppt_age_ranges', {}).get(ppt_name)
        maturity_max = int(_mmax_raw) if isinstance(_mmax_raw, (int, float)) else PLAN_OPTION_MAX_MATURITY_AGE.get(plan_option, 62)
        _mmin_raw = epic_counts.get('MinimumMaturityAge', {}).get('ppt_age_ranges', {}).get(ppt_name)
        maturity_min = int(_mmin_raw) if isinstance(_mmin_raw, (int, float)) else 27
        scenario_text = f"The maturity age of Life Assured should be less than or equal to {maturity_max} years for {plan_option}"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year, maturity_min, maturity_max = get_out_of_range_maturity_year_for_range(
                ppt_name,
                age,
                maturity_min,
                maturity_max,
                deferment_period=deferment_period,
                max=True
            )
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: MaximumMaturityAgePlanOption3 ---
    if 'MaximumMaturityAgePlanOption3' in selected_epics:
        target_rule = 'MaximumMaturityAgePlanOption3'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        plan_option = PLAN_OPTIONS[2]
        _mmax_raw = epic_counts.get(target_rule, {}).get('ppt_age_ranges', {}).get(ppt_name)
        maturity_max = int(_mmax_raw) if isinstance(_mmax_raw, (int, float)) else PLAN_OPTION_MAX_MATURITY_AGE.get(plan_option, 62)
        _mmin_raw = epic_counts.get('MinimumMaturityAge', {}).get('ppt_age_ranges', {}).get(ppt_name)
        maturity_min = int(_mmin_raw) if isinstance(_mmin_raw, (int, float)) else 27
        scenario_text = f"The maturity age of Life Assured should be less than or equal to {maturity_max} years for {plan_option}"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year, maturity_min, maturity_max = get_out_of_range_maturity_year_for_range(
                ppt_name,
                age,
                maturity_min,
                maturity_max,
                deferment_period=deferment_period,
                max=True
            )
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: MaximumMaturityAgePlanOption4 ---
    if 'MaximumMaturityAgePlanOption4' in selected_epics:
        target_rule = 'MaximumMaturityAgePlanOption4'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        plan_option = PLAN_OPTIONS[3]
        _mmax_raw = epic_counts.get(target_rule, {}).get('ppt_age_ranges', {}).get(ppt_name)
        maturity_max = int(_mmax_raw) if isinstance(_mmax_raw, (int, float)) else PLAN_OPTION_MAX_MATURITY_AGE.get(plan_option, 62)
        _mmin_raw = epic_counts.get('MinimumMaturityAge', {}).get('ppt_age_ranges', {}).get(ppt_name)
        maturity_min = int(_mmin_raw) if isinstance(_mmin_raw, (int, float)) else 27
        scenario_text = f"The maturity age of Life Assured should be less than or equal to {maturity_max} years for {plan_option}"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year, maturity_min, maturity_max = get_out_of_range_maturity_year_for_range(
                ppt_name,
                age,
                maturity_min,
                maturity_max,
                deferment_period=deferment_period,
                max=True
            )
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: PremiumValidation ---
    if 'PremiumValidation' in selected_epics:
        target_rule = 'PremiumValidation'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        # annualized_premium_range is already updated from UI by apply_premium_validation_overrides
        _pv_min, _pv_max = PPT_RULES[ppt_name].get('annualized_premium_range', (36000, 500000))
        scenario_text = f"Installment premium should be {_pv_min} or above"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            # annualized_premium: valid (above threshold)
            ann_prem = random.randint(_pv_min, _pv_max)
            discount_info = {
                "Existing Customer Discount (%)": i%2,
                "Discount Type": 0,
                "Existing Customer Discount Calculated": "Yes" if i%2 else "No",
                "sumAssured": int(10.5 * ann_prem),
                "annualized_premium": ann_prem,
            }
            install_premium = compute_install_premium(ann_prem, payment_freq)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                install_premium=install_premium,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            # annualized_premium: invalid (below threshold)
            neg_ann_prem = random.randint(1000, max(1000, _pv_min - 2))
            neg_discount_info = {
                "Existing Customer Discount (%)": i%2,
                "Discount Type": 0,
                "Existing Customer Discount Calculated": "Yes" if i%2 else "No",
                "sumAssured": int(10.5 * neg_ann_prem),
                "annualized_premium": neg_ann_prem,
            }
            install_premium = compute_install_premium(neg_ann_prem, payment_freq)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                neg_discount_info,
                idx,
                deferment_period=deferment_period,
                install_premium=install_premium,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: IncomePeriodPPT8 ---
    if 'IncomePeriodPPT8' in selected_epics:
        target_rule = 'IncomePeriodPPT8'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        scenario_text = SCENARIO_MAP['IncomePeriodPPT8']
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            # Force PPT = 8 for this epic
            charge_year = 8
            coverage_year = charge_year + deferment_period
            maturity_year = age + coverage_year
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                income_period=random.choice(INCOME_PERIOD_PPT8_VALID),
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year = 8
            coverage_year = charge_year + deferment_period
            maturity_year = age + coverage_year
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                income_period=random.choice([3, 7, 8]),  # values outside INCOME_PERIOD_PPT8_VALID
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: IncomePeriodPPT10And12 ---
    if 'IncomePeriodPPT10And12' in selected_epics:
        target_rule = 'IncomePeriodPPT10And12'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        scenario_text = SCENARIO_MAP['IncomePeriodPPT10And12']
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            # Force PPT = 10 or 12 for this epic
            charge_year = random.choice([10, 12])
            coverage_year = charge_year + deferment_period
            maturity_year = age + coverage_year
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                income_period=random.choice(INCOME_PERIOD_PPT10_12_VALID),
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year = random.choice([10, 12])
            coverage_year = charge_year + deferment_period
            maturity_year = age + coverage_year
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                income_period=random.choice([3, 8, 9]),  # values outside INCOME_PERIOD_PPT10_12_VALID
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: DefermentPeriod ---
    if 'DefermentPeriod' in selected_epics:
        target_rule = 'DefermentPeriod'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        scenario_text = f"Deferment period should be between {DEFERMENT_PERIOD_RANGE[0]} to {DEFERMENT_PERIOD_RANGE[1]} years"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=False)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: IncomeShieldPayoutDuration ---
    if 'IncomeShieldPayoutDuration' in selected_epics:
        target_rule = 'IncomeShieldPayoutDuration'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        scenario_text = SCENARIO_MAP['IncomeShieldPayoutDuration']
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                income_shield_period=random.choice(INCOME_SHIELD_VALID_PERIODS),
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                income_shield_period=random.choice([1, 3, 7, 12]),  # values outside INCOME_SHIELD_VALID_PERIODS
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: IncomePayoutFrequency ---
    if 'IncomePayoutFrequency' in selected_epics:
        target_rule = 'IncomePayoutFrequency'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        scenario_text = "Income payout frequency should be YEARLY"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                payout_frequency=PAYOUT_FREQUENCY_DEFAULT,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                payout_frequency=random.choice(["Single Pay", "Monthly", "Quarterly", "Half-Yearly"]),  # values outside PAYOUT_FREQUENCY_DEFAULT       
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: AdvanceFeatureOption ---
    if 'AdvanceFeatureOption' in selected_epics:
        target_rule = 'AdvanceFeatureOption'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        scenario_text = "Advance income option should be True or False"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            advance_income_option = random.choice([True, False])
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                advance_income_option=advance_income_option,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                advance_income_option='Invalid',
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: PlanOptions ---
    if 'PlanOptions' in selected_epics:
        target_rule = 'PlanOptions'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        scenario_text = "Plan option should be in CS_I, CS_HSI, CS_SI, CS_LSI"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option='CS_Invalid',
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: ExistingCustomer ---
    if 'ExistingCustomer' in selected_epics:
        target_rule = 'ExistingCustomer'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        scenario_text = "Existing customer should be Yes or No"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            existing_customer = random.choice(YES_NO_OPTIONS)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                existing_customer=existing_customer,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                existing_customer=random.choice(['Unknown', '']),
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: BandhanLifeEmployee ---
    if 'BandhanLifeEmployee' in selected_epics:
        target_rule = 'BandhanLifeEmployee'
        pos_count, neg_count = resolve_simple_counts(epic_counts, target_rule)
        ppt_name = "Regular Pay"
        scenario_text = "Bandhan life employee should be Yes or No"
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            bandhan_employee = random.choice(BANDHAN_EMPLOYEE_OPTIONS)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Positive',
                EXPECTED_RESULT_MAP['Positive'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                bandhan_employee=bandhan_employee,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            common_row = build_common_row(
                tuid_counter,
                MODULE_NAME,
                get_api_operation(target_rule),
                CHECKING_NOTE_CREATE_VALUE,
                ppt_name,
                scenario_text,
                'Negative',
                EXPECTED_RESULT_MAP['Negative'],
                INCEPTION_DATE_VALUE,
                random.choice(policy_holder_location),
                random.choice(insurer_location),
                current_year - int(age),
                age,
                random.choice(GENDER),
                random.choice(SMOKING),
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                bandhan_employee=random.choice(['Unknown', '']),
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})

    # --- EPIC: PaymentFrequency ---
    if 'PaymentFrequency' in selected_epics:
        target_rule = 'PaymentFrequency'
        counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
        PAYMENT_FREQUENCY_U = epic_counts.get('PaymentFrequency', {}).get('payment_frequency_options') or PAYMENT_FREQUENCY
        # Positive Cases
        for i in range(counts.get('positive', 0)):
            tuid_counter += 1
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            # if 5 not in PAYMENT_FREQUENCY_U:
            #     filtered_PPT_NAME = [ppt for ppt in PPT_NAME if ppt != "Single Pay"]
            # else:
            #     filtered_PPT_NAME = PPT_NAME.copy()
            #ppt_name = filtered_PPT_NAME[(idx+i) % len(filtered_PPT_NAME)]
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY_U)
            
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
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            scenarios.append({**common_data, **common_row})
        # Negative Cases
        for i in range(counts.get('negative', 0)):
            tuid_counter += 1
            # age = random.randint(min_entry_age, max_entry_age)
            idx = random.randint(0, 2)
            ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            age = random.randint(min_entry_age, max_entry_age)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            # payment_freq = random.choice(PAYMENT_FREQUENCY)
            # invalid_freq = random.choice([6, 7]) # Invalid frequencies
            # paymentFreqStr = "invalid_freq"
            payment_freq = 5
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
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
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
            # Per-PPT age range uses the most restrictive plan option max entry age
            plan_option = random.choice(PLAN_OPTIONS)
            _ppt_min_ages = [get_entry_age_range_for_plan_option(p)[0] for p in PLAN_OPTIONS]
            _ppt_max_ages = [get_entry_age_range_for_plan_option(p)[1] for p in PLAN_OPTIONS]
            min_entry_age = min(_ppt_min_ages)
            max_entry_age = min(_ppt_max_ages)  # conservative: use smallest max
            # if per_ppt_mode:
            #     pos_count = int(ppt_pos_counts.get(ppt_name, 0))
            #     neg_count = int(ppt_neg_counts.get(ppt_name, 0))
            # elif ppt_enabled.get(ppt_name, False):
            pos_count = epic_counts.get(target_rule, {}).get('positive', 0)
            neg_count = epic_counts.get(target_rule, {}).get('negative', 0)
            # else:
            #     continue
            
            # Scenario message uses discrete valid PPT values
            message = SCENARIO_MAP['PremiumPayingTerm'](ppt_name, valid_ppTs=PPT_VALID_CHARGE_YEARS)
            # Positive cases for this PPT
            for i in range(pos_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
                deferment_period = build_deferment_period(valid=True)
                charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, deferment_period=deferment_period, PPT_RULES=premium_paying_ppt_rules)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
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
                    random.choice(MEDICAL_INDI),
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    deferment_period=deferment_period,
                    plan_option=plan_option,
                    current_date_value=current_date_value
                )
                scenarios.append({**common_data, **common_row})
            # Negative cases for this PPT
            for i in range(neg_count):
                tuid_counter += 1
                idx = random.randint(0, 2)
                positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
                deferment_period = build_deferment_period(valid=True)
                charge_year, coverage_year, maturity_year = get_out_of_range_charge_year(ppt_name, positive_age, deferment_period=deferment_period, PPT_RULES=premium_paying_ppt_rules)
                discount_info = calculate_discounts(ppt_name)
                payment_freq = random.choice(PAYMENT_FREQUENCY)
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
                    random.choice(MEDICAL_INDI),
                    PRODUCT_CODE,
                    coverage_year,
                    charge_year,
                    maturity_year,
                    payment_freq,
                    discount_info,
                    idx,
                    deferment_period=deferment_period,
                    plan_option=plan_option,
                    current_date_value=current_date_value
                )
                scenarios.append({**common_data, **common_row})

    # --- EPIC: SumAssuredValidation ---
    if 'SumAssuredValidation' in selected_epics:
        target_rule = 'SumAssuredValidation'
        sum_assured_validation_config = epic_counts.get(target_rule, {})
        ppt_name = "Regular Pay"
        pos_count = sum_assured_validation_config.get(ppt_name, {}).get('positive', sum_assured_validation_config.get('positive', 0))
        neg_count = sum_assured_validation_config.get(ppt_name, {}).get('negative', sum_assured_validation_config.get('negative', 0))
        # sum_assured_range already updated from UI by apply_sum_assured_overrides
        min_sum, max_sum = PPT_RULES[ppt_name].get('sum_assured_range', (378000, 5000000))
        message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum)

        # Positive cases
        for i in range(pos_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
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
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            extra_fields = {'sumAssured': random.randint(min_sum, max_sum)}
            scenarios.append({**common_data, **common_row, **extra_fields})

        # Negative cases
        for i in range(neg_count):
            tuid_counter += 1
            idx = random.randint(0, 2)
            plan_option = random.choice(PLAN_OPTIONS)
            min_entry_age, max_entry_age = get_entry_age_range_for_plan_option(plan_option)
            positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
            deferment_period = build_deferment_period(valid=True)
            charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, deferment_period=deferment_period)
            discount_info = calculate_discounts(ppt_name)
            payment_freq = random.choice(PAYMENT_FREQUENCY)
            neg_assured_sum = min_sum - 1000
            message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum)
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
                random.choice(MEDICAL_INDI),
                PRODUCT_CODE,
                coverage_year,
                charge_year,
                maturity_year,
                payment_freq,
                discount_info,
                idx,
                deferment_period=deferment_period,
                plan_option=plan_option,
                current_date_value=current_date_value
            )
            extra_fields = {'sumAssured': neg_assured_sum}
            scenarios.append({**common_data, **common_row, **extra_fields})

   
    # Convert to DataFrame
    df = pd.DataFrame(scenarios)
    if not df.empty:
        df = df.reindex(columns=column_order)
            
    return df


