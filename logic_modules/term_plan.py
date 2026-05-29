# # logic_module.py

# import sys
# import logging
# import pandas as pd
# import random 
# import numpy as np
# from datetime import date
# import copy
# import traceback

# # import logging
# # logging.basicConfig(level=logging.DEBUG)
# # logging.debug("Debugging is enabled")

# #Global declarations 
# MIN_ENTRY_AGE = 18
# MAX_ENTRY_AGE = 65
# PRODUCT_CODE = 'ARMP0000145'

# GENDER = ['Male', 'Female']
# SMOKING = ['Smoker', 'Non Smoker']
# policy_holder_location = ['MH', 'KA'] 
# insurer_location = ['MH', 'KA']

# ONLINE_DISCOUNT = [2, 15]
# EXISTING_CUSTOMER_DISCOUNT = [0, 2]
# LUMPSUM_PERCENT = [0, 100, 50]
# MONTHLY_PERCENTAGE = [100, 0, 50]
# DB_PAY_OPTION = ['Monthly', 'Lumpsum', 'Lumpsum + Monthly']
# DB_PAY_OPTION_C = ['Monthly Income Payout', 'Lumpsum Payment', 'Lumpsum Payment + Monthly Income Payout']
# INSTALLMENT_PERIOD = ['NA', '60', '120']
# SUM_ASSURED = [1000000, 5000000, 10000000, 20000000]
# PAYMENT_FREQUENCY = [1, 2, 3, 4, 5] # Annual, Half-Yearly, Quarterly, Monthly, Single
# PAYMENT_FREQUENCY_STR = {1: 'Annual', 2: 'Half-Yearly', 3: 'Quarterly', 4: 'Monthly', 5: 'Single'}

# MODULE_NAME = "Term Plan" 
# API_MODE_VALUE = "Base plan" 
# API_MODE_VALUE_RIDER = "Base Plan + AD"

# INCEPTION_DATE_VALUE = "1/Sept/2025" #can be changed to current date
# EXECUTE_VALUE = "N"
# MEDICAL_INDI = "Medical"
# CHECKING_NOTE_CREATE_VALUE = "Create"
# CHECKING_NOTE_UPDATE_VALUE = "Create , Update"

# PREMIUM_PAY_OPTION = "YEAR"
# CHANNEL = "Direct/Online" # can be other also
# TENANT_ID = ["SALES-APP", "POLICYBAZAAR"]
# AD_RIDER_VARIANT = ["Classic", "Premium"]
# AD_RIDER_VARIANT_C = ["Classic Option", "Premium Option"]

# EXPECTED_RESULT_MAP = {
#     'Positive': 'System should allow to generate Premium and all fields should match to the offline BI',
#     'Negative': 'System should throw error message and should not generate Premium'
# }

# PPT_NAME = ["Single Pay", "Limited Pay (5 pay)", "Limited Pay (10 pay)", "Limited Pay (15 pay)", "Limited Pay (Pay till age 60)", "Regular Pay"]

# EPIC_MAP = {
#     'EntryAge': 'Check for Minimum - Maximum entry age',
#     'PolicyTerm': 'Check for Policy Term',
#     'MaturityAge': 'Check for Minimum - Maximum maturity age',
#     'PaymentFrequency': 'Check for Premium Frequency validation',
#     'PremiumPayingTerm': 'Check for Premium Paying Term',
#     'SumAssuredValidation': 'Check for Sum Assured Validation',
#     # 'ExistingCustomerDiscount': 'Check for Existing Customer Discount validation',
#     # 'OnlinePlatformDiscountRP': 'Check for Online Platform Discount validation for Regular Pay',
#     # 'OnlinePlatformDiscountLP': 'Check for Online Platform Discount validation for Limited Pay',
#     # 'TotalDiscountValidation': 'Check for Total Discount validation',
# }

# EPIC_MAP_RIDER = {
#     'EntryAge': 'Check for Minimum - Maximum entry age',
#     'PolicyTerm': 'Check for Policy Term',
#     'MaturityAge': 'Check for Minimum - Maximum maturity age',
#     'PaymentFrequency': 'Check for Premium Frequency validation',
#     'PremiumPayingTerm': 'Check for Premium Paying Term',
#     'SumAssuredValidation': 'Check for Sum Assured Validation',
# }


# def get_api_operation(key):
#     """Return the human readable API operation name for an epic key.

#     Falls back to the rider map or the key itself if not found to avoid KeyError
#     when code references EPIC_MAP entries that were intentionally omitted.
#     """
#     return EPIC_MAP.get(key) or EPIC_MAP_RIDER.get(key) or key

# POLICY_TERM_NAMES = {"Single Pay": "SP", "Limited Pay (5 pay)": "LP5", "Limited Pay (10 pay)": "LP10", "Limited Pay (15 pay)": "LP15", "Limited Pay (Pay till age 60)": "LP60", "Regular Pay": "RP"}

# def premium_paying_term_message(ppt, min_ppt=None, max_ppt=None, ppt_limit=None):
#     if ppt_limit is not None:
#         return f"Premium Paying Term should be {ppt_limit} years for {ppt}."
#     elif min_ppt is not None and max_ppt is not None:
#         return f"Premium Paying Term chosen should be between {min_ppt} and {max_ppt} years for {ppt}."

# def sum_assured_validation_message(ppt, min_sum=None, max_sum=None):
#     if min_sum is not None and max_sum is not None and ppt == "SP_neg_max":
#         return f"Max Base SA should not be greater than {max_sum} for Single pay"
#     elif min_sum is not None and max_sum is not None:
#         return f"Min Base SA should not be less than {min_sum} for Single pay"
#     else:
#         return f"Min Base SA should not be less than {min_sum} for Regular & Limited pay (including Pay Till 60)"

# SCENARIO_MAP = {
#         'EntryAge': lambda ppt, min_entry_age, max_entry_age: f"The age of Life Assured should be between {min_entry_age} to {max_entry_age} years for {ppt}",
#         'PolicyTerm': lambda ppt, min_policy_term, max_policy_term: f"Policy term chosen should be between {min_policy_term} years to {max_policy_term} years for {ppt}",
#         'MaturityAge': lambda ppt, min_maturity_age, max_maturity_age: f"The maturity age of Life Assured should be between {min_maturity_age} to {max_maturity_age} years for {ppt}",
#         'PaymentFrequency': f"To check for premium Frequency chosen should be Single, Yearly, Half-Yearly, Quarterly & Monthly",
#         'PremiumPayingTerm': premium_paying_term_message,
#         'SumAssuredValidation': sum_assured_validation_message,
#         'ExistingCustomerDiscount': f"To check for Existing Customer Discount should be 0% or 2%",
#         'OnlinePlatformDiscountRP': f"To check for Online Platform Discount should be 0%, 2% or 10% for Regular Pay",
#         'OnlinePlatformDiscountLP': f"To check for Online Platform Discount should be 0%, 2% or 15% for Limited Pay",
#         'TotalDiscountValidation': f"To check for Total Discount should not be more than 17%",
#         'SumAssuredValidation_Rider_min': lambda ppt, min_sum=None: f"Min Rider SA should not be less than {min_sum} for Rider AD",
#         'SumAssuredValidation_Rider_max': lambda ppt, max_sum=None: f"Max Rider SA should not be greater than {max_sum} for Rider AD",
#     }

# column_order = [
#     "Execute", "TUID", "API_Mode", "API_Operation", "Checking_Note", "Test Scenario", "Test_Type", "Expected_Result",
#     "inceptionDate", "policyHolderLocation", "insurerLocation", "birthdate", "Age", "gender", "smoking", "Medicalindi",
#     "productCode", "coverageYear", "chargeYear", "Premium Payment Option", "premiumPayOption", "Coverage upto Age",
#     "chargePeriod", "paymentFreqW", "paymentFreq", "Channel", "ddaMandateIndi", "discountType", "Digital Discount Value",
#     "Digital Discount", "Existing Customer discount", "Existing Customer discount calc", "discountpercentage", "tenantID",
#     "sumAssured", "ADRider Opted", "ADsumAssured", "ADRiderVariant", "ADCoverageyear", "ADRiderChargeYear",
#     "Rider Coverage upto Age", "ComprehensiveCareB6", "CancerCareB1", "CardiacCareB2", "NeuroCareB5", "DisabilityCareB4",
#     "PremiumCareB7", "RenalCareB3", "DBpayOption", "LumpsumPercent", "MonthlyPercentage", "Income Instalment Period",
#     "BaseEMR_extraType", "BaseEMR_extraArith", "BaseEMR_extraPara", "BasePerMille_extraType", "BasePerMille_extraArith",
#     "BasePerMille_extraPara", "Standard Age Proof", "NSAP_extraType", "NSAP_extraArith", "NSAP_extraPara",
#     "RiderEMR_extraType", "RiderEMR_extraArith", "RiderEMR_extraPara", "RiderPerMille_extraType", "RiderPerMille_extraArith",
#     "RiderPerMille_extraPara", "KeyMan", "relationToHolder", "Difference_Value", "paymentFreqC", "DBpayOptionC",
#     "ADRiderVariantC"
# ]

