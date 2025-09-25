#!/usr/bin/env python3
"""
Streamlined Compound Risk Scorer for Health Risk Assessment Data
Creates alternative risk scoring mechanisms that capture multi-factor risk patterns.
Builds predictive risk models using additive or interaction-weighted approaches.

Usage:
    python compound_risk_scorer_refactored.py input_path output_path
    python compound_risk_scorer_refactored.py input_path output_path --method interaction-weighted
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Analysis Configuration
MIN_SAMPLE_SIZE = 15  # Minimum sample size for factor analysis

# Import standardized column categories
from categories import (
    EXCLUSION_COLUMNS,
    OUTCOME_COLUMNS,
    DEMOGRAPHIC_VARIABLES,
    LIFESTYLE_FACTORS,
    STRESS_FACTORS,
    NUTRITION_FACTORS,
    PHYSICAL_HEALTH_FACTORS,
    CHRONIC_CONDITION_FACTORS
)

# High-impact interaction pairs for interaction-weighted method
INTERACTION_PAIRS = [
    ('A.stress_level_irritability', 'A.depression_mood'),  # Mental health stacking
    ('A.smoking_status', 'A.alcohol_consumption'),        # Substance use combination
    ('A.activity_level', 'A.sleep_quality'),             # Lifestyle synergy
    # ('age_group', 'diabetes_status'),                          # Age + chronic condition - missing age_group
    # ('age_group', 'hypertension_status'),                      # Age + chronic condition - missing age_group
    ('A.depression_mood', 'A.loneliness'),               # Mental health amplification
    ('A.physical_pain', 'A.perceived_health'),           # Physical health correlation
    ('bmi_category', 'A.activity_level'),                   # Weight + exercise interaction
    ('A.stress_level_irritability', 'A.sleep_quality'),  # Stress + sleep interaction
    ('A.smoking_status', 'A.physical_pain')             # Smoking + pain interaction
]

def load_and_prepare_data(input_path):
    """Load and prepare the health risk assessment data."""
    df = pd.read_csv(input_path)

    # Remove exclusion columns from analysis
    analysis_columns = [col for col in df.columns if col not in EXCLUSION_COLUMNS]
    df_analysis = df[analysis_columns]

    return df_analysis

def get_available_factor_groups(df):
    """Get available factor groups from the dataset."""
    factor_groups = {
        'demographic_factors': [col for col in DEMOGRAPHIC_VARIABLES if col in df.columns],
        'lifestyle_factors': [col for col in LIFESTYLE_FACTORS if col in df.columns],
        'stress_factors': [col for col in STRESS_FACTORS if col in df.columns],
        'nutrition_factors': [col for col in NUTRITION_FACTORS if col in df.columns],
        'physical_health_factors': [col for col in PHYSICAL_HEALTH_FACTORS if col in df.columns],
        'chronic_condition_factors': [col for col in CHRONIC_CONDITION_FACTORS if col in df.columns]
    }

    # Remove empty groups
    factor_groups = {name: factors for name, factors in factor_groups.items() if factors}

    return factor_groups

def calculate_population_baselines(df, outcome_col):
    """Calculate population baseline rates for risk levels."""
    if outcome_col not in df.columns:
        raise ValueError(f"Outcome column '{outcome_col}' not found in dataset")

    baselines = {
        'high_risk': (df[outcome_col] == 'high_risk').mean(),
        'elevated_risk': df[outcome_col].isin(['high_risk', 'moderate_risk']).mean()
    }

    return baselines

def calculate_factor_weights(df, factor_groups, baselines, output_lines, outcome_col):
    """Calculate individual risk contribution weights for each factor value."""
    output_lines.append(f"\nCalculating individual factor risk weights...")
    output_lines.append(f"Population baselines: {baselines['high_risk']*100:.1f}% high risk, {baselines['elevated_risk']*100:.1f}% elevated risk")

    factor_weights = {}

    for group_name, factors in factor_groups.items():
        factor_weights[group_name] = {}

        for factor in factors:
            factor_weights[group_name][factor] = {}

            # Calculate risk rate for each factor value
            factor_values = df[factor].value_counts()

            for value, count in factor_values.items():
                if count >= MIN_SAMPLE_SIZE:
                    value_df = df[df[factor] == value]

                    # Calculate risk rates
                    high_risk_rate = (value_df[outcome_col] == 'high_risk').mean()
                    elevated_risk_rate = value_df[outcome_col].isin(['high_risk', 'moderate_risk']).mean()

                    # Calculate risk multipliers
                    high_risk_multiplier = high_risk_rate / baselines['high_risk'] if baselines['high_risk'] > 0 else 1
                    elevated_risk_multiplier = elevated_risk_rate / baselines['elevated_risk'] if baselines['elevated_risk'] > 0 else 1

                    factor_weights[group_name][factor][str(value)] = {
                        'high_risk_multiplier': round(high_risk_multiplier, 3),
                        'elevated_risk_multiplier': round(elevated_risk_multiplier, 3),
                        'sample_size': count,
                        'high_risk_rate': round(high_risk_rate * 100, 1),
                        'elevated_risk_rate': round(elevated_risk_rate * 100, 1)
                    }

    return factor_weights

def calculate_additive_score(df, factor_weights, factor_groups, outcome_col):
    """Create compound risk score using additive approach (simple average)."""
    compound_scores = []

    for index, row in df.iterrows():
        total_high_risk_score = 0
        total_elevated_risk_score = 0
        factors_counted = 0

        # Sum risk multipliers across all factor groups
        for group_name, group_factors in factor_groups.items():
            for factor in group_factors:
                factor_value = str(row[factor])

                if (factor in factor_weights[group_name] and
                    factor_value in factor_weights[group_name][factor]):

                    weights = factor_weights[group_name][factor][factor_value]
                    total_high_risk_score += weights['high_risk_multiplier']
                    total_elevated_risk_score += weights['elevated_risk_multiplier']
                    factors_counted += 1

        # Normalize by number of factors
        if factors_counted > 0:
            avg_high_risk_score = total_high_risk_score / factors_counted
            avg_elevated_risk_score = total_elevated_risk_score / factors_counted
        else:
            avg_high_risk_score = 1.0  # Neutral
            avg_elevated_risk_score = 1.0

        compound_scores.append({
            'record_index': index,
            'compound_high_risk_score': round(avg_high_risk_score, 3),
            'compound_elevated_risk_score': round(avg_elevated_risk_score, 3),
            'factors_included': factors_counted,
            'actual_high_risk': row[outcome_col] == 'high_risk' if outcome_col in row else False,
            'actual_elevated_risk': row[outcome_col] in ['high_risk', 'moderate_risk'] if outcome_col in row else False
        })

    return compound_scores

def calculate_interaction_weighted_score(df, factor_weights, factor_groups, outcome_col):
    """Create compound score with interaction bonuses for known high-risk combinations."""
    compound_scores = []

    for index, row in df.iterrows():
        # Base additive score
        base_score = 0
        factors_counted = 0

        for group_name, group_factors in factor_groups.items():
            for factor in group_factors:
                factor_value = str(row[factor])

                if (factor in factor_weights[group_name] and
                    factor_value in factor_weights[group_name][factor]):

                    weights = factor_weights[group_name][factor][factor_value]
                    base_score += weights['elevated_risk_multiplier']
                    factors_counted += 1

        if factors_counted > 0:
            base_score = base_score / factors_counted
        else:
            base_score = 1.0

        # Interaction bonuses
        interaction_bonus = 0
        interactions_found = 0

        for var1, var2 in INTERACTION_PAIRS:
            if var1 in df.columns and var2 in df.columns:
                val1, val2 = str(row[var1]), str(row[var2])

                # High-risk interaction patterns
                bonus = 0
                if (var1 == 'A.stress_level_irritability' and var2 == 'A.depression_mood'):
                    if ('often_irritated' in val1 or 'frequently_irritated' in val1) and ('frequent_sadness' in val2 or 'persistent_sadness' in val2):
                        bonus = 0.5  # Stress + depression amplification

                elif (var1 == 'A.smoking_status' and var2 == 'A.alcohol_consumption'):
                    if 'daily_smoker' in val1 and val2 != 'no_alcohol':
                        bonus = 0.3  # Smoking + alcohol combination

                elif (var1 == 'A.activity_level' and var2 == 'A.sleep_quality'):
                    if 'no_exercise' in val1 and 'insufficient_sleep' in val2:
                        bonus = 0.4  # Sedentary + poor sleep

                elif (var1 == 'A.depression_mood' and var2 == 'A.loneliness'):
                    if ('frequent_sadness' in val1 or 'persistent_sadness' in val1) and ('often_lonely' in val2 or 'always_lonely' in val2):
                        bonus = 0.4  # Depression + loneliness

                elif (var1 == 'A.stress_level_irritability' and var2 == 'A.sleep_quality'):
                    if ('often_irritated' in val1 or 'frequently_irritated' in val1) and 'insufficient_sleep' in val2:
                        bonus = 0.3  # Stress + poor sleep

                elif (var1 == 'age_group' and 'diabetes' in var2):
                    if ('middle_adult' in val1 or 'mature' in val1) and 'has_diabetes' in val2:
                        bonus = 0.4  # Older age + diabetes

                elif (var1 == 'age_group' and 'hypertension' in var2):
                    if ('middle_adult' in val1 or 'mature' in val1) and 'has_hypertension' in val2:
                        bonus = 0.3  # Older age + hypertension

                if bonus > 0:
                    interaction_bonus += bonus
                    interactions_found += 1

        final_score = base_score + interaction_bonus

        compound_scores.append({
            'record_index': index,
            'compound_risk_score': round(final_score, 3),
            'base_additive_score': round(base_score, 3),
            'interaction_bonus': round(interaction_bonus, 3),
            'interactions_found': interactions_found,
            'factors_included': factors_counted,
            'actual_high_risk': row[outcome_col] == 'high_risk' if outcome_col in row else False,
            'actual_elevated_risk': row[outcome_col] in ['high_risk', 'moderate_risk'] if outcome_col in row else False
        })

    return compound_scores

def evaluate_score_performance(compound_scores, method, output_lines):
    """Evaluate how well compound scores predict actual risk levels."""
    scores_df = pd.DataFrame(compound_scores)

    if method == 'additive':
        score_col = 'compound_high_risk_score'  # Use high_risk_score for more dramatic variation
    else:
        score_col = 'compound_risk_score'

    score_thresholds = [1.5, 2.0, 2.5, 3.0]

    output_lines.append(f"\n" + "-"*60)
    output_lines.append(f"COMPOUND SCORE EVALUATION ({method.upper()} METHOD)")
    output_lines.append("-"*60)

    evaluation_results = []
    best_threshold = None
    best_balance = 0

    for threshold in score_thresholds:
        # Employees flagged as high risk by compound score
        high_score_mask = scores_df[score_col] >= threshold
        flagged_count = high_score_mask.sum()

        if flagged_count > 0:
            # How many flagged employees are actually high risk?
            actual_high_risk = scores_df[high_score_mask]['actual_high_risk'].sum()
            actual_elevated_risk = scores_df[high_score_mask]['actual_elevated_risk'].sum()

            precision_high = actual_high_risk / flagged_count * 100
            precision_elevated = actual_elevated_risk / flagged_count * 100

            # How many actual high-risk employees did we catch?
            total_actual_high = scores_df['actual_high_risk'].sum()
            total_actual_elevated = scores_df['actual_elevated_risk'].sum()

            recall_high = actual_high_risk / total_actual_high * 100 if total_actual_high > 0 else 0
            recall_elevated = actual_elevated_risk / total_actual_elevated * 100 if total_actual_elevated > 0 else 0

            # F1-like balance score
            balance = 2 * (precision_elevated * recall_elevated) / (precision_elevated + recall_elevated) if (precision_elevated + recall_elevated) > 0 else 0

            result = {
                'threshold': threshold,
                'flagged_employees': flagged_count,
                'flagged_pct': round(flagged_count / len(scores_df) * 100, 1),
                'precision_high_risk': round(precision_high, 1),
                'precision_elevated_risk': round(precision_elevated, 1),
                'recall_high_risk': round(recall_high, 1),
                'recall_elevated_risk': round(recall_elevated, 1),
                'balance_score': round(balance, 1)
            }

            evaluation_results.append(result)

            if balance > best_balance:
                best_balance = balance
                best_threshold = result

            output_lines.append(f"\nThreshold {threshold}x: Flags {flagged_count} employees ({result['flagged_pct']}%)")
            output_lines.append(f"  Precision: {precision_high:.1f}% high risk, {precision_elevated:.1f}% elevated risk")
            output_lines.append(f"  Recall: {recall_high:.1f}% of high risk caught, {recall_elevated:.1f}% of elevated risk caught")

    if best_threshold:
        output_lines.append(f"\nBest performing threshold: {best_threshold['threshold']}x")
        output_lines.append(f"  Flags {best_threshold['flagged_employees']} employees ({best_threshold['flagged_pct']}% of workforce)")
        output_lines.append(f"  {best_threshold['precision_elevated_risk']}% precision on elevated risk")
        output_lines.append(f"  Catches {best_threshold['recall_elevated_risk']}% of all elevated risk employees")

    return evaluation_results, best_threshold

def find_score_outliers(df, compound_scores, method, output_lines):
    """Find employees with surprising compound vs actual risk mismatches."""
    scores_df = pd.DataFrame(compound_scores)

    if method == 'additive':
        score_col = 'compound_high_risk_score'  # Use high_risk_score for more dramatic variation
    else:
        score_col = 'compound_risk_score'

    outliers = {
        'underestimated_risk': [],  # Low compound score but actually high risk
        'overestimated_risk': [],   # High compound score but actually low risk
    }

    for _, row in scores_df.iterrows():
        compound_score = row[score_col]
        actual_high = row['actual_high_risk']
        actual_elevated = row['actual_elevated_risk']

        # Underestimated: Low compound score but high actual risk
        if compound_score < 1.5 and actual_high:
            employee_data = df.iloc[row['record_index']]
            outliers['underestimated_risk'].append({
                'compound_score': compound_score,
                'actual_risk': 'high_risk',
                'profile': extract_employee_profile(employee_data)
            })

        # Overestimated: High compound score but low actual risk
        elif compound_score >= 2.5 and not actual_elevated:
            employee_data = df.iloc[row['record_index']]
            outliers['overestimated_risk'].append({
                'compound_score': compound_score,
                'actual_risk': 'low_risk',
                'profile': extract_employee_profile(employee_data)
            })

    # Report outliers
    if outliers['underestimated_risk']:
        output_lines.append(f"\n" + "-"*60)
        output_lines.append("UNDERESTIMATED RISK CASES")
        output_lines.append("-"*60)
        output_lines.append("Employees with low compound scores but actually high risk:")

        for case in outliers['underestimated_risk'][:3]:
            output_lines.append(f"\n• Compound score: {case['compound_score']:.2f} | Actual: {case['actual_risk']}")
            profile = case['profile']
            key_chars = [f"{k}={v}" for k, v in profile.items()][:4]
            output_lines.append(f"  Profile: {', '.join(key_chars)}")

    if outliers['overestimated_risk']:
        output_lines.append(f"\n" + "-"*60)
        output_lines.append("OVERESTIMATED RISK CASES")
        output_lines.append("-"*60)
        output_lines.append("Employees with high compound scores but actually low risk:")

        for case in outliers['overestimated_risk'][:3]:
            output_lines.append(f"\n• Compound score: {case['compound_score']:.2f} | Actual: {case['actual_risk']}")
            profile = case['profile']
            key_chars = [f"{k}={v}" for k, v in profile.items()][:4]
            output_lines.append(f"  Profile: {', '.join(key_chars)}")

    return outliers

def extract_employee_profile(employee_row):
    """Extract key characteristics of an individual employee for profiling."""
    profile = {}

    # Core demographics
    demo_vars = ['age_group', 'A.gender', 'A.has_children', 'bmi_category']
    for var in demo_vars:
        if var in employee_row.index:
            profile[var] = str(employee_row[var])

    # Key risk factors
    risk_vars = ['A.stress_level_irritability', 'A.depression_mood', 'A.smoking_status', 'diabetes_status']
    for var in risk_vars:
        if var in employee_row.index:
            profile[var] = str(employee_row[var])

    return profile

def identify_high_impact_factors(factor_weights, output_lines):
    """Identify factor values with highest risk impact."""
    high_impact = []

    for group_name, group_factors in factor_weights.items():
        for factor, factor_values in group_factors.items():
            for value, weights in factor_values.items():
                if weights['sample_size'] >= MIN_SAMPLE_SIZE:
                    # Focus on high risk multiplier as main impact measure (more dramatic differences)
                    impact_score = weights['high_risk_multiplier']

                    if impact_score >= 1.5 or impact_score <= 0.7:  # High impact or protective
                        high_impact.append({
                            'factor_group': group_name,
                            'factor': factor,
                            'value': value,
                            'impact_multiplier': impact_score,
                            'risk_rate': weights['elevated_risk_rate'],
                            'sample_size': weights['sample_size'],
                            'impact_type': 'AMPLIFYING' if impact_score >= 1.5 else 'PROTECTIVE'
                        })

    # Sort by impact magnitude
    high_impact.sort(key=lambda x: abs(x['impact_multiplier'] - 1), reverse=True)

    if high_impact:
        output_lines.append(f"\n" + "-"*60)
        output_lines.append("HIGHEST IMPACT INDIVIDUAL FACTORS")
        output_lines.append("-"*60)

        for factor in high_impact[:8]:
            impact_type = factor['impact_type']
            output_lines.append(f"\n• {factor['factor']} = {factor['value']} ({impact_type})")
            output_lines.append(f"  Impact: {factor['impact_multiplier']:.2f}x baseline | Risk rate: {factor['risk_rate']}%")
            output_lines.append(f"  Sample: {factor['sample_size']} employees | Group: {factor['factor_group']}")

    return high_impact[:15]

def run_compound_risk_analysis(input_path, output_path, method='additive'):
    """Run comprehensive compound risk scoring analysis and output to text file."""
    output_lines = []

    # Load and prepare data
    df = load_and_prepare_data(input_path)
    factor_groups = get_available_factor_groups(df)

    # Check which outcome columns exist
    available_outcomes = [col for col in OUTCOME_COLUMNS if col in df.columns]
    if not available_outcomes:
        output_lines.append(f"ERROR: No outcome columns found in dataset.")
        output_lines.append(f"Expected columns: {OUTCOME_COLUMNS}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        return

    output_lines.append("="*80)
    output_lines.append("COMPOUND RISK SCORING ANALYSIS REPORT")
    output_lines.append("="*80)

    output_lines.append(f"\nSCORING METHOD: {method.upper()}")
    output_lines.append(f"Dataset: {df.shape[0]} records, {df.shape[1]} variables")

    # Display factor groups
    total_factors = sum(len(factors) for factors in factor_groups.values())
    output_lines.append(f"Factor groups: {len(factor_groups)} groups, {total_factors} total factors")
    for group_name, factors in factor_groups.items():
        output_lines.append(f"  {group_name}: {len(factors)} factors")

    # Process each outcome column separately
    for outcome_col in available_outcomes:
        output_lines.append(f"\n{'='*80}")
        output_lines.append(f"ANALYSIS FOR OUTCOME: {outcome_col.upper()}")
        output_lines.append(f"{'='*80}")

        # Calculate population baselines for this outcome
        baselines = calculate_population_baselines(df, outcome_col)

        # Calculate factor weights for this outcome
        factor_weights = calculate_factor_weights(df, factor_groups, baselines, output_lines, outcome_col)

        # Create compound scores based on method
        if method == 'additive':
            compound_scores = calculate_additive_score(df, factor_weights, factor_groups, outcome_col)
        elif method == 'interaction-weighted':
            compound_scores = calculate_interaction_weighted_score(df, factor_weights, factor_groups, outcome_col)
        else:
            output_lines.append(f"\nERROR: Unknown scoring method '{method}'")
            continue

        # Evaluate performance for this outcome
        evaluation_results, best_threshold = evaluate_score_performance(compound_scores, method, output_lines)

        # Find scoring outliers for this outcome
        outliers = find_score_outliers(df, compound_scores, method, output_lines)

        # Identify high-impact factors for this outcome
        high_impact_factors = identify_high_impact_factors(factor_weights, output_lines)

        # Analysis summary for this outcome
        output_lines.append(f"\n" + "="*80)
        output_lines.append("ANALYSIS SUMMARY")
        output_lines.append("="*80)
        output_lines.append(f"Total records analyzed: {len(df)}")
        output_lines.append(f"Scoring method: {method}")
        output_lines.append(f"Factor groups analyzed: {len(factor_groups)}")
        output_lines.append(f"Total factors included: {total_factors}")
        output_lines.append(f"High-impact factors found: {len(high_impact_factors)}")
        output_lines.append(f"Underestimated risk cases: {len(outliers['underestimated_risk'])}")
        output_lines.append(f"Overestimated risk cases: {len(outliers['overestimated_risk'])}")

        if best_threshold:
            output_lines.append(f"Optimal threshold: {best_threshold['threshold']}x (flags {best_threshold['flagged_pct']}% of workforce)")
            output_lines.append(f"Best precision/recall balance: {best_threshold['balance_score']}")

        output_lines.append(f"\nThis analysis creates predictive risk scores for individual employee assessment")
        output_lines.append(f"and identifies high-impact factors for targeted wellness interventions.")

    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

def main():
    parser = argparse.ArgumentParser(description='Streamlined Compound Risk Scorer for Health Risk Assessment')
    parser.add_argument('input_path', help='Path to the input CSV file')
    parser.add_argument('output_path', help='Path to the output text file')
    parser.add_argument('--method', choices=['additive', 'interaction-weighted'], default='additive',
                       help='Scoring method: additive (default) or interaction-weighted')

    args = parser.parse_args()

    # Validate input path
    if not Path(args.input_path).exists():
        print(f"Error: Input file not found: {args.input_path}")
        return

    # Run analysis
    run_compound_risk_analysis(args.input_path, args.output_path, args.method)

    print(f"✓ Compound risk scoring analysis complete using {args.method} method. Results saved to: {args.output_path}")

if __name__ == "__main__":
    main()