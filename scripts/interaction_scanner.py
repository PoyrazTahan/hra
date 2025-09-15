#!/usr/bin/env python3
"""
Interaction Effect Scanner for Health Risk Assessment Data - Version 2

Simple, robust interaction detector that finds variable combinations with 
amplified or protective effects. Focuses on practical insights for LLM consumption.

Usage:
    python interaction_scanner_v2.py --data path/to/data.csv
    python interaction_scanner_v2.py --data path/to/data.csv --include smoking_status,stress_calm
    python interaction_scanner_v2.py --data path/to/data.csv --exclude record_id,user_id --threshold 1.5
"""

import pandas as pd
import numpy as np
import argparse
import json
import sys
from pathlib import Path
from scipy.stats import chi2_contingency
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

class InteractionScanner:
    def __init__(self, data_path, amplification_threshold=1.5, min_sample=15, verbose=False):
        self.data_path = data_path
        self.amplification_threshold = amplification_threshold
        self.min_sample = min_sample
        self.verbose = verbose
        self.df = None
        self.interactions = []
        
    def load_data(self):
        """Load the health risk assessment data."""
        try:
            self.df = pd.read_csv(self.data_path)
            print(f"Data loaded: {self.df.shape[0]} records, {self.df.shape[1]} columns")
        except Exception as e:
            print(f"Error loading data: {e}")
            sys.exit(1)
    
    def filter_variables(self, include_vars=None, exclude_vars=None):
        """Filter variables for meaningful interaction analysis."""
        
        all_columns = self.df.columns.tolist()
        
        # Always exclude ID fields (they're meaningless for analysis)
        auto_exclude = []
        for col in all_columns:
            if any(pattern in col.lower() for pattern in ['id', 'record']):
                auto_exclude.append(col)
        
        # Start with meaningful columns only
        candidate_vars = [col for col in all_columns if col not in auto_exclude]
        
        # Manual exclusions
        if exclude_vars:
            exclude_list = exclude_vars.split(',')
            candidate_vars = [col for col in candidate_vars if col not in exclude_list]
            print(f"Excluded variables: {exclude_list}")
        
        # Manual inclusions (override everything)
        if include_vars:
            include_list = include_vars.split(',')
            candidate_vars = [col for col in include_list if col in all_columns]
            print(f"Including only: {include_list}")
        
        # Separate outcomes from predictors
        outcome_vars = ['health_risk_level', 'health_risk_score']
        available_outcomes = [col for col in outcome_vars if col in candidate_vars]
        
        predictor_vars = [col for col in candidate_vars if col not in outcome_vars]
        
        if auto_exclude and self.verbose:
            print(f"Excluded ID fields: {auto_exclude}")
        
        print(f"Testing: {len(predictor_vars)} predictors against {len(available_outcomes)} outcomes")
        
        return predictor_vars, available_outcomes
    
    def calculate_baseline_risk_rate(self, outcome_var):
        """Calculate population baseline risk rate for an outcome."""
        
        if outcome_var == 'health_risk_level':
            # High risk rate
            return (self.df[outcome_var] == 'high_risk').mean() * 100
        elif outcome_var == 'health_risk_score':
            # Moderate-high risk (score >= 2)
            return (self.df[outcome_var] >= 2).mean() * 100
        else:
            # Generic high-risk detection
            values = self.df[outcome_var].value_counts()
            high_risk_values = [val for val in values.index if 'high' in str(val).lower() or '3' in str(val) or '4' in str(val)]
            if high_risk_values:
                return (self.df[outcome_var].isin(high_risk_values)).mean() * 100
        
        return 0
    
    def test_variable_pair_interaction(self, var1, var2, outcome_var):
        """Test interaction between two variables for a specific outcome."""
        
        # Calculate baseline population risk
        baseline_risk = self.calculate_baseline_risk_rate(outcome_var)
        
        if baseline_risk == 0:
            return None
        
        # Create all combinations of var1 × var2
        df_clean = self.df[[var1, var2, outcome_var]].dropna()
        
        if len(df_clean) < self.min_sample * 2:
            return None
        
        combinations_found = []
        
        # Test each unique combination
        for val1 in df_clean[var1].unique():
            for val2 in df_clean[var2].unique():
                
                # Filter to this specific combination
                combo_mask = (df_clean[var1] == val1) & (df_clean[var2] == val2)
                combo_df = df_clean[combo_mask]
                
                if len(combo_df) >= self.min_sample:
                    
                    # Calculate risk rate for this combination
                    if outcome_var == 'health_risk_level':
                        combo_risk_rate = (combo_df[outcome_var] == 'high_risk').mean() * 100
                    elif outcome_var == 'health_risk_score':
                        combo_risk_rate = (combo_df[outcome_var] >= 2).mean() * 100
                    else:
                        # Generic approach
                        high_risk_values = [val for val in combo_df[outcome_var].unique() if 'high' in str(val).lower()]
                        if high_risk_values:
                            combo_risk_rate = combo_df[outcome_var].isin(high_risk_values).mean() * 100
                        else:
                            continue
                    
                    # Calculate amplification factor
                    amplification = combo_risk_rate / baseline_risk if baseline_risk > 0 else 1
                    
                    combinations_found.append({
                        'val1': str(val1),
                        'val2': str(val2),
                        'combination': f"{val1} + {val2}",
                        'risk_rate': round(combo_risk_rate, 1),
                        'amplification': round(amplification, 2),
                        'sample_size': len(combo_df)
                    })
        
        if not combinations_found:
            return None
        
        # Find most interesting combinations (highest amplification or protection)
        combinations_found.sort(key=lambda x: abs(x['amplification'] - 1), reverse=True)
        
        # Check if any combinations meet threshold
        significant_combos = [c for c in combinations_found 
                            if c['amplification'] >= self.amplification_threshold or c['amplification'] <= 0.5]
        
        if significant_combos:
            return {
                'variable1': var1,
                'variable2': var2,
                'outcome': outcome_var,
                'baseline_risk': round(baseline_risk, 1),
                'total_combinations': len(combinations_found),
                'significant_combinations': len(significant_combos),
                'top_combinations': significant_combos[:5],
                'max_amplification': max([c['amplification'] for c in combinations_found]),
                'min_amplification': min([c['amplification'] for c in combinations_found])
            }
        
        return None
    
    def analyze_all_interactions(self, predictor_vars, outcome_vars):
        """Analyze interactions between all variable pairs."""
        
        total_pairs = len(list(combinations(predictor_vars, 2))) * len(outcome_vars)
        print(f"\nTesting {total_pairs} variable pair × outcome combinations...")
        
        for var1, var2 in combinations(predictor_vars, 2):
            for outcome in outcome_vars:
                interaction = self.test_variable_pair_interaction(var1, var2, outcome)
                if interaction:
                    self.interactions.append(interaction)
        
        print(f"Found {len(self.interactions)} meaningful interactions")
    
    def generate_insights(self):
        """Generate LLM-ready insights from interactions."""
        
        if not self.interactions:
            return {
                'summary': {
                    'total_interactions': 0,
                    'amplification_threshold': self.amplification_threshold
                },
                'findings': []
            }
        
        # Sort by maximum amplification
        sorted_interactions = sorted(self.interactions, key=lambda x: x['max_amplification'], reverse=True)
        
        # Extract different types of insights
        high_amplifiers = []
        protective_effects = []
        
        for interaction in sorted_interactions:
            # High amplification patterns
            high_amp_combos = [c for c in interaction['top_combinations'] 
                             if c['amplification'] >= self.amplification_threshold]
            if high_amp_combos:
                high_amplifiers.append({
                    'variables': f"{interaction['variable1']} × {interaction['variable2']}",
                    'outcome': interaction['outcome'],
                    'baseline': interaction['baseline_risk'],
                    'combinations': high_amp_combos
                })
            
            # Protective effects (low amplification)
            protective_combos = [c for c in interaction['top_combinations'] 
                               if c['amplification'] <= 0.5]
            if protective_combos:
                protective_effects.append({
                    'variables': f"{interaction['variable1']} × {interaction['variable2']}",
                    'outcome': interaction['outcome'],
                    'baseline': interaction['baseline_risk'],
                    'combinations': protective_combos
                })
        
        insights = {
            'summary': {
                'total_interactions': len(sorted_interactions),
                'amplification_threshold': self.amplification_threshold,
                'high_amplifiers': len(high_amplifiers),
                'protective_effects': len(protective_effects)
            },
            'all_interactions': sorted_interactions,
            'high_amplification_patterns': high_amplifiers[:10],
            'protective_patterns': protective_effects[:5]
        }
        
        return insights
    
    def print_report(self, insights):
        """Print human-readable report."""
        
        print("\n" + "="*80)
        print("INTERACTION EFFECT ANALYSIS REPORT")
        print("="*80)
        
        summary = insights['summary']
        print(f"\nSUMMARY:")
        print(f"Total meaningful interactions: {summary['total_interactions']}")
        print(f"Amplification threshold: {summary['amplification_threshold']}x")
        print(f"High amplification patterns: {summary['high_amplifiers']}")
        print(f"Protective patterns: {summary['protective_effects']}")
        
        if insights['high_amplification_patterns']:
            print(f"\n" + "-"*60)
            print("HIGH RISK AMPLIFICATION PATTERNS")
            print("-"*60)
            
            for i, pattern in enumerate(insights['high_amplification_patterns'], 1):
                print(f"\n{i}. {pattern['variables']} → {pattern['outcome']}")
                print(f"   Population baseline: {pattern['baseline']}%")
                print(f"   High-risk combinations:")
                
                for combo in pattern['combinations'][:3]:
                    print(f"     • {combo['combination']}: {combo['risk_rate']}% ({combo['amplification']}x baseline, n={combo['sample_size']})")
        
        if insights['protective_patterns']:
            print(f"\n" + "-"*60)
            print("PROTECTIVE COMBINATION PATTERNS")  
            print("-"*60)
            
            for pattern in insights['protective_patterns']:
                print(f"• {pattern['variables']} → {pattern['outcome']}")
                print(f"  Population baseline: {pattern['baseline']}%")
                print(f"  Protective combinations:")
                
                for combo in pattern['combinations'][:2]:
                    protection = pattern['baseline'] - combo['risk_rate']
                    print(f"    {combo['combination']}: {combo['risk_rate']}% (-{protection:.1f}% protection, n={combo['sample_size']})")
    
    def save_output(self, insights, output_path):
        """Save insights to JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(insights, f, indent=2)
            print(f"\nInsights saved to: {output_path}")
        except Exception as e:
            print(f"Error saving output: {e}")
    
    def run_analysis(self, include_vars=None, exclude_vars=None):
        """Run the complete interaction analysis."""
        
        print("Interaction Effect Scanner v2")
        print(f"Amplification threshold: {self.amplification_threshold}x")
        print(f"Minimum sample size: {self.min_sample}")
        
        # Load and filter data
        self.load_data()
        predictor_vars, outcome_vars = self.filter_variables(include_vars, exclude_vars)
        
        if not outcome_vars:
            print("Error: No outcome variables found. Include health_risk_level or health_risk_score.")
            return {'summary': {'total_interactions': 0}, 'findings': []}
        
        # Analyze interactions
        self.analyze_all_interactions(predictor_vars, outcome_vars)
        
        # Generate and display insights
        insights = self.generate_insights()
        self.print_report(insights)
        
        return insights

def main():
    parser = argparse.ArgumentParser(
        description='Interaction Effect Scanner v2 - Simple and Robust',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python interaction_scanner_v2.py --data preprocessed_data/HRA_data.csv
  python interaction_scanner_v2.py --data data.csv --include smoking_status,stress_calm,age_group,health_risk_level
  python interaction_scanner_v2.py --data data.csv --exclude bmi,weight_kg --threshold 2.0
        """
    )
    
    parser.add_argument('--data', 
                       default='preprocessed_data/HRA_data.csv',
                       help='Path to the processed health data CSV file')
    
    parser.add_argument('--include', 
                       help='Comma-separated list of variables to include (must include outcomes)')
    
    parser.add_argument('--exclude', 
                       help='Comma-separated list of variables to exclude')
    
    parser.add_argument('--threshold', 
                       type=float, 
                       default=1.5,
                       help='Risk amplification threshold (default: 1.5x)')
    
    parser.add_argument('--min-sample', 
                       type=int, 
                       default=15,
                       help='Minimum sample size for combinations (default: 15)')
    
    parser.add_argument('--output', 
                       help='Output JSON file path')
    
    parser.add_argument('--verbose', 
                       action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Validate data path
    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = Path.cwd() / data_path
    
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)
    
    # Run analysis
    scanner = InteractionScanner(
        data_path=data_path,
        amplification_threshold=args.threshold,
        min_sample=args.min_sample,
        verbose=args.verbose
    )
    
    insights = scanner.run_analysis(
        include_vars=args.include,
        exclude_vars=args.exclude
    )
    
    # Save output
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        scanner.save_output(insights, output_path)
    
    print(f"\nAnalysis complete. {insights['summary']['total_interactions']} interactions detected.")

if __name__ == "__main__":
    main()