# # Discount and sum assured calculation based on PPT type
# PPT_RULES_TT2 = {
#         "Single Pay": (2500000, 5000000),
#         "Limited Pay (5 pay)": (5000000, 20000000),
#         "Limited Pay (10 pay)": (5000000, 20000000),
#         "Limited Pay (15 pay)": (5000000, 20000000),
#         "Limited Pay (Pay till age 60)": (5000000, 20000000),
#         "Regular Pay": (5000000, 20000000)
#     }
# def calculate_discounts(ppt_type):

#     min_sa, max_sa = PPT_RULES_TT2[ppt_type]
#     sum_assured = random.randint(min_sa, max_sa)
#     if(ppt_type == "Regular Pay"):
#         if(sum_assured < 7500000):
#             online_discount = random.choice([4])
#         else:
#             online_discount = random.choice([10])
#     elif(ppt_type == "Single Pay"):
#         online_discount = random.choice([2])
#     else:
#         online_discount = random.choice([15])
#     existing_discount = random.choice(EXISTING_CUSTOMER_DISCOUNT)
#     total_discount = online_discount + existing_discount

#     discount_type = 20 if existing_discount and online_discount else 0
#     digital_platform = "Digital Platform" if online_discount > 0 else "Non Digital Platform"
#     existing_customer_discount_calc = "Yes" if existing_discount > 0 else "No"
#     if online_discount:
#         tenantID = random.choice(TENANT_ID)
#     else:
#         tenantID = "None"
#     return {
#         "Online Discount (%)": online_discount,
#         "Existing Customer Discount (%)": existing_discount,
#         "Total Discount": total_discount,
#         "Discount Type": discount_type,
#         "Digital Platform": digital_platform,
#         "Existing Customer Discount Calculated": existing_customer_discount_calc,
#         "tenantID": tenantID,
#         "sumAssured": sum_assured
#     }

# PPT_RULES = {
#     "Single Pay": {
#         "entry_age_range": (18, 65),
#         "charge_year": lambda age: 1,
#         "coverage_year_range": lambda age: (1, 5),
#         "maturity_year": lambda age, coverage_year: age + coverage_year,
#         "maturity_age_range": (19, 85),
#     },
#     "Limited Pay (5 pay)": {
#         "entry_age_range": (18, 65),
#         "charge_year": lambda age: 5,
#         "coverage_year_range": lambda age: (10, 85 - age),
#         "maturity_year": lambda age, coverage_year: age + coverage_year,
#         "maturity_age_range": (28, 85),
#     },
#     "Limited Pay (10 pay)": {
#         "entry_age_range": (18, 65),
#         "charge_year": lambda age: 10,
#         "coverage_year_range": lambda age: (15, 85 - age),
#         "maturity_year": lambda age, coverage_year: age + coverage_year,
#         "maturity_age_range": (33, 85),
#     },
#     "Limited Pay (15 pay)": {
#         "entry_age_range": (18, 65),
#         "charge_year": lambda age: 15,
#         "coverage_year_range": lambda age: (20, 85 - age),
#         "maturity_year": lambda age, coverage_year: age + coverage_year,
#         "maturity_age_range": (38, 85),
#     },
#     "Limited Pay (Pay till age 60)": {
#         "entry_age_range": (18, 55),
#         "charge_year": lambda age: 60 - age,
#         "charge_year_range": (5, 42),
#         "coverage_year_range": lambda age, charge_year: (charge_year + 5, 85 - age),
#         "maturity_year": lambda age, coverage_year: age + coverage_year,
#         "maturity_age_range": (65, 85),
#     },
#     "Regular Pay": {
#         "entry_age_range": (18, 65),
#         "charge_year": lambda age: random.randint(5, 85 - age),
#         "charge_year_range": (5, 67),
#         "coverage_year_range": lambda age: (5, 85 - age),
#         "maturity_year": lambda age, coverage_year: age + coverage_year,
#         "maturity_age_range": (23, 85),
#     },
# }

# PPT_RULES_RIDER = {
#     "Rider AD": {
#         "entry_age_range": (18, 65),
#         "charge_year": lambda age: random.randint(5, 57),
#         "coverage_year_range": lambda age: (5, 57),
#         "maturity_year": lambda age, coverage_year: age + coverage_year,
#         "maturity_age_range": (23, 75),
#         "sum_assured_range": (25000, 10000000)
#     },
# }

# def get_rider_years(ppt_name, age, PPT_RULES=PPT_RULES_RIDER):
#     rule = PPT_RULES.get(ppt_name)
#     charge_year = rule.get('charge_year_override', rule['charge_year'](age))
#     # Determine coverage year range
#     coverage_min, coverage_max = rule['coverage_year_range'](age)
#     # Ensure valid range
#     if coverage_min > coverage_max:
#         coverage_year = coverage_min
#     else:
#         coverage_year = random.randint(coverage_min, coverage_max)
#     maturity_year = rule['maturity_year'](age, coverage_year)
#     return charge_year, coverage_year, maturity_year

# def get_years(ppt_name, age, PPT_RULES=PPT_RULES):
#     rule = PPT_RULES.get(ppt_name)
#     charge_year = rule.get('charge_year_override', rule['charge_year'](age))
#     charge_year_max = 85-age # improve this logic later
#     if charge_year > charge_year_max:
#         charge_year = charge_year_max
#     # Determine coverage year range
#     if ppt_name == "Limited Pay (Pay till age 60)":
#         coverage_min, coverage_max = rule['coverage_year_range'](age, charge_year)
#     else:
#         coverage_min, coverage_max = rule['coverage_year_range'](age)
#     coverage_max = min(coverage_max, 85 - age)
#     # Ensure valid range
#     if coverage_min > coverage_max:
#         coverage_year = coverage_min
#     else:
#         coverage_year = random.randint(coverage_min, coverage_max)
#     # if ppt_name == "Regular Pay":
#     #     coverage_year = charge_year
#     maturity_year = rule['maturity_year'](age, coverage_year)
#     return charge_year, coverage_year, maturity_year

# def get_out_of_range_coverage(ppt_name, age, PPT_RULES=PPT_RULES):
#     rule = PPT_RULES.get(ppt_name)
#     charge_year = rule['charge_year'](age)
#     # Determine valid coverage year range
#     if ppt_name == "Limited Pay (Pay till age 60)":
#         coverage_min, coverage_max = rule['coverage_year_range'](age, charge_year)
#     else:
#         coverage_min, coverage_max = rule['coverage_year_range'](age)

#     # Force an out-of-range coverage year
#     coverage_year = coverage_max + 1 if ppt_name == "Single Pay" or not random.choice([True, False]) else coverage_min - 1
#     maturity_year = rule['maturity_year'](age, coverage_year)
#     return charge_year, coverage_year, maturity_year, coverage_min, coverage_max

# def get_out_of_range_maturity_year(ppt_name, age, PPT_RULES=PPT_RULES):
#     rule = PPT_RULES.get(ppt_name)
#     charge_year = rule['charge_year'](age)
#     maturity_min, maturity_max = rule['maturity_age_range']
#     # Determine coverage year range
#     if ppt_name == "Limited Pay (Pay till age 60)":
#         coverage_min, coverage_max = rule['coverage_year_range'](age, charge_year)
#     else:
#         coverage_min, coverage_max = rule['coverage_year_range'](age)

#     # --Can add below value for single pay--
#     coverage_year = maturity_max - age + random.randint(1,5)
#     maturity_year = rule['maturity_year'](age, coverage_year)
#     return  charge_year, coverage_year, maturity_year, maturity_min, maturity_max

# def get_out_of_range_charge_year(ppt_name, age, PPT_RULES=PPT_RULES):
#     rule = PPT_RULES.get(ppt_name)
#     charge_year_range = rule.get('charge_year_range')
#     if not charge_year_range:
#         charge_year = rule.get('charge_year_override', rule['charge_year'](age))
#         charge_year_out = charge_year - 1 if random.choice([True, False]) else charge_year + 1
#     else:
#         min_charge, max_charge = charge_year_range
#         # Randomly choose below or above range
#         charge_year_out = min_charge - 1 if random.choice([True, False]) else max_charge + 1
#     if ppt_name == "Single Pay":
#         charge_year_out = 2
#     # Determine coverage year range
#     if ppt_name == "Limited Pay (Pay till age 60)":
#         coverage_min, coverage_max = rule['coverage_year_range'](age, charge_year_out)
#     else:
#         coverage_min, coverage_max = rule['coverage_year_range'](age)

#     # Pick a valid coverage year within range
#     coverage_year = coverage_min if coverage_min <= coverage_max else coverage_max
#     maturity_year = rule['maturity_year'](age, coverage_year)

#     return charge_year_out, coverage_year, maturity_year


# def make_constant_coverage_func(range_tuple):
#     return lambda age, charge_year=None, _range_tuple=range_tuple: (_range_tuple[0], _range_tuple[1])


