#!/usr/bin/env python3
"""
Convert AI-generated JSON insights to CSV format.

Finds all JSON files in a directory and converts them to a single unified CSV,
flattening the nested insight structure into tabular format.
"""

import argparse
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any


def flatten_insight(insight: Dict[str, Any], source_file_path: str) -> Dict[str, Any]:
    """Flatten a nested insight object into a flat dictionary for CSV."""
    # Clean text fields - replace newlines and extra whitespace
    def clean_text(text: str) -> str:
        if not text:
            return ''
        # Replace newlines and tabs with spaces, then normalize whitespace
        return ' '.join(text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').split())

    flat = {
        'source_file': source_file_path,
        'insight_id': insight.get('id', ''),
        'index': insight.get('index', ''),

        # English content (cleaned)
        'english_message': clean_text(insight.get('english', {}).get('message', '')),
        'english_proof': clean_text(insight.get('english', {}).get('proof', '')),

        # Turkish content (cleaned)
        'turkish_message': clean_text(insight.get('turkish', {}).get('message', '')),
        'turkish_score': insight.get('turkish', {}).get('score', ''),

        # Categories and tags (convert arrays to semicolon-separated strings to avoid CSV issues)
        'categories': '; '.join(insight.get('categories', [])),
        'health_tags': '; '.join(insight.get('health_tags', [])),
        'demographic_tags': '; '.join(insight.get('demographic_tags', [])),

        # Target group details
        'target_group_size': insight.get('target_group', {}).get('size', ''),
        'target_group_percentage': insight.get('target_group', {}).get('percentage', ''),
        'target_group_filters': '; '.join(insight.get('target_group', {}).get('filters_applied', [])),
        'target_group_total_population': insight.get('target_group', {}).get('total_population', ''),
    }

    return flat


def find_json_files(directory: Path) -> List[Path]:
    """Recursively find all JSON files in a directory."""
    return sorted(directory.rglob('*.json'))


def main():
    parser = argparse.ArgumentParser(
        description='Convert AI-generated JSON insights to a unified CSV file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all JSON files in 03_ai directory to single CSV
  python scripts/convert_output_json_to_csv.py 03_ai

  # Specify custom output file
  python scripts/convert_output_json_to_csv.py 03_ai --output insights.csv
        """
    )

    parser.add_argument(
        'input_path',
        type=Path,
        help='Input directory containing JSON files to convert'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=Path('insights.csv'),
        help='Output CSV file path (default: insights.csv in current directory)'
    )

    args = parser.parse_args()

    # Check if input exists
    if not args.input_path.exists():
        print(f"❌ Error: Path not found: {args.input_path}", file=sys.stderr)
        sys.exit(1)

    # Find JSON files to process
    if args.input_path.is_file():
        if args.input_path.suffix != '.json':
            print(f"❌ Error: File is not a JSON file: {args.input_path}", file=sys.stderr)
            sys.exit(1)
        json_files = [args.input_path]
    else:
        json_files = find_json_files(args.input_path)

    if not json_files:
        print(f"❌ No JSON files found in {args.input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"📂 Found {len(json_files)} JSON file(s) to convert")
    print(f"📁 Input: {args.input_path}")
    print(f"📄 Output: {args.output}")
    print()

    # Collect all insights from all JSON files
    all_insights = []
    processed_files = 0
    failed_files = 0
    total_insights = 0

    for json_file in json_files:
        try:
            # Read JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            insights = data.get('insights', [])

            if not insights:
                print(f"⚠️  No insights found in {json_file.name}")
                continue

            # Use relative path from input directory as source identifier
            if args.input_path.is_dir():
                source_file = str(json_file.relative_to(args.input_path))
            else:
                source_file = json_file.name

            # Flatten and add all insights from this file
            for insight in insights:
                flattened = flatten_insight(insight, source_file)
                all_insights.append(flattened)

            print(f"✅ Processed: {source_file} ({len(insights)} insights)")
            processed_files += 1
            total_insights += len(insights)

        except Exception as e:
            print(f"❌ Failed to process {json_file.name}: {e}")
            failed_files += 1

    # Write unified CSV
    if all_insights:
        fieldnames = all_insights[0].keys()

        try:
            with open(args.output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                writer.writerows(all_insights)

            print(f"\n{'='*60}")
            print(f"✅ Conversion complete!")
            print(f"📊 Files processed: {processed_files}")
            if failed_files:
                print(f"❌ Files failed: {failed_files}")
            print(f"📝 Total insights: {total_insights}")
            print(f"📄 Output file: {args.output}")
            print(f"💾 File size: {args.output.stat().st_size / 1024:.1f} KB")
            print(f"{'='*60}")

        except Exception as e:
            print(f"❌ Failed to write CSV file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"❌ No insights found to convert", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
