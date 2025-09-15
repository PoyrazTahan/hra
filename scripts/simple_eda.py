#!/usr/bin/env python3
"""
Health Risk Assessment EDA Pipeline
A two-phase exploratory data analysis tool for employee health risk data.

Usage:
    python simple_eda.py --phase 1                    # Complete 1D statistics dump
    python simple_eda.py --phase 2                    # Multi-dimensional cross-patterns
    python simple_eda.py --phase all                  # Both phases sequentially
"""

import pandas as pd
import numpy as np
import argparse
import sys
import io
import contextlib
from pathlib import Path
from scipy import stats
from scipy.stats import chi2_contingency, spearmanr, kruskal
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

class HealthRiskEDA:
    def __init__(self, data_path, verbose=False):
        self.data_path = data_path
        self.verbose = verbose
        self.df = None
        self.numeric_cols = []
        self.categorical_cols = []
        
    def load_data(self):
        """Load and prepare the health risk assessment data."""
        try:
            self.df = pd.read_csv(self.data_path)
            print(f"✓ Data loaded successfully: {self.df.shape[0]} records, {self.df.shape[1]} columns")
            
            # Identify column types
            self.numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            self.categorical_cols = self.df.select_dtypes(include=['object']).columns.tolist()
            
            if self.verbose:
                print(f"  - Numeric columns: {len(self.numeric_cols)}")
                print(f"  - Categorical columns: {len(self.categorical_cols)}")
                
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            sys.exit(1)
    
    def phase1_one_dimensional_stats(self):
        """Phase 1: Complete dump of all one-dimensional statistics for every column."""
        print("\n" + "="*80)
        print("PHASE 1: ONE-DIMENSIONAL STATISTICS DUMP")
        print("="*80)
        
        # Dataset Overview
        print(f"\nDATASET OVERVIEW:")
        print(f"Shape: {self.df.shape[0]} rows × {self.df.shape[1]} columns")
        print(f"Memory Usage: {self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        print(f"Duplicate Records: {self.df.duplicated().sum()} ({self.df.duplicated().sum()/len(self.df)*100:.1f}%)")
        
        # Missing Data Analysis
        print(f"\nMISSING DATA ANALYSIS:")
        missing_summary = self.df.isnull().sum()
        missing_pct = (missing_summary / len(self.df)) * 100
        missing_df = pd.DataFrame({
            'Missing_Count': missing_summary,
            'Missing_Pct': missing_pct
        }).sort_values('Missing_Pct', ascending=False)
        
        if missing_df['Missing_Pct'].max() > 0:
            print(missing_df[missing_df['Missing_Pct'] > 0])
        else:
            print("✓ No missing values detected")
        
        # NUMERIC COLUMNS COMPREHENSIVE STATISTICS
        if self.numeric_cols:
            print(f"\n" + "-"*60)
            print(f"NUMERIC COLUMNS STATISTICS ({len(self.numeric_cols)} columns)")
            print("-"*60)
            
            for col in self.numeric_cols:
                print(f"\n{col.upper()}:")
                series = self.df[col].dropna()
                
                if len(series) == 0:
                    print("  No data available")
                    continue
                
                # Basic statistics
                print(f"  Count: {len(series)} | Missing: {self.df[col].isnull().sum()}")
                print(f"  Mean: {series.mean():.3f} | Std: {series.std():.3f}")
                print(f"  Min: {series.min():.3f} | Max: {series.max():.3f}")
                print(f"  Q1: {series.quantile(0.25):.3f} | Median: {series.median():.3f} | Q3: {series.quantile(0.75):.3f}")
                
                # Outliers using IQR method
                q1, q3 = series.quantile(0.25), series.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = ((series < lower_bound) | (series > upper_bound)).sum()
                print(f"  Outliers (IQR): {outliers} ({outliers/len(series)*100:.1f}%)")
                
                # Distribution characteristics
                skewness = series.skew()
                kurtosis = series.kurtosis()
                print(f"  Skewness: {skewness:.3f} | Kurtosis: {kurtosis:.3f}")
                
                # Unique values info
                unique_count = series.nunique()
                print(f"  Unique Values: {unique_count} ({unique_count/len(series)*100:.1f}% of records)")
                
                if self.verbose and unique_count <= 10:
                    value_counts = series.value_counts().head(10)
                    print(f"  Value Distribution:")
                    for val, count in value_counts.items():
                        print(f"    {val}: {count} ({count/len(series)*100:.1f}%)")
        
        # CATEGORICAL COLUMNS COMPREHENSIVE STATISTICS  
        if self.categorical_cols:
            print(f"\n" + "-"*60)
            print(f"CATEGORICAL COLUMNS STATISTICS ({len(self.categorical_cols)} columns)")
            print("-"*60)
            
            for col in self.categorical_cols:
                print(f"\n{col.upper()}:")
                series = self.df[col].dropna()
                
                if len(series) == 0:
                    print("  No data available")
                    continue
                
                # Basic info
                unique_count = series.nunique()
                total_count = len(series)
                missing_count = self.df[col].isnull().sum()
                
                print(f"  Count: {total_count} | Missing: {missing_count}")
                print(f"  Unique Values: {unique_count}")
                
                # Value distribution
                value_counts = series.value_counts()
                print(f"  Value Distribution:")
                
                # Show top values (all if ≤20, otherwise top 15)
                show_count = min(unique_count, 20) if unique_count <= 20 else 15
                for val, count in value_counts.head(show_count).items():
                    pct = count / total_count * 100
                    print(f"    {val}: {count} ({pct:.1f}%)")
                
                if unique_count > 20:
                    print(f"    ... and {unique_count - 15} more unique values")
                
                # Concentration analysis
                top_3_pct = value_counts.head(3).sum() / total_count * 100
                print(f"  Concentration: Top 3 values = {top_3_pct:.1f}% of data")
                
                if self.verbose:
                    # Entropy (diversity measure)
                    probabilities = value_counts / total_count
                    entropy = -np.sum(probabilities * np.log2(probabilities))
                    max_entropy = np.log2(unique_count) if unique_count > 1 else 0
                    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
                    print(f"  Diversity Score: {normalized_entropy:.3f} (0=uniform, 1=max diversity)")
    
    def phase2_multi_dimensional_patterns(self):
        """Phase 2: Multi-dimensional cross-pattern analysis to discover interesting relationships."""
        print("\n" + "="*80)
        print("PHASE 2: MULTI-DIMENSIONAL CROSS-PATTERN ANALYSIS")  
        print("="*80)
        
        # Key demographic and outcome variables for cross-analysis
        key_demographics = ['age_group', 'gender', 'has_children']
        key_outcomes = ['health_risk_level', 'health_risk_score', 'bmi_category']
        key_lifestyle = ['smoking_status', 'alcohol_level', 'exercise_freq', 'nutrition_quality', 'sleep_duration']
        key_health = ['chronic_conditions', 'mood_positivity', 'stress_calm', 'depression_mood', 'pain_level']
        
        available_demographics = [col for col in key_demographics if col in self.df.columns]
        available_outcomes = [col for col in key_outcomes if col in self.df.columns]  
        available_lifestyle = [col for col in key_lifestyle if col in self.df.columns]
        available_health = [col for col in key_health if col in self.df.columns]
        
        # CORRELATIONS: Numeric variable relationships
        self._analyze_numeric_correlations()
        
        # CROSS-TABULATIONS: Categorical associations
        print(f"\n" + "-"*60)
        print("CATEGORICAL CROSS-PATTERN ANALYSIS")
        print("-"*60)
        
        # Demographics vs Outcomes
        self._cross_analyze_categories("DEMOGRAPHICS vs OUTCOMES", available_demographics, available_outcomes)
        
        # Demographics vs Lifestyle  
        self._cross_analyze_categories("DEMOGRAPHICS vs LIFESTYLE", available_demographics, available_lifestyle)
        
        # Lifestyle vs Health Outcomes
        self._cross_analyze_categories("LIFESTYLE vs HEALTH OUTCOMES", available_lifestyle, available_outcomes)
        
        # Health Conditions vs Mental Health
        mental_health_vars = [col for col in available_health if any(x in col.lower() for x in ['mood', 'stress', 'depression'])]
        physical_health_vars = [col for col in available_health + available_outcomes if any(x in col.lower() for x in ['chronic', 'pain', 'bmi', 'risk'])]
        
        if mental_health_vars and physical_health_vars:
            self._cross_analyze_categories("MENTAL vs PHYSICAL HEALTH", mental_health_vars, physical_health_vars)
        
        # AGE-SPECIFIC PATTERN ANALYSIS
        if 'age_group' in self.df.columns:
            self._analyze_age_specific_patterns(available_lifestyle, available_health, available_outcomes)
        
        # HIGH-RISK GROUP DEEP DIVE
        if 'health_risk_level' in self.df.columns:
            self._analyze_high_risk_patterns(available_demographics, available_lifestyle, available_health)
    
    def _analyze_numeric_correlations(self):
        """Analyze correlations between numeric variables."""
        if len(self.numeric_cols) < 2:
            return
            
        print(f"\n" + "-"*60)
        print("NUMERIC CORRELATIONS")
        print("-"*60)
        
        numeric_df = self.df[self.numeric_cols].dropna()
        
        # Spearman correlation (better for ordinal/non-normal data)
        corr_matrix = numeric_df.corr(method='spearman')
        
        print(f"\nCORRELATION STRENGTH ANALYSIS:")
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
            print(f"Strong Correlations (|r| > 0.5):")
            strong_corrs = [(v1, v2, r) for v1, v2, r in correlations if abs(r) > 0.5]
            
            if strong_corrs:
                for var1, var2, corr_val in strong_corrs:
                    print(f"  {var1} ↔ {var2}: r = {corr_val:.3f}")
            else:
                print("  No strong correlations found")
            
            print(f"\nModerate Correlations (0.3 < |r| ≤ 0.5):")
            moderate_corrs = [(v1, v2, r) for v1, v2, r in correlations if 0.3 < abs(r) <= 0.5]
            
            if moderate_corrs:
                for var1, var2, corr_val in moderate_corrs[:10]:  # Top 10
                    print(f"  {var1} ↔ {var2}: r = {corr_val:.3f}")
            else:
                print("  No moderate correlations found")
        
        # Health Risk Score specific correlations
        if 'health_risk_score' in numeric_df.columns:
            print(f"\nHEALTH RISK SCORE CORRELATIONS:")
            risk_corrs = []
            
            for col in numeric_df.columns:
                if col != 'health_risk_score':
                    corr_val = corr_matrix.loc['health_risk_score', col]
                    if not np.isnan(corr_val) and abs(corr_val) > 0.1:
                        risk_corrs.append((col, corr_val))
            
            risk_corrs.sort(key=lambda x: abs(x[1]), reverse=True)
            
            if risk_corrs:
                for col, corr_val in risk_corrs[:10]:
                    significance = "***" if abs(corr_val) > 0.5 else "**" if abs(corr_val) > 0.3 else "*"
                    print(f"  {col}: r = {corr_val:.3f} {significance}")
    
    def _cross_analyze_categories(self, analysis_name, group1_vars, group2_vars):
        """Perform cross-tabulation analysis between two groups of categorical variables."""
        if not group1_vars or not group2_vars:
            return
            
        print(f"\n{analysis_name}:")
        
        significant_pairs = []
        
        for var1 in group1_vars:
            for var2 in group2_vars:
                if var1 != var2 and var1 in self.df.columns and var2 in self.df.columns:
                    try:
                        # Create contingency table
                        contingency_table = pd.crosstab(self.df[var1], self.df[var2])
                        
                        if contingency_table.size > 0:
                            # Chi-square test
                            chi2, p_val, dof, expected = chi2_contingency(contingency_table)
                            
                            # Calculate effect size (Cramer's V)
                            n = contingency_table.sum().sum()
                            cramers_v = np.sqrt(chi2 / (n * (min(contingency_table.shape) - 1)))
                            
                            # Determine significance  
                            significance = ""
                            if p_val < 0.001:
                                significance = " (***)"
                            elif p_val < 0.01:
                                significance = " (**)" 
                            elif p_val < 0.05:
                                significance = " (*)"
                            
                            if p_val < 0.05:  # Only show significant relationships
                                significant_pairs.append((var1, var2, chi2, p_val, cramers_v, contingency_table))
                                
                    except Exception as e:
                        continue
        
        # Sort by effect size (Cramer's V)
        significant_pairs.sort(key=lambda x: x[4], reverse=True)
        
        if significant_pairs:
            for var1, var2, chi2, p_val, cramers_v, contingency_table in significant_pairs[:5]:  # Top 5
                significance = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*"
                print(f"  {var1} × {var2}: χ² = {chi2:.2f}, p = {p_val:.3f} {significance}, Effect = {cramers_v:.3f}")
                
                if self.verbose or cramers_v > 0.3:  # Show crosstab for strong effects
                    print(f"    Crosstab proportions:")
                    prop_table = pd.crosstab(self.df[var1], self.df[var2], normalize='index')
                    print(f"    {prop_table.round(3)}")
        else:
            print("  No significant associations found")
    
    def _analyze_age_specific_patterns(self, lifestyle_vars, health_vars, outcome_vars):
        """Analyze patterns specific to different age groups."""
        print(f"\n" + "-"*60)
        print("AGE-SPECIFIC PATTERN ANALYSIS")
        print("-"*60)
        
        age_groups = self.df['age_group'].value_counts().index.tolist()
        
        print(f"\nAGE GROUP DISTRIBUTION:")
        for age_group, count in self.df['age_group'].value_counts().items():
            pct = count / len(self.df) * 100
            print(f"  {age_group}: {count} ({pct:.1f}%)")
        
        # Health outcomes by age
        if outcome_vars:
            print(f"\nHEALTH OUTCOMES BY AGE:")
            for outcome_var in outcome_vars[:3]:  # Top 3 outcomes
                if outcome_var in self.df.columns:
                    print(f"\n  {outcome_var.upper()} by age group:")
                    age_outcome = pd.crosstab(self.df['age_group'], self.df[outcome_var], normalize='index')
                    
                    for age_group in age_groups:
                        if age_group in age_outcome.index:
                            # Focus on risk/negative outcomes
                            risk_cols = [col for col in age_outcome.columns 
                                       if any(risk_word in str(col).lower() 
                                             for risk_word in ['high', 'risk', 'obese', 'poor', 'bad'])]
                            
                            if risk_cols:
                                risk_pct = age_outcome.loc[age_group, risk_cols].sum() * 100
                                print(f"    {age_group}: {risk_pct:.1f}% high risk indicators")
        
        # Lifestyle patterns by age
        if lifestyle_vars:
            print(f"\nLIFESTYLE PATTERNS BY AGE:")
            
            for lifestyle_var in lifestyle_vars[:3]:  # Top 3 lifestyle factors
                if lifestyle_var in self.df.columns:
                    print(f"\n  {lifestyle_var.upper()}:")
                    
                    # Find the most concerning lifestyle patterns per age group
                    for age_group in age_groups[:4]:  # Top 4 age groups
                        if age_group in self.df['age_group'].values:
                            age_subset = self.df[self.df['age_group'] == age_group]
                            lifestyle_dist = age_subset[lifestyle_var].value_counts(normalize=True)
                            
                            # Identify negative lifestyle indicators
                            negative_patterns = [val for val in lifestyle_dist.index 
                                               if any(neg_word in str(val).lower() 
                                                     for neg_word in ['no', 'never', 'poor', 'excessive', 'heavy', 'daily'])]
                            
                            if negative_patterns:
                                negative_pct = lifestyle_dist.loc[negative_patterns].sum() * 100
                                print(f"    {age_group}: {negative_pct:.1f}% concerning patterns")
    
    def _analyze_high_risk_patterns(self, demographic_vars, lifestyle_vars, health_vars):
        """Deep dive into high-risk employee patterns."""
        if 'health_risk_level' not in self.df.columns:
            return
            
        print(f"\n" + "-"*60)
        print("HIGH-RISK GROUP DEEP DIVE ANALYSIS")
        print("-"*60)
        
        high_risk_df = self.df[self.df['health_risk_level'] == 'high_risk']
        total_high_risk = len(high_risk_df)
        
        if total_high_risk == 0:
            print("No high-risk employees found.")
            return
            
        print(f"High-risk employees: {total_high_risk} ({total_high_risk/len(self.df)*100:.1f}% of population)")
        
        # Demographics of high-risk group
        print(f"\nDEMOGRAPHIC PROFILE OF HIGH-RISK GROUP:")
        for demo_var in demographic_vars:
            if demo_var in self.df.columns:
                print(f"\n  {demo_var.upper()}:")
                high_risk_dist = high_risk_df[demo_var].value_counts()
                
                for val, count in high_risk_dist.head(5).items():
                    # Compare to overall population
                    overall_pct = (self.df[demo_var] == val).mean() * 100
                    high_risk_pct = count / total_high_risk * 100
                    
                    risk_ratio = high_risk_pct / overall_pct if overall_pct > 0 else 0
                    print(f"    {val}: {count} ({high_risk_pct:.1f}%) - Risk Ratio: {risk_ratio:.2f}x")
        
        # Lifestyle factors in high-risk group
        print(f"\nLIFESTYLE RISK FACTORS:")
        for lifestyle_var in lifestyle_vars[:5]:  # Top 5 lifestyle factors
            if lifestyle_var in self.df.columns:
                print(f"\n  {lifestyle_var.upper()}:")
                high_risk_dist = high_risk_df[lifestyle_var].value_counts(normalize=True)
                
                for val, prop in high_risk_dist.head(3).items():
                    print(f"    {val}: {prop*100:.1f}%")
        
        # Health conditions in high-risk group
        print(f"\nHEALTH CONDITIONS:")
        for health_var in health_vars[:5]:
            if health_var in self.df.columns:
                print(f"\n  {health_var.upper()}:")
                high_risk_dist = high_risk_df[health_var].value_counts(normalize=True)
                
                for val, prop in high_risk_dist.head(3).items():
                    print(f"    {val}: {prop*100:.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Health Risk Assessment EDA Pipeline - Two Phase Analysis')
    parser.add_argument('--phase', 
                       choices=['1', '2', 'all'],
                       default='1',
                       help='Analysis phase: 1=1D stats dump, 2=multi-dimensional patterns, all=both')
    parser.add_argument('--data', 
                       default='preprocessed_data/HRA_data.csv',
                       help='Path to the processed health data CSV file')
    parser.add_argument('--verbose', 
                       action='store_true',
                       help='Enable verbose output with detailed statistics')
    parser.add_argument('--output', 
                       help='Output file path to save analysis results')
    
    args = parser.parse_args()
    
    # Set up data path
    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = Path.cwd() / data_path
    
    if not data_path.exists():
        print(f"✗ Data file not found: {data_path}")
        sys.exit(1)
    
    # Initialize EDA analyzer
    analyzer = HealthRiskEDA(data_path, verbose=args.verbose)
    analyzer.load_data()
    
    # Capture output if saving to file
    if args.output:
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            # Run analysis based on phase
            if args.phase in ['1', 'all']:
                analyzer.phase1_one_dimensional_stats()
            
            if args.phase in ['2', 'all']:
                analyzer.phase2_multi_dimensional_patterns()
            
            print(f"\n✓ Phase {args.phase} analysis complete. Total records analyzed: {len(analyzer.df)}")
        
        # Save output to file
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        
        with open(output_path, 'w') as f:
            f.write(output_buffer.getvalue())
        
        print(f"✓ Analysis saved to: {output_path}")
    else:
        # Run analysis with normal output
        if args.phase in ['1', 'all']:
            analyzer.phase1_one_dimensional_stats()
        
        if args.phase in ['2', 'all']:
            analyzer.phase2_multi_dimensional_patterns()
        
        print(f"\n✓ Phase {args.phase} analysis complete. Total records analyzed: {len(analyzer.df)}")

if __name__ == "__main__":
    main()