# def apply_entry_age_overrides(epic_counts_local):
#     entry_conf = epic_counts_local.get('EntryAge', {})
#     for ppt_name, (min_age, max_age) in entry_conf.get('ppt_age_ranges', {}).items():
#         if ppt_name in PPT_RULES:
#             PPT_RULES[ppt_name]['entry_age_range'] = (min_age, max_age)


# def apply_policy_term_overrides(epic_counts_local):
#     policy_conf = epic_counts_local.get('PolicyTerm', {})
#     for ppt_name, (min_cov, max_cov) in policy_conf.get('ppt_age_ranges', {}).items():
#         if ppt_name in PPT_RULES:
#             if ppt_name == "Limited Pay (Pay till age 60)":
#                 continue
#             PPT_RULES[ppt_name]['coverage_year_range'] = make_constant_coverage_func((min_cov, max_cov))


# def apply_maturity_age_overrides(epic_counts_local):
#     maturity_conf = epic_counts_local.get('MaturityAge', {})
#     for ppt_name, (min_mat, max_mat) in maturity_conf.get('ppt_age_ranges', {}).items():
#         if ppt_name in PPT_RULES:
#             PPT_RULES[ppt_name]['maturity_age_range'] = (min_mat, max_mat)


# def apply_premium_paying_term_overrides(epic_counts_local):
#     ppt_conf = epic_counts_local.get('PremiumPayingTerm', {})
#     for ppt_name, value in ppt_conf.get('ppt_age_ranges', {}).items():
#         if ppt_name == "Limited Pay (Pay till age 60)":
#             continue
#         if ppt_name not in PPT_RULES:
#             continue
#         try:
#             min_value, max_value = value
#         except Exception:
#             continue
#         if min_value == max_value:
#             PPT_RULES[ppt_name]['charge_year_override'] = min_value
#         else:
#             PPT_RULES[ppt_name]['charge_year_range'] = (min_value, max_value)
#             PPT_RULES[ppt_name]['charge_year'] = lambda age, value_range=(min_value, max_value): random.randint(value_range[0], value_range[1])


# def apply_sum_assured_overrides(epic_counts_local):
#     sum_assured_conf = epic_counts_local.get('SumAssuredValidation', {})
#     print("SumAssuredValidation overrides:", sum_assured_conf)

#     min_sa = sum_assured_conf.get("Single Pay", {}).get('min_val')
#     max_sa = sum_assured_conf.get("Single Pay", {}).get('max_val')
#     if max_sa is not None or min_sa is not None:
#         PPT_RULES_TT2["Single Pay"] = (min_sa, max_sa)

#     min_sa = sum_assured_conf.get("Others", {}).get('min_val')
#     max_sa = sum_assured_conf.get("Others", {}).get('max_val')
#     if max_sa is not None or min_sa is not None:
#         PPT_RULES_TT2["Limited Pay (5 pay)"] = (min_sa, max_sa)
#         PPT_RULES_TT2["Limited Pay (10 pay)"] = (min_sa, max_sa)
#         PPT_RULES_TT2["Limited Pay (15 pay)"] = (min_sa, max_sa)
#         PPT_RULES_TT2["Limited Pay (Pay till age 60)"] = (min_sa, max_sa)
#         PPT_RULES_TT2["Regular Pay"] = (min_sa, max_sa)


# def apply_rider_overrides(epic_counts_rider_local):
#     if not epic_counts_rider_local:
#         return

#     entry_conf_rider = epic_counts_rider_local.get('EntryAge', {})
#     for ppt_name, (min_age, max_age) in entry_conf_rider.get('ppt_age_ranges', {}).items():
#         if ppt_name in PPT_RULES_RIDER:
#             PPT_RULES_RIDER[ppt_name]['entry_age_range'] = (min_age, max_age)

#     maturity_conf_rider = epic_counts_rider_local.get('MaturityAge', {})
#     for ppt_name, (min_mat, max_mat) in maturity_conf_rider.get('ppt_age_ranges', {}).items():
#         if ppt_name in PPT_RULES_RIDER:
#             PPT_RULES_RIDER[ppt_name]['maturity_age_range'] = (min_mat, max_mat)


# def update_ppt_rules_with_epic_counts(epic_counts_local, epic_counts_rider_local=None):
#     if not epic_counts_local:
#         return

#     apply_entry_age_overrides(epic_counts_local)
#     apply_policy_term_overrides(epic_counts_local)
#     apply_maturity_age_overrides(epic_counts_local)
#     apply_premium_paying_term_overrides(epic_counts_local)
#     apply_sum_assured_overrides(epic_counts_local)
#     apply_rider_overrides(epic_counts_rider_local)


# def resolve_ppt_case_counts(target_rule, epic_config, epic_count_source, ppt_name):
#     ppt_pos_counts = epic_config.get('ppt_pos_counts', {})
#     ppt_neg_counts = epic_config.get('ppt_neg_counts', {})
#     per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME)
#     ppt_enabled = epic_config.get('ppt_enabled', {})

#     if per_ppt_mode:
#         return int(ppt_pos_counts.get(ppt_name, 0)), int(ppt_neg_counts.get(ppt_name, 0)), per_ppt_mode, ppt_enabled
#     if ppt_enabled.get(ppt_name, False):
#         shared_counts = epic_count_source.get(target_rule, {})
#         return shared_counts.get('positive', 0), shared_counts.get('negative', 0), per_ppt_mode, ppt_enabled
#     return None, None, per_ppt_mode, ppt_enabled


# def normalize_payment_frequency(ppt_name, payment_freq):
#     if ppt_name == "Single Pay":
#         return 5
#     if payment_freq == 5:
#         return 1
#     return payment_freq


# def build_case_age(min_age, max_age, iteration_index):
#     if iteration_index % 2 == 0:
#         return max(min_age, min(max_age - iteration_index, max_age))
#     return min(max_age, min_age + iteration_index)


# def build_entry_age_negative(min_age, max_age, iteration_index, ppt_name):
#     if iteration_index % 2 == 0:
#         negative_age = round(random.uniform(max_age + 1, max_age + 10))
#     else:
#         negative_age = round(random.uniform(1, min_age - 1))
#     if ppt_name == "Limited Pay (Pay till age 60)" and negative_age >= 55:
#         negative_age = round(random.uniform(1, min_age - 1))
#     return negative_age


# def build_rider_years(charge_year, coverage_year, maturity_year, apply_min_charge_floor=True):
#     rider_charge_year = max(5, charge_year) if apply_min_charge_floor else charge_year
#     rider_coverage_year = min(coverage_year, 57)
#     rider_maturity_year = min(maturity_year, 75)
#     return rider_charge_year, rider_coverage_year, rider_maturity_year


# def build_rider_fields(ad_sum_assured, rider_variant_index, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=None, payment_freq=None):
#     rider_fields = {
#         'API_Mode': API_MODE_VALUE_RIDER,
#         'ADRider Opted': 'Yes',
#         'ADsumAssured': ad_sum_assured,
#         'ADRiderVariant': AD_RIDER_VARIANT[rider_variant_index],
#         'ADCoverageyear': coverage_year_rider,
#         'ADRiderChargeYear': charge_year_rider,
#         'Rider Coverage upto Age': maturity_year_rider,
#         'ADRiderVariantC': AD_RIDER_VARIANT_C[rider_variant_index],
#     }
#     if idx is not None:
#         rider_fields['DBpayOption'] = DB_PAY_OPTION[idx]
#         rider_fields['DBpayOptionC'] = DB_PAY_OPTION_C[idx]
#     if payment_freq is not None and idx is not None:
#         rider_fields['paymentFreqC'] = PAYMENT_FREQUENCY_STR[payment_freq]
#     return rider_fields


