#!/usr/bin/env python3
"""
Column Relationship Analysis for Health Risk Assessment Data
Discovers descriptive-to-descriptive relationships and patterns in employee health data.
Focuses on lifestyle clustering, demographic differences, and surprising correlations.

Usage:
    python 05_column_relation_analysis.py input_path output_path
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from scipy.stats import chi2_contingency
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# Configuration Constants
MIN_SAMPLE_SIZE = 3        # Minimum sample per cell for reliable analysis
MIN_EFFECT_SIZE = 0.15     # Minimum Cramer's V for small-medium effect
MIN_PROPORTION_DIFF = 3.0  # Minimum percentage point difference to report

# Exclusion columns (ID fields and target variables)
EXCLUSION_COLUMNS = ['_id', 'UserId', 'health_risk_level', 'Total_Health_Score']

# Lifestyle behavior cluster
LIFESTYLE_FACTORS = [
    'Data.smoking_status', 'Data.alcohol_consumption', 'Data.activity_level',
    'Data.sleep_quality', 'Data.daily_steps', 'Data.supplement_usage'
]

# Mental health & stress cluster
MENTAL_HEALTH_FACTORS = [
    'Data.stress_level_irritability', 'Data.stress_level_loc', 'Data.depression_mood',
    'Data.depression_anhedonia', 'Data.loneliness', 'Data.perceived_health'
]

# Nutrition behavior cluster
NUTRITION_FACTORS = [
    'Data.fruit_veg_intake', 'Data.sugar_intake', 'Data.processed_food_intake', 'Data.water_intake'
]

# Core demographics
DEMOGRAPHIC_FACTORS = ['age_group', 'Data.gender', 'Data.has_children', 'bmi_category']

# Physical health descriptors
PHYSICAL_HEALTH_FACTORS = [
    'Data.physical_pain', 'Data.chronic_conditions_diabetes', 'Data.chronic_conditions_obesity',
    'Data.chronic_conditions_hypertension', 'Data.chronic_conditions_heart_disease'
]

def load_and_prepare_data(input_path):
    """Load and prepare the health data for relationship analysis."""
    df = pd.read_csv(input_path)

    # Remove exclusion columns from analysis
    analysis_columns = [col for col in df.columns if col not in EXCLUSION_COLUMNS]
    df_analysis = df[analysis_columns]

    return df_analysis

def calculate_cramers_v(contingency_table):
    """Calculate Cramer's V as measure of association between categorical variables."""
    chi2, p_val, dof, expected = chi2_contingency(contingency_table)
    n = contingency_table.sum().sum()

    # Cramer's V calculation
    cramers_v = np.sqrt(chi2 / (n * (min(contingency_table.shape) - 1)))

    return cramers_v, p_val

def test_categorical_association(df, var1, var2):
    """Test association between two categorical variables."""
    # Create contingency table
    contingency_table = pd.crosstab(df[var1], df[var2])

    # Check minimum sample size requirement
    if contingency_table.min().min() < 5:
        return None

    # Calculate Cramer's V and p-value
    cramers_v, p_val = calculate_cramers_v(contingency_table)

    # Only return if effect size is meaningful
    if cramers_v >= MIN_EFFECT_SIZE and p_val < 0.05:
        return {
            'variable1': var1,
            'variable2': var2,
            'cramers_v': round(cramers_v, 3),
            'p_value': p_val,
            'sample_size': contingency_table.sum().sum(),
            'contingency_table': contingency_table
        }

    return None

