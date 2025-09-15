#!/usr/bin/env python3
"""
Base Analysis Runner for Health Risk Assessment Data

Automatically runs all foundation-level analyses that don't require decision-making.
Saves all outputs to the outputs/ folder for LLM review and drilling-deeper decisions.

This script runs:
1. Complete EDA (simple_eda.py --phase all --verbose)
2. Statistical surprise detection (broad threshold)
3. Interaction scanning (exploratory threshold)  
4. Demographic outlier spotting (standard thresholds)
5. Both compound scoring methods

Usage:
    python base.py --data path/to/data.csv
    python base.py --data path/to/data.csv --quick
    python base.py --data path/to/data.csv --timestamp custom_name
"""

import pandas as pd
import subprocess
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURABLE COLUMN MAPPINGS - EDIT HERE FOR DIFFERENT DATASETS
# =============================================================================

# Health outcome variables (in order of preference)
HEALTH_RISK_LEVEL_COLS = ['health_risk_level', 'risk_level', 'health_risk']
HEALTH_RISK_SCORE_COLS = ['health_risk_score', 'Total_Health_Score', 'total_health_score', 'risk_score']

# Core demographic variables to analyze
DEMOGRAPHIC_VARIABLES = [
    'age_group', 'gender', 'has_children', 'bmi_category',
    'chronic_conditions', 'supplements', 'health_perception'
]

# Extended demographic/lifestyle variables
EXTENDED_VARIABLES = [
    'smoking_status', 'alcohol_level', 'exercise_freq', 'nutrition_quality',
    'sleep_duration', 'stress_calm', 'mood_positivity', 'water_intake',
    'Data.smoking_status'
]

