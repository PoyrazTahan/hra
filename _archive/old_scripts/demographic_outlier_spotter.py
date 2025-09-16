#!/usr/bin/env python3
"""
Demographic Outlier Spotter for Health Risk Assessment Data

Identifies small demographic segments with disproportionate health impacts.
Focuses on finding "hidden populations" - micro-segments that might be overlooked
but show significantly different risk patterns.

Usage:
    python demographic_outlier_spotter.py --data path/to/data.csv
    python demographic_outlier_spotter.py --data path/to/data.csv --max-size 10 --min-risk-ratio 2.0
    python demographic_outlier_spotter.py --data path/to/data.csv --focus age_group,gender
"""

import pandas as pd
import numpy as np
import argparse
import json
import sys
from pathlib import Path
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

class DemographicOutlierSpotter:
    def __init__(self, data_path, max_segment_size=5.0, min_risk_ratio=1.5, min_sample=10, verbose=False):
        self.data_path = data_path
        self.max_segment_size = max_segment_size  # Maximum % of population for "small segment"
        self.min_risk_ratio = min_risk_ratio  # Minimum risk ratio to be considered outlier
        self.min_sample = min_sample
        self.verbose = verbose
        self.df = None
        self.outliers = []
        
    def load_data(self):
        """Load the health risk assessment data."""
        try:
            self.df = pd.read_csv(self.data_path)
            print(f"Data loaded: {self.df.shape[0]} records, {self.df.shape[1]} columns")
        except Exception as e:
            print(f"Error loading data: {e}")
            sys.exit(1)
    
    def identify_demographic_variables(self, focus_vars=None):
        """Identify demographic variables for analysis."""
        
        # Core demographic variables
        demographic_candidates = [
            'age_group', 'gender', 'has_children', 'bmi_category',
            'chronic_conditions', 'supplements', 'health_perception'
        ]
        
        # Filter to available columns
        available_demographics = [col for col in demographic_candidates if col in self.df.columns]
        
        # Apply focus filter if specified
        if focus_vars:
            focus_list = focus_vars.split(',')
            available_demographics = [col for col in focus_list if col in self.df.columns]
            print(f"Focusing on demographics: {focus_list}")
        
        outcome_vars = ['health_risk_level', 'health_risk_score']
        available_outcomes = [col for col in outcome_vars if col in self.df.columns]
        
        print(f"Demographic variables: {available_demographics}")
        print(f"Outcome variables: {available_outcomes}")
        
        return available_demographics, available_outcomes
    
    def calculate_population_baselines(self, outcome_vars):
        """Calculate population baseline rates for each outcome."""
        
        baselines = {}
        
        for outcome in outcome_vars:
            if outcome == 'health_risk_level':
                # High risk rate
                high_risk_rate = (self.df[outcome] == 'high_risk').mean() * 100
                moderate_risk_rate = (self.df[outcome] == 'moderate_risk').mean() * 100
                baselines[outcome] = {
                    'high_risk': high_risk_rate,
                    'moderate_risk': moderate_risk_rate,
                    'elevated_risk': high_risk_rate + moderate_risk_rate  # Combined moderate+high
                }
            elif outcome == 'health_risk_score':
                # Score-based risk rates
                high_score_rate = (self.df[outcome] >= 3).mean() * 100
                moderate_score_rate = (self.df[outcome] == 2).mean() * 100
                baselines[outcome] = {
                    'high_score': high_score_rate,
                    'moderate_score': moderate_score_rate,
                    'elevated_score': high_score_rate + moderate_score_rate
                }
        
        return baselines
    
    def analyze_single_variable_outliers(self, demographic_vars, outcome_vars, baselines):
        """Find outlier segments within single demographic variables."""
        
        print(f"\nAnalyzing single-variable demographic outliers...")
        
        for demo_var in demographic_vars:
            for outcome_var in outcome_vars:
                
                # Get baseline rates for this outcome
                outcome_baselines = baselines[outcome_var]
                
                # Analyze each demographic segment
                demo_segments = self.df[demo_var].value_counts()
                
                for segment_value, segment_count in demo_segments.items():
                    
                    # Check if segment is small enough to be considered outlier candidate
                    segment_pct = (segment_count / len(self.df)) * 100
                    
                    if (segment_pct <= self.max_segment_size and 
                        segment_count >= self.min_sample):
                        
                        # Calculate risk rates for this segment
                        segment_df = self.df[self.df[demo_var] == segment_value]
                        outlier_found = False
                        
                        # Test different risk definitions
                        for risk_type, baseline_rate in outcome_baselines.items():
                            
                            if outcome_var == 'health_risk_level':
                                if risk_type == 'high_risk':
                                    segment_rate = (segment_df[outcome_var] == 'high_risk').mean() * 100
                                elif risk_type == 'moderate_risk':
                                    segment_rate = (segment_df[outcome_var] == 'moderate_risk').mean() * 100
                                elif risk_type == 'elevated_risk':
                                    segment_rate = segment_df[outcome_var].isin(['high_risk', 'moderate_risk']).mean() * 100
                            elif outcome_var == 'health_risk_score':
                                if risk_type == 'high_score':
                                    segment_rate = (segment_df[outcome_var] >= 3).mean() * 100
                                elif risk_type == 'moderate_score':
                                    segment_rate = (segment_df[outcome_var] == 2).mean() * 100
                                elif risk_type == 'elevated_score':
                                    segment_rate = (segment_df[outcome_var] >= 2).mean() * 100
                            
                            # Calculate risk ratio
                            risk_ratio = segment_rate / baseline_rate if baseline_rate > 0 else 0
                            
                            # Check if this qualifies as an outlier
                            if risk_ratio >= self.min_risk_ratio or risk_ratio <= (1/self.min_risk_ratio):
                                
                                outlier_direction = "ELEVATED" if risk_ratio >= self.min_risk_ratio else "PROTECTED"
                                
                                self.outliers.append({
                                    'type': 'SINGLE_VARIABLE',
                                    'demographic_variable': demo_var,
                                    'segment_value': str(segment_value),
                                    'segment_description': f"{demo_var} = {segment_value}",
                                    'outcome_variable': outcome_var,
                                    'risk_type': risk_type,
                                    'segment_size': segment_count,
                                    'segment_pct': round(segment_pct, 1),
                                    'segment_rate': round(segment_rate, 1),
                                    'population_rate': round(baseline_rate, 1),
                                    'risk_ratio': round(risk_ratio, 2),
                                    'direction': outlier_direction,
                                    'rate_difference': round(segment_rate - baseline_rate, 1)
                                })
                                
                                outlier_found = True
                        
                        if outlier_found and self.verbose:
                            print(f"  Found outlier: {demo_var}={segment_value} (n={segment_count}, {segment_pct:.1f}%)")
    
    def analyze_two_variable_outliers(self, demographic_vars, outcome_vars, baselines):
        """Find outlier segments from combinations of two demographic variables."""
        
        print(f"\nAnalyzing two-variable demographic combinations...")
        
        # Test pairs of demographic variables
        for var1, var2 in combinations(demographic_vars, 2):
            for outcome_var in outcome_vars:
                
                outcome_baselines = baselines[outcome_var]
                
                # Create all combinations of var1 × var2
                df_clean = self.df[[var1, var2, outcome_var]].dropna()
                
                if len(df_clean) < self.min_sample * 2:
                    continue
                
                # Test each unique combination
                for val1 in df_clean[var1].unique():
                    for val2 in df_clean[var2].unique():
                        
                        # Filter to this specific combination
                        combo_mask = (df_clean[var1] == val1) & (df_clean[var2] == val2)
                        combo_df = df_clean[combo_mask]
                        
                        if len(combo_df) >= self.min_sample:
                            
                            combo_pct = (len(combo_df) / len(self.df)) * 100
                            
                            # Only analyze small segments
                            if combo_pct <= self.max_segment_size:
                                
                                # Test different risk definitions
                                for risk_type, baseline_rate in outcome_baselines.items():
                                    
                                    # Calculate segment risk rate
                                    if outcome_var == 'health_risk_level':
                                        if risk_type == 'high_risk':
                                            segment_rate = (combo_df[outcome_var] == 'high_risk').mean() * 100
                                        elif risk_type == 'moderate_risk':
                                            segment_rate = (combo_df[outcome_var] == 'moderate_risk').mean() * 100
                                        elif risk_type == 'elevated_risk':
                                            segment_rate = combo_df[outcome_var].isin(['high_risk', 'moderate_risk']).mean() * 100
                                    elif outcome_var == 'health_risk_score':
                                        if risk_type == 'high_score':
                                            segment_rate = (combo_df[outcome_var] >= 3).mean() * 100
                                        elif risk_type == 'moderate_score':
                                            segment_rate = (combo_df[outcome_var] == 2).mean() * 100
                                        elif risk_type == 'elevated_score':
                                            segment_rate = (combo_df[outcome_var] >= 2).mean() * 100
                                    
                                    risk_ratio = segment_rate / baseline_rate if baseline_rate > 0 else 0
                                    
                                    # Check if this qualifies as an outlier
                                    if risk_ratio >= self.min_risk_ratio or risk_ratio <= (1/self.min_risk_ratio):
                                        
                                        outlier_direction = "ELEVATED" if risk_ratio >= self.min_risk_ratio else "PROTECTED"
                                        
                                        self.outliers.append({
                                            'type': 'TWO_VARIABLE',
                                            'demographic_variable': f"{var1} × {var2}",
                                            'segment_value': f"{val1} + {val2}",
                                            'segment_description': f"{var1}={val1}, {var2}={val2}",
                                            'outcome_variable': outcome_var,
                                            'risk_type': risk_type,
                                            'segment_size': len(combo_df),
                                            'segment_pct': round(combo_pct, 1),
                                            'segment_rate': round(segment_rate, 1),
                                            'population_rate': round(baseline_rate, 1),
                                            'risk_ratio': round(risk_ratio, 2),
                                            'direction': outlier_direction,
                                            'rate_difference': round(segment_rate - baseline_rate, 1)
                                        })
    
    def find_extreme_outliers(self):
        """Identify the most extreme demographic outliers."""
        
        if not self.outliers:
            return []
        
        # Sort by risk ratio (most extreme first)
        sorted_outliers = sorted(self.outliers, key=lambda x: abs(x['risk_ratio'] - 1), reverse=True)
        
        # Group by type
        extreme_outliers = {
            'highest_risk_ratios': [o for o in sorted_outliers if o['direction'] == 'ELEVATED'][:5],
            'strongest_protection': [o for o in sorted_outliers if o['direction'] == 'PROTECTED'][:3],
            'smallest_segments': sorted(sorted_outliers, key=lambda x: x['segment_pct'])[:5],
            'largest_impact': sorted(sorted_outliers, key=lambda x: abs(x['rate_difference']), reverse=True)[:5]
        }
        
        return extreme_outliers
    
    def analyze_segment_characteristics(self):
        """Analyze characteristics of outlier segments beyond just risk rates."""
        
        segment_profiles = []
        
        # Focus on most extreme outliers
        extreme_outliers = sorted(self.outliers, key=lambda x: abs(x['risk_ratio'] - 1), reverse=True)[:10]
        
        for outlier in extreme_outliers:
            if outlier['type'] == 'SINGLE_VARIABLE':
                # Single variable segment
                demo_var = outlier['demographic_variable']
                segment_val = outlier['segment_value']
                
                segment_df = self.df[self.df[demo_var] == segment_val]
                
            elif outlier['type'] == 'TWO_VARIABLE':
                # Two variable combination
                var1, var2 = outlier['demographic_variable'].split(' × ')
                val1, val2 = outlier['segment_value'].split(' + ')
                
                segment_df = self.df[(self.df[var1] == val1) & (self.df[var2] == val2)]
            
            else:
                continue
            
            if len(segment_df) >= self.min_sample:
                # Calculate distinctive characteristics
                characteristics = self._extract_segment_characteristics(segment_df, outlier)
                if characteristics:
                    segment_profiles.append(characteristics)
        
        return segment_profiles
    
    def _extract_segment_characteristics(self, segment_df, outlier_info):
        """Extract distinctive characteristics of an outlier segment."""
        
        # Focus on lifestyle and health variables that might explain the outlier pattern
        lifestyle_vars = [
            'smoking_status', 'alcohol_level', 'exercise_freq', 'nutrition_quality',
            'sleep_duration', 'stress_calm', 'mood_positivity', 'water_intake'
        ]
        
        available_lifestyle = [col for col in lifestyle_vars if col in segment_df.columns]
        
        distinctive_patterns = []
        
        for var in available_lifestyle:
            # Get segment distribution
            segment_dist = segment_df[var].value_counts(normalize=True)
            
            # Get population distribution  
            population_dist = self.df[var].value_counts(normalize=True)
            
            # Find values where segment significantly differs from population
            for value in segment_dist.index:
                if value in population_dist.index:
                    segment_pct = segment_dist[value] * 100
                    population_pct = population_dist[value] * 100
                    
                    # Check for meaningful differences (>15 percentage points)
                    if abs(segment_pct - population_pct) > 15:
                        distinctive_patterns.append({
                            'variable': var,
                            'value': str(value),
                            'segment_pct': round(segment_pct, 1),
                            'population_pct': round(population_pct, 1),
                            'difference': round(segment_pct - population_pct, 1)
                        })
        
        if distinctive_patterns:
            # Sort by magnitude of difference
            distinctive_patterns.sort(key=lambda x: abs(x['difference']), reverse=True)
            
            return {
                'outlier_info': outlier_info,
                'distinctive_characteristics': distinctive_patterns[:5]  # Top 5 differences
            }
        
        return None
    
    def generate_outlier_insights(self):
        """Generate LLM-optimized insights about demographic outliers."""
        
        if not self.outliers:
            return {
                'summary': {
                    'total_outliers': 0,
                    'risk_ratio_threshold': self.min_risk_ratio,
                    'max_segment_size': self.max_segment_size,
                    'elevated_risk_segments': 0,
                    'protected_segments': 0
                },
                'extreme_outliers': {
                    'highest_risk_ratios': [],
                    'strongest_protection': []
                },
                'segment_profiles': [],
                'findings': []
            }
        
        # Find extreme outliers
        extreme_outliers = self.find_extreme_outliers()
        
        # Get segment characteristics
        segment_profiles = self.analyze_segment_characteristics()
        
        insights = {
            'summary': {
                'total_outliers': len(self.outliers),
                'risk_ratio_threshold': self.min_risk_ratio,
                'max_segment_size': self.max_segment_size,
                'elevated_risk_segments': len([o for o in self.outliers if o['direction'] == 'ELEVATED']),
                'protected_segments': len([o for o in self.outliers if o['direction'] == 'PROTECTED'])
            },
            'extreme_outliers': extreme_outliers,
            'segment_profiles': segment_profiles,
            'all_outliers': sorted(self.outliers, key=lambda x: abs(x['risk_ratio'] - 1), reverse=True)
        }
        
        return insights
    
    def print_outlier_report(self, insights):
        """Print human-readable demographic outlier report."""
        
        print("\n" + "="*80)
        print("DEMOGRAPHIC OUTLIER ANALYSIS REPORT")
        print("="*80)
        
        summary = insights['summary']
        print(f"\nOUTLIER DETECTION SUMMARY:")
        print(f"Total outlier segments found: {summary['total_outliers']}")
        print(f"Risk ratio threshold: {summary['risk_ratio_threshold']}x")
        print(f"Max segment size: {summary['max_segment_size']}% of population")
        print(f"Elevated risk segments: {summary['elevated_risk_segments']}")
        print(f"Protected segments: {summary['protected_segments']}")
        
        extreme = insights['extreme_outliers']
        
        if extreme['highest_risk_ratios']:
            print(f"\n" + "-"*60)
            print("HIGHEST RISK DEMOGRAPHIC OUTLIERS")
            print("-"*60)
            
            for outlier in extreme['highest_risk_ratios']:
                print(f"\n• {outlier['segment_description']}")
                print(f"  Segment size: {outlier['segment_size']} employees ({outlier['segment_pct']}% of population)")
                print(f"  {outlier['risk_type']}: {outlier['segment_rate']}% (vs {outlier['population_rate']}% population)")
                print(f"  Risk ratio: {outlier['risk_ratio']}x | Difference: {outlier['rate_difference']:+.1f}pp")
        
        if extreme['strongest_protection']:
            print(f"\n" + "-"*60)
            print("STRONGEST DEMOGRAPHIC PROTECTION")
            print("-"*60)
            
            for outlier in extreme['strongest_protection']:
                protection_factor = 1 / outlier['risk_ratio'] if outlier['risk_ratio'] > 0 else float('inf')
                print(f"\n• {outlier['segment_description']}")
                print(f"  Segment size: {outlier['segment_size']} employees ({outlier['segment_pct']}% of population)")
                print(f"  {outlier['risk_type']}: {outlier['segment_rate']}% (vs {outlier['population_rate']}% population)")
                print(f"  Protection factor: {protection_factor:.1f}x | Difference: {outlier['rate_difference']:+.1f}pp")
        
        if insights['segment_profiles']:
            print(f"\n" + "-"*60)
            print("OUTLIER SEGMENT CHARACTERISTICS")
            print("-"*60)
            
            for profile in insights['segment_profiles'][:3]:  # Top 3 most characterized
                outlier = profile['outlier_info']
                print(f"\n• {outlier['segment_description']} ({outlier['direction']} risk)")
                print(f"  Distinctive characteristics vs population:")
                
                for char in profile['distinctive_characteristics'][:3]:
                    direction = "more" if char['difference'] > 0 else "less"
                    print(f"    {char['variable']}: {char['segment_pct']}% {char['value']} ({char['difference']:+.1f}pp {direction} than population)")
    
    def save_output(self, insights, output_path):
        """Save outlier insights to JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(insights, f, indent=2)
            print(f"\nOutlier insights saved to: {output_path}")
        except Exception as e:
            print(f"Error saving output: {e}")
    
    def run_analysis(self, focus_vars=None):
        """Execute the complete demographic outlier analysis."""
        
        print("Demographic Outlier Spotter")
        print(f"Max segment size: {self.max_segment_size}% of population")
        print(f"Min risk ratio: {self.min_risk_ratio}x")
        print(f"Min sample size: {self.min_sample}")
        
        # Load data and identify variables
        self.load_data()
        demographic_vars, outcome_vars = self.identify_demographic_variables(focus_vars)
        
        if not outcome_vars:
            print("Error: No outcome variables found.")
            return {'summary': {'total_outliers': 0}, 'findings': []}
        
        # Calculate population baselines
        baselines = self.calculate_population_baselines(outcome_vars)
        
        if self.verbose:
            print(f"\nPopulation baselines:")
            for outcome, rates in baselines.items():
                for risk_type, rate in rates.items():
                    print(f"  {outcome}.{risk_type}: {rate:.1f}%")
        
        # Find outlier segments
        self.analyze_single_variable_outliers(demographic_vars, outcome_vars, baselines)
        
        if len(demographic_vars) >= 2:
            self.analyze_two_variable_outliers(demographic_vars, outcome_vars, baselines)
        
        # Generate and display insights
        insights = self.generate_outlier_insights()
        self.print_outlier_report(insights)
        
        return insights

def main():
    parser = argparse.ArgumentParser(
        description='Demographic Outlier Spotter for Health Risk Assessment Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demographic_outlier_spotter.py --data preprocessed_data/HRA_data.csv
  python demographic_outlier_spotter.py --data data.csv --max-size 3 --min-risk-ratio 2.5
  python demographic_outlier_spotter.py --data data.csv --focus age_group,gender,has_children
        """
    )
    
    parser.add_argument('--data', 
                       default='preprocessed_data/HRA_data.csv',
                       help='Path to the processed health data CSV file')
    
    parser.add_argument('--max-size', 
                       type=float, 
                       default=5.0,
                       help='Maximum segment size as % of population (default: 5.0)')
    
    parser.add_argument('--min-risk-ratio', 
                       type=float, 
                       default=1.5,
                       help='Minimum risk ratio to flag as outlier (default: 1.5)')
    
    parser.add_argument('--min-sample', 
                       type=int, 
                       default=10,
                       help='Minimum sample size for segment analysis (default: 10)')
    
    parser.add_argument('--focus', 
                       help='Comma-separated list of demographic variables to focus on')
    
    parser.add_argument('--output', 
                       help='Output JSON file path')
    
    parser.add_argument('--verbose', 
                       action='store_true',
                       help='Verbose output with detailed analysis')
    
    args = parser.parse_args()
    
    # Validate data path
    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = Path.cwd() / data_path
    
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)
    
    # Run analysis
    spotter = DemographicOutlierSpotter(
        data_path=data_path,
        max_segment_size=args.max_size,
        min_risk_ratio=args.min_risk_ratio,
        min_sample=args.min_sample,
        verbose=args.verbose
    )
    
    insights = spotter.run_analysis(focus_vars=args.focus)
    
    # Save output
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        spotter.save_output(insights, output_path)
    
    print(f"\nAnalysis complete. {insights['summary']['total_outliers']} demographic outliers detected.")

if __name__ == "__main__":
    main()