# def build_common_row(tuid_counter, module_name, api_operation, checking_note, ppt_name, scenario_text, test_type,
#                      expected_result, inception_date, policy_loc, insurer_loc, birth_year,
#                      age, gender, smoking, medical_indi, product_code,
#                      coverage_year, charge_year, maturity_year, payment_freq, discount_info,
#                      idx):
#     """Return the common base row dict used across many test scenarios."""
#     return {
#         'Execute': EXECUTE_VALUE,
#         'TUID': f'TC_{module_name}_{tuid_counter:03d}',
#         'API_Mode': API_MODE_VALUE,
#         'API_Operation': api_operation,
#         'Checking_Note': checking_note,
#         'Test Scenario': scenario_text,
#         'Test_Type': test_type,
#         'Expected_Result': expected_result,
#         'inceptionDate': inception_date,
#         'policyHolderLocation': policy_loc,
#         'insurerLocation': insurer_loc,
#         'birthdate': f"01/Jan/{birth_year}",
#         'Age': age,
#         'gender': gender,
#         'smoking': smoking,
#         'Medicalindi': medical_indi,
#         'productCode': product_code,
#         'coverageYear': coverage_year,
#         'chargeYear': charge_year,
#         'Coverage upto Age': maturity_year,
#         'chargePeriod': 2,
#         'paymentFreq': payment_freq,
#         'ddaMandateIndi': 'N',
#         'Digital Discount Value': discount_info.get("Online Discount (%)"),
#         'Existing Customer discount': discount_info.get("Existing Customer Discount (%)"),
#         'discountpercentage': discount_info.get("Total Discount"),
#         'LumpsumPercent': LUMPSUM_PERCENT[idx],
#         'MonthlyPercentage': MONTHLY_PERCENTAGE[idx],
#         'Income Instalment Period': str(random.choice(INSTALLMENT_PERIOD)),
#         'sumAssured': discount_info.get("sumAssured"),
#         'Premium Payment Option': ppt_name,
#         'premiumPayOption': PREMIUM_PAY_OPTION,
#         'paymentFreqW': PAYMENT_FREQUENCY_STR.get(payment_freq, ''),
#         'Channel': CHANNEL,
#         'discountType': discount_info.get('Discount Type'),
#         'Digital Discount': discount_info.get("Digital Platform"),
#         'Existing Customer discount calc': discount_info.get("Existing Customer Discount Calculated"),
#         'tenantID': discount_info.get('tenantID'),
#         'ADRider Opted': 'No',
#         'ADsumAssured': 0,
#         'ADRiderVariant': 'Classic',
#         'ADCoverageyear': 0,
#         'ADRiderChargeYear': 0,
#         'Rider Coverage upto Age': 0,
#         'DBpayOption': DB_PAY_OPTION[idx],
#         'paymentFreqC': PAYMENT_FREQUENCY_STR.get(payment_freq, ''),
#         'DBpayOptionC': DB_PAY_OPTION_C[idx],
#         'ADRiderVariantC': 'Classic Option',
#     }


# def generate_test_cases(epic_counts, selected_epics=None, epic_counts_rider=None, selected_epics_rider=None):
#     scenarios = []
#     tuid_counter = 0
#     current_year = date.today().year

#     print("#"*50,"\n\niTerm Elite N logic module")
#     # apply overrides in-place before generation
#     try:
#         update_ppt_rules_with_epic_counts(epic_counts or {}, epic_counts_rider or {})
#     except Exception:
#         # if anything goes wrong during applying user overrides, ensure generation continues with original rules
#         logging.exception('Failed to apply PPT_RULES overrides from epic_counts')

#     common_data = {
#                 'ComprehensiveCareB6': 'No',
#                 'CancerCareB1': 'No',
#                 'CardiacCareB2': 'No',
#                 'NeuroCareB5': 'No',
#                 'DisabilityCareB4': 'No',
#                 'PremiumCareB7': 'No',
#                 'RenalCareB3': 'No',
#                 # 'payOption': 'No',             
#                 # 'planType': 0,                 
#                 'BaseEMR_extraType': 'A',      
#                 'BaseEMR_extraArith': 8,
#                 'BaseEMR_extraPara': 0,
#                 'BasePerMille_extraType': 'F',
#                 'BasePerMille_extraArith': 1,
#                 'BasePerMille_extraPara': 0,
#                 'Standard Age Proof': 'Yes',
#                 'NSAP_extraType': 'F',
#                 'NSAP_extraArith': 2,
#                 'NSAP_extraPara': 0,
#                 'RiderEMR_extraType': 'A',
#                 'RiderEMR_extraArith': 8,
#                 'RiderEMR_extraPara': 0,
#                 'RiderPerMille_extraType': 'F',
#                 'RiderPerMille_extraArith': 1,
#                 'RiderPerMille_extraPara': 0,
#                 # 'Proposal Number': '',
#                 'KeyMan': 'No',
#                 "relationToHolder": 'SELF',
#                 'Difference_Value': ''}
    
#     # --- EPIC: EntryAge ---
#     if 'EntryAge' in selected_epics:
#         target_rule = 'EntryAge'
#         entry_age_config = epic_counts.get(target_rule, {})
#         ppt_age_ranges = entry_age_config.get('ppt_age_ranges', {})
#         ppt_pos_counts = entry_age_config.get('ppt_pos_counts', {})
#         ppt_neg_counts = entry_age_config.get('ppt_neg_counts', {})

#         entryage_ppt_rules = PPT_RULES
#         # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
#         per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
#         ppt_enabled = entry_age_config.get('ppt_enabled', {}) # for same count mode
#         # if ppt_age_ranges and per_ppt_mode:
#         for ppt_name in PPT_NAME:
#             min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
#             if per_ppt_mode:
#                 pos_count = int(ppt_pos_counts.get(ppt_name, 0))
#                 neg_count = int(ppt_neg_counts.get(ppt_name, 0))
#             elif ppt_enabled.get(ppt_name, False):
#                 pos_count = epic_counts.get(target_rule, {}).get('positive', 0)
#                 neg_count = epic_counts.get(target_rule, {}).get('negative', 0)
#             else:
#                 continue
#             # Positive cases for this PPT
#             for i in range(pos_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)

#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, entryage_ppt_rules)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                     payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     get_api_operation(target_rule),
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_entry_age, max_entry_age),
#                     'Positive',
#                     EXPECTED_RESULT_MAP['Positive'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(positive_age),
#                     positive_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 scenarios.append({**common_data, **common_row})
#             # Negative cases for this PPT
#             for i in range(neg_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 if i % 2 == 0:
#                     negative_age = round(random.uniform(max_entry_age + 1, max_entry_age + 10))
#                 else:
#                     negative_age = round(random.uniform(1, min_entry_age - 1))
#                 if ppt_name == "Limited Pay (Pay till age 60)" and negative_age >= 55:
#                     negative_age = round(random.uniform(1, min_entry_age - 1))
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, negative_age, entryage_ppt_rules)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                     payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     get_api_operation(target_rule),
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_entry_age, max_entry_age),
#                     'Negative',
#                     EXPECTED_RESULT_MAP['Negative'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(negative_age),
#                     negative_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 scenarios.append({**common_data, **common_row})

#     # --- EPIC: PolicyTerm ---
#     if 'PolicyTerm' in selected_epics:
#         target_rule = 'PolicyTerm'
#         # counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
#         policy_term_config = epic_counts.get(target_rule, {})
#         ppt_age_ranges = policy_term_config.get('ppt_age_ranges', {})
#         ppt_pos_counts = policy_term_config.get('ppt_pos_counts', {})
#         ppt_neg_counts = policy_term_config.get('ppt_neg_counts', {})

#         policy_term_ppt_rules = PPT_RULES
#         # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
#         per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
#         ppt_enabled = policy_term_config.get('ppt_enabled', {}) # for same count mode
#         # if ppt_age_ranges and per_ppt_mode:
#         for ppt_name in PPT_NAME:
#             if per_ppt_mode:
#                 pos_count = int(ppt_pos_counts.get(ppt_name, 0))
#                 neg_count = int(ppt_neg_counts.get(ppt_name, 0))
#             elif ppt_enabled.get(ppt_name, False):
#                 pos_count = epic_counts.get(target_rule, {}).get('positive', 0)
#                 neg_count = epic_counts.get(target_rule, {}).get('negative', 0)
#             else:
#                 continue
#             # Positive Cases
#             for i in range(pos_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#                 rule = policy_term_ppt_rules.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 age = random.randint(min_entry_age, max_entry_age)
#                 min_policy_term, max_policy_term = ppt_age_ranges.get(ppt_name, (5, 85))
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, age, policy_term_ppt_rules)
#                 # if(ppt_name != "Limited Pay (Pay till age 60)"):
#                 #     policy_term_ppt_rules[ppt_name]["coverage_year_range"] = lambda age: (min(min_policy_term, charge_year+5), min(max_policy_term, 85-age))
#                 # else:
#                 #     policy_term_ppt_rules[ppt_name]["coverage_year_range"] = lambda age, charge_year: (max(charge_year+5, min_policy_term), min(max_policy_term, 85-age))
#                 # Use coverage_year_range from PPT_RULES
#                 if ppt_name == "Limited Pay (Pay till age 60)":
#                     min_policy_term, max_policy_term = rule['coverage_year_range'](age, charge_year)
#                 else:
#                     min_policy_term, max_policy_term = rule['coverage_year_range'](age)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                         payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     get_api_operation(target_rule) + " - " + POLICY_TERM_NAMES[ppt_name],
#                     CHECKING_NOTE_UPDATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_policy_term, max_policy_term),
#                     'Positive',
#                     EXPECTED_RESULT_MAP['Positive'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(age),
#                     age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 scenarios.append({**common_data, **common_row})
#             # Negative Cases
#             for i in range(neg_count):
#                 tuid_counter += 1
#                 # age = random.randint(min_entry_age, max_entry_age)
#                 idx = random.randint(0, 2)
#                 # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#                 rule = policy_term_ppt_rules.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 age = random.randint(min_entry_age, max_entry_age)
#                 charge_year, coverage_year, maturity_year, coverage_min, coverage_max = get_out_of_range_coverage(ppt_name, age, policy_term_ppt_rules)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                         payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule] + " - " + POLICY_TERM_NAMES[ppt_name],
#                     CHECKING_NOTE_UPDATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, coverage_min, coverage_max),
#                     'Negative',
#                     EXPECTED_RESULT_MAP['Negative'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(age),
#                     age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 scenarios.append({**common_data, **common_row})