class BaseAnalysisRunner:
    def __init__(self, data_path, output_dir="outputs", include_json=False, verbose=False):
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.include_json = include_json
        self.verbose = verbose
        self.standardized_data_path = None
        
        # Create outputs directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Track analysis results
        self.analysis_summary = {
            'data_path': str(data_path),
            'analyses_completed': [],
            'total_runtime_seconds': 0,
            'key_findings_summary': {}
        }
    
    def _resolve_column_name(self, column_options, df_columns):
        """Find the first available column from options list."""
        for col in column_options:
            if col in df_columns:
                return col
        return None
    
    def validate_and_standardize_data(self):
        """Validate data and create a standardized version for all scripts to use."""
        
        print("\n" + "="*60)
        print("DATA VALIDATION AND STANDARDIZATION")
        print("="*60)
        
        try:
            # Load original data
            df = pd.read_csv(self.data_path)
            print(f"✓ Data loaded: {df.shape[0]} records, {df.shape[1]} columns")
            
            # Check for health risk level column
            health_risk_level_col = self._resolve_column_name(HEALTH_RISK_LEVEL_COLS, df.columns)
            health_risk_score_col = self._resolve_column_name(HEALTH_RISK_SCORE_COLS, df.columns)
            
            if not health_risk_level_col and not health_risk_score_col:
                print(f"\n❌ ERROR: No health outcome columns found!")
                print(f"Looking for health risk level columns: {HEALTH_RISK_LEVEL_COLS}")
                print(f"Looking for health risk score columns: {HEALTH_RISK_SCORE_COLS}")
                print(f"Available columns: {list(df.columns)}")
                raise ValueError("Required health outcome columns not found in dataset")
            
            # Standardize column names by creating aliases
            standardization_notes = []
            
            if health_risk_level_col and health_risk_level_col != 'health_risk_level':
                df['health_risk_level'] = df[health_risk_level_col]
                standardization_notes.append(f"'{health_risk_level_col}' → 'health_risk_level'")
                
            if health_risk_score_col and health_risk_score_col != 'health_risk_score':
                df['health_risk_score'] = df[health_risk_score_col]
                standardization_notes.append(f"'{health_risk_score_col}' → 'health_risk_score'")
            
            # Check available demographic variables
            all_demo_vars = DEMOGRAPHIC_VARIABLES + EXTENDED_VARIABLES
            available_demographics = [col for col in all_demo_vars if col in df.columns]
            
            if not available_demographics:
                print(f"\n⚠️  WARNING: No standard demographic variables found!")
                print(f"Looking for: {all_demo_vars}")
                print("Scripts may have limited functionality")
            else:
                print(f"✓ Available demographic variables: {len(available_demographics)}")
            
            # Save standardized data
            self.standardized_data_path = self.output_dir / "standardized_data.csv"
            df.to_csv(self.standardized_data_path, index=False)
            
            print(f"✓ Standardized data saved to: {self.standardized_data_path}")
            
            if standardization_notes:
                print("\nColumn standardizations applied:")
                for note in standardization_notes:
                    print(f"  • {note}")
            
            # Validate outcome columns are working
            if 'health_risk_level' in df.columns:
                risk_counts = df['health_risk_level'].value_counts()
                print(f"✓ Health risk level distribution: {dict(risk_counts)}")
            
            if 'health_risk_score' in df.columns:
                score_stats = df['health_risk_score'].describe()
                print(f"✓ Health risk score range: {score_stats['min']:.1f} - {score_stats['max']:.1f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in data validation: {e}")
            raise
    
    def run_command_with_output_capture(self, command, output_filename, analysis_name):
        """Run a command and capture both stdout and save to file."""
        
        print(f"\n{'='*60}")
        print(f"Running: {analysis_name}")
        print(f"Command: {command}")
        print(f"{'='*60}")
        
        start_time = datetime.now()
        
        try:
            # Run command and capture output
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=Path.cwd()
            )
            
            end_time = datetime.now()
            runtime = (end_time - start_time).total_seconds()
            
            # Save output to file
            output_path = self.output_dir / output_filename
            
            with open(output_path, 'w') as f:
                f.write(f"Command: {command}\\n")
                f.write(f"Timestamp: {start_time}\\n")
                f.write(f"Runtime: {runtime:.2f} seconds\\n")
                f.write(f"Return code: {result.returncode}\\n")
                f.write("=" * 80 + "\\n")
                f.write("STDOUT:\\n")
                f.write(result.stdout)
                if result.stderr:
                    f.write("\\n" + "=" * 80 + "\\n")
                    f.write("STDERR:\\n")
                    f.write(result.stderr)
            
            # Print condensed output to console
            print(f"✓ Completed in {runtime:.1f}s")
            print(f"✓ Output saved to: {output_path}")
            
            # Show key results preview
            if result.stdout:
                lines = result.stdout.strip().split('\\n')
                summary_lines = [line for line in lines[-10:] if line.strip()]
                if summary_lines:
                    print("Key results:")
                    for line in summary_lines[-3:]:
                        print(f"  {line}")
            
            # Track completion
            self.analysis_summary['analyses_completed'].append({
                'name': analysis_name,
                'output_file': str(output_path),
                'runtime_seconds': runtime,
                'success': result.returncode == 0
            })
            
            return result.returncode == 0, str(output_path)
            
        except Exception as e:
            print(f"✗ Error running {analysis_name}: {e}")
            return False, None
    
    def run_foundation_eda(self):
        """Run complete foundation EDA analysis."""
        
        command = f"python scripts/simple_eda.py --data {self.standardized_data_path} --phase all --verbose"
        success, output_path = self.run_command_with_output_capture(
            command, 
            "0_foundation_eda.txt",
            "Foundation EDA (Complete Statistics + Cross-Patterns)"
        )
        
        if success:
            self.analysis_summary['key_findings_summary']['foundation_eda'] = {
                'status': 'completed',
                'output_file': output_path,
                'description': 'Complete 1D and 2D statistical analysis foundation'
            }
    
    def run_statistical_surprises(self):
        """Run statistical surprise detection with broad threshold."""
        
        # Text output
        command = f"python scripts/statistical_surprise.py --data {self.standardized_data_path} --threshold 2.0 --min-sample 10"
        success, output_path = self.run_command_with_output_capture(
            command,
            "1_statistical_surprises.txt", 
            "Statistical Surprise Detection (Broad Threshold)"
        )
        
        # JSON output if requested
        if success and self.include_json:
            json_path = self.output_dir / "1_statistical_surprises.json"
            json_command = f"python scripts/statistical_surprise.py --data {self.standardized_data_path} --threshold 2.0 --output {json_path}"
            subprocess.run(json_command, shell=True, capture_output=True)
            
            self.analysis_summary['key_findings_summary']['statistical_surprises'] = {
                'status': 'completed',
                'text_output': output_path,
                'json_output': str(json_path) if self.include_json else None,
                'description': 'Demographic and lifestyle subgroups with unexpected outcomes'
            }
        elif success:
            self.analysis_summary['key_findings_summary']['statistical_surprises'] = {
                'status': 'completed',
                'text_output': output_path,
                'description': 'Demographic and lifestyle subgroups with unexpected outcomes'
            }
    
    def run_interaction_scanning(self):
        """Run interaction effect scanning with exploratory settings."""
        
        # Standard exploratory mode
        command = f"python scripts/interaction_scanner.py --data {self.standardized_data_path} --threshold 1.8"
        success, output_path = self.run_command_with_output_capture(
            command,
            "2_interaction_effects.txt",
            "Interaction Scanning (Exploratory - All Variables)"
        )
        
        # JSON output if requested
        if success and self.include_json:
            json_path = self.output_dir / "2_interaction_effects.json" 
            json_command = command + f" --output {json_path}"
            subprocess.run(json_command, shell=True, capture_output=True)
            
            self.analysis_summary['key_findings_summary']['interaction_effects'] = {
                'status': 'completed',
                'text_output': output_path,
                'json_output': str(json_path) if self.include_json else None,
                'description': 'Variable combinations with amplified or protective effects'
            }
        elif success:
            self.analysis_summary['key_findings_summary']['interaction_effects'] = {
                'status': 'completed',
                'text_output': output_path,
                'description': 'Variable combinations with amplified or protective effects'
            }
    
    def run_demographic_outliers(self):
        """Run demographic outlier detection with standard settings."""
        
        # Text output
        command = f"python scripts/demographic_outlier_spotter.py --data {self.standardized_data_path} --max-size 15.0 --min-risk-ratio 1.5 --min-sample 8"
        success, output_path = self.run_command_with_output_capture(
            command,
            "3_demographic_outliers.txt",
            "Demographic Outlier Detection (Standard Settings)"
        )
        
        # JSON output if requested
        if success and self.include_json:
            json_path = self.output_dir / "3_demographic_outliers.json"
            json_command = command + f" --output {json_path}"
            subprocess.run(json_command, shell=True, capture_output=True)
            
            self.analysis_summary['key_findings_summary']['demographic_outliers'] = {
                'status': 'completed', 
                'text_output': output_path,
                'json_output': str(json_path) if self.include_json else None,
                'description': 'Small demographic segments with disproportionate health impacts'
            }
        elif success:
            self.analysis_summary['key_findings_summary']['demographic_outliers'] = {
                'status': 'completed', 
                'text_output': output_path,
                'description': 'Small demographic segments with disproportionate health impacts'
            }
    
    def run_compound_scoring(self):
        """Run both compound scoring methods."""
        
        # Additive method
        additive_command = f"python scripts/compound_risk_scorer.py --data {self.standardized_data_path} --method additive"
        success1, output_path1 = self.run_command_with_output_capture(
            additive_command,
            "4_compound_scoring_additive.txt",
            "Compound Risk Scoring (Additive Method)"
        )
        
        # Interaction-weighted method  
        interaction_command = f"python scripts/compound_risk_scorer.py --data {self.standardized_data_path} --method interaction-weighted"
        success2, output_path2 = self.run_command_with_output_capture(
            interaction_command,
            "5_compound_scoring_interaction.txt", 
            "Compound Risk Scoring (Interaction-Weighted Method)"
        )
        
        # JSON outputs if requested
        if self.include_json:
            if success1:
                json_path1 = self.output_dir / "4_compound_scoring_additive.json"
                subprocess.run(additive_command + f" --output {json_path1}", shell=True, capture_output=True)
            if success2:
                json_path2 = self.output_dir / "5_compound_scoring_interaction.json"
                subprocess.run(interaction_command + f" --output {json_path2}", shell=True, capture_output=True)
        
        if success1 or success2:
            self.analysis_summary['key_findings_summary']['compound_scoring'] = {
                'additive_method': {
                    'status': 'completed' if success1 else 'failed',
                    'text_output': output_path1 if success1 else None,
                    'json_output': str(self.output_dir / "4_compound_scoring_additive.json") if (success1 and self.include_json) else None
                },
                'interaction_method': {
                    'status': 'completed' if success2 else 'failed', 
                    'text_output': output_path2 if success2 else None,
                    'json_output': str(self.output_dir / "5_compound_scoring_interaction.json") if (success2 and self.include_json) else None
                },
                'description': 'Alternative risk scoring approaches and performance evaluation'
            }
    
    def generate_analysis_index(self):
        """Generate an index file for LLM to understand what analyses are available."""
        
        index_path = self.output_dir / "analysis_index.json"
        
        # Add file sizes and key statistics
        for analysis_name, analysis_info in self.analysis_summary['key_findings_summary'].items():
            if isinstance(analysis_info, dict) and 'text_output' in analysis_info:
                try:
                    if analysis_info['text_output'] and Path(analysis_info['text_output']).exists():
                        file_size = Path(analysis_info['text_output']).stat().st_size
                        analysis_info['text_file_size_kb'] = round(file_size / 1024, 1)
                        
                        # Extract key statistics from output files
                        with open(analysis_info['text_output'], 'r') as f:
                            content = f.read()
                            analysis_info['key_stats'] = self._extract_key_statistics(content, analysis_name)
                except:
                    pass
        
        # Save comprehensive index
        with open(index_path, 'w') as f:
            json.dump(self.analysis_summary, f, indent=2)
        
        print(f"\\n✓ Analysis index saved to: {index_path}")
        return str(index_path)
    
    def _extract_key_statistics(self, content, analysis_type):
        """Extract key statistics from analysis output for quick LLM review."""
        
        key_stats = {}
        
        if analysis_type == 'foundation_eda':
            # Extract dataset basics
            lines = content.split('\\n')
            for line in lines:
                if 'Shape:' in line:
                    key_stats['dataset_shape'] = line.split('Shape:')[1].strip()
                elif 'Strong Correlations' in line:
                    key_stats['has_strong_correlations'] = True
                elif 'No strong correlations found' in line:
                    key_stats['has_strong_correlations'] = False
        
        elif analysis_type == 'statistical_surprises':
            # Count surprise types
            surprise_count = content.count('Magnitude:')
            key_stats['total_surprises'] = surprise_count
            key_stats['has_high_magnitude'] = '>5.0σ' in content
        
        elif analysis_type == 'interaction_effects':
            # Count interactions and max amplification
            interaction_count = content.count('amplification')
            key_stats['total_amplifications'] = interaction_count
            key_stats['has_extreme_amplification'] = '10.0x' in content or '5.0x' in content
        
        elif analysis_type == 'demographic_outliers':
            # Count outliers and risk ratios
            outlier_count = content.count('Risk ratio:')
            key_stats['total_outliers'] = outlier_count
            key_stats['has_high_risk_ratios'] = '3.0x' in content or '4.0x' in content
        
        return key_stats
    
    def print_completion_summary(self, index_path):
        """Print summary of completed analyses."""
        
        print("\\n" + "="*80)
        print("BASE ANALYSIS COMPLETION SUMMARY")
        print("="*80)
        
        total_runtime = sum([a['runtime_seconds'] for a in self.analysis_summary['analyses_completed']])
        success_count = len([a for a in self.analysis_summary['analyses_completed'] if a['success']])
        total_count = len(self.analysis_summary['analyses_completed'])
        
        print(f"\\nExecution Summary:")
        print(f"  Total analyses: {total_count}")
        print(f"  Successful: {success_count}")
        print(f"  Total runtime: {total_runtime:.1f} seconds")
        print(f"  Output directory: {self.output_dir}")
        print(f"  Analysis index: {index_path}")
        
        print(f"\\nCompleted Analyses:")
        for analysis in self.analysis_summary['analyses_completed']:
            status = "✓" if analysis['success'] else "✗"
            print(f"  {status} {analysis['name']} ({analysis['runtime_seconds']:.1f}s)")
        
        # Show key findings preview
        findings = self.analysis_summary['key_findings_summary']
        
        print(f"\\nKey Findings Preview:")
        
        if 'statistical_surprises' in findings:
            surprise_stats = findings['statistical_surprises'].get('key_stats', {})
            surprise_count = surprise_stats.get('total_surprises', 0)
            print(f"  📊 Statistical surprises detected: {surprise_count}")
        
        if 'interaction_effects' in findings:
            interaction_stats = findings['interaction_effects'].get('key_stats', {})
            interaction_count = interaction_stats.get('total_amplifications', 0)
            print(f"  ⚡ Interaction amplifications found: {interaction_count}")
        
        if 'demographic_outliers' in findings:
            outlier_stats = findings['demographic_outliers'].get('key_stats', {})
            outlier_count = outlier_stats.get('total_outliers', 0)
            print(f"  🎯 Demographic outliers identified: {outlier_count}")
        
        print(f"\\nNext Steps for LLM Analysis:")
        print(f"1. Review analysis index: {index_path}")
        print(f"2. Read foundation EDA for data understanding")
        print(f"3. Identify 2-3 most surprising patterns")
        print(f"4. Use discovery tools with focused --include/--focus arguments")
        print(f"5. Generate insights and narratives from findings")
    
    def run_all_base_analyses(self):
        """Execute all foundation-level analyses automatically."""
        
        print("Health Risk Assessment - Base Analysis Runner")
        print(f"Data: {self.data_path}")
        print(f"Output directory: {self.output_dir}")
        print(f"Include JSON outputs: {self.include_json}")
        
        start_time = datetime.now()
        
        # 0. Validate and standardize data first
        self.validate_and_standardize_data()
        
        # 1. Foundation EDA (always run)
        self.run_foundation_eda()
        
        # 2. Statistical surprises (broad threshold for discovery)
        self.run_statistical_surprises()
        
        # 3. Interaction scanning
        self.run_interaction_scanning() 
        
        # 4. Demographic outliers (standard settings)
        self.run_demographic_outliers()
        
        # 5. Compound scoring (both methods)
        self.run_compound_scoring()
        
        # Generate analysis index
        end_time = datetime.now()
        self.analysis_summary['total_runtime_seconds'] = (end_time - start_time).total_seconds()
        
        index_path = self.generate_analysis_index()
        
        # Print completion summary
        self.print_completion_summary(index_path)
        
        return index_path