def analyze_lifestyle_clustering(df, output_lines):
    """Find clustering patterns within lifestyle behaviors."""
    output_lines.append(f"\n" + "-"*60)
    output_lines.append("LIFESTYLE CLUSTERING PATTERNS")
    output_lines.append("-"*60)

    available_lifestyle = [col for col in LIFESTYLE_FACTORS if col in df.columns]
    # output_lines.append(f"\nDEBUG: Available lifestyle columns: {available_lifestyle}")

    total_pairs = len(list(combinations(available_lifestyle, 2)))
    # output_lines.append(f"DEBUG: Testing {total_pairs} lifestyle pairs")

    lifestyle_associations = []
    tested_pairs = 0
    failed_sample_size = 0
    failed_effect_size = 0
    passed_all_filters = 0

    # Test all pairs within lifestyle factors
    for var1, var2 in combinations(available_lifestyle, 2):
        tested_pairs += 1
        association = test_categorical_association(df, var1, var2)
        if association:
            lifestyle_associations.append(association)
            passed_all_filters += 1
        else:
            # Debug why this pair failed
            try:
                contingency_table = pd.crosstab(df[var1], df[var2])
                if contingency_table.min().min() < 5:
                    failed_sample_size += 1
                else:
                    cramers_v, p_val = calculate_cramers_v(contingency_table)
                    if cramers_v < MIN_EFFECT_SIZE or p_val >= 0.05:
                        failed_effect_size += 1
            except:
                failed_sample_size += 1

    # output_lines.append(f"DEBUG: Tested {tested_pairs} pairs")
    # output_lines.append(f"DEBUG: Failed sample size: {failed_sample_size}")
    # output_lines.append(f"DEBUG: Failed effect size/significance: {failed_effect_size}")
    # output_lines.append(f"DEBUG: Passed all filters: {passed_all_filters}")

    # Sort by effect size
    lifestyle_associations.sort(key=lambda x: x['cramers_v'], reverse=True)

    if lifestyle_associations:
        for assoc in lifestyle_associations[:5]:  # Top 5
            var1, var2 = assoc['variable1'], assoc['variable2']
            cramers_v = assoc['cramers_v']

            output_lines.append(f"\n• Strong Clustering: {var1} ↔ {var2} (Cramer's V = {cramers_v})")

            # Get contingency table for detailed insights
            ct = assoc['contingency_table']
            ct_prop = pd.crosstab(df[var1], df[var2], normalize='index')

            # Find most interesting patterns
            for val1 in ct.index[:3]:  # Top 3 values of var1
                for val2 in ct.columns:
                    if ct.loc[val1, val2] >= MIN_SAMPLE_SIZE:
                        segment_pct = ct_prop.loc[val1, val2] * 100
                        population_pct = (df[var2] == val2).mean() * 100

                        if abs(segment_pct - population_pct) >= MIN_PROPORTION_DIFF:
                            output_lines.append(f"  - {val1}: {segment_pct:.0f}% {val2} vs {population_pct:.0f}% population")

            # Add interpretive insight
            effect_desc = "very strong" if cramers_v > 0.5 else "strong" if cramers_v > 0.4 else "moderate"
            output_lines.append(f"  - Insight: {effect_desc} clustering between {var1.replace('Data.', '')} and {var2.replace('Data.', '')}")
    else:
        output_lines.append("\nNo strong lifestyle clustering patterns found above threshold.")

        # Fallback: Show top relationships regardless of threshold
        if tested_pairs > 0:
            output_lines.append(f"\nDEBUG: Top relationships found (regardless of threshold):")
            all_relationships = []
            for var1, var2 in combinations(available_lifestyle, 2):
                try:
                    contingency_table = pd.crosstab(df[var1], df[var2])
                    if contingency_table.min().min() >= 3:  # Very low threshold for debug
                        cramers_v, p_val = calculate_cramers_v(contingency_table)
                        all_relationships.append((var1, var2, cramers_v, p_val))
                except:
                    pass

            all_relationships.sort(key=lambda x: x[2], reverse=True)
            for var1, var2, cramers_v, p_val in all_relationships[:3]:
                output_lines.append(f"  {var1} ↔ {var2}: V={cramers_v:.3f}, p={p_val:.3f}")