#     # --- EPIC: MaturityAge ---
#     if 'MaturityAge' in selected_epics:
#         target_rule = 'MaturityAge'
#         # counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
#         maturity_age_config = epic_counts.get(target_rule, {})
#         ppt_age_ranges = maturity_age_config.get('ppt_age_ranges', {})
#         ppt_pos_counts = maturity_age_config.get('ppt_pos_counts', {})
#         ppt_neg_counts = maturity_age_config.get('ppt_neg_counts', {})

#         # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
#         per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
#         ppt_enabled = maturity_age_config.get('ppt_enabled', {}) # for same count mode
#         # if ppt_age_ranges and per_ppt_mode:
#         for ppt_name in PPT_NAME:
#             # min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
#             if per_ppt_mode:
#                 pos_count = int(ppt_pos_counts.get(ppt_name, 0))
#                 neg_count = int(ppt_neg_counts.get(ppt_name, 0))
#             elif ppt_enabled.get(ppt_name, False):
#                 pos_count = epic_counts.get(target_rule, {}).get('positive', 0)
#                 neg_count = epic_counts.get(target_rule, {}).get('negative', 0)
#             else:
#                 continue
#             # Positive Cases
#             for i in range(pos_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 rule = PPT_RULES.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 age = random.randint(min_entry_age, max_entry_age)
#                 min_maturity_age, max_maturity_age = rule['maturity_age_range']
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                         payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
                
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     get_api_operation(target_rule),
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_maturity_age, max_maturity_age),
#                     'Positive',
#                     EXPECTED_RESULT_MAP['Positive'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(age),
#                     age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 scenarios.append({**common_data, **common_row})
#             # Negative Cases
#             for i in range(neg_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 rule = PPT_RULES.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 age = random.randint(min_entry_age, max_entry_age)
#                 charge_year, coverage_year, maturity_year, min_maturity_age, max_maturity_age = get_out_of_range_maturity_year(ppt_name, age)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                         payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule],
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_maturity_age, max_maturity_age),
#                     'Negative',
#                     EXPECTED_RESULT_MAP['Negative'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(age),
#                     age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 scenarios.append({**common_data, **common_row})

#     # --- EPIC: PaymentFrequency ---
#     if 'PaymentFrequency' in selected_epics:
#         target_rule = 'PaymentFrequency'
#         counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
#         PAYMENT_FREQUENCY_U = epic_counts.get('PaymentFrequency', {}).get('payment_frequency_options')
#         # Positive Cases
#         for i in range(counts.get('positive', 0)):
#             tuid_counter += 1
#             idx = random.randint(0, 2)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             payment_freq = random.choice(PAYMENT_FREQUENCY_U)
#             if(ppt_name == "Single Pay"):
#                     payment_freq = 5
#             if(payment_freq == 5 and ppt_name != "Single Pay"):
#                 payment_freq = 1
            
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Positive',
#                 EXPECTED_RESULT_MAP['Positive'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})
#         # Negative Cases
#         for i in range(counts.get('negative', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             # payment_freq = random.choice(PAYMENT_FREQUENCY)
#             # invalid_freq = random.choice([6, 7]) # Invalid frequencies
#             # paymentFreqStr = "invalid_freq"
#             if(ppt_name == "Single Pay"):
#                 payment_freq = random.choice([1, 2, 3, 4]) # Invalid frequencies for Single Pay
#             else:
#                 payment_freq = 5 # Invalid frequency for others
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Negative',
#                 EXPECTED_RESULT_MAP['Negative'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})

#     # --- EPIC: PremiumPayingTerm ---
#     if 'PremiumPayingTerm' in selected_epics:
#         target_rule = 'PremiumPayingTerm'
#         premium_paying_term_config = epic_counts.get(target_rule, {})
#         ppt_age_ranges = premium_paying_term_config.get('ppt_age_ranges', {})
#         ppt_pos_counts = premium_paying_term_config.get('ppt_pos_counts', {})
#         ppt_neg_counts = premium_paying_term_config.get('ppt_neg_counts', {})

#         premium_paying_ppt_rules = PPT_RULES
#         per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # check for 'different count' mode
#         ppt_enabled = premium_paying_term_config.get('ppt_enabled', {}) # check for 'same count' mode

#         for ppt_name in PPT_NAME:
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             if per_ppt_mode:
#                 pos_count = int(ppt_pos_counts.get(ppt_name, 0))
#                 neg_count = int(ppt_neg_counts.get(ppt_name, 0))
#             elif ppt_enabled.get(ppt_name, False):
#                 pos_count = epic_counts.get(target_rule, {}).get('positive', 0)
#                 neg_count = epic_counts.get(target_rule, {}).get('negative', 0)
#             else:
#                 continue
            
#             # Prepare scenario message based on PPT type
#             if(ppt_name == "Limited Pay (Pay till age 60)" or ppt_name == "Regular Pay"):
#                 min_ppt, max_ppt = premium_paying_ppt_rules[ppt_name]['charge_year_range']
#                 message = SCENARIO_MAP['PremiumPayingTerm'](ppt_name, min_ppt=min_ppt, max_ppt=max_ppt)
#             elif pos_count > 0 or neg_count > 0:
#                 # If an explicit override isn't provided, fall back to a sensible default
#                 ppt_limit = premium_paying_ppt_rules[ppt_name]['charge_year'](0)
#                 # if ppt_limit is None:
#                 #     # try charge_year_range lower bound, or compute via charge_year callable
#                 #     ppt_limit = premium_paying_ppt_rules[ppt_name].get('charge_year_range')[0]
#                 message = SCENARIO_MAP['PremiumPayingTerm'](ppt_name, ppt_limit=ppt_limit)
#             # Positive cases for this PPT
#             for i in range(pos_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
#                 # if ppt_name == "Limited Pay (Pay till age 60)" and positive_age >= 55:
#                 #     positive_age = 54
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, premium_paying_ppt_rules)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                     payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule],
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     message,
#                     'Positive',
#                     EXPECTED_RESULT_MAP['Positive'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(positive_age),
#                     positive_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 scenarios.append({**common_data, **common_row})
#             # Negative cases for this PPT
#             for i in range(neg_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
#                 charge_year, coverage_year, maturity_year = get_out_of_range_charge_year(ppt_name, positive_age, premium_paying_ppt_rules)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                     payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule],
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     message,
#                     'Negative',
#                     EXPECTED_RESULT_MAP['Negative'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(positive_age),
#                     positive_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 scenarios.append({**common_data, **common_row})

#     # --- EPIC: SumAssuredValidation ---
#     if 'SumAssuredValidation' in selected_epics:
#         target_rule = 'SumAssuredValidation'
#         sum_assured_validation_config = epic_counts.get(target_rule, {})

#         PPTS_NAME = {"Single Pay", "Others"}
#         for ppt_name in PPTS_NAME:
#             pos_count = sum_assured_validation_config.get(ppt_name, {}).get('positive', 0)
#             neg_count = sum_assured_validation_config.get(ppt_name, {}).get('negative', 0)
#             if(ppt_name == "Single Pay"):
#                 # min_sum = sum_assured_validation_config.get(ppt_name, {}).get('min_val', 2500000)
#                 # max_sum = sum_assured_validation_config.get(ppt_name, {}).get('max_val', 5000000)
#                 min_sum, max_sum = PPT_RULES_TT2.get(ppt_name)
#                 message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum, max_sum=max_sum)

#             # Positive cases for this PPT
#             for i in range(pos_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 if(ppt_name != "Single Pay"):
#                     # min_sum = sum_assured_validation_config.get(ppt_name, {}).get('min_val', 5000000)
#                     # max_sum = 50000000 # assuming an upper limit for positive cases
#                     ppt_name = random.choice(["Regular Pay", "Limited Pay (5 pay)", "Limited Pay (10 pay)", "Limited Pay (15 pay)", "Limited Pay (Pay till age 60)"])
#                     min_sum, max_sum = PPT_RULES_TT2.get(ppt_name)
#                     message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum)
#                 rule = PPT_RULES.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
#                 # if ppt_name == "Limited Pay (Pay till age 60)" and positive_age >= 55:
#                 #     positive_age = 54
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                     payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule],
#                     CHECKING_NOTE_UPDATE_VALUE,
#                     ppt_name,
#                     message,
#                     'Positive',
#                     EXPECTED_RESULT_MAP['Positive'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(positive_age),
#                     positive_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 # override sumAssured for this scenario
#                 extra_fields = {'sumAssured': random.randint(min_sum, max_sum)}
#                 scenarios.append({**common_data, **common_row, **extra_fields})
#             # Negative cases for this PPT
#             for i in range(neg_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 if(ppt_name != "Single Pay"):
#                     ppt_name = random.choice(["Regular Pay", "Limited Pay (5 pay)", "Limited Pay (10 pay)", "Limited Pay (15 pay)", "Limited Pay (Pay till age 60)"])
#                     # min_sum = sum_assured_validation_config.get(ppt_name, {}).get('min_val', 500000)
#                     min_sum, max_sum = PPT_RULES_TT2.get(ppt_name)
#                     message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum)
#                     neg_assured_sum = min_sum - 1000 # just below min
#                 else:
#                     neg_assured_sum = min_sum - 1000 if (i % 2 == 0) else max_sum + 1000 # just below min or just above max
#                     message = SCENARIO_MAP['SumAssuredValidation'](ppt_name, min_sum=min_sum, max_sum=max_sum) if(i % 2 == 0) else SCENARIO_MAP['SumAssuredValidation']("SP_neg_max", min_sum=min_sum, max_sum=max_sum)
#                 rule = PPT_RULES.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age)
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = random.choice(PAYMENT_FREQUENCY)
#                 if(ppt_name == "Single Pay"):
#                     payment_freq = 5
#                 if(payment_freq == 5 and ppt_name != "Single Pay"):
#                     payment_freq = 1
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule],
#                     CHECKING_NOTE_UPDATE_VALUE,
#                     ppt_name,
#                     message,
#                     'Negative',
#                     EXPECTED_RESULT_MAP['Negative'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(positive_age),
#                     positive_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 extra_fields = {'sumAssured': neg_assured_sum}
#                 scenarios.append({**common_data, **common_row, **extra_fields})

