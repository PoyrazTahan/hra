#!/usr/bin/env python3
"""
Statistical Surprise Detector for Health Risk Assessment Data
Identifies demographic subgroups and lifestyle combinations where observed health
outcomes significantly differ from population expectations.

Usage:
    python statistical_surprise_refactored.py input_path output_path [--min_sample_size 10] [--threshold 2.0]
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from scipy.stats import chi2_contingency
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

# Analysis Parameters (defaults - can be overridden via command line)
DEFAULT_MIN_SAMPLE_SIZE = 10
DEFAULT_SURPRISE_THRESHOLD = 2.0


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



def load_and_prepare_data(input_path):
    """Load and prepare the health risk assessment data."""
    df = pd.read_csv(input_path)
    analysis_columns = [col for col in df.columns if col not in EXCLUSION_COLUMNS]
    return df[analysis_columns]

def get_available_variables(df, variable_list):
    """Filter variable list to only include columns that exist in the data."""
    return [var for var in variable_list if var in df.columns]

def calculate_surprises(df, grouping_vars, outcome_vars, min_sample_size, surprise_threshold):
    """Calculate statistical surprises for given variable combinations."""
    surprises = []

    for group_var in grouping_vars:
        for outcome_var in outcome_vars:
            if group_var == outcome_var:
                continue

            contingency = pd.crosstab(df[group_var], df[outcome_var])
            if contingency.size == 0:
                continue

            chi2, p_val, dof, expected = chi2_contingency(contingency)
            std_residuals = (contingency - expected) / np.sqrt(expected)

            surprise_mask = np.abs(std_residuals) > surprise_threshold
            surprise_indices = np.where(surprise_mask)

            for i, j in zip(*surprise_indices):
                subgroup = contingency.index[i]
                outcome = contingency.columns[j]

                observed_count = contingency.iloc[i, j]
                subgroup_total = contingency.iloc[i].sum()

                if subgroup_total >= min_sample_size:
                    observed_rate = observed_count / subgroup_total * 100
                    population_rate = contingency.iloc[:, j].sum() / contingency.sum().sum() * 100
                    surprise_magnitude = std_residuals.iloc[i, j]

                    confidence = "HIGH" if p_val < 0.001 else "MEDIUM" if p_val < 0.01 else "LOW" if p_val < 0.05 else "NONE"

                    surprises.append({
                        'subgroup': str(subgroup),
                        'outcome': str(outcome),
                        'outcome_var': outcome_var,
                        'observed_rate': observed_rate,
                        'population_rate': population_rate,
                        'surprise_magnitude': surprise_magnitude,
                        'sample_size': int(subgroup_total),
                        'direction': 'HIGHER' if surprise_magnitude > 0 else 'LOWER',
                        'confidence': confidence,
                        'p_value': p_val
                    })

    return surprises

def calculate_compound_surprises(df, group1_vars, group2_vars, outcome_vars, min_sample_size, surprise_threshold):
    """Calculate surprises for compound factor combinations."""
    compound_surprises = []

    for var1 in group1_vars:
        for var2 in group2_vars:
            if var1 == var2:
                continue

            for outcome_var in outcome_vars:
                # Create compound grouping
                compound_groups = df[var1].astype(str) + " + " + df[var2].astype(str)
                temp_df = pd.DataFrame({
                    'compound_group': compound_groups,
                    'outcome': df[outcome_var]
                }).dropna()

                if len(temp_df) == 0:
                    continue

                contingency = pd.crosstab(temp_df['compound_group'], temp_df['outcome'])
                if contingency.size == 0:
                    continue

                chi2, p_val, dof, expected = chi2_contingency(contingency)
                std_residuals = (contingency - expected) / np.sqrt(expected)

                surprise_mask = np.abs(std_residuals) > surprise_threshold
                surprise_indices = np.where(surprise_mask)

                for i, j in zip(*surprise_indices):
                    compound_group = contingency.index[i]
                    outcome = contingency.columns[j]

                    observed_count = contingency.iloc[i, j]
                    subgroup_total = contingency.iloc[i].sum()

                    if subgroup_total >= min_sample_size:
                        observed_rate = observed_count / subgroup_total * 100
                        population_rate = contingency.iloc[:, j].sum() / contingency.sum().sum() * 100
                        surprise_magnitude = std_residuals.iloc[i, j]

                        confidence = "HIGH" if p_val < 0.001 else "MEDIUM" if p_val < 0.01 else "LOW" if p_val < 0.05 else "NONE"

                        compound_surprises.append({
                            'subgroup': compound_group,
                            'outcome': str(outcome),
                            'outcome_var': outcome_var,
                            'observed_rate': observed_rate,
                            'population_rate': population_rate,
                            'surprise_magnitude': surprise_magnitude,
                            'sample_size': int(subgroup_total),
                            'direction': 'HIGHER' if surprise_magnitude > 0 else 'LOWER',
                            'confidence': confidence
                        })

    return compound_surprises

def run_statistical_surprise_analysis(input_path, output_path, min_sample_size=DEFAULT_MIN_SAMPLE_SIZE, surprise_threshold=DEFAULT_SURPRISE_THRESHOLD):
    """Run comprehensive statistical surprise analysis and output to text file."""
    df = load_and_prepare_data(input_path)
    output_lines = []

    # Get available variables
    demographics = get_available_variables(df, DEMOGRAPHIC_VARIABLES)
    outcomes = get_available_variables(df, OUTCOME_COLUMNS)

    # Combine all lifestyle factors
    all_lifestyle = (
        LIFESTYLE_FACTORS +
        STRESS_FACTORS +
        NUTRITION_FACTORS + 
        PHYSICAL_HEALTH_FACTORS +
        CHRONIC_CONDITION_FACTORS
    )
    lifestyle_vars = get_available_variables(df, all_lifestyle)

    output_lines.append("="*80)
    output_lines.append("STATISTICAL SURPRISE ANALYSIS")
    output_lines.append("="*80)
    output_lines.append(f"Dataset: {len(df)} records, {len(df.columns)} variables")
    output_lines.append(f"Demographics: {len(demographics)} variables: {demographics}")
    output_lines.append(f"Lifestyle factors: {len(lifestyle_vars)} variables")
    output_lines.append(f"Variables: {lifestyle_vars}")
    output_lines.append(f"Parameters: min_sample={min_sample_size}, threshold={surprise_threshold}σ")

    # Calculate all surprises
    demographic_surprises = calculate_surprises(df, demographics, outcomes, min_sample_size, surprise_threshold)
    lifestyle_surprises = calculate_surprises(df, lifestyle_vars, outcomes, min_sample_size, surprise_threshold)

    # Compound surprises - comprehensive analysis like original
    compound_surprises = []

    # Demographics vs All Lifestyle (like original)
    compound_surprises.extend(calculate_compound_surprises(df, demographics, lifestyle_vars, outcomes, min_sample_size, surprise_threshold))

    # Additional high-value combinations
    compound_surprises.extend(calculate_compound_surprises(df, LIFESTYLE_FACTORS, STRESS_FACTORS, outcomes, min_sample_size, surprise_threshold))
    compound_surprises.extend(calculate_compound_surprises(df, CHRONIC_CONDITION_FACTORS, LIFESTYLE_FACTORS, outcomes, min_sample_size, surprise_threshold))

    # Combine and categorize all surprises
    all_surprises = []
    for surprise in demographic_surprises:
        surprise['category'] = 'DEMOGRAPHIC'
        all_surprises.append(surprise)
    for surprise in lifestyle_surprises:
        surprise['category'] = 'LIFESTYLE'
        all_surprises.append(surprise)
    for surprise in compound_surprises:
        surprise['category'] = 'COMPOUND'
        all_surprises.append(surprise)

    # Sort by magnitude
    all_surprises.sort(key=lambda x: abs(x['surprise_magnitude']), reverse=True)

    # Summary
    high_confidence = len([s for s in all_surprises if s['confidence'] == 'HIGH'])
    categories = list(set([s['category'] for s in all_surprises]))

    output_lines.append(f"\nSURPRISE DETECTION SUMMARY:")
    output_lines.append(f"Total patterns analyzed: {len(all_surprises)}")
    output_lines.append(f"High confidence surprises: {high_confidence}")
    output_lines.append(f"Categories with surprises: {', '.join(categories)}")

    # Top surprises overall
    if all_surprises:
        output_lines.append(f"\n" + "-"*60)
        output_lines.append("TOP STATISTICAL SURPRISES (ALL TARGETS)")
        output_lines.append("-"*60)

        for i, surprise in enumerate(all_surprises[:15], 1):  # Top 15
            direction_symbol = "↑" if surprise['direction'] == 'HIGHER' else "↓"
            outcome_display = f"{surprise['outcome']} in {surprise['outcome_var']}"

            output_lines.append(f"\n{i}. [{surprise['category']}] {surprise['subgroup']} {direction_symbol}")
            output_lines.append(f"   Outcome: {outcome_display}")
            output_lines.append(f"   Rate: {surprise['observed_rate']:.1f}% (vs {surprise['population_rate']:.1f}% population)")
            output_lines.append(f"   Magnitude: {abs(surprise['surprise_magnitude']):.2f}σ | Confidence: {surprise['confidence']}")
            output_lines.append(f"   Sample: {surprise['sample_size']} employees")

        # Surprises organized by target variable
        for outcome_var in outcomes:
            target_surprises = [s for s in all_surprises if s['outcome_var'] == outcome_var]
            if target_surprises:
                output_lines.append(f"\n" + "="*60)
                output_lines.append(f"SURPRISES FOR {outcome_var.upper()}")
                output_lines.append("="*60)

                # Get unique outcome values for this target
                outcome_values = sorted(list(set([s['outcome'] for s in target_surprises])))

                for outcome_value in outcome_values:
                    value_surprises = [s for s in target_surprises if s['outcome'] == outcome_value][:10]  # Top 10 per outcome value

                    if value_surprises:
                        output_lines.append(f"\n{outcome_value.upper()} surprises:")
                        output_lines.append("-" * 40)

                        for i, surprise in enumerate(value_surprises, 1):
                            direction_symbol = "↑" if surprise['direction'] == 'HIGHER' else "↓"
                            rate_diff = abs(surprise['observed_rate'] - surprise['population_rate'])

                            output_lines.append(f"{i}. [{surprise['category']}] {surprise['subgroup']} {direction_symbol}")
                            output_lines.append(f"   Rate: {surprise['observed_rate']:.1f}% (vs {surprise['population_rate']:.1f}% population)")
                            output_lines.append(f"   Effect: {rate_diff:.1f}pp {'higher' if surprise['direction'] == 'HIGHER' else 'lower'} | {abs(surprise['surprise_magnitude']):.2f}σ")
                            output_lines.append(f"   Sample: n={surprise['sample_size']}")
                            output_lines.append("")

        # Legacy sections removed - all information now organized by target variable above

    else:
        output_lines.append(f"\nNo statistical surprises detected at {surprise_threshold}σ threshold.")

    output_lines.append(f"\n" + "="*80)
    output_lines.append("ANALYSIS COMPLETE")
    output_lines.append("="*80)

    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

def main():
    parser = argparse.ArgumentParser(description='Statistical Surprise Detector for Health Risk Assessment')
    parser.add_argument('input_path', help='Path to the input CSV file')
    parser.add_argument('output_path', help='Path to the output text file')
    parser.add_argument('--min_sample_size', type=int, default=DEFAULT_MIN_SAMPLE_SIZE,
                       help=f'Minimum sample size for subgroup analysis (default: {DEFAULT_MIN_SAMPLE_SIZE})')
    parser.add_argument('--threshold', type=float, default=DEFAULT_SURPRISE_THRESHOLD,
                       help=f'Statistical surprise threshold in standard deviations (default: {DEFAULT_SURPRISE_THRESHOLD})')

    args = parser.parse_args()

    if not Path(args.input_path).exists():
        print(f"Error: Input file not found: {args.input_path}")
        return

    run_statistical_surprise_analysis(args.input_path, args.output_path,
                                    args.min_sample_size, args.threshold)

    print(f"✓ Statistical surprise analysis complete. Results saved to: {args.output_path}")
    print(f"  Parameters: min_sample_size={args.min_sample_size}, threshold={args.threshold}σ")

if __name__ == "__main__":
    main()