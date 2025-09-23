#!/usr/bin/env python3
"""
Streamlined Health Risk Assessment EDA Analysis
A single-phase comprehensive exploratory data analysis tool for employee health risk data.
Outputs analysis to a text file for LLM consumption.

Usage:
    python simple_eda_refactored.py input_path output_path
"""

import pandas as pd
import numpy as np
import argparse
import json
from pathlib import Path
from scipy.stats import chi2_contingency, spearmanr
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# Import standardized column categories
from categories import (
    EXCLUSION_COLUMNS,
    OUTCOME_COLUMNS,
    DEMOGRAPHIC_VARIABLES,
    LIFESTYLE_FACTORS,
    STRESS_FACTORS,
    NUTRITION_FACTORS,
    PHYSICAL_HEALTH_FACTORS,
    CHRONIC_CONDITION_FACTORS,
    NON_EXCLUDED_NON_TARGET_COLUMNS
)

def load_and_prepare_data(input_path):
    """Load and prepare the health risk assessment data."""
    df = pd.read_csv(input_path)

    # Remove exclusion columns from analysis
    analysis_columns = [col for col in df.columns if col not in EXCLUSION_COLUMNS]
    df_analysis = df[analysis_columns]

    # Identify column types
    numeric_cols = df_analysis.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df_analysis.select_dtypes(include=['object']).columns.tolist()

    return df_analysis, numeric_cols, categorical_cols