def analyze_mental_health_clustering(df, output_lines):
    """Find clustering patterns within mental health factors."""
    output_lines.append(f"\n" + "-"*60)
    output_lines.append("MENTAL HEALTH CLUSTERING PATTERNS")
    output_lines.append("-"*60)

    available_mental = [col for col in MENTAL_HEALTH_FACTORS if col in df.columns]
    mental_associations = []

    # Test all pairs within mental health factors
    for var1, var2 in combinations(available_mental, 2):
        association = test_categorical_association(df, var1, var2)
        if association:
            mental_associations.append(association)

    # Sort by effect size
    mental_associations.sort(key=lambda x: x['cramers_v'], reverse=True)

    if mental_associations:
        for assoc in mental_associations[:4]:  # Top 4
            var1, var2 = assoc['variable1'], assoc['variable2']
            cramers_v = assoc['cramers_v']

            output_lines.append(f"\n• Mental Health Clustering: {var1} ↔ {var2} (V = {cramers_v})")

            # Find concerning combinations (negative mental health clustering)
            ct = assoc['contingency_table']
            ct_prop = pd.crosstab(df[var1], df[var2], normalize='index')

            # Look for high-stress/negative combinations
            negative_indicators = ['high', 'frequent', 'often', 'severe', 'persistent', 'always', 'poor', 'very_poor']

            for val1 in ct.index:
                for val2 in ct.columns:
                    if (any(neg in str(val1).lower() for neg in negative_indicators) and
                        any(neg in str(val2).lower() for neg in negative_indicators) and
                        ct.loc[val1, val2] >= MIN_SAMPLE_SIZE):

                        segment_pct = ct_prop.loc[val1, val2] * 100
                        population_pct = (df[var2] == val2).mean() * 100

                        if segment_pct > population_pct + MIN_PROPORTION_DIFF:
                            output_lines.append(f"  - {val1} individuals: {segment_pct:.0f}% also {val2} vs {population_pct:.0f}% population")

            output_lines.append(f"  - Insight: Mental health factors cluster together - addressing one may impact others")
    else:
        output_lines.append("\nNo strong mental health clustering patterns found above threshold.")

def analyze_demographic_differences(df, output_lines):
    """Analyze how demographics relate to lifestyle and health behaviors."""
    output_lines.append(f"\n" + "-"*60)
    output_lines.append("DEMOGRAPHIC BEHAVIOR DIFFERENCES")
    output_lines.append("-"*60)

    available_demographics = [col for col in DEMOGRAPHIC_FACTORS if col in df.columns]
    behavior_factors = LIFESTYLE_FACTORS + MENTAL_HEALTH_FACTORS + NUTRITION_FACTORS
    available_behaviors = [col for col in behavior_factors if col in df.columns]

    demographic_insights = []

    for demo_var in available_demographics:
        for behavior_var in available_behaviors[:10]:  # Limit to prevent explosion
            association = test_categorical_association(df, demo_var, behavior_var)
            if association:
                demographic_insights.append(association)

    # Sort by effect size and focus on interpretable differences
    demographic_insights.sort(key=lambda x: x['cramers_v'], reverse=True)

    if demographic_insights:
        # Group by demographic variable for cleaner reporting
        demo_groups = {}
        for insight in demographic_insights[:15]:  # Top 15
            demo_var = insight['variable1']
            if demo_var not in demo_groups:
                demo_groups[demo_var] = []
            demo_groups[demo_var].append(insight)

        for demo_var, insights in list(demo_groups.items())[:3]:  # Top 3 demo variables
            output_lines.append(f"\n• {demo_var.replace('Data.', '').title()} Behavior Patterns:")

            for insight in insights[:2]:  # Top 2 insights per demographic
                behavior_var = insight['variable2']
                cramers_v = insight['cramers_v']

                # Find most contrasting groups
                ct_prop = pd.crosstab(df[demo_var], df[behavior_var], normalize='index')

                # Look for biggest differences between demographic groups
                max_diff = 0
                best_contrast = None

                for demo_val in ct_prop.index:
                    for behavior_val in ct_prop.columns:
                        demo_pct = ct_prop.loc[demo_val, behavior_val] * 100
                        overall_pct = (df[behavior_var] == behavior_val).mean() * 100
                        diff = abs(demo_pct - overall_pct)

                        if diff > max_diff and diff >= MIN_PROPORTION_DIFF:
                            max_diff = diff
                            best_contrast = (demo_val, behavior_val, demo_pct, overall_pct)

                if best_contrast:
                    demo_val, behavior_val, demo_pct, overall_pct = best_contrast
                    direction = "higher" if demo_pct > overall_pct else "lower"
                    output_lines.append(f"  - {demo_val}: {demo_pct:.0f}% {behavior_val} vs {overall_pct:.0f}% population ({direction})")
    else:
        output_lines.append("\nNo strong demographic behavior differences found above threshold.")

