#!/usr/bin/env python3
"""
Statistical Surprise Detector for Health Risk Assessment Data

Identifies demographic subgroups and lifestyle combinations where observed health 
outcomes significantly differ from population expectations. Outputs LLM-optimized 
insights with statistical confidence and contextual comparisons.

Usage:
    python statistical_surprise.py --data path/to/data.csv
    python statistical_surprise.py --data path/to/data.csv --min-sample 15 --threshold 2.5
    python statistical_surprise.py --data path/to/data.csv --output surprises.json
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

class StatisticalSurpriseDetector:
    def __init__(self, data_path, min_sample_size=10, surprise_threshold=2.0, verbose=False):
        self.data_path = data_path
        self.min_sample_size = min_sample_size
        self.surprise_threshold = surprise_threshold
        self.verbose = verbose
        self.df = None
        self.surprises = []
        
    def load_data(self):
        """Load and validate the health risk assessment data."""
        try:
            self.df = pd.read_csv(self.data_path)
            print(f"Data loaded: {self.df.shape[0]} records, {self.df.shape[1]} columns")
            
            # Validate required columns exist
            required_cols = ['health_risk_level', 'health_risk_score']
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            
            if missing_cols:
                print(f"Warning: Missing required columns: {missing_cols}")
                print("Available columns for outcomes:", [col for col in self.df.columns if 'risk' in col.lower()])
                
        except Exception as e:
            print(f"Error loading data: {e}")
            sys.exit(1)
    
    def detect_demographic_surprises(self):
        """Find demographic subgroups with unexpected health outcomes."""
        
        # Define variable groups
        demographic_vars = ['age_group', 'gender', 'has_children', 'bmi_category']
        outcome_vars = ['health_risk_level', 'health_risk_score']
        
        # Filter to available columns
        available_demographics = [col for col in demographic_vars if col in self.df.columns]
        available_outcomes = [col for col in outcome_vars if col in self.df.columns]
        
        print(f"\nAnalyzing demographic surprises...")
        print(f"Demographics: {available_demographics}")
        print(f"Outcomes: {available_outcomes}")
        
        for demo_var in available_demographics:
            for outcome_var in available_outcomes:
                self._analyze_subgroup_surprises(demo_var, outcome_var, "DEMOGRAPHIC")
    
    def detect_lifestyle_surprises(self):
        """Find lifestyle combinations with unexpected health impacts."""
        
        lifestyle_vars = [
            'smoking_status', 'alcohol_level', 'exercise_freq', 'nutrition_quality',
            'sleep_duration', 'stress_calm', 'mood_positivity', 'water_intake'
        ]
        outcome_vars = ['health_risk_level', 'health_risk_score', 'bmi_category']
        
        available_lifestyle = [col for col in lifestyle_vars if col in self.df.columns]
        available_outcomes = [col for col in outcome_vars if col in self.df.columns]
        
        print(f"\nAnalyzing lifestyle surprises...")
        print(f"Lifestyle factors: {available_lifestyle}")
        
        for lifestyle_var in available_lifestyle:
            for outcome_var in available_outcomes:
                self._analyze_subgroup_surprises(lifestyle_var, outcome_var, "LIFESTYLE")
    
    def detect_compound_surprises(self):
        """Find unexpected patterns in demographic-lifestyle combinations."""
        
        demographic_vars = ['age_group', 'gender', 'has_children']
        lifestyle_vars = ['smoking_status', 'stress_calm', 'exercise_freq', 'nutrition_quality']
        outcome_vars = ['health_risk_level']
        
        available_demographics = [col for col in demographic_vars if col in self.df.columns]
        available_lifestyle = [col for col in lifestyle_vars if col in self.df.columns]
        available_outcomes = [col for col in outcome_vars if col in self.df.columns]
        
        print(f"\nAnalyzing compound demographic-lifestyle surprises...")
        
        # Test 2-way combinations
        for demo_var in available_demographics:
            for lifestyle_var in available_lifestyle:
                for outcome_var in available_outcomes:
                    self._analyze_compound_surprises(demo_var, lifestyle_var, outcome_var)
    
    def _analyze_subgroup_surprises(self, grouping_var, outcome_var, category):
        """Analyze surprises for a single grouping variable against an outcome."""
        
        # Create contingency table
        contingency = pd.crosstab(self.df[grouping_var], self.df[outcome_var])
        
        if contingency.size == 0:
            return
        
        try:
            # Chi-square test
            chi2, p_val, dof, expected = chi2_contingency(contingency)
            
            # Calculate standardized residuals
            std_residuals = (contingency - expected) / np.sqrt(expected)
            
            # Find surprising cells
            surprise_mask = np.abs(std_residuals) > self.surprise_threshold
            surprise_indices = np.where(surprise_mask)
            
            for i, j in zip(*surprise_indices):
                subgroup = contingency.index[i]
                outcome = contingency.columns[j]
                
                # Calculate rates and context
                observed_count = contingency.iloc[i, j]
                subgroup_total = contingency.iloc[i].sum()
                
                if subgroup_total >= self.min_sample_size:
                    observed_rate = observed_count / subgroup_total
                    expected_rate = expected[i, j] / subgroup_total
                    population_rate = contingency.iloc[:, j].sum() / contingency.sum().sum()
                    
                    surprise_magnitude = std_residuals.iloc[i, j]
                    
                    surprise_data = {
                        'category': category,
                        'subgroup_variable': grouping_var,
                        'subgroup_value': str(subgroup),
                        'outcome_variable': outcome_var,
                        'outcome_value': str(outcome),
                        'observed_rate': round(observed_rate * 100, 1),
                        'expected_rate': round(expected_rate * 100, 1),
                        'population_rate': round(population_rate * 100, 1),
                        'surprise_magnitude': round(surprise_magnitude, 2),
                        'sample_size': int(subgroup_total),
                        'direction': 'HIGHER' if surprise_magnitude > 0 else 'LOWER',
                        'statistical_significance': self._get_significance_level(p_val)
                    }
                    
                    self.surprises.append(surprise_data)
                    
        except Exception as e:
            if self.verbose:
                print(f"  Warning: Could not analyze {grouping_var} × {outcome_var}: {e}")
    
    def _analyze_compound_surprises(self, demo_var, lifestyle_var, outcome_var):
        """Analyze surprises in demographic-lifestyle combinations."""
        
        # Create compound grouping variable
        compound_groups = self.df[demo_var].astype(str) + "_X_" + self.df[lifestyle_var].astype(str)
        
        # Create contingency table for compound variable
        compound_df = pd.DataFrame({
            'compound_group': compound_groups,
            'outcome': self.df[outcome_var]
        }).dropna()
        
        contingency = pd.crosstab(compound_df['compound_group'], compound_df['outcome'])
        
        if contingency.size == 0:
            return
        
        try:
            chi2, p_val, dof, expected = chi2_contingency(contingency)
            std_residuals = (contingency - expected) / np.sqrt(expected)
            
            surprise_mask = np.abs(std_residuals) > self.surprise_threshold
            surprise_indices = np.where(surprise_mask)
            
            for i, j in zip(*surprise_indices):
                compound_group = contingency.index[i]
                outcome = contingency.columns[j]
                
                observed_count = contingency.iloc[i, j]
                subgroup_total = contingency.iloc[i].sum()
                
                if subgroup_total >= self.min_sample_size:
                    observed_rate = observed_count / subgroup_total
                    population_rate = contingency.iloc[:, j].sum() / contingency.sum().sum()
                    surprise_magnitude = std_residuals.iloc[i, j]
                    
                    # Parse compound group back to components
                    demo_value, lifestyle_value = compound_group.split('_X_')
                    
                    surprise_data = {
                        'category': 'COMPOUND',
                        'subgroup_variable': f"{demo_var} × {lifestyle_var}",
                        'subgroup_value': f"{demo_value} + {lifestyle_value}",
                        'outcome_variable': outcome_var,
                        'outcome_value': str(outcome),
                        'observed_rate': round(observed_rate * 100, 1),
                        'population_rate': round(population_rate * 100, 1),
                        'surprise_magnitude': round(surprise_magnitude, 2),
                        'sample_size': int(subgroup_total),
                        'direction': 'HIGHER' if surprise_magnitude > 0 else 'LOWER',
                        'statistical_significance': self._get_significance_level(p_val)
                    }
                    
                    self.surprises.append(surprise_data)
                    
        except Exception as e:
            if self.verbose:
                print(f"  Warning: Could not analyze compound {demo_var} × {lifestyle_var}: {e}")
    
    def _get_significance_level(self, p_val):
        """Convert p-value to significance level."""
        if p_val < 0.001:
            return "HIGH"
        elif p_val < 0.01:
            return "MEDIUM"
        elif p_val < 0.05:
            return "LOW"
        else:
            return "NONE"
    
    def generate_insights(self):
        """Generate LLM-optimized insights from detected surprises."""
        
        if not self.surprises:
            print("\nNo statistical surprises detected.")
            return []
        
        # Sort by surprise magnitude
        sorted_surprises = sorted(self.surprises, key=lambda x: abs(x['surprise_magnitude']), reverse=True)
        
        insights = {
            'summary': {
                'total_surprises': len(sorted_surprises),
                'high_confidence': len([s for s in sorted_surprises if s['statistical_significance'] == 'HIGH']),
                'categories_analyzed': list(set([s['category'] for s in sorted_surprises]))
            },
            'top_surprises': sorted_surprises[:10],  # Top 10 most surprising
            'demographic_outliers': [s for s in sorted_surprises if s['category'] == 'DEMOGRAPHIC'][:5],
            'lifestyle_anomalies': [s for s in sorted_surprises if s['category'] == 'LIFESTYLE'][:5],
            'compound_effects': [s for s in sorted_surprises if s['category'] == 'COMPOUND'][:5]
        }
        
        return insights
    
    def print_human_readable_report(self, insights):
        """Print human-readable report of statistical surprises."""
        
        print("\n" + "="*80)
        print("STATISTICAL SURPRISE ANALYSIS REPORT")
        print("="*80)
        
        summary = insights['summary']
        print(f"\nSURPRISE DETECTION SUMMARY:")
        print(f"Total patterns analyzed: {summary['total_surprises']}")
        print(f"High confidence surprises: {summary['high_confidence']}")
        print(f"Categories with surprises: {', '.join(summary['categories_analyzed'])}")
        
        print(f"\n" + "-"*60)
        print("TOP STATISTICAL SURPRISES")
        print("-"*60)
        
        for i, surprise in enumerate(insights['top_surprises'], 1):
            direction_symbol = "↑" if surprise['direction'] == 'HIGHER' else "↓"
            
            print(f"\n{i}. [{surprise['category']}] {surprise['subgroup_value']} {direction_symbol}")
            print(f"   Outcome: {surprise['outcome_value']} in {surprise['outcome_variable']}")
            print(f"   Rate: {surprise['observed_rate']}% (vs {surprise['population_rate']}% population)")
            print(f"   Magnitude: {surprise['surprise_magnitude']}σ | Confidence: {surprise['statistical_significance']}")
            print(f"   Sample: {surprise['sample_size']} employees")
        
        # Category-specific insights
        categories = [
            ('DEMOGRAPHIC OUTLIERS', insights['demographic_outliers']),
            ('LIFESTYLE ANOMALIES', insights['lifestyle_anomalies']),
            ('COMPOUND EFFECTS', insights['compound_effects'])
        ]
        
        for category_name, category_surprises in categories:
            if category_surprises:
                print(f"\n" + "-"*60)
                print(category_name)
                print("-"*60)
                
                for surprise in category_surprises:
                    direction = "higher" if surprise['direction'] == 'HIGHER' else "lower"
                    rate_diff = abs(surprise['observed_rate'] - surprise['population_rate'])
                    
                    print(f"• {surprise['subgroup_value']}: {surprise['observed_rate']}% {surprise['outcome_value']}")
                    print(f"  ({rate_diff:.1f}pp {direction} than population average, n={surprise['sample_size']})")
    
    def save_json_output(self, insights, output_path):
        """Save insights in JSON format for LLM consumption."""
        try:
            with open(output_path, 'w') as f:
                json.dump(insights, f, indent=2)
            print(f"\nInsights saved to: {output_path}")
        except Exception as e:
            print(f"Error saving JSON output: {e}")
    
    def run_analysis(self):
        """Execute the complete statistical surprise analysis."""
        
        print("Statistical Surprise Detector")
        print(f"Minimum sample size: {self.min_sample_size}")
        print(f"Surprise threshold: {self.surprise_threshold}σ")
        
        # Load data
        self.load_data()
        
        # Run surprise detection
        self.detect_demographic_surprises()
        self.detect_lifestyle_surprises()
        self.detect_compound_surprises()
        
        # Generate insights
        insights = self.generate_insights()
        
        # Output results
        self.print_human_readable_report(insights)
        
        return insights

def main():
    parser = argparse.ArgumentParser(
        description='Statistical Surprise Detector for Health Risk Assessment Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python statistical_surprise.py --data preprocessed_data/HRA_data.csv
  python statistical_surprise.py --data data.csv --min-sample 15 --threshold 2.5
  python statistical_surprise.py --data data.csv --output insights.json --verbose
        """
    )
    
    parser.add_argument('--data', 
                       default='preprocessed_data/HRA_data.csv',
                       help='Path to the processed health data CSV file')
    
    parser.add_argument('--min-sample', 
                       type=int, 
                       default=10,
                       help='Minimum sample size for subgroup analysis (default: 10)')
    
    parser.add_argument('--threshold', 
                       type=float, 
                       default=2.0,
                       help='Statistical surprise threshold in standard deviations (default: 2.0)')
    
    parser.add_argument('--output', 
                       help='Output file path for JSON insights (optional)')
    
    parser.add_argument('--verbose', 
                       action='store_true',
                       help='Enable verbose output with detailed analysis')
    
    args = parser.parse_args()
    
    # Validate data path
    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = Path.cwd() / data_path
    
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)
    
    # Initialize and run analyzer
    detector = StatisticalSurpriseDetector(
        data_path=data_path,
        min_sample_size=args.min_sample,
        surprise_threshold=args.threshold,
        verbose=args.verbose
    )
    
    insights = detector.run_analysis()
    
    # Save JSON output if requested
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        
        detector.save_json_output(insights, output_path)
    
    print(f"\nAnalysis complete. {len(insights['top_surprises'])} surprises detected.")

if __name__ == "__main__":
    main()