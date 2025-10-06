#!/usr/bin/env python3
"""
Re-calculate group sizes for existing JSON insights files.

This script updates existing JSON files with fresh group size calculations
without re-running the expensive Claude API calls. Useful when you've updated
the group_size_calculator logic and want to apply the changes.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

# Add llm to path
sys.path.insert(0, str(Path(__file__).parent / 'llm'))
from group_size_calculator import GroupSizeCalculator


def recalculate_json_file(json_path: Path, csv_path: Path) -> bool:
    """
    Re-calculate group sizes for a single JSON file.

    Args:
        json_path: Path to the JSON insights file
        csv_path: Path to the CSV data file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read existing JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        insights = data.get('insights', [])
        if not insights:
            print(f"  ⚠️  No insights found in {json_path.name}")
            return False

        # Create calculator
        calculator = GroupSizeCalculator(str(csv_path))

        # Re-calculate group sizes for all insights
        updated_insights = calculator.calculate_sizes_for_insights(insights)

        # Update the data
        data['insights'] = updated_insights

        # Save back to file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  ✅ Updated {len(updated_insights)} insights in {json_path.name}")
        return True

    except Exception as e:
        print(f"  ❌ Failed to process {json_path.name}: {e}")
        return False


def determine_csv_path(json_path: Path, base_csv_dir: Path) -> Path:
    """
    Determine the correct CSV file based on JSON file path.

    Args:
        json_path: Path to the JSON insights file
        base_csv_dir: Base directory containing CSV files (e.g., 01_in)

    Returns:
        Path to the appropriate CSV file
    """
    # Check if this is a company-specific file
    if 'company' in json_path.parts:
        # Extract company identifier from filename
        # Example: Company_28_report_insights.json -> Company_28
        stem = json_path.stem.replace('_report_insights', '').replace('_insights', '')
        csv_path = base_csv_dir / 'company' / f"{stem}.csv"

        if csv_path.exists():
            return csv_path
        else:
            print(f"  ⚠️  Company CSV not found: {csv_path}")
            print(f"     Falling back to main CSV")

    # Default to main CSV
    return base_csv_dir / 'HRA_data.csv'


def main():
    parser = argparse.ArgumentParser(
        description='Re-calculate group sizes for existing JSON insights files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Re-calculate all JSON files in 03_ai directory
  python scripts/recalculate_group_sizes.py 03_ai

  # Re-calculate specific file
  python scripts/recalculate_group_sizes.py 03_ai/HRA_data_report_insights.json

  # Specify custom CSV directory
  python scripts/recalculate_group_sizes.py 03_ai --csv-dir 01_in
        """
    )

    parser.add_argument(
        'input_path',
        type=Path,
        help='Path to JSON file or directory containing JSON files'
    )

    parser.add_argument(
        '--csv-dir',
        type=Path,
        default=Path('01_in'),
        help='Base directory containing CSV files (default: 01_in)'
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.input_path.exists():
        print(f"❌ Error: Path not found: {args.input_path}", file=sys.stderr)
        sys.exit(1)

    if not args.csv_dir.exists():
        print(f"❌ Error: CSV directory not found: {args.csv_dir}", file=sys.stderr)
        sys.exit(1)

    # Find JSON files to process
    if args.input_path.is_file():
        if args.input_path.suffix != '.json':
            print(f"❌ Error: Not a JSON file: {args.input_path}", file=sys.stderr)
            sys.exit(1)
        json_files = [args.input_path]
    else:
        json_files = sorted(args.input_path.rglob('*.json'))

    if not json_files:
        print(f"❌ No JSON files found in {args.input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"🔄 Re-calculating Group Sizes")
    print(f"📂 Input: {args.input_path}")
    print(f"📁 CSV directory: {args.csv_dir}")
    print(f"📊 Found {len(json_files)} JSON file(s)")
    print()

    # Process each file
    success_count = 0
    failed_count = 0

    for json_file in json_files:
        print(f"Processing: {json_file.relative_to(args.input_path.parent if args.input_path.is_file() else args.input_path)}")

        # Determine correct CSV
        csv_path = determine_csv_path(json_file, args.csv_dir)

        if not csv_path.exists():
            print(f"  ❌ CSV file not found: {csv_path}")
            failed_count += 1
            continue

        print(f"  Using CSV: {csv_path.relative_to(args.csv_dir.parent)}")

        # Re-calculate
        if recalculate_json_file(json_file, csv_path):
            success_count += 1
        else:
            failed_count += 1

        print()

    # Summary
    print("=" * 60)
    print(f"✅ Re-calculation Complete!")
    print(f"   Successful: {success_count}")
    if failed_count:
        print(f"   Failed: {failed_count}")
    print("=" * 60)


if __name__ == '__main__':
    main()
