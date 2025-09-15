#!/usr/bin/env python3
"""
Simple Orchestrator for Health Risk Assessment Analysis Scripts

Runs all analysis scripts in scripts_new/ and saves outputs to text files.
Clear, simple, and easy to understand what's being executed.

Usage:
    python main.py --data path/to/data.csv
    python main.py --data data.csv --output-dir results
"""

import subprocess
import argparse
import sys
from pathlib import Path
from datetime import datetime
import os

def run_script_with_output(script_path, command_args, description):
    """Run a script with simple output."""

    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"Command: python {script_path} {command_args}")
    print(f"{'='*60}")

    full_command = f"python {script_path} {command_args}"

    try:
        result = subprocess.run(full_command, shell=True, cwd=Path.cwd())
        if result.returncode == 0:
            print(f"✓ SUCCESS")
        else:
            print(f"✗ FAILED (code {result.returncode})")
        return result.returncode == 0
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Simple Health Risk Assessment Analysis Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --data data.csv
  python main.py --data data.csv --output-dir results
        """
    )

    parser.add_argument('--data',
                       required=True,
                       help='Path to the CSV data file')

    parser.add_argument('--output-dir',
                       default='outputs',
                       help='Output directory for analysis results (default: outputs)')

    args = parser.parse_args()

    # Validate data file
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print(f"Health Risk Assessment Analysis Orchestrator")
    print(f"Data: {data_path}")
    print(f"Output Directory: {output_dir}")
    print(f"Started: {datetime.now()}")

    # Track results
    results = []

    # 1. Simple EDA - Comprehensive exploratory data analysis
    success = run_script_with_output(
        script_path="scripts_new/simple_eda.py",
        command_args=f"--data {data_path} --output {output_dir / '01_simple_eda.txt'}",
        description="Exploratory Data Analysis (EDA) - Complete statistical overview"
    )
    results.append(("Simple EDA", success))

    # 2. Statistical Surprise Detection - Find unexpected patterns
    success = run_script_with_output(
        script_path="scripts_new/statistical_surprise.py",
        command_args=f"--data {data_path} --threshold 2.0 --min-sample 10 --verbose --output {output_dir / '02_statistical_surprises.txt'}",
        description="Statistical Surprise Detection - Unexpected demographic/lifestyle patterns"
    )
    results.append(("Statistical Surprises", success))

    # 3. Demographic Outlier Spotting - Small segments with big health impacts
    success = run_script_with_output(
        script_path="scripts_new/demographic_outlier_spotter.py",
        command_args=f"--data {data_path} --output {output_dir / '03_demographic_outliers.txt'}",
        description="Demographic Outlier Detection - Small segments with disproportionate health impacts"
    )
    results.append(("Demographic Outliers", success))

    # 4. Compound Risk Scoring - Additive Method
    success = run_script_with_output(
        script_path="scripts_new/compound_risk_scorer.py",
        command_args=f"--data {data_path} --method additive --output {output_dir / '04_compound_risk_additive.txt'}",
        description="Compound Risk Scoring - Additive method for multi-factor risk assessment"
    )
    results.append(("Compound Risk (Additive)", success))

    # 5. Compound Risk Scoring - Interaction-Weighted Method
    success = run_script_with_output(
        script_path="scripts_new/compound_risk_scorer.py",
        command_args=f"--data {data_path} --method interaction-weighted --output {output_dir / '05_compound_risk_interaction.txt'}",
        description="Compound Risk Scoring - Interaction-weighted method with factor amplification"
    )
    results.append(("Compound Risk (Interaction)", success))

    # 6. Interaction Scanner - General Mode
    success = run_script_with_output(
        script_path="scripts_new/interaction_scanner.py",
        command_args=f"--data {data_path} --mode general --output {output_dir / '06_interactions_general.txt'}",
        description="Interaction Scanner - General mode (broad variable interaction analysis)"
    )
    results.append(("Interactions (General)", success))

    # 7. Interaction Scanner - Focused Mode
    success = run_script_with_output(
        script_path="scripts_new/interaction_scanner.py",
        command_args=f"--data {data_path} --mode focused --output {output_dir / '07_interactions_focused.txt'}",
        description="Interaction Scanner - Focused mode (key risk factor interactions only)"
    )
    results.append(("Interactions (Focused)", success))

    # Final Summary
    print(f"\n{'='*80}")
    print("ANALYSIS ORCHESTRATION COMPLETE")
    print(f"{'='*80}")

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    print(f"\nResults Summary:")
    print(f"  Total analyses: {total_count}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {total_count - success_count}")
    print(f"  Output directory: {output_dir}")

    print(f"\nDetailed Results:")
    for analysis_name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {status} {analysis_name}")

    if success_count == total_count:
        print(f"\n All analyses completed successfully!")
        print(f" Check {output_dir}/ for detailed results")
    else:
        print(f"\n  {total_count - success_count} analyses failed - check output files for details")

    print(f"\nFinished: {datetime.now()}")

if __name__ == "__main__":
    main()