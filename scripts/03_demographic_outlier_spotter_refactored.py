#!/usr/bin/env python3
"""
Streamlined Demographic Outlier Spotter for Health Risk Assessment Data
Identifies small demographic segments with disproportionate health impacts.
Finds "hidden populations" that might need targeted wellness interventions.

Usage:
    python demographic_outlier_spotter_refactored.py input_path output_path
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# Analysis Configuration Constants
MAX_SEGMENT_SIZE = 15.0  # Maximum % of population for "small segment"
MIN_RISK_RATIO = 2.5    # Minimum risk ratio to be considered outlier (1.5x = 50% higher)
MIN_SAMPLE_SIZE = 8    # Minimum sample size for reliable analysis

# Exclusion columns (ID fields that should not be analyzed)
EXCLUSION_COLUMNS = ['_id', 'UserId']

# Outcome columns (health metrics to analyze)
OUTCOME_COLUMNS = ['health_risk_level']

# Core demographic segmentation variables
DEMOGRAPHIC_VARIABLES = ['age_group', 'Data.gender', 'Data.has_children', 'bmi_category']

# Lifestyle variables that can create demographic segments
LIFESTYLE_DEMOGRAPHICS = [
    'Data.smoking_status', 'Data.alcohol_consumption', 'Data.activity_level',
    'Data.sleep_quality', 'Data.perceived_health', 'Data.daily_steps'
]

# Mental health and stress factors (key for outlier combinations)
STRESS_FACTORS = [
    'Data.stress_level_irritability', 'Data.stress_level_loc', 'Data.depression_mood',
    'Data.depression_anhedonia', 'Data.loneliness'
]

# Nutrition factors
NUTRITION_FACTORS = [
    'Data.fruit_veg_intake', 'Data.sugar_intake', 'Data.processed_food_intake', 'Data.water_intake'
]

# Physical health factors
PHYSICAL_HEALTH_FACTORS = [
    'Data.physical_pain', 'Data.supplement_usage'
]

# Chronic conditions (binary flags)
CHRONIC_CONDITION_DEMOGRAPHICS = [
    'Data.chronic_conditions_diabetes', 'Data.chronic_conditions_obesity',
    'Data.chronic_conditions_hypertension', 'Data.chronic_conditions_heart_disease',
    'Data.chronic_conditions_thyroid', 'Data.chronic_conditions_kidney_disease',
    'Data.chronic_conditions_cancer'
]

# Strategic two-variable combinations for analysis (avoid combinatorial explosion)
STRATEGIC_COMBINATIONS = [
    ('age_group', 'Data.gender'),
    ('age_group', 'bmi_category'),
    ('Data.gender', 'Data.has_children'),
    ('bmi_category', 'Data.activity_level'),
    ('Data.smoking_status', 'Data.alcohol_consumption'),
    ('Data.stress_level_irritability', 'Data.sleep_quality'),
    ('Data.depression_mood', 'Data.loneliness'),
    ('age_group', 'Data.chronic_conditions_diabetes'),
    ('age_group', 'Data.chronic_conditions_hypertension'),
    ('Data.gender', 'Data.smoking_status'),
    ('bmi_category', 'Data.chronic_conditions_obesity'),
    ('Data.activity_level', 'Data.sleep_quality'),
    ('Data.stress_level_irritability', 'Data.depression_mood'),
    ('Data.perceived_health', 'Data.physical_pain'),
    ('Data.alcohol_consumption', 'Data.stress_level_irritability')
]

def load_and_prepare_data(input_path):
    """Load and prepare the health risk assessment data."""
    df = pd.read_csv(input_path)

    # Remove exclusion columns from analysis
    analysis_columns = [col for col in df.columns if col not in EXCLUSION_COLUMNS]
    df_analysis = df[analysis_columns]

    return df_analysis

def get_available_variables(df):
    """Get available demographic and outcome variables from the dataset."""
    all_demographic_vars = (DEMOGRAPHIC_VARIABLES + LIFESTYLE_DEMOGRAPHICS +
                           STRESS_FACTORS + NUTRITION_FACTORS +
                           PHYSICAL_HEALTH_FACTORS + CHRONIC_CONDITION_DEMOGRAPHICS)

    available_demographics = [col for col in all_demographic_vars if col in df.columns]
    available_outcomes = [col for col in OUTCOME_COLUMNS if col in df.columns]

    return available_demographics, available_outcomes

def calculate_population_baselines(df, outcome_vars):
    """Calculate population baseline rates for each outcome."""
    baselines = {}

    for outcome in outcome_vars:
        if outcome == 'health_risk_level':
            baselines[outcome] = {
                'high_risk': (df[outcome] == 'high_risk').mean() * 100,
                'moderate_risk': (df[outcome] == 'moderate_risk').mean() * 100,
                'elevated_risk': df[outcome].isin(['high_risk', 'moderate_risk']).mean() * 100
            }

    return baselines

def calculate_segment_risk_rate(segment_df, outcome_var, risk_type):
    """Calculate risk rate for a specific segment and risk type."""
    if outcome_var == 'health_risk_level':
        if risk_type == 'high_risk':
            return (segment_df[outcome_var] == 'high_risk').mean() * 100
        elif risk_type == 'moderate_risk':
            return (segment_df[outcome_var] == 'moderate_risk').mean() * 100
        elif risk_type == 'elevated_risk':
            return segment_df[outcome_var].isin(['high_risk', 'moderate_risk']).mean() * 100

    return 0.0

def find_single_variable_outliers(df, demographic_vars, outcome_vars, baselines, output_lines):
    """Find outlier segments within single demographic variables."""
    outliers = []

    output_lines.append(f"\nAnalyzing single-variable demographic outliers...")

    for demo_var in demographic_vars:
        if demo_var not in df.columns:
            continue

        for outcome_var in outcome_vars:
            if outcome_var not in df.columns:
                continue

            outcome_baselines = baselines[outcome_var]
            demo_segments = df[demo_var].value_counts()

            for segment_value, segment_count in demo_segments.items():
                segment_pct = (segment_count / len(df)) * 100

                # Check if segment qualifies as small outlier candidate
                if (segment_pct <= MAX_SEGMENT_SIZE and segment_count >= MIN_SAMPLE_SIZE):

                    segment_df = df[df[demo_var] == segment_value]

                    # Test different risk definitions
                    for risk_type, baseline_rate in outcome_baselines.items():
                        if baseline_rate <= 0:
                            continue

                        segment_rate = calculate_segment_risk_rate(segment_df, outcome_var, risk_type)
                        risk_ratio = segment_rate / baseline_rate if baseline_rate > 0 else 0

                        # Check if this qualifies as an outlier
                        if risk_ratio >= MIN_RISK_RATIO or risk_ratio <= (1/MIN_RISK_RATIO):
                            direction = "ELEVATED" if risk_ratio >= MIN_RISK_RATIO else "PROTECTED"

                            outliers.append({
                                'type': 'SINGLE_VARIABLE',
                                'demographic_variable': demo_var,
                                'segment_description': f"{demo_var} = {segment_value}",
                                'outcome_variable': outcome_var,
                                'risk_type': risk_type,
                                'segment_size': segment_count,
                                'segment_pct': round(segment_pct, 1),
                                'segment_rate': round(segment_rate, 1),
                                'population_rate': round(baseline_rate, 1),
                                'risk_ratio': round(risk_ratio, 2),
                                'direction': direction,
                                'rate_difference': round(segment_rate - baseline_rate, 1)
                            })

    return outliers

def find_two_variable_outliers(df, demographic_vars, outcome_vars, baselines, output_lines):
    """Find outlier segments from strategic combinations of two demographic variables."""
    outliers = []

    output_lines.append(f"\nAnalyzing strategic two-variable demographic combinations...")

    # Use strategic combinations instead of all possible pairs
    for var1, var2 in STRATEGIC_COMBINATIONS:
        if var1 not in df.columns or var2 not in df.columns:
            continue
        if var1 not in demographic_vars or var2 not in demographic_vars:
            continue

        for outcome_var in outcome_vars:
            if outcome_var not in df.columns:
                continue

            outcome_baselines = baselines[outcome_var]
            df_clean = df[[var1, var2, outcome_var]].dropna()

            if len(df_clean) < MIN_SAMPLE_SIZE * 2:
                continue

            # Test each unique combination
            for val1 in df_clean[var1].unique():
                for val2 in df_clean[var2].unique():

                    combo_mask = (df_clean[var1] == val1) & (df_clean[var2] == val2)
                    combo_df = df_clean[combo_mask]

                    if len(combo_df) >= MIN_SAMPLE_SIZE:
                        combo_pct = (len(combo_df) / len(df)) * 100

                        # Only analyze small segments
                        if combo_pct <= MAX_SEGMENT_SIZE:

                            # Test different risk definitions
                            for risk_type, baseline_rate in outcome_baselines.items():
                                if baseline_rate <= 0:
                                    continue

                                segment_rate = calculate_segment_risk_rate(combo_df, outcome_var, risk_type)
                                risk_ratio = segment_rate / baseline_rate if baseline_rate > 0 else 0

                                # Check if this qualifies as an outlier
                                if risk_ratio >= MIN_RISK_RATIO or risk_ratio <= (1/MIN_RISK_RATIO):
                                    direction = "ELEVATED" if risk_ratio >= MIN_RISK_RATIO else "PROTECTED"

                                    outliers.append({
                                        'type': 'TWO_VARIABLE',
                                        'demographic_variable': f"{var1} × {var2}",
                                        'segment_description': f"{var1}={val1}, {var2}={val2}",
                                        'outcome_variable': outcome_var,
                                        'risk_type': risk_type,
                                        'segment_size': len(combo_df),
                                        'segment_pct': round(combo_pct, 1),
                                        'segment_rate': round(segment_rate, 1),
                                        'population_rate': round(baseline_rate, 1),
                                        'risk_ratio': round(risk_ratio, 2),
                                        'direction': direction,
                                        'rate_difference': round(segment_rate - baseline_rate, 1)
                                    })

    return outliers

def analyze_outlier_patterns(df, outliers, output_lines):
    """Analyze characteristics of outlier segments to understand patterns."""
    if not outliers:
        return

    output_lines.append(f"\n" + "-"*60)
    output_lines.append("OUTLIER PATTERN ANALYSIS")
    output_lines.append("-"*60)

    # Sort outliers by extremeness (distance from 1.0 risk ratio)
    sorted_outliers = sorted(outliers, key=lambda x: abs(x['risk_ratio'] - 1), reverse=True)

    # Analyze top outliers for additional characteristics
    top_outliers = sorted_outliers[:5]

    for outlier in top_outliers:
        output_lines.append(f"\n• {outlier['segment_description']} ({outlier['direction']} risk)")
        output_lines.append(f"  {outlier['risk_type']}: {outlier['segment_rate']}% vs {outlier['population_rate']}% population")
        output_lines.append(f"  Risk ratio: {outlier['risk_ratio']}x | Size: {outlier['segment_size']} ({outlier['segment_pct']}%)")

        # Try to find this segment and analyze additional characteristics
        try:
            if outlier['type'] == 'SINGLE_VARIABLE':
                var_name = outlier['demographic_variable']
                var_value = outlier['segment_description'].split(' = ')[1]
                segment_df = df[df[var_name] == var_value]
            elif outlier['type'] == 'TWO_VARIABLE':
                var1, var2 = outlier['demographic_variable'].split(' × ')
                val1, val2 = outlier['segment_description'].replace(f'{var1}=', '').replace(f'{var2}=', '').split(', ')
                segment_df = df[(df[var1] == val1) & (df[var2] == val2)]

            # Look for distinguishing lifestyle characteristics
            lifestyle_vars = ['Data.activity_level', 'Data.sleep_quality', 'Data.smoking_status',
                            'Data.stress_level_irritability', 'Data.perceived_health']

            distinctive_chars = []
            for var in lifestyle_vars:
                if var in df.columns and var in segment_df.columns:
                    if len(segment_df[var].dropna()) > 0:
                        segment_mode = segment_df[var].mode()
                        if len(segment_mode) > 0:
                            most_common = segment_mode.iloc[0]
                            segment_pct = (segment_df[var] == most_common).mean() * 100
                            pop_pct = (df[var] == most_common).mean() * 100

                            if abs(segment_pct - pop_pct) > 15:  # 15% difference threshold
                                distinctive_chars.append(f"{var}: {segment_pct:.0f}% {most_common} (vs {pop_pct:.0f}% population)")

            if distinctive_chars:
                output_lines.append(f"  Distinctive characteristics:")
                for char in distinctive_chars[:3]:  # Top 3
                    output_lines.append(f"    {char}")
        except:
            # Skip additional analysis if any errors occur
            continue

def generate_comprehensive_report(df, outliers, output_lines):
    """Generate comprehensive outlier analysis report."""
    output_lines.append("="*80)
    output_lines.append("DEMOGRAPHIC OUTLIER ANALYSIS REPORT")
    output_lines.append("="*80)

    # Summary statistics
    elevated_risk = [o for o in outliers if o['direction'] == 'ELEVATED']
    protected = [o for o in outliers if o['direction'] == 'PROTECTED']

    output_lines.append(f"\nOUTLIER DETECTION SUMMARY:")
    output_lines.append(f"Total outlier segments found: {len(outliers)}")
    output_lines.append(f"Max segment size threshold: {MAX_SEGMENT_SIZE}% of population")
    output_lines.append(f"Min risk ratio threshold: {MIN_RISK_RATIO}x")
    output_lines.append(f"Min sample size: {MIN_SAMPLE_SIZE}")
    output_lines.append(f"Elevated risk segments: {len(elevated_risk)}")
    output_lines.append(f"Protected segments: {len(protected)}")

    if not outliers:
        output_lines.append(f"\nNo demographic outliers detected with current thresholds.")
        output_lines.append(f"Consider adjusting parameters or analyzing larger demographic groups.")
        return

    # Sort outliers by risk ratio extremeness
    sorted_outliers = sorted(outliers, key=lambda x: abs(x['risk_ratio'] - 1), reverse=True)

    # Highest risk outliers
    if elevated_risk:
        output_lines.append(f"\n" + "-"*60)
        output_lines.append("HIGHEST RISK DEMOGRAPHIC OUTLIERS")
        output_lines.append("-"*60)

        for outlier in sorted([o for o in sorted_outliers if o['direction'] == 'ELEVATED'],
                             key=lambda x: x['risk_ratio'], reverse=True)[:8]:
            output_lines.append(f"\n• {outlier['segment_description']}")
            output_lines.append(f"  Segment size: {outlier['segment_size']} employees ({outlier['segment_pct']}% of population)")
            output_lines.append(f"  {outlier['risk_type']}: {outlier['segment_rate']}% (vs {outlier['population_rate']}% population)")
            output_lines.append(f"  Risk ratio: {outlier['risk_ratio']}x | Difference: {outlier['rate_difference']:+.1f}pp")

    # Protected segments
    if protected:
        output_lines.append(f"\n" + "-"*60)
        output_lines.append("STRONGEST DEMOGRAPHIC PROTECTION")
        output_lines.append("-"*60)

        for outlier in sorted([o for o in sorted_outliers if o['direction'] == 'PROTECTED'],
                             key=lambda x: x['risk_ratio'])[:5]:
            protection_factor = 1 / outlier['risk_ratio'] if outlier['risk_ratio'] > 0 else float('inf')
            output_lines.append(f"\n• {outlier['segment_description']}")
            output_lines.append(f"  Segment size: {outlier['segment_size']} employees ({outlier['segment_pct']}% of population)")
            output_lines.append(f"  {outlier['risk_type']}: {outlier['segment_rate']}% (vs {outlier['population_rate']}% population)")
            output_lines.append(f"  Protection factor: {protection_factor:.1f}x | Difference: {outlier['rate_difference']:+.1f}pp")

    # Smallest high-risk segments (intervention priorities)
    small_high_risk = [o for o in elevated_risk if o['segment_pct'] <= 3.0]
    if small_high_risk:
        output_lines.append(f"\n" + "-"*60)
        output_lines.append("SMALLEST HIGH-RISK SEGMENTS (INTERVENTION PRIORITIES)")
        output_lines.append("-"*60)

        for outlier in sorted(small_high_risk, key=lambda x: x['segment_pct'])[:5]:
            output_lines.append(f"\n• {outlier['segment_description']}")
            output_lines.append(f"  Micro-segment: {outlier['segment_size']} employees ({outlier['segment_pct']}% of population)")
            output_lines.append(f"  {outlier['risk_type']}: {outlier['segment_rate']}% (vs {outlier['population_rate']}% population)")
            output_lines.append(f"  Risk ratio: {outlier['risk_ratio']}x | High intervention potential")

def run_demographic_outlier_analysis(input_path, output_path):
    """Run comprehensive demographic outlier analysis and output to text file."""
    output_lines = []

    # Load and prepare data
    df = load_and_prepare_data(input_path)
    demographic_vars, outcome_vars = get_available_variables(df)

    if not outcome_vars:
        output_lines.append("ERROR: No outcome variables found in dataset.")
        output_lines.append(f"Expected columns: {OUTCOME_COLUMNS}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        return

    # Calculate population baselines
    baselines = calculate_population_baselines(df, outcome_vars)

    output_lines.append(f"Demographic Outlier Analysis")
    output_lines.append(f"Dataset: {df.shape[0]} records, {df.shape[1]} variables")
    output_lines.append(f"Available demographics: {len(demographic_vars)}")
    output_lines.append(f"Available outcomes: {len(outcome_vars)}")

    output_lines.append(f"\nPopulation Baselines:")
    for outcome, rates in baselines.items():
        for risk_type, rate in rates.items():
            output_lines.append(f"  {outcome}.{risk_type}: {rate:.1f}%")

    # Find outlier segments
    single_var_outliers = find_single_variable_outliers(df, demographic_vars, outcome_vars, baselines, output_lines)
    two_var_outliers = find_two_variable_outliers(df, demographic_vars, outcome_vars, baselines, output_lines)

    # Combine all outliers
    all_outliers = single_var_outliers + two_var_outliers

    output_lines.append(f"\nOutlier Detection Results:")
    output_lines.append(f"Single-variable outliers: {len(single_var_outliers)}")
    output_lines.append(f"Two-variable outliers: {len(two_var_outliers)}")
    output_lines.append(f"Total outliers: {len(all_outliers)}")

    # Generate comprehensive report
    generate_comprehensive_report(df, all_outliers, output_lines)

    # Analyze patterns in top outliers
    analyze_outlier_patterns(df, all_outliers, output_lines)

    # Analysis summary
    output_lines.append(f"\n" + "="*80)
    output_lines.append("ANALYSIS SUMMARY")
    output_lines.append("="*80)
    output_lines.append(f"Total records analyzed: {len(df)}")
    output_lines.append(f"Demographic variables analyzed: {len(demographic_vars)}")
    output_lines.append(f"Outcome variables: {', '.join(outcome_vars)}")
    output_lines.append(f"Strategic combinations tested: {len([c for c in STRATEGIC_COMBINATIONS if c[0] in demographic_vars and c[1] in demographic_vars])}")
    output_lines.append(f"Max segment size: {MAX_SEGMENT_SIZE}%")
    output_lines.append(f"Min risk ratio: {MIN_RISK_RATIO}x")
    output_lines.append(f"Min sample size: {MIN_SAMPLE_SIZE}")
    output_lines.append(f"\nThis analysis identifies small demographic segments with disproportionate health risks")
    output_lines.append(f"suitable for targeted wellness interventions and LLM-based insights.")

    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

def main():
    parser = argparse.ArgumentParser(description='Streamlined Demographic Outlier Spotter for Health Risk Assessment')
    parser.add_argument('input_path', help='Path to the input CSV file')
    parser.add_argument('output_path', help='Path to the output text file')

    args = parser.parse_args()

    # Validate input path
    if not Path(args.input_path).exists():
        print(f"Error: Input file not found: {args.input_path}")
        return

    # Run analysis
    run_demographic_outlier_analysis(args.input_path, args.output_path)

    print(f"✓ Demographic outlier analysis complete. Results saved to: {args.output_path}")

if __name__ == "__main__":
    main()