def find_surprising_correlations(df, output_lines):
    """Find unexpected correlations between different factor groups."""
    output_lines.append(f"\n" + "-"*60)
    output_lines.append("SURPRISING CROSS-CLUSTER CORRELATIONS")
    output_lines.append("-"*60)

    # Define factor groups for cross-cluster analysis
    factor_groups = {
        'Physical Health': [col for col in PHYSICAL_HEALTH_FACTORS if col in df.columns],
        'Mental Health': [col for col in MENTAL_HEALTH_FACTORS if col in df.columns],
        'Lifestyle': [col for col in LIFESTYLE_FACTORS if col in df.columns],
        'Nutrition': [col for col in NUTRITION_FACTORS if col in df.columns]
    }

    surprising_correlations = []

    # Test correlations between different factor groups
    group_pairs = [('Physical Health', 'Mental Health'), ('Physical Health', 'Lifestyle'),
                   ('Mental Health', 'Nutrition'), ('Lifestyle', 'Nutrition')]

    for group1_name, group2_name in group_pairs:
        group1_vars = factor_groups[group1_name]
        group2_vars = factor_groups[group2_name]

        for var1 in group1_vars[:3]:  # Limit to prevent explosion
            for var2 in group2_vars[:3]:
                association = test_categorical_association(df, var1, var2)
                if association:
                    association['group1'] = group1_name
                    association['group2'] = group2_name
                    surprising_correlations.append(association)

    # Sort by effect size
    surprising_correlations.sort(key=lambda x: x['cramers_v'], reverse=True)

    if surprising_correlations:
        output_lines.append(f"\nUnexpected relationships between factor groups:")

        for assoc in surprising_correlations[:5]:  # Top 5 surprising correlations
            var1, var2 = assoc['variable1'], assoc['variable2']
            cramers_v = assoc['cramers_v']
            group1, group2 = assoc['group1'], assoc['group2']

            output_lines.append(f"\n• {group1} ↔ {group2}: {var1} × {var2} (V = {cramers_v})")

            # Find the most striking association
            ct_prop = pd.crosstab(df[var1], df[var2], normalize='index')

            max_deviation = 0
            best_example = None

            for val1 in ct_prop.index:
                for val2 in ct_prop.columns:
                    segment_pct = ct_prop.loc[val1, val2] * 100
                    population_pct = (df[var2] == val2).mean() * 100
                    deviation = abs(segment_pct - population_pct)

                    if deviation > max_deviation and deviation >= MIN_PROPORTION_DIFF:
                        max_deviation = deviation
                        best_example = (val1, val2, segment_pct, population_pct)

            if best_example:
                val1, val2, segment_pct, population_pct = best_example
                output_lines.append(f"  - {val1}: {segment_pct:.0f}% {val2} vs {population_pct:.0f}% population")
                output_lines.append(f"  - Insight: {var1.replace('Data.', '')} and {var2.replace('Data.', '')} show unexpected correlation")
    else:
        output_lines.append("\nNo surprising cross-cluster correlations found above threshold.")

