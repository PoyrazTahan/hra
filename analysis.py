#!/usr/bin/env python3
"""
Health Risk Assessment Data Science Analysis Pipeline

Orchestrates data science analysis scripts to generate unified reports.
Pure data science processing - produces analysis reports for downstream LLM processing.

Usage:
    python analysis.py                                     # Process default main dataset and all eligible companies
    python analysis.py --main-only                        # Process only main dataset
    python analysis.py --data custom.csv                  # Process custom dataset and companies
    python analysis.py --data data.csv --output-dir results  # Custom input and output
"""

import subprocess
import argparse
import sys
from pathlib import Path
from datetime import datetime
import os
import csv

def count_records(csv_file):
    """Count records in CSV file (excluding header)."""
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        return sum(1 for row in reader) - 1

def process_dataset(data_path, output_file, dataset_name="Dataset", record_threshold=30):
    """Process a single dataset through all analysis scripts."""

    # Check if dataset has enough records
    record_count = count_records(data_path)
    if record_count < record_threshold:
        print(f"⚠ SKIPPING {dataset_name}: Only {record_count} records (minimum 30 required)")
        return False

    print(f"📊 PROCESSING {dataset_name}: {record_count} records")

    # Define analysis scripts with their descriptions
    analyses = [
        ("scripts/stats/01_simple_eda.py", "Simple EDA", "Exploratory Data Analysis (EDA) - Complete statistical overview"),
        ("scripts/stats/02_statistical_surprise_refactored.py", "Statistical Surprises", "Statistical Surprise Detection - Unexpected demographic/lifestyle patterns"),
        ("scripts/stats/03_demographic_outlier_spotter_refactored.py", "Demographic Outliers", "Demographic Outlier Detection - Small segments with disproportionate health impacts"),
        ("scripts/stats/04_compound_risk_scorer_refactored.py", "Compound Risk (Additive)", "Compound Risk Scoring - Additive method for multi-factor risk assessment", "--method additive"),
        ("scripts/stats/04_compound_risk_scorer_refactored.py", "Compound Risk (Interaction)", "Compound Risk Scoring - Interaction-weighted method with factor amplification", "--method interaction-weighted"),
        ("scripts/stats/05_column_relation_analysis.py", "Column Relationships", "Column Relationship Analysis - Descriptive-to-descriptive correlations and clustering")
    ]

    # Initialize report
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"HEALTH RISK ASSESSMENT - {dataset_name.upper()} ANALYSIS REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"Data Source: {data_path}\n")
        f.write(f"Records: {record_count}\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write("="*80 + "\n\n")

    # Process each analysis
    temp_files_created = []
    output_dir = Path(output_file).parent

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

        # FAIL-FAST: If any script fails, clean up and exit
        if not success:
            print(f"\n❌ ANALYSIS FAILED - STOPPING PIPELINE")
            print(f"   Failed script: {analysis_name}")
            print(f"   Dataset: {dataset_name}")
            print(f"   Error occurred in: {script_path}")

            # Clean up temp files
            for temp_file in temp_files_created:
                if temp_file.exists():
                    temp_file.unlink()

            # Remove incomplete output file
            if Path(output_file).exists():
                Path(output_file).unlink()

            sys.exit(1)

        # Append to report if successful
        if temp_output.exists():
            with open(output_file, 'a') as unified_file:
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
            with open(output_file, 'a') as unified_file:
                unified_file.write(f"\n{'='*60}\n")
                unified_file.write(f"ANALYSIS: {analysis_name.upper()}\n")
                unified_file.write(f"{'='*60}\n\n")
                unified_file.write("No output generated by script.\n")
                unified_file.write(f"\n{'='*60}\n")
                unified_file.write(f"END: {analysis_name.upper()}\n")
                unified_file.write(f"{'='*60}\n\n")

    return True

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
        description='Health Risk Assessment Multi-Company Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Process default main dataset and all eligible companies
  python main.py --main-only                       # Process only main dataset
  python main.py --data custom.csv                 # Process custom dataset and companies
  python main.py --data data.csv --output-dir results  # Custom input and output
        """
    )

    parser.add_argument('--data',
                       default='01_in/HRA_data.csv',
                       help='Path to the main CSV data file (default: 01_in/HRA_data.csv)')

    parser.add_argument('--output-dir',
                       default='02_out',
                       help='Output directory for analysis results (default: 02_out)')

    parser.add_argument('--main-only',
                       action='store_true',
                       help='Process only the main dataset (skip company processing)')

    args = parser.parse_args()

    print(f"Health Risk Assessment Multi-Company Analysis Pipeline")
    print(f"Started: {datetime.now()}")

    # Create output directories
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    company_output_dir = output_dir / "company"
    company_output_dir.mkdir(exist_ok=True)

    # Process main dataset
    main_data_path = Path(args.data)
    if not main_data_path.exists():
        print(f"Error: Main data file not found: {main_data_path}")
        sys.exit(1)

    # Use the filename stem for the main report (e.g., HRA_data.csv -> HRA_data_report.txt)
    main_output_file = output_dir / f"{main_data_path.stem}_report.txt"
    print(f"\n{'='*80}")
    print("PROCESSING MAIN DATASET")
    print(f"{'='*80}")

    success = process_dataset(main_data_path, main_output_file, "Main Dataset")
    if not success:
        print("Main dataset processing failed")
        sys.exit(1)

    # Process company datasets (unless main-only flag is set)
    if not args.main_only:
        print(f"\n{'='*80}")
        print("PROCESSING COMPANY DATASETS")
        print(f"{'='*80}")

        company_dir = Path("01_in/company")
        if not company_dir.exists():
            print(f"Warning: Company directory not found: {company_dir}")
        else:
            processed_companies = 0
            skipped_companies = 0

            # Process each company CSV file
            for company_file in sorted(company_dir.glob("Company_*.csv")):
                company_name = company_file.stem  # e.g., "Company_10"
                company_output_file = company_output_dir / f"{company_name}_report.txt"

                success = process_dataset(company_file, company_output_file, company_name)
                if success:
                    processed_companies += 1
                else:
                    skipped_companies += 1

            print(f"\n{'='*80}")
            print("COMPANY PROCESSING SUMMARY")
            print(f"{'='*80}")
            print(f"Companies processed: {processed_companies}")
            print(f"Companies skipped: {skipped_companies}")

    print(f"\n{'='*80}")
    print("PIPELINE COMPLETE")
    print(f"{'='*80}")
    print(f"Main report: {main_output_file}")
    if not args.main_only:
        print(f"Company reports: {company_output_dir}")
    print(f"Finished: {datetime.now()}")

if __name__ == "__main__":
    main()