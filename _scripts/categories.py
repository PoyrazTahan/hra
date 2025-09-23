#!/usr/bin/env python3
"""
Global Column Categories for Health Risk Assessment Analysis
"""

# Exclusion columns
EXCLUSION_COLUMNS = [
    '_id',
    'UserId',
    'A.perceived_health',
    'Evaluation.TotalScore',
    'Evaluation.QuestionnaireScores.Aktivite',
    'Evaluation.QuestionnaireScores.Beslenme',
    'Evaluation.QuestionnaireScores.Fiziksel sağlık',
    'Evaluation.QuestionnaireScores.Genel sağlık',
    'Evaluation.QuestionnaireScores.Mental sağlık',
    'Evaluation.QuestionnaireScores.Sağlık öyküsü',
    'Evaluation.QuestionnaireScores.Uyku',
    'Evaluation.QuestionnaireScores.Yaşam tarzı',
    'SponsorId'
]

# Outcome columns
OUTCOME_COLUMNS = [
    'health_risk_level'
]

# Demographics
DEMOGRAPHIC_VARIABLES = [
    'bmi_category',
    # 'age_group',
    # 'A.gender',
    # 'A.has_children'
]

# Lifestyle factors
LIFESTYLE_FACTORS = [
    'A.smoking_status',
    'A.alcohol_consumption',
    'A.activity_level',
    'A.sleep_quality',
    'A.daily_steps'
]

# Mental health and stress
STRESS_FACTORS = [
    'A.stress_level_irritability',
    'A.stress_level_loc',
    'A.depression_mood',
    'A.depression_anhedonia',
    'A.loneliness'
]

# Nutrition
NUTRITION_FACTORS = [
    'A.fruit_veg_intake',
    'A.sugar_intake',
    'A.processed_food_intake',
    'A.water_intake'
]

# Physical health
PHYSICAL_HEALTH_FACTORS = [
    'A.physical_pain',
    'A.supplement_usage',
    'A.bmi',
    'A.height',
    'A.weight'
]

# Chronic conditions
CHRONIC_CONDITION_FACTORS = [
    'diabetes_status',
    'thyroid_disorder_status',
    'kidney_disease_status',
    'heart_disease_status',
    'obesity_status',
    'hypertension_status',
    'cancer_status',
    'other_condition_status'
]

# Combined lists for script reuse
ALL_ANALYSIS_COLUMNS = (
    DEMOGRAPHIC_VARIABLES +
    LIFESTYLE_FACTORS +
    STRESS_FACTORS +
    NUTRITION_FACTORS +
    PHYSICAL_HEALTH_FACTORS +
    CHRONIC_CONDITION_FACTORS
)

ALL_COLUMNS = EXCLUSION_COLUMNS + OUTCOME_COLUMNS + ALL_ANALYSIS_COLUMNS

NON_EXCLUDED_COLUMNS = OUTCOME_COLUMNS + ALL_ANALYSIS_COLUMNS

NON_EXCLUDED_NON_TARGET_COLUMNS = ALL_ANALYSIS_COLUMNS