def generate_summary_insights(df, output_lines):
    """Generate high-level summary insights about column relationships."""
    output_lines.append(f"\n" + "="*80)
    output_lines.append("RELATIONSHIP ANALYSIS SUMMARY")
    output_lines.append("="*80)

    # Count available variables by category
    lifestyle_count = len([col for col in LIFESTYLE_FACTORS if col in df.columns])
    mental_count = len([col for col in MENTAL_HEALTH_FACTORS if col in df.columns])
    nutrition_count = len([col for col in NUTRITION_FACTORS if col in df.columns])
    demo_count = len([col for col in DEMOGRAPHIC_FACTORS if col in df.columns])
    physical_count = len([col for col in PHYSICAL_HEALTH_FACTORS if col in df.columns])

    output_lines.append(f"Total records analyzed: {len(df)}")
    output_lines.append(f"Variables analyzed by category:")
    output_lines.append(f"  - Demographics: {demo_count}")
    output_lines.append(f"  - Lifestyle factors: {lifestyle_count}")
    output_lines.append(f"  - Mental health factors: {mental_count}")
    output_lines.append(f"  - Nutrition factors: {nutrition_count}")
    output_lines.append(f"  - Physical health factors: {physical_count}")

    output_lines.append(f"\nAnalysis parameters:")
    output_lines.append(f"  - Minimum effect size (Cramer's V): {MIN_EFFECT_SIZE}")
    output_lines.append(f"  - Minimum sample size per cell: {MIN_SAMPLE_SIZE}")
    output_lines.append(f"  - Minimum proportion difference: {MIN_PROPORTION_DIFF}%")

    output_lines.append(f"\nThis analysis reveals descriptive relationships between employee characteristics,")
    output_lines.append(f"behaviors, and health factors independent of outcome prediction.")
    output_lines.append(f"Findings help understand employee behavior patterns and clustering for targeted interventions.")

def run_column_relationship_analysis(input_path, output_path):
    """Run comprehensive column relationship analysis and output to text file."""
    output_lines = []

    # Load and prepare data
    df = load_and_prepare_data(input_path)

    output_lines.append("="*80)
    output_lines.append("COLUMN RELATIONSHIP ANALYSIS REPORT")
    output_lines.append("="*80)

    output_lines.append(f"\nDataset: {df.shape[0]} records, {df.shape[1]} variables")
    output_lines.append(f"Analysis focus: Descriptive-to-descriptive relationships")
    output_lines.append(f"Excluded from analysis: {', '.join(EXCLUSION_COLUMNS)}")

    # Debug: Show all available columns
    # output_lines.append(f"\nDEBUG: All available columns: {list(df.columns)}")

    # Debug: Check which factor columns exist
    lifestyle_found = [col for col in LIFESTYLE_FACTORS if col in df.columns]
    mental_found = [col for col in MENTAL_HEALTH_FACTORS if col in df.columns]
    demo_found = [col for col in DEMOGRAPHIC_FACTORS if col in df.columns]
    nutrition_found = [col for col in NUTRITION_FACTORS if col in df.columns]
    physical_found = [col for col in PHYSICAL_HEALTH_FACTORS if col in df.columns]

    # output_lines.append(f"\nDEBUG: Factor columns found:")
    # output_lines.append(f"  Lifestyle: {lifestyle_found}")
    # output_lines.append(f"  Mental Health: {mental_found}")
    # output_lines.append(f"  Demographics: {demo_found}")
    # output_lines.append(f"  Nutrition: {nutrition_found}")
    # output_lines.append(f"  Physical Health: {physical_found}")

    # Run core analyses
    analyze_lifestyle_clustering(df, output_lines)
    analyze_mental_health_clustering(df, output_lines)
    analyze_demographic_differences(df, output_lines)
    find_surprising_correlations(df, output_lines)

    # Generate summary
    generate_summary_insights(df, output_lines)

    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

def main():
    parser = argparse.ArgumentParser(description='Column Relationship Analysis for Health Risk Assessment')
    parser.add_argument('input_path', help='Path to the input CSV file')
    parser.add_argument('output_path', help='Path to the output text file')

    args = parser.parse_args()

    # Validate input path
    if not Path(args.input_path).exists():
        print(f"Error: Input file not found: {args.input_path}")
        return

    # Run analysis
    run_column_relationship_analysis(args.input_path, args.output_path)

    print(f"✓ Column relationship analysis complete. Results saved to: {args.output_path}")

if __name__ == "__main__":
    main()