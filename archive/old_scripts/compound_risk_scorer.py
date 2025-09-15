#!/usr/bin/env python3
"""
Compound Risk Scorer for Health Risk Assessment Data

Creates alternative risk scoring mechanisms that capture multi-factor risk patterns
beyond the standard health_risk_score. Discovers hidden risk amplification through
factor combination analysis and creates interpretable compound scores.

Usage:
    python compound_risk_scorer.py --data path/to/data.csv
    python compound_risk_scorer.py --data path/to/data.csv --method interaction-weighted
    python compound_risk_scorer.py --data path/to/data.csv --factors stress,lifestyle,demographics
"""

import pandas as pd
import numpy as np
import argparse
import json
import sys
from pathlib import Path
from scipy.stats import chi2_contingency
import warnings
warnings.filterwarnings('ignore')

class CompoundRiskScorer:
    def __init__(self, data_path, scoring_method='additive', min_sample=15, verbose=False):
        self.data_path = data_path
        self.scoring_method = scoring_method
        self.min_sample = min_sample
        self.verbose = verbose
        self.df = None
        self.risk_factors = {}
        self.compound_scores = {}
        
    def load_data(self):
        """Load the health risk assessment data."""
        try:
            self.df = pd.read_csv(self.data_path)
            print(f"Data loaded: {self.df.shape[0]} records, {self.df.shape[1]} columns")
        except Exception as e:
            print(f"Error loading data: {e}")
            sys.exit(1)
    
    def define_risk_factor_groups(self, factor_focus=None):
        """Define and organize risk factors into logical groups."""
        
        all_factor_groups = {
            'stress_factors': ['stress_calm', 'mood_positivity', 'depression_mood', 'depression_interest'],
            'lifestyle_factors': ['smoking_status', 'alcohol_level', 'exercise_freq', 'nutrition_quality', 'sleep_duration'],
            'demographic_factors': ['age_group', 'gender', 'has_children', 'bmi_category'],
            'health_factors': ['chronic_conditions', 'pain_level', 'health_perception'],
            'behavior_factors': ['water_intake', 'sugar_frequency', 'processed_food', 'supplements', 'daily_steps']
        }
        
        # Filter to available columns
        available_factor_groups = {}
        for group_name, factors in all_factor_groups.items():
            available_factors = [f for f in factors if f in self.df.columns]
            if available_factors:
                available_factor_groups[group_name] = available_factors
        
        # Apply focus filter if specified
        if factor_focus:
            focus_groups = factor_focus.split(',')
            filtered_groups = {}
            for group in focus_groups:
                if group in available_factor_groups:
                    filtered_groups[group] = available_factor_groups[group]
                else:
                    print(f"Warning: Factor group '{group}' not found. Available: {list(available_factor_groups.keys())}")
            available_factor_groups = filtered_groups
        
        self.risk_factors = available_factor_groups
        
        print(f"Risk factor groups: {list(self.risk_factors.keys())}")
        for group, factors in self.risk_factors.items():
            print(f"  {group}: {factors}")
        
        return available_factor_groups
    
    def calculate_individual_risk_weights(self):
        """Calculate individual risk contribution weights for each factor value."""
        
        if 'health_risk_level' not in self.df.columns:
            print("Warning: health_risk_level not found. Using health_risk_score.")
            return {}
        
        # Population baseline
        baseline_high_risk = (self.df['health_risk_level'] == 'high_risk').mean()
        baseline_elevated_risk = self.df['health_risk_level'].isin(['high_risk', 'moderate_risk']).mean()
        
        factor_weights = {}
        
        print(f"\nCalculating individual factor risk weights...")
        print(f"Population baselines: {baseline_high_risk*100:.1f}% high risk, {baseline_elevated_risk*100:.1f}% elevated risk")
        
        for group_name, factors in self.risk_factors.items():
            factor_weights[group_name] = {}
            
            for factor in factors:
                factor_weights[group_name][factor] = {}
                
                # Calculate risk rate for each factor value
                factor_values = self.df[factor].value_counts()
                
                for value, count in factor_values.items():
                    if count >= self.min_sample:
                        
                        value_df = self.df[self.df[factor] == value]
                        
                        # High risk rate
                        high_risk_rate = (value_df['health_risk_level'] == 'high_risk').mean()
                        elevated_risk_rate = value_df['health_risk_level'].isin(['high_risk', 'moderate_risk']).mean()
                        
                        # Calculate risk multipliers
                        high_risk_multiplier = high_risk_rate / baseline_high_risk if baseline_high_risk > 0 else 1
                        elevated_risk_multiplier = elevated_risk_rate / baseline_elevated_risk if baseline_elevated_risk > 0 else 1
                        
                        factor_weights[group_name][factor][str(value)] = {
                            'high_risk_multiplier': round(high_risk_multiplier, 3),
                            'elevated_risk_multiplier': round(elevated_risk_multiplier, 3),
                            'sample_size': count,
                            'high_risk_rate': round(high_risk_rate * 100, 1),
                            'elevated_risk_rate': round(elevated_risk_rate * 100, 1)
                        }
        
        return factor_weights
    
    def create_additive_compound_score(self, factor_weights):
        """Create compound risk score using additive approach."""
        
        compound_scores = []
        
        for index, row in self.df.iterrows():
            
            total_high_risk_score = 0
            total_elevated_risk_score = 0
            factors_counted = 0
            
            # Sum risk multipliers across all factor groups
            for group_name, group_factors in self.risk_factors.items():
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
                'actual_high_risk': row['health_risk_level'] == 'high_risk' if 'health_risk_level' in row else False,
                'actual_elevated_risk': row['health_risk_level'] in ['high_risk', 'moderate_risk'] if 'health_risk_level' in row else False
            })
        
        return compound_scores
    
    def create_interaction_weighted_score(self, factor_weights):
        """Create compound score that weights based on interaction strength."""
        
        # This is a simplified interaction-aware scoring
        # Real implementation would use interaction scanner results
        
        compound_scores = []
        
        # Define high-impact interaction pairs (from interaction scanner insights)
        high_impact_pairs = [
            ('stress_calm', 'mood_positivity'),  # Strong correlation in data
            ('smoking_status', 'alcohol_level'),
            ('age_group', 'chronic_conditions'),
            ('exercise_freq', 'bmi_category')
        ]
        
        for index, row in self.df.iterrows():
            
            base_score = 0
            interaction_bonus = 0
            
            # Base additive score
            factors_counted = 0
            for group_name, group_factors in self.risk_factors.items():
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
            for var1, var2 in high_impact_pairs:
                if var1 in row and var2 in row:
                    val1, val2 = str(row[var1]), str(row[var2])
                    
                    # Simple interaction bonus rules (could be enhanced with actual interaction data)
                    if 'stressed' in val1 and 'negative' in val2:
                        interaction_bonus += 0.5  # Stress + negative mood amplification
                    elif 'smoker' in val1 and 'alcohol' in val2:
                        interaction_bonus += 0.3  # Smoking + alcohol combination
            
            final_score = base_score + interaction_bonus
            
            compound_scores.append({
                'record_index': index,
                'compound_risk_score': round(final_score, 3),
                'base_additive_score': round(base_score, 3),
                'interaction_bonus': round(interaction_bonus, 3),
                'factors_included': factors_counted,
                'actual_high_risk': row['health_risk_level'] == 'high_risk' if 'health_risk_level' in row else False,
                'actual_elevated_risk': row['health_risk_level'] in ['high_risk', 'moderate_risk'] if 'health_risk_level' in row else False
            })
        
        return compound_scores
    
    def evaluate_compound_score_performance(self, compound_scores):
        """Evaluate how well compound scores predict actual risk levels."""
        
        scores_df = pd.DataFrame(compound_scores)
        
        if self.scoring_method == 'additive':
            score_col = 'compound_elevated_risk_score'
        else:
            score_col = 'compound_risk_score'
        
        # Define score thresholds
        score_thresholds = [1.5, 2.0, 2.5, 3.0]
        
        evaluation_results = {
            'method': self.scoring_method,
            'total_employees': len(scores_df),
            'threshold_analysis': []
        }
        
        print(f"\n" + "-"*60)
        print(f"COMPOUND SCORE EVALUATION ({self.scoring_method.upper()} METHOD)")
        print("-"*60)
        
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
                
                evaluation_results['threshold_analysis'].append({
                    'threshold': threshold,
                    'flagged_employees': flagged_count,
                    'flagged_pct': round(flagged_count / len(scores_df) * 100, 1),
                    'precision_high_risk': round(precision_high, 1),
                    'precision_elevated_risk': round(precision_elevated, 1),
                    'recall_high_risk': round(recall_high, 1),
                    'recall_elevated_risk': round(recall_elevated, 1)
                })
                
                print(f"\nThreshold {threshold}x: Flags {flagged_count} employees ({flagged_count/len(scores_df)*100:.1f}%)")
                print(f"  Precision: {precision_high:.1f}% high risk, {precision_elevated:.1f}% elevated risk")
                print(f"  Recall: {recall_high:.1f}% of high risk caught, {recall_elevated:.1f}% of elevated risk caught")
        
        return evaluation_results
    
    def find_score_outliers(self, compound_scores):
        """Find employees with surprising compound vs actual risk mismatches."""
        
        scores_df = pd.DataFrame(compound_scores)
        
        if self.scoring_method == 'additive':
            score_col = 'compound_elevated_risk_score'
        else:
            score_col = 'compound_risk_score'
        
        outliers = {
            'underestimated_risk': [],  # Low compound score but actually high risk
            'overestimated_risk': [],   # High compound score but actually low risk
            'perfect_predictions': []   # Compound score perfectly predicts risk
        }
        
        for _, row in scores_df.iterrows():
            compound_score = row[score_col]
            actual_high = row['actual_high_risk']
            actual_elevated = row['actual_elevated_risk']
            
            # Underestimated: Low compound score but high actual risk
            if compound_score < 1.5 and actual_high:
                employee_data = self.df.iloc[row['record_index']]
                outliers['underestimated_risk'].append({
                    'compound_score': compound_score,
                    'actual_risk': 'high_risk',
                    'sample_characteristics': self._extract_employee_profile(employee_data)
                })
            
            # Overestimated: High compound score but low actual risk  
            elif compound_score >= 2.5 and not actual_elevated:
                employee_data = self.df.iloc[row['record_index']]
                outliers['overestimated_risk'].append({
                    'compound_score': compound_score,
                    'actual_risk': 'low_risk',
                    'sample_characteristics': self._extract_employee_profile(employee_data)
                })
            
            # Perfect predictions: High score and high risk, or low score and low risk
            elif ((compound_score >= 2.0 and actual_elevated) or 
                  (compound_score < 1.5 and not actual_elevated)):
                employee_data = self.df.iloc[row['record_index']]
                outliers['perfect_predictions'].append({
                    'compound_score': compound_score,
                    'actual_risk': 'high_risk' if actual_high else 'elevated_risk' if actual_elevated else 'low_risk',
                    'sample_characteristics': self._extract_employee_profile(employee_data)
                })
        
        return outliers
    
    def _extract_employee_profile(self, employee_row):
        """Extract key characteristics of an individual employee for profiling."""
        
        profile = {}
        
        # Core demographics
        demo_vars = ['age_group', 'gender', 'has_children', 'bmi_category']
        for var in demo_vars:
            if var in employee_row:
                profile[var] = str(employee_row[var])
        
        # Key risk factors
        risk_vars = ['stress_calm', 'mood_positivity', 'smoking_status', 'chronic_conditions']
        for var in risk_vars:
            if var in employee_row:
                profile[var] = str(employee_row[var])
        
        return profile
    
    def generate_compound_scoring_insights(self):
        """Generate LLM-optimized insights about compound risk patterns."""
        
        # Calculate factor weights
        factor_weights = self.calculate_individual_risk_weights()
        
        # Create compound scores
        if self.scoring_method == 'additive':
            compound_scores = self.create_additive_compound_score(factor_weights)
        elif self.scoring_method == 'interaction-weighted':
            compound_scores = self.create_interaction_weighted_score(factor_weights)
        else:
            print(f"Unknown scoring method: {self.scoring_method}")
            return {}
        
        # Evaluate performance
        evaluation = self.evaluate_compound_score_performance(compound_scores)
        
        # Find scoring outliers
        score_outliers = self.find_score_outliers(compound_scores)
        
        # Identify high-impact factor values
        high_impact_factors = self._identify_high_impact_factors(factor_weights)
        
        insights = {
            'scoring_method': self.scoring_method,
            'evaluation': evaluation,
            'score_outliers': score_outliers,
            'high_impact_factors': high_impact_factors,
            'factor_weights': factor_weights,
            'sample_compound_scores': compound_scores[:20]  # Sample for inspection
        }
        
        return insights
    
    def _identify_high_impact_factors(self, factor_weights):
        """Identify factor values with highest risk impact."""
        
        high_impact = []
        
        for group_name, group_factors in factor_weights.items():
            for factor, factor_values in group_factors.items():
                for value, weights in factor_values.items():
                    
                    if weights['sample_size'] >= self.min_sample:
                        # Focus on elevated risk multiplier as main impact measure
                        impact_score = weights['elevated_risk_multiplier']
                        
                        if impact_score >= 2.0 or impact_score <= 0.5:  # High impact or protective
                            high_impact.append({
                                'factor_group': group_name,
                                'factor': factor,
                                'value': value,
                                'impact_multiplier': impact_score,
                                'risk_rate': weights['elevated_risk_rate'],
                                'sample_size': weights['sample_size'],
                                'impact_type': 'AMPLIFYING' if impact_score >= 2.0 else 'PROTECTIVE'
                            })
        
        # Sort by impact magnitude
        high_impact.sort(key=lambda x: abs(x['impact_multiplier'] - 1), reverse=True)
        
        return high_impact[:15]  # Top 15 highest impact factors
    
    def print_compound_score_report(self, insights):
        """Print human-readable compound scoring report."""
        
        print("\n" + "="*80)
        print("COMPOUND RISK SCORING ANALYSIS REPORT")
        print("="*80)
        
        print(f"\nSCORING METHOD: {insights['scoring_method'].upper()}")
        
        # Evaluation results
        evaluation = insights['evaluation']
        print(f"\n" + "-"*60)
        print("COMPOUND SCORE PERFORMANCE")
        print("-"*60)
        
        best_threshold = None
        best_balance = 0
        
        for threshold_result in evaluation['threshold_analysis']:
            threshold = threshold_result['threshold']
            precision = threshold_result['precision_elevated_risk']
            recall = threshold_result['recall_elevated_risk']
            
            # F1-like balance score
            balance = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            if balance > best_balance:
                best_balance = balance
                best_threshold = threshold_result
        
        if best_threshold:
            print(f"\nBest performing threshold: {best_threshold['threshold']}x")
            print(f"  Flags {best_threshold['flagged_employees']} employees ({best_threshold['flagged_pct']}% of workforce)")
            print(f"  {best_threshold['precision_elevated_risk']}% precision on elevated risk")
            print(f"  Catches {best_threshold['recall_elevated_risk']}% of all elevated risk employees")
        
        # High impact factors
        if insights['high_impact_factors']:
            print(f"\n" + "-"*60)
            print("HIGHEST IMPACT INDIVIDUAL FACTORS")
            print("-"*60)
            
            for factor in insights['high_impact_factors'][:8]:
                impact_type = factor['impact_type']
                symbol = "⚠" if impact_type == 'AMPLIFYING' else "🛡"
                
                print(f"\n• {factor['factor']} = {factor['value']} ({impact_type})")
                print(f"  Impact: {factor['impact_multiplier']}x baseline | Risk rate: {factor['risk_rate']}%")
                print(f"  Sample: {factor['sample_size']} employees | Group: {factor['factor_group']}")
        
        # Scoring outliers
        outliers = insights['score_outliers']
        
        if outliers['underestimated_risk']:
            print(f"\n" + "-"*60)
            print("UNDERESTIMATED RISK CASES")
            print("-"*60)
            print("Employees with low compound scores but actually high risk:")
            
            for case in outliers['underestimated_risk'][:3]:
                print(f"\n• Compound score: {case['compound_score']:.2f} | Actual: {case['actual_risk']}")
                profile = case['sample_characteristics']
                key_chars = [f"{k}={v}" for k, v in profile.items()][:4]
                print(f"  Profile: {', '.join(key_chars)}")
        
        if outliers['overestimated_risk']:
            print(f"\n" + "-"*60)
            print("OVERESTIMATED RISK CASES")  
            print("-"*60)
            print("Employees with high compound scores but actually low risk:")
            
            for case in outliers['overestimated_risk'][:3]:
                print(f"\n• Compound score: {case['compound_score']:.2f} | Actual: {case['actual_risk']}")
                profile = case['sample_characteristics']
                key_chars = [f"{k}={v}" for k, v in profile.items()][:4]
                print(f"  Profile: {', '.join(key_chars)}")
    
    def save_output(self, insights, output_path):
        """Save compound scoring insights to JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(insights, f, indent=2)
            print(f"\nCompound scoring insights saved to: {output_path}")
        except Exception as e:
            print(f"Error saving output: {e}")
    
    def run_analysis(self, factor_focus=None):
        """Execute the complete compound risk scoring analysis."""
        
        print("Compound Risk Scorer")
        print(f"Scoring method: {self.scoring_method}")
        print(f"Minimum sample size: {self.min_sample}")
        
        # Load data and define factor groups
        self.load_data()
        self.define_risk_factor_groups(factor_focus)
        
        if not self.risk_factors:
            print("Error: No risk factor groups defined.")
            return {'summary': {'method': self.scoring_method}, 'findings': []}
        
        # Generate compound scoring insights
        insights = self.generate_compound_scoring_insights()
        
        # Display results
        self.print_compound_score_report(insights)
        
        return insights

def main():
    parser = argparse.ArgumentParser(
        description='Compound Risk Scorer for Health Risk Assessment Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compound_risk_scorer.py --data preprocessed_data/HRA_data.csv
  python compound_risk_scorer.py --data data.csv --method interaction-weighted
  python compound_risk_scorer.py --data data.csv --factors stress,lifestyle --min-sample 20
        """
    )
    
    parser.add_argument('--data', 
                       default='preprocessed_data/HRA_data.csv',
                       help='Path to the processed health data CSV file')
    
    parser.add_argument('--method', 
                       choices=['additive', 'interaction-weighted'],
                       default='additive',
                       help='Compound scoring method (default: additive)')
    
    parser.add_argument('--factors', 
                       help='Comma-separated list of factor groups: stress,lifestyle,demographics,health,behavior')
    
    parser.add_argument('--min-sample', 
                       type=int, 
                       default=15,
                       help='Minimum sample size for factor analysis (default: 15)')
    
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
    scorer = CompoundRiskScorer(
        data_path=data_path,
        scoring_method=args.method,
        min_sample=args.min_sample,
        verbose=args.verbose
    )
    
    insights = scorer.run_analysis(factor_focus=args.factors)
    
    # Save output
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        scorer.save_output(insights, output_path)
    
    method = insights.get('scoring_method', args.method)
    print(f"\nCompound risk scoring analysis complete using {method} method.")

if __name__ == "__main__":
    main()