#     # --- EPIC: ExistingCustomerDiscount ---
#     if 'ExistingCustomerDiscount' in selected_epics:
#         target_rule = 'ExistingCustomerDiscount'
#         counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
#         # Positive Cases
#         for i in range(counts.get('positive', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             # min_maturity_age, max_maturity_age = rule['maturity_age_range']
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             payment_freq = random.choice(PAYMENT_FREQUENCY)
            
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 EPIC_MAP[target_rule],
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Positive',
#                 EXPECTED_RESULT_MAP['Positive'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})
#         # Negative Cases
#         for i in range(counts.get('negative', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             invalid_discount = random.choice([1, 3]) # Invalid frequencies
#             discount_info["Total Discount"] = discount_info["Online Discount (%)"] + invalid_discount
#             discount_info["Existing Customer Discount (%)"] = invalid_discount
#             payment_freq = random.choice(PAYMENT_FREQUENCY)
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 EPIC_MAP[target_rule],
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Negative',
#                 EXPECTED_RESULT_MAP['Negative'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})

#     # --- EPIC: OnlinePlatformDiscountRP ---
#     if 'OnlinePlatformDiscountRP' in selected_epics:
#         target_rule = 'OnlinePlatformDiscountRP'
#         counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
#         # Positive Cases
#         for i in range(counts.get('positive', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             # min_maturity_age, max_maturity_age = rule['maturity_age_range']
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             payment_freq = random.choice(PAYMENT_FREQUENCY)
            
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Positive',
#                 EXPECTED_RESULT_MAP['Positive'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})
#         # Negative Cases
#         for i in range(counts.get('negative', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             ppt_name = "Regular Pay"
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             invalid_discount = random.choice([11, 12]) # Invalid discounts
#             discount_info["Total Discount"] = discount_info["Existing Customer Discount (%)"] + invalid_discount
#             discount_info["Online Discount (%)"] = invalid_discount
#             payment_freq = random.choice(PAYMENT_FREQUENCY)
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Negative',
#                 EXPECTED_RESULT_MAP['Negative'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})

#     # --- EPIC: OnlinePlatformDiscountLP ---
#     if 'OnlinePlatformDiscountLP' in selected_epics:
#         target_rule = 'OnlinePlatformDiscountLP'
#         counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
#         # Positive Cases
#         for i in range(counts.get('positive', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             ppt_name = random.choice(["Limited Pay (5 pay)", "Limited Pay (10 pay)", "Limited Pay (15 pay)", "Limited Pay (Pay till age 60)"])
#             rule = PPT_RULES.get(ppt_name)
#             # min_maturity_age, max_maturity_age = rule['maturity_age_range']
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             payment_freq = random.choice(PAYMENT_FREQUENCY)
            
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Positive',
#                 EXPECTED_RESULT_MAP['Positive'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})
#         # Negative Cases
#         for i in range(counts.get('negative', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             ppt_name = random.choice(["Limited Pay (5 pay)", "Limited Pay (10 pay)", "Limited Pay (15 pay)", "Limited Pay (Pay till age 60)"])
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             invalid_discount = random.choice([11, 12]) # Invalid discounts
#             discount_info["Total Discount"] = discount_info["Existing Customer Discount (%)"] + invalid_discount
#             discount_info["Online Discount (%)"] = invalid_discount
#             payment_freq = random.choice(PAYMENT_FREQUENCY)
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Negative',
#                 EXPECTED_RESULT_MAP['Negative'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})

#     # --- EPIC: TotalDiscountValidation ---
#     if 'TotalDiscountValidation' in selected_epics:
#         target_rule = 'TotalDiscountValidation'
#         counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
#         # Positive Cases
#         for i in range(counts.get('positive', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             # min_maturity_age, max_maturity_age = rule['maturity_age_range']
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             payment_freq = random.choice(PAYMENT_FREQUENCY)
            
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Positive',
#                 EXPECTED_RESULT_MAP['Positive'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})
#         # Negative Cases
#         for i in range(counts.get('negative', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             ppt_name = "Regular Pay"
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             discount_info = calculate_discounts(ppt_name)
#             discount_info["Total Discount"] = random.choice([18, 19, 20]) # Invalid total discount
#             payment_freq = random.choice(PAYMENT_FREQUENCY)
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Negative',
#                 EXPECTED_RESULT_MAP['Negative'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             scenarios.append({**common_data, **common_row})

#     ########################
#     # Rider Epics
#     ########################
#     # --- EPIC: EntryAge ---
#     if 'EntryAge' in selected_epics_rider: # rider
#         target_rule = 'EntryAge'
#         entry_age_config = epic_counts_rider.get(target_rule, {}) #rider
#         ppt_age_ranges = entry_age_config.get('ppt_age_ranges', {})
#         ppt_pos_counts = entry_age_config.get('ppt_pos_counts', {})
#         ppt_neg_counts = entry_age_config.get('ppt_neg_counts', {})
#         # Update PPT_RULES entry_age_range for each PPT if provided
#         entryage_ppt_rules = PPT_RULES

#         # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
#         per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
#         ppt_enabled = entry_age_config.get('ppt_enabled', {}) # for same count mode
#         # if ppt_age_ranges and per_ppt_mode:
#         for ppt_name in PPT_NAME:
#             min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
#             if per_ppt_mode:
#                 pos_count = int(ppt_pos_counts.get(ppt_name, 0))
#                 neg_count = int(ppt_neg_counts.get(ppt_name, 0))
#             elif ppt_enabled.get(ppt_name, False):
#                 pos_count = epic_counts_rider.get(target_rule, {}).get('positive', 0)
#                 neg_count = epic_counts_rider.get(target_rule, {}).get('negative', 0)
#             else:
#                 continue
#             # Positive cases for this PPT
#             for i in range(pos_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 idy = random.randint(0, 1) # rider
#                 positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
#                 # if ppt_name == "Limited Pay (Pay till age 60)" and positive_age >= 55:
#                 #     positive_age = 54
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, entryage_ppt_rules)
#                 # charge_year_rider, coverage_year_rider, maturity_year_rider = get_years("Rider AD", positive_age, PPT_RULES_RIDER) # rider, no positive_age
#                 # charge_year_rider = min(charge_year_rider, charge_year) # rider
#                 # maturity_year_rider = min(maturity_year_rider, maturity_year) # rider
#                 charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#                 ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"])) # rider
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule],
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_entry_age, max_entry_age),
#                     'Positive',
#                     EXPECTED_RESULT_MAP['Positive'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(positive_age),
#                     positive_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider)
#                 scenarios.append({**common_data, **common_row, **rider_fields})
#             # Negative cases for this PPT
#             for i in range(neg_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 idy = random.randint(0, 1)
#                 if i % 2 == 0:
#                     negative_age = round(random.uniform(max_entry_age + 1, max_entry_age + 10))
#                 else:
#                     negative_age = round(random.uniform(1, min_entry_age - 1))
#                 if ppt_name == "Limited Pay (Pay till age 60)" and negative_age >= 55:
#                     negative_age = round(random.uniform(1, min_entry_age - 1))
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, negative_age, entryage_ppt_rules)
#                 charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#                 ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"])) 
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule],
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_entry_age, max_entry_age),
#                     'Negative',
#                     EXPECTED_RESULT_MAP['Negative'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(negative_age),
#                     negative_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider)
#                 scenarios.append({**common_data, **common_row, **rider_fields})