def main():
    parser = argparse.ArgumentParser(
        description='Base Analysis Runner - Automated Foundation Analysis Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python base.py --data preprocessed_data/HRA_data.csv
  python base.py --data data.csv --json
  python base.py --data data.csv --output-dir weekly_reports --json
        """
    )
    
    parser.add_argument('--data', 
                       default='preprocessed_data/HRA_data.csv',
                       help='Path to the processed health data CSV file')
    
    parser.add_argument('--output-dir', 
                       default='outputs',
                       help='Output directory for analysis results (default: outputs)')
    
    parser.add_argument('--json', 
                       action='store_true',
                       help='Include JSON outputs in addition to text outputs')
    
    parser.add_argument('--verbose', 
                       action='store_true',
                       help='Verbose output during execution')
    
    args = parser.parse_args()
    
    # Validate data path
    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = Path.cwd() / data_path
    
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)
    
    # Run base analysis suite
    runner = BaseAnalysisRunner(
        data_path=data_path,
        output_dir=args.output_dir,
        include_json=args.json,
        verbose=args.verbose
    )
    
    index_path = runner.run_all_base_analyses()
    
    print(f"\\n🎉 Base analysis suite complete!")
    print(f"📁 All outputs available in: {runner.output_dir}")
    print(f"📋 Analysis index: {index_path}")

if __name__ == "__main__":
    main()