def analyze_dataset_overview(df, output_lines):
    """Analyze overall dataset characteristics."""
    output_lines.append("="*80)
    output_lines.append("COMPREHENSIVE HEALTH RISK ASSESSMENT DATA ANALYSIS")
    output_lines.append("="*80)

    output_lines.append(f"\nDATASET OVERVIEW:")
    output_lines.append(f"Shape: {df.shape[0]} records × {df.shape[1]} columns")
    output_lines.append(f"Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    output_lines.append(f"Duplicate Records: {df.duplicated().sum()} ({df.duplicated().sum()/len(df)*100:.1f}%)")

    # Excluded columns info
    output_lines.append(f"\nEXCLUDED FROM ANALYSIS:")
    output_lines.append(f"ID Columns: {', '.join(EXCLUSION_COLUMNS)}")
    output_lines.append("These columns contain unique identifiers and are not included in statistical analysis")

def analyze_missing_data(df, output_lines):
    """Analyze missing data patterns."""
    output_lines.append(f"\nMISSING DATA ANALYSIS:")
    missing_summary = df.isnull().sum()
    missing_pct = (missing_summary / len(df)) * 100
    missing_df = pd.DataFrame({
        'Missing_Count': missing_summary,
        'Missing_Pct': missing_pct
    }).sort_values('Missing_Pct', ascending=False)

    if missing_df['Missing_Pct'].max() > 0:
        output_lines.append("Columns with missing values:")
        for col, row in missing_df[missing_df['Missing_Pct'] > 0].iterrows():
            output_lines.append(f"  {col}: {int(row['Missing_Count'])} missing ({row['Missing_Pct']:.1f}%)")
    else:
        output_lines.append("✓ No missing values detected in any column")

def analyze_numeric_columns(df, numeric_cols, output_lines):
    """Comprehensive analysis of all numeric columns."""
    if not numeric_cols:
        return

    output_lines.append(f"\n" + "-"*60)
    output_lines.append(f"NUMERIC COLUMNS COMPREHENSIVE STATISTICS ({len(numeric_cols)} columns)")
    output_lines.append("-"*60)

    for col in numeric_cols:
        output_lines.append(f"\n{col.upper()}:")
        series = df[col].dropna()

        if len(series) == 0:
            output_lines.append("  No data available")
            continue

        # Basic statistics
        output_lines.append(f"  Count: {len(series)} | Missing: {df[col].isnull().sum()}")
        output_lines.append(f"  Mean: {series.mean():.3f} | Std: {series.std():.3f}")
        output_lines.append(f"  Min: {series.min():.3f} | Max: {series.max():.3f}")
        output_lines.append(f"  Q1: {series.quantile(0.25):.3f} | Median: {series.median():.3f} | Q3: {series.quantile(0.75):.3f}")

        # Outliers using IQR method
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = ((series < lower_bound) | (series > upper_bound)).sum()
        output_lines.append(f"  Outliers (IQR): {outliers} ({outliers/len(series)*100:.1f}%)")

        # Distribution characteristics
        skewness = series.skew()
        kurtosis = series.kurtosis()
        output_lines.append(f"  Skewness: {skewness:.3f} | Kurtosis: {kurtosis:.3f}")

        # Unique values info
        unique_count = series.nunique()
        output_lines.append(f"  Unique Values: {unique_count} ({unique_count/len(series)*100:.1f}% of records)")

        # Show value distribution for discrete-like numeric variables
        if unique_count <= 20:
            output_lines.append(f"  Value Distribution:")
            value_counts = series.value_counts().head(10)
            for val, count in value_counts.items():
                output_lines.append(f"    {val}: {count} ({count/len(series)*100:.1f}%)")

def analyze_categorical_columns(df, categorical_cols, output_lines):
    """Comprehensive analysis of all categorical columns."""
    if not categorical_cols:
        return

    output_lines.append(f"\n" + "-"*60)
    output_lines.append(f"CATEGORICAL COLUMNS COMPREHENSIVE STATISTICS ({len(categorical_cols)} columns)")
    output_lines.append("-"*60)

    for col in categorical_cols:
        output_lines.append(f"\n{col.upper()}:")
        series = df[col].dropna()

        if len(series) == 0:
            output_lines.append("  No data available")
            continue

        # Basic info
        unique_count = series.nunique()
        total_count = len(series)
        missing_count = df[col].isnull().sum()

        output_lines.append(f"  Count: {total_count} | Missing: {missing_count}")
        output_lines.append(f"  Unique Values: {unique_count}")

        # Value distribution
        value_counts = series.value_counts()
        output_lines.append(f"  Value Distribution:")

        # Show top values (all if ≤20, otherwise top 15)
        show_count = min(unique_count, 20) if unique_count <= 20 else 15
        for val, count in value_counts.head(show_count).items():
            pct = count / total_count * 100
            output_lines.append(f"    {val}: {count} ({pct:.1f}%)")

        if unique_count > 20:
            output_lines.append(f"    ... and {unique_count - 15} more unique values")

        # Concentration analysis
        top_3_pct = value_counts.head(3).sum() / total_count * 100
        output_lines.append(f"  Concentration: Top 3 values represent {top_3_pct:.1f}% of data")

        # Diversity analysis
        probabilities = value_counts / total_count
        entropy = -np.sum(probabilities * np.log2(probabilities))
        max_entropy = np.log2(unique_count) if unique_count > 1 else 0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        output_lines.append(f"  Diversity Score: {normalized_entropy:.3f} (0=concentrated, 1=evenly distributed)")

def analyze_numeric_correlations(df, numeric_cols, output_lines):
    """Analyze correlations between numeric variables."""
    if len(numeric_cols) < 2:
        return

    output_lines.append(f"\n" + "-"*60)
    output_lines.append("NUMERIC CORRELATIONS ANALYSIS")
    output_lines.append("-"*60)

    numeric_df = df[numeric_cols].dropna()

    # Spearman correlation (better for ordinal/non-normal data)
    corr_matrix = numeric_df.corr(method='spearman')

    correlations = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            var1, var2 = corr_matrix.columns[i], corr_matrix.columns[j]
            corr_val = corr_matrix.iloc[i, j]

            if not np.isnan(corr_val):
                correlations.append((var1, var2, corr_val))

    # Sort by absolute correlation strength
    correlations.sort(key=lambda x: abs(x[2]), reverse=True)

    if correlations:
        output_lines.append(f"\nStrong Correlations (|r| > 0.5):")
        strong_corrs = [(v1, v2, r) for v1, v2, r in correlations if abs(r) > 0.5]

        if strong_corrs:
            for var1, var2, corr_val in strong_corrs:
                output_lines.append(f"  {var1} ↔ {var2}: r = {corr_val:.3f}")
        else:
            output_lines.append("  No strong correlations found")

        output_lines.append(f"\nModerate Correlations (0.3 < |r| ≤ 0.5):")
        moderate_corrs = [(v1, v2, r) for v1, v2, r in correlations if 0.3 < abs(r) <= 0.5]

        if moderate_corrs:
            for var1, var2, corr_val in moderate_corrs[:10]:
                output_lines.append(f"  {var1} ↔ {var2}: r = {corr_val:.3f}")
        else:
            output_lines.append("  No moderate correlations found")

    # Health Risk Score specific correlations
    health_risk_cols = [col for col in numeric_df.columns if 'health' in col.lower() and 'risk' in col.lower()]
    for risk_col in health_risk_cols:
        if risk_col in numeric_df.columns:
            output_lines.append(f"\n{risk_col.upper()} CORRELATIONS:")
            risk_corrs = []

            for col in numeric_df.columns:
                if col != risk_col:
                    corr_val = corr_matrix.loc[risk_col, col]
                    if not np.isnan(corr_val) and abs(corr_val) > 0.1:
                        risk_corrs.append((col, corr_val))

            risk_corrs.sort(key=lambda x: abs(x[1]), reverse=True)

            if risk_corrs:
                for col, corr_val in risk_corrs[:10]:
                    significance = "***" if abs(corr_val) > 0.5 else "**" if abs(corr_val) > 0.3 else "*"
                    output_lines.append(f"  {col}: r = {corr_val:.3f} {significance}")

def analyze_cross_patterns(df, group1_vars, group2_vars, analysis_name, output_lines):
    """Perform cross-tabulation analysis between two groups of categorical variables."""
    available_group1 = [var for var in group1_vars if var in df.columns]
    available_group2 = [var for var in group2_vars if var in df.columns]

    if not available_group1 or not available_group2:
        return

    output_lines.append(f"\n{analysis_name}:")

    significant_pairs = []

    for var1 in available_group1:
        for var2 in available_group2:
            if var1 != var2:
                contingency_table = pd.crosstab(df[var1], df[var2])

                if contingency_table.size > 0 and contingency_table.min().min() >= 1:
                    chi2, p_val, dof, expected = chi2_contingency(contingency_table)

                    # Calculate effect size (Cramer's V)
                    n = contingency_table.sum().sum()
                    cramers_v = np.sqrt(chi2 / (n * (min(contingency_table.shape) - 1)))

                    if p_val < 0.05:
                        significant_pairs.append((var1, var2, chi2, p_val, cramers_v, contingency_table))

    # Sort by effect size (Cramer's V)
    significant_pairs.sort(key=lambda x: x[4], reverse=True)

    if significant_pairs:
        for var1, var2, chi2, p_val, cramers_v, contingency_table in significant_pairs[:5]:
            significance = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*"
            output_lines.append(f"  {var1} × {var2}: χ² = {chi2:.2f}, p = {p_val:.3f} {significance}, Effect = {cramers_v:.3f}")

            if cramers_v > 0.3:
                output_lines.append(f"    Cross-tabulation percentages (row percentages):")
                prop_table = pd.crosstab(df[var1], df[var2], normalize='index') * 100
                for idx, row in prop_table.iterrows():
                    output_lines.append(f"      {idx}: " + " | ".join([f"{col}={val:.1f}%" for col, val in row.items()]))
    else:
        output_lines.append("  No significant associations found")

def analyze_age_patterns(df, output_lines):
    """Analyze patterns specific to different age groups."""
    if 'age_group' not in df.columns:
        return

    output_lines.append(f"\n" + "-"*60)
    output_lines.append("AGE-SPECIFIC PATTERN ANALYSIS")
    output_lines.append("-"*60)

    age_groups = df['age_group'].value_counts().index.tolist()

    output_lines.append(f"\nAge Group Distribution:")
    for age_group, count in df['age_group'].value_counts().items():
        pct = count / len(df) * 100
        output_lines.append(f"  {age_group}: {count} ({pct:.1f}%)")

    # Health outcomes by age
    available_outcomes = [col for col in OUTCOME_COLUMNS if col in df.columns]
    if available_outcomes:
        output_lines.append(f"\nHealth Outcomes by Age:")
        for outcome_var in available_outcomes:
            output_lines.append(f"\n  {outcome_var.upper()} by age group:")
            age_outcome = pd.crosstab(df['age_group'], df[outcome_var], normalize='index')

            for age_group in age_groups[:5]:
                if age_group in age_outcome.index:
                    risk_cols = [col for col in age_outcome.columns
                               if any(risk_word in str(col).lower()
                                     for risk_word in ['high', 'risk', 'obese', 'poor', 'bad'])]

                    if risk_cols:
                        risk_pct = age_outcome.loc[age_group, risk_cols].sum() * 100
                        output_lines.append(f"    {age_group}: {risk_pct:.1f}% high risk indicators")

    # Lifestyle patterns by age
    available_lifestyle = [col for col in LIFESTYLE_FACTORS if col in df.columns]
    if available_lifestyle:
        output_lines.append(f"\nLifestyle Patterns by Age:")

        for lifestyle_var in available_lifestyle[:3]:
            output_lines.append(f"\n  {lifestyle_var.upper()}:")

            for age_group in age_groups[:4]:
                if age_group in df['age_group'].values:
                    age_subset = df[df['age_group'] == age_group]
                    lifestyle_dist = age_subset[lifestyle_var].value_counts(normalize=True)

                    negative_patterns = [val for val in lifestyle_dist.index
                                       if any(neg_word in str(val).lower()
                                             for neg_word in ['no', 'never', 'poor', 'excessive', 'heavy', 'daily'])]

                    if negative_patterns:
                        negative_pct = lifestyle_dist.loc[negative_patterns].sum() * 100
                        output_lines.append(f"    {age_group}: {negative_pct:.1f}% concerning patterns")

def analyze_high_risk_patterns(df, output_lines):
    """Deep dive into high-risk employee patterns."""
    high_risk_col = None
    for col in df.columns:
        if 'health_risk_level' in col.lower() or ('health' in col.lower() and 'risk' in col.lower() and 'level' in col.lower()):
            high_risk_col = col
            break

    if not high_risk_col:
        return

    output_lines.append(f"\n" + "-"*60)
    output_lines.append("HIGH-RISK GROUP DEEP DIVE ANALYSIS")
    output_lines.append("-"*60)

    # Identify high risk values
    unique_vals = df[high_risk_col].value_counts()
    high_risk_values = [val for val in unique_vals.index if 'high' in str(val).lower()]

    if not high_risk_values:
        output_lines.append("No high-risk categories identified in the data.")
        return

    high_risk_df = df[df[high_risk_col].isin(high_risk_values)]
    total_high_risk = len(high_risk_df)

    output_lines.append(f"High-risk employees: {total_high_risk} ({total_high_risk/len(df)*100:.1f}% of population)")

    # Demographics of high-risk group
    available_demographics = [col for col in DEMOGRAPHIC_VARIABLES if col in df.columns]
    if available_demographics:
        output_lines.append(f"\nDemographic Profile of High-Risk Group:")
        for demo_var in available_demographics:
            output_lines.append(f"\n  {demo_var.upper()}:")
            high_risk_dist = high_risk_df[demo_var].value_counts()

            for val, count in high_risk_dist.head(5).items():
                overall_pct = (df[demo_var] == val).mean() * 100
                high_risk_pct = count / total_high_risk * 100

                risk_ratio = high_risk_pct / overall_pct if overall_pct > 0 else 0
                output_lines.append(f"    {val}: {count} ({high_risk_pct:.1f}%) - Risk Ratio: {risk_ratio:.2f}x")

    # Lifestyle factors in high-risk group
    available_lifestyle = [col for col in LIFESTYLE_FACTORS if col in df.columns]
    if available_lifestyle:
        output_lines.append(f"\nLifestyle Risk Factors:")
        for lifestyle_var in available_lifestyle[:5]:
            output_lines.append(f"\n  {lifestyle_var.upper()}:")
            high_risk_dist = high_risk_df[lifestyle_var].value_counts(normalize=True)

            for val, prop in high_risk_dist.head(3).items():
                output_lines.append(f"    {val}: {prop*100:.1f}%")

def run_comprehensive_analysis(input_path, output_path):
    """Run comprehensive EDA analysis and output to text file."""
    output_lines = []

    # Load and prepare data
    df, numeric_cols, categorical_cols = load_and_prepare_data(input_path)


    # Dataset overview
    analyze_dataset_overview(df, output_lines)

    # Missing data analysis
    analyze_missing_data(df, output_lines)

    # Numeric columns analysis
    analyze_numeric_columns(df, numeric_cols, output_lines)

    # Categorical columns analysis
    analyze_categorical_columns(df, categorical_cols, output_lines)

    # Numeric correlations
    analyze_numeric_correlations(df, numeric_cols, output_lines)

    # Cross-pattern analysis
    output_lines.append(f"\n" + "="*80)
    output_lines.append("CROSS-PATTERN RELATIONSHIP ANALYSIS")
    output_lines.append("="*80)

    analyze_cross_patterns(df, DEMOGRAPHIC_VARIABLES, OUTCOME_COLUMNS,
                          "DEMOGRAPHICS vs HEALTH OUTCOMES", output_lines)

    analyze_cross_patterns(df, DEMOGRAPHIC_VARIABLES, LIFESTYLE_FACTORS,
                          "DEMOGRAPHICS vs LIFESTYLE PATTERNS", output_lines)

    analyze_cross_patterns(df, LIFESTYLE_FACTORS, OUTCOME_COLUMNS,
                          "LIFESTYLE vs HEALTH OUTCOMES", output_lines)

    analyze_cross_patterns(df, STRESS_FACTORS, OUTCOME_COLUMNS,
                          "MENTAL HEALTH vs HEALTH OUTCOMES", output_lines)

    analyze_cross_patterns(df, NUTRITION_FACTORS, OUTCOME_COLUMNS,
                          "NUTRITION vs HEALTH OUTCOMES", output_lines)

    analyze_cross_patterns(df, CHRONIC_CONDITION_FACTORS, OUTCOME_COLUMNS,
                          "CHRONIC CONDITIONS vs HEALTH OUTCOMES", output_lines)

    # Age-specific analysis
    analyze_age_patterns(df, output_lines)

    # High-risk group analysis
    analyze_high_risk_patterns(df, output_lines)

    # Summary
    output_lines.append(f"\n" + "="*80)
    output_lines.append("ANALYSIS SUMMARY")
    output_lines.append("="*80)
    output_lines.append(f"Total records analyzed: {len(df)}")
    output_lines.append(f"Total variables analyzed: {len(df.columns)}")
    output_lines.append(f"Variables excluded: {len(EXCLUSION_COLUMNS)} ({', '.join(EXCLUSION_COLUMNS)})")
    output_lines.append(f"Numeric variables: {len(numeric_cols)}")
    output_lines.append(f"Categorical variables: {len(categorical_cols)}")
    output_lines.append(f"Statistical significance threshold used: 0.05")
    output_lines.append("\nThis analysis provides comprehensive insights into employee health risk patterns")
    output_lines.append("suitable for LLM interpretation and further analysis.")

    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

def main():
    parser = argparse.ArgumentParser(description='Streamlined Health Risk Assessment EDA Analysis')
    parser.add_argument('input_path', help='Path to the input CSV file')
    parser.add_argument('output_path', help='Path to the output text file')

    args = parser.parse_args()

    # Validate input path
    if not Path(args.input_path).exists():
        print(f"Error: Input file not found: {args.input_path}")
        return

    # Run analysis
    run_comprehensive_analysis(args.input_path, args.output_path)

    print(f"✓ Comprehensive EDA analysis complete. Results saved to: {args.output_path}")

if __name__ == "__main__":
    main()