#     # --- EPIC: PolicyTerm ---
#     if 'PolicyTerm' in selected_epics_rider:
#         target_rule = 'PolicyTerm'
#         # counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
#         policy_term_config = epic_counts_rider.get(target_rule, {})
#         ppt_age_ranges = policy_term_config.get('ppt_age_ranges', {})
#         ppt_pos_counts = policy_term_config.get('ppt_pos_counts', {})
#         ppt_neg_counts = policy_term_config.get('ppt_neg_counts', {})
#         # Update PPT_RULES entry_age_range for each PPT if provided
#         policy_term_ppt_rules = PPT_RULES
#         # for ppt_name, (min_age, max_age) in ppt_age_ranges.items():
#         #     if ppt_name in policy_term_ppt_rules:
#         #         policy_term_ppt_rules[ppt_name]['coverage_year_range'] = (min_age, max_age)

#         # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
#         per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
#         ppt_enabled = policy_term_config.get('ppt_enabled', {}) # for same count mode
#         # if ppt_age_ranges and per_ppt_mode:
#         for ppt_name in PPT_NAME:
#             # min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
#             if per_ppt_mode:
#                 pos_count = int(ppt_pos_counts.get(ppt_name, 0))
#                 neg_count = int(ppt_neg_counts.get(ppt_name, 0))
#             elif ppt_enabled.get(ppt_name, False):
#                 pos_count = policy_term_config.get('positive', 0)
#                 neg_count = policy_term_config.get('negative', 0)
#             else:
#                 continue
#             # Positive Cases
#             for i in range(pos_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 idy = random.randint(0, 1) 
#                 # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#                 rule = policy_term_ppt_rules.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 age = random.randint(min_entry_age, max_entry_age)
#                 min_policy_term, max_policy_term = ppt_age_ranges.get(ppt_name)
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, age, policy_term_ppt_rules)
#                 min_coverage_year_rider, max_coverage_year_rider = PPT_RULES_RIDER["Rider AD"]["coverage_year_range"](age)
#                 charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#                 ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"]))
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     get_api_operation(target_rule) + " - " + POLICY_TERM_NAMES[ppt_name],
#                     CHECKING_NOTE_UPDATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_coverage_year_rider, max_coverage_year_rider),
#                     'Positive',
#                     EXPECTED_RESULT_MAP['Positive'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(age),
#                     age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
#                 scenarios.append({**common_data, **common_row, **rider_fields})
#             # Negative Cases
#             for i in range(neg_count):
#                 tuid_counter += 1
#                 # age = random.randint(min_entry_age, max_entry_age)
#                 idx = random.randint(0, 2)
#                 idy = random.randint(0, 1)
#                 # ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#                 rule = policy_term_ppt_rules.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 age = random.randint(min_entry_age, max_entry_age)
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, age, policy_term_ppt_rules)
#                 charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#                 coverage_year_rider = random.choice([4, 58]) # Invalid policy term
#                 maturity_year_rider = age + coverage_year_rider
#                 min_coverage_year_rider, max_coverage_year_rider = PPT_RULES_RIDER["Rider AD"]["coverage_year_range"](age)
#                 ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"]))
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     get_api_operation(target_rule) + " - " + POLICY_TERM_NAMES[ppt_name],
#                     CHECKING_NOTE_UPDATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_coverage_year_rider, max_coverage_year_rider),
#                     'Negative',
#                     EXPECTED_RESULT_MAP['Negative'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(age),
#                     age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
#                 scenarios.append({**common_data, **common_row, **rider_fields})

#     # --- EPIC: MaturityAge ---
#     if 'MaturityAge' in selected_epics_rider:
#         target_rule = 'MaturityAge'
#         # counts = epic_counts.get(target_rule, {'positive': 0, 'negative': 0})
#         maturity_age_config = epic_counts_rider.get(target_rule, {})
#         ppt_age_ranges = maturity_age_config.get('ppt_age_ranges', {})
#         ppt_pos_counts = maturity_age_config.get('ppt_pos_counts', {})
#         ppt_neg_counts = maturity_age_config.get('ppt_neg_counts', {})
#         maturity_age_ppt_rules = PPT_RULES

#         for ppt in PPT_NAME:
#             rule = PPT_RULES
#             rule[ppt]['maturity_age_range'] = ppt_age_ranges.get(ppt, rule[ppt]['maturity_age_range'])

#         # If any PPT has a nonzero pos/neg count, treat as per-PPT mode
#         per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # for different count mode
#         ppt_enabled = maturity_age_config.get('ppt_enabled', {}) # for same count mode
#         # if ppt_age_ranges and per_ppt_mode:
#         for ppt_name in PPT_NAME:
#             # min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
#             if per_ppt_mode:
#                 pos_count = int(ppt_pos_counts.get(ppt_name, 0))
#                 neg_count = int(ppt_neg_counts.get(ppt_name, 0))
#             elif ppt_enabled.get(ppt_name, False):
#                 pos_count = epic_counts_rider.get(target_rule, {}).get('positive', 0)
#                 neg_count = epic_counts_rider.get(target_rule, {}).get('negative', 0)
#             else:
#                 continue
#             # Positive Cases
#             for i in range(pos_count):
#                 tuid_counter += 1
#                 # age = random.randint(min_entry_age, max_entry_age)
#                 idx = random.randint(0, 2)
#                 idy = random.randint(0, 1)
#                 ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#                 rule = PPT_RULES.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 age = random.randint(min_entry_age, max_entry_age)
#                 min_maturity_age_rider, max_maturity_age_rider = PPT_RULES_RIDER["Rider AD"]["maturity_age_range"]
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#                 charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#                 ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"])) 
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
                
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     get_api_operation(target_rule),
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_maturity_age_rider, max_maturity_age_rider),
#                     'Positive',
#                     EXPECTED_RESULT_MAP['Positive'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(age),
#                     age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
#                 scenarios.append({**common_data, **common_row, **rider_fields})
#             # Negative Cases
#             for i in range(neg_count):
#                 tuid_counter += 1
#                 # age = random.randint(min_entry_age, max_entry_age)
#                 idx = random.randint(0, 2)
#                 idy = random.randint(0, 1)
#                 ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#                 rule = PPT_RULES.get(ppt_name)
#                 min_entry_age, max_entry_age = rule['entry_age_range']
#                 age = random.randint(min_entry_age, max_entry_age)
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#                 min_maturity_age_rider, max_maturity_age_rider = PPT_RULES_RIDER["Rider AD"]["maturity_age_range"]
#                 charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#                 maturity_year_rider = 76
#                 coverage_year_rider = maturity_year_rider - age
#                 ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"])) 
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     get_api_operation(target_rule),
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     SCENARIO_MAP[target_rule](ppt_name, min_maturity_age_rider, max_maturity_age_rider),
#                     'Negative',
#                     EXPECTED_RESULT_MAP['Negative'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(age),
#                     age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
#                 scenarios.append({**common_data, **common_row, **rider_fields})

#     # --- EPIC: PaymentFrequency ---
#     if 'PaymentFrequency' in selected_epics_rider:
#         target_rule = 'PaymentFrequency'
#         counts = epic_counts_rider.get(target_rule, {'positive': 0, 'negative': 0})
#         # Positive Cases
#         for i in range(counts.get('positive', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             idy = random.randint(0, 1)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             # min_maturity_age, max_maturity_age = rule['maturity_age_range']
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             # charge_year_rider, coverage_year_rider, maturity_year_rider = get_years("Rider AD", age, PPT_RULES_RIDER)
#             # charge_year_rider = min(charge_year_rider, charge_year)
#             # maturity_year_rider = min(maturity_year_rider, maturity_year)
#             charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#             ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"]))
#             discount_info = calculate_discounts(ppt_name)
#             payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
            
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Positive',
#                 EXPECTED_RESULT_MAP['Positive'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
#             scenarios.append({**common_data, **common_row, **rider_fields})
#         # Negative Cases
#         for i in range(counts.get('negative', 0)):
#             tuid_counter += 1
#             # age = random.randint(min_entry_age, max_entry_age)
#             idx = random.randint(0, 2)
#             idy = random.randint(0, 1)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             age = random.randint(min_entry_age, max_entry_age)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, age)
#             # charge_year_rider, coverage_year_rider, maturity_year_rider = get_years("Rider AD", age, PPT_RULES_RIDER)
#             # charge_year_rider = min(charge_year_rider, charge_year)
#             # maturity_year_rider = min(maturity_year_rider, maturity_year)
#             charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#             ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"]))
#             discount_info = calculate_discounts(ppt_name)
#             # payment_freq = random.choice(PAYMENT_FREQUENCY)
#             # invalid_freq = random.choice([6, 7]) # Invalid frequencies
#             # paymentFreqStr = "invalid_freq"
#             if(ppt_name == "Single Pay"):
#                 payment_freq = random.choice([1, 2, 3, 4]) # Invalid frequencies for Single Pay
#             else:
#                 payment_freq = 5 # Invalid frequency for others
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 get_api_operation(target_rule),
#                 CHECKING_NOTE_CREATE_VALUE,
#                 ppt_name,
#                 SCENARIO_MAP[target_rule],
#                 'Negative',
#                 EXPECTED_RESULT_MAP['Negative'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(age),
#                 age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
#             scenarios.append({**common_data, **common_row, **rider_fields})

