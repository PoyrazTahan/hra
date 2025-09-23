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

def run_script(script_path, command_args, description):
    """Run a script that writes directly to output file."""

    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"Command: python {script_path} {command_args}")
    print(f"{'='*60}")

    full_command = f"python {script_path} {command_args}"

    try:
        result = subprocess.run(full_command, shell=True, cwd=Path.cwd(),
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ SUCCESS")
            if result.stdout.strip():
                print(f"  Output: {result.stdout.strip()}")
        else:
            print(f"✗ FAILED (code {result.returncode})")
            if result.stderr.strip():
                print(f"  Error: {result.stderr.strip()}")
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

    # Define analysis scripts with their descriptions
    analyses = [
        ("_scripts/01_simple_eda.py", "Simple EDA", "Exploratory Data Analysis (EDA) - Complete statistical overview"),
        ("_scripts/02_statistical_surprise_refactored.py", "Statistical Surprises", "Statistical Surprise Detection - Unexpected demographic/lifestyle patterns"),
        ("_scripts/03_demographic_outlier_spotter_refactored.py", "Demographic Outliers", "Demographic Outlier Detection - Small segments with disproportionate health impacts"),
        ("_scripts/04_compound_risk_scorer_refactored.py", "Compound Risk (Additive)", "Compound Risk Scoring - Additive method for multi-factor risk assessment", "--method additive"),
        ("_scripts/04_compound_risk_scorer_refactored.py", "Compound Risk (Interaction)", "Compound Risk Scoring - Interaction-weighted method with factor amplification", "--method interaction-weighted"),
        ("_scripts/05_column_relation_analysis.py", "Column Relationships", "Column Relationship Analysis - Descriptive-to-descriptive correlations and clustering")
    ]

    # Create unified output file
    unified_output = output_dir / "unified_analysis_report.txt"

    # Initialize unified report
    with open(unified_output, 'w') as f:
        f.write("="*80 + "\n")
        f.write("HEALTH RISK ASSESSMENT - UNIFIED ANALYSIS REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"Data Source: {data_path}\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write("="*80 + "\n\n")

    # Run each analysis and collect results (fail-fast approach)
    temp_files_created = []

    for analysis in analyses:
        script_path = analysis[0]
        analysis_name = analysis[1]
        description = analysis[2]
        extra_args = analysis[3] if len(analysis) > 3 else ""

        # Create temporary output file
        temp_output = output_dir / f"temp_{analysis_name.replace(' ', '_').replace('(', '').replace(')', '').lower()}.txt"
        temp_files_created.append(temp_output)

        # Run script with temp output
        command_args = f"{data_path} {temp_output} {extra_args}".strip()
        success = run_script(
            script_path=script_path,
            command_args=command_args,
            description=description
        )
        results.append((analysis_name, success))

        # FAIL-FAST: If any script fails, clean up and exit
        if not success:
            print(f"\n❌ ANALYSIS FAILED - STOPPING PIPELINE")
            print(f"   Failed script: {analysis_name}")
            print(f"   Error occurred in: {script_path}")

            # Clean up any temp files created
            for temp_file in temp_files_created:
                if temp_file.exists():
                    temp_file.unlink()

            # Remove incomplete unified output file
            if unified_output.exists():
                unified_output.unlink()

            print(f"\n   Temporary files cleaned up.")
            print(f"   Fix the error in {script_path} and try again.")
            sys.exit(1)

        # Append to unified report if successful
        if temp_output.exists():
            with open(unified_output, 'a') as unified_file:
                unified_file.write(f"\n{'='*60}\n")
                unified_file.write(f"ANALYSIS: {analysis_name.upper()}\n")
                unified_file.write(f"{'='*60}\n\n")

                with open(temp_output, 'r') as temp_file:
                    unified_file.write(temp_file.read())

                unified_file.write(f"\n{'='*60}\n")
                unified_file.write(f"END: {analysis_name.upper()}\n")
                unified_file.write(f"{'='*60}\n\n")

            # Clean up temp file
            temp_output.unlink()
        else:
            # Script succeeded but no output file created
            with open(unified_output, 'a') as unified_file:
                unified_file.write(f"\n{'='*60}\n")
                unified_file.write(f"ANALYSIS: {analysis_name.upper()}\n")
                unified_file.write(f"{'='*60}\n\n")
                unified_file.write("No output generated by script.\n")
                unified_file.write(f"\n{'='*60}\n")
                unified_file.write(f"END: {analysis_name.upper()}\n")
                unified_file.write(f"{'='*60}\n\n")

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
        print(f"\n✓ All analyses completed successfully!")
        print(f"  Unified report: {unified_output}")
    else:
        print(f"\n⚠ {total_count - success_count} analyses failed - check unified report for details")
        print(f"  Unified report: {unified_output}")

    print(f"\nFinished: {datetime.now()}")

if __name__ == "__main__":
    main()