#     # --- EPIC: PremiumPayingTerm ---
#     if 'PremiumPayingTerm' in selected_epics_rider:
#         target_rule = 'PremiumPayingTerm'
#         premium_paying_term_config = epic_counts_rider.get(target_rule, {})
#         ppt_age_ranges = premium_paying_term_config.get('ppt_age_ranges', {})
#         ppt_pos_counts = premium_paying_term_config.get('ppt_pos_counts', {})
#         ppt_neg_counts = premium_paying_term_config.get('ppt_neg_counts', {})
#         # Premium paying term adjustments are applied globally; use the module-level rules
#         premium_paying_ppt_rules = PPT_RULES

#         per_ppt_mode = any(int(ppt_pos_counts.get(ppt, 0)) > 0 or int(ppt_neg_counts.get(ppt, 0)) > 0 for ppt in PPT_NAME) # check for 'different count' mode
#         ppt_enabled = premium_paying_term_config.get('ppt_enabled', {}) # check for 'same count' mode
#         # print(premium_paying_term_config)
#         for ppt_name in PPT_NAME:
            
#             # min_entry_age, max_entry_age = ppt_age_ranges.get(ppt_name, (18, 65))
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             if per_ppt_mode:
#                 pos_count = int(ppt_pos_counts.get(ppt_name, 0))
#                 neg_count = int(ppt_neg_counts.get(ppt_name, 0))
#             elif ppt_enabled.get(ppt_name, False):
#                 pos_count = premium_paying_term_config.get('positive', 0)
#                 neg_count = premium_paying_term_config.get('negative', 0)
#             else:
#                 continue
#             # Prepare scenario message based on PPT type
#             if(ppt_name == "Limited Pay (Pay till age 60)" or ppt_name == "Regular Pay"):
#                 min_ppt, max_ppt = premium_paying_ppt_rules[ppt_name]['charge_year_range']
#                 message = SCENARIO_MAP['PremiumPayingTerm'](ppt_name, min_ppt=min_ppt, max_ppt=max_ppt)
#             elif pos_count > 0 or neg_count > 0:
#                 ppt_limit = premium_paying_ppt_rules[ppt_name]['charge_year'](0)
#                 message = SCENARIO_MAP['PremiumPayingTerm'](ppt_name, ppt_limit=ppt_limit)
#             # Positive cases for this PPT
#             for i in range(pos_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 idy = random.randint(0, 1)
#                 positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
#                 # if ppt_name == "Limited Pay (Pay till age 60)" and positive_age >= 55:
#                 #     positive_age = 54
#                 charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age, premium_paying_ppt_rules)
#                 charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year, apply_min_charge_floor=False)
#                 ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"]))
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule],
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     message,
#                     'Positive',
#                     EXPECTED_RESULT_MAP['Positive'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(positive_age),
#                     positive_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 # Merge rider-specific fields
#                 rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider)
#                 scenarios.append({**common_data, **common_row, **rider_fields})
#             # Negative cases for this PPT
#             for i in range(neg_count):
#                 tuid_counter += 1
#                 idx = random.randint(0, 2)
#                 idy = random.randint(0, 1)
#                 positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
#                 charge_year, coverage_year, maturity_year = get_out_of_range_charge_year(ppt_name, positive_age, premium_paying_ppt_rules)
#                 charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year, apply_min_charge_floor=False)
#                 ad_sum_assured = min(30000000, random.randint(25000, 3 * calculate_discounts(ppt_name)["sumAssured"]))
#                 discount_info = calculate_discounts(ppt_name)
#                 payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
#                 common_row = build_common_row(
#                     tuid_counter,
#                     MODULE_NAME,
#                     EPIC_MAP[target_rule],
#                     CHECKING_NOTE_CREATE_VALUE,
#                     ppt_name,
#                     message,
#                     'Negative',
#                     EXPECTED_RESULT_MAP['Negative'],
#                     INCEPTION_DATE_VALUE,
#                     random.choice(policy_holder_location),
#                     random.choice(insurer_location),
#                     current_year - int(positive_age),
#                     positive_age,
#                     random.choice(GENDER),
#                     random.choice(SMOKING),
#                     MEDICAL_INDI,
#                     PRODUCT_CODE,
#                     coverage_year,
#                     charge_year,
#                     maturity_year,
#                     payment_freq,
#                     discount_info,
#                     idx
#                 )
#                 rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
#                 scenarios.append({**common_data, **common_row, **rider_fields})

#     # --- EPIC: SumAssuredValidation ---
#     if 'SumAssuredValidation' in selected_epics_rider:
#         target_rule = 'SumAssuredValidation'
#         sum_assured_validation_config = epic_counts_rider.get(target_rule, {})
#         counts = epic_counts_rider.get(target_rule, {'positive': 0, 'negative': 0})
#         for i in range(counts.get('positive', 0)):
#             tuid_counter += 1
#             min_sum_assured, max_sum_assured = PPT_RULES_RIDER["Rider AD"]["sum_assured_range"]
#             idx = random.randint(0, 2)
#             idy = random.randint(0, 1)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age)
#             charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#             # Adjust max_sum_assured for variant
#             min_sum_assured, max_sum_assured = PPT_RULES_RIDER["Rider AD"]["sum_assured_range"]
#             max_sum_assured = max_sum_assured * 3 if idy == 1 else max_sum_assured
#             x = 3 if idy == 1 else 1
#             ad_sum_assured = min(max_sum_assured, random.randint(min_sum_assured, x * calculate_discounts(ppt_name)["sumAssured"]))
#             message = SCENARIO_MAP['SumAssuredValidation_Rider_max'](ppt_name, max_sum_assured) if (i % 2 == 0) else SCENARIO_MAP['SumAssuredValidation_Rider_min'](ppt_name, min_sum_assured)
#             discount_info = calculate_discounts(ppt_name)
#             payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 EPIC_MAP[target_rule],
#                 CHECKING_NOTE_UPDATE_VALUE,
#                 ppt_name,
#                 message,
#                 'Positive',
#                 EXPECTED_RESULT_MAP['Positive'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(positive_age),
#                 positive_age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             rider_fields = build_rider_fields(ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
#             scenarios.append({**common_data, **common_row, **rider_fields})
#         # Negative cases for this PPT
#         for i in range(counts.get('negative', 0)):
#             tuid_counter += 1
#             idx = random.randint(0, 2)
#             idy = random.randint(0, 1)
#             ppt_name = PPT_NAME[(idx+i) % len(PPT_NAME)]
#             rule = PPT_RULES.get(ppt_name)
#             min_entry_age, max_entry_age = rule['entry_age_range']
#             positive_age = max(min_entry_age, min(max_entry_age - i, max_entry_age)) if i % 2 == 0 else min(max_entry_age, min_entry_age + i)
#             charge_year, coverage_year, maturity_year = get_years(ppt_name, positive_age)
#             charge_year_rider, coverage_year_rider, maturity_year_rider = build_rider_years(charge_year, coverage_year, maturity_year)
#             min_sum_assured, max_sum_assured = PPT_RULES_RIDER["Rider AD"]["sum_assured_range"]
#             max_sum_assured = max_sum_assured * 3 if idy == 1 else max_sum_assured
#             # x = 3 if idy == 1 else 1
#             # ad_sum_assured = min(max_sum_assured, random.randint(min_sum_assured, x * calculate_discounts(ppt_name)["sumAssured"]))
#             neg_ad_sum_assured = max_sum_assured + 1000 if (i % 2 == 0) else min_sum_assured - 1000
#             message = SCENARIO_MAP['SumAssuredValidation_Rider_max'](ppt_name, max_sum_assured) if (i % 2 == 0) else SCENARIO_MAP['SumAssuredValidation_Rider_min'](ppt_name, min_sum_assured)
#             discount_info = calculate_discounts(ppt_name)
#             payment_freq = normalize_payment_frequency(ppt_name, random.choice(PAYMENT_FREQUENCY))
#             common_row = build_common_row(
#                 tuid_counter,
#                 MODULE_NAME,
#                 EPIC_MAP[target_rule],
#                 CHECKING_NOTE_UPDATE_VALUE,
#                 ppt_name,
#                 message,
#                 'Negative',
#                 EXPECTED_RESULT_MAP['Negative'],
#                 INCEPTION_DATE_VALUE,
#                 random.choice(policy_holder_location),
#                 random.choice(insurer_location),
#                 current_year - int(positive_age),
#                 positive_age,
#                 random.choice(GENDER),
#                 random.choice(SMOKING),
#                 MEDICAL_INDI,
#                 PRODUCT_CODE,
#                 coverage_year,
#                 charge_year,
#                 maturity_year,
#                 payment_freq,
#                 discount_info,
#                 idx
#             )
#             rider_fields = build_rider_fields(neg_ad_sum_assured, idy, charge_year_rider, coverage_year_rider, maturity_year_rider, idx=idx, payment_freq=payment_freq)
#             scenarios.append({**common_data, **common_row, **rider_fields})

#     # Convert to DataFrame
#     df = pd.DataFrame(scenarios)
#     if not df.empty:
#         df = df.reindex(columns=column_order)
            
#     return df

