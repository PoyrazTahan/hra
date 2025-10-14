#!/usr/bin/env python3
"""
Recovery Orchestrator for Failed AI Processing

Recovers insights from malformed XML output when Claude generates invalid XML.
This script combines XML recovery and JSON conversion into a single workflow.

Usage:
    # Basic usage - recovers XML and generates insights JSON
    python recovery.py --input problematic_xml_debug.txt --output 03_ai/recovered_insights.json

    # Specify custom CSV for group size calculation
    python recovery.py --input problematic_xml_debug.txt --output 03_ai/insights.json --csv 01_in/HRA_data.csv

    # Dry run - just diagnose without fixing
    python recovery.py --input problematic_xml_debug.txt --dry-run
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Import recovery and processing modules
sys.path.append(str(Path(__file__).parent / 'scripts' / 'llm'))
from xml_recovery import XMLRecovery
from xml_parser import XMLInsightParser
from group_size_calculator import GroupSizeCalculator


class RecoveryOrchestrator:
    """Orchestrates XML recovery and insight generation from malformed Claude output."""

    def __init__(self, input_file: Path, output_file: Path, csv_path: Path = None, dry_run: bool = False):
        self.input_file = input_file
        self.output_file = output_file
        self.dry_run = dry_run

        # Determine CSV path for group size calculation
        if csv_path:
            self.csv_path = csv_path
        else:
            # Default to main CSV in 01_in
            self.csv_path = Path('01_in/HRA_data.csv')

        if not self.csv_path.exists():
            print(f"⚠️  Warning: CSV file not found at {self.csv_path}")
            print("   Group size calculation will be skipped.")
            self.csv_path = None

        # Validate input
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")

    def run(self) -> None:
        """Execute the complete recovery pipeline."""
        print("=" * 80)
        print("XML RECOVERY & INSIGHT GENERATION ORCHESTRATOR")
        print("=" * 80)
        print(f"📂 Input XML: {self.input_file}")
        print(f"📁 Output JSON: {self.output_file}")
        if self.csv_path:
            print(f"📊 CSV data: {self.csv_path}")
        print()

        try:
            # Step 1: Read problematic XML
            print("Step 1: Reading problematic XML...")
            with open(self.input_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            print(f"   Size: {len(xml_content):,} characters")
            print()

            # Step 2: Diagnose and optionally fix XML
            print("Step 2: Analyzing XML structure...")
            recovery = XMLRecovery()

            if self.dry_run:
                print("   🔍 DRY RUN MODE - Diagnosing only\n")
                issues = recovery.diagnose(xml_content)

                if issues:
                    print("   Issues found:")
                    for issue in issues:
                        print(f"     • {issue}")
                    print("\n   Run without --dry-run to apply fixes and generate insights")
                else:
                    print("   ✅ No obvious issues detected")

                return

            # Apply recovery
            fixed_xml = recovery.recover(xml_content)
            print()

            # Step 3: Parse fixed XML to structured insights
            print("Step 3: Parsing fixed XML to insights...")
            parser = XMLInsightParser()
            insights_data = parser.parse_claude_response(fixed_xml)
            print(f"   ✅ Parsed {insights_data['total_insights']} insights")
            print()

            # Step 4: Calculate group sizes
            if self.csv_path:
                print("Step 4: Calculating target group sizes...")
                try:
                    calculator = GroupSizeCalculator(str(self.csv_path))
                    insights_data['insights'] = calculator.calculate_sizes_for_insights(
                        insights_data['insights']
                    )
                    print(f"   ✅ Group sizes calculated for {len(insights_data['insights'])} insights")
                except Exception as e:
                    print(f"   ⚠️  Warning: Failed to calculate group sizes: {e}")
                    print("   Insights will be saved without group size information.")
                print()
            else:
                print("Step 4: Skipping group size calculation (CSV not available)")
                print()

            # Step 5: Add metadata
            print("Step 5: Adding metadata...")
            insights_data.update({
                'source_file': str(self.input_file),
                'recovery_date': datetime.now().isoformat(),
                'recovered': True,
                'recovery_notes': {
                    'original_file': str(self.input_file),
                    'fixes_applied': recovery.fixes_applied,
                    'recovery_tool': 'recovery.py'
                }
            })
            print()

            # Step 6: Save to JSON
            print("Step 6: Saving insights to JSON...")
            self.output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(insights_data, f, indent=2, ensure_ascii=False)

            print(f"   ✅ Saved to: {self.output_file}")
            print()

            # Summary
            print("=" * 80)
            print("🎉 RECOVERY COMPLETE")
            print("=" * 80)
            print(f"Total insights recovered: {insights_data['total_insights']}")

            if recovery.fixes_applied:
                print(f"\nFixes applied:")
                for fix in recovery.fixes_applied:
                    print(f"  • {fix}")

            # Show score distribution if available
            insights = insights_data.get('insights', [])
            scores = [
                insight.get('turkish', {}).get('score')
                for insight in insights
                if insight.get('turkish', {}).get('score') is not None
            ]

            if scores:
                avg_score = sum(scores) / len(scores)
                print(f"\nTurkish score statistics:")
                print(f"  Average: {avg_score:.1f}")
                print(f"  Range: {min(scores)}-{max(scores)}")

            print(f"\n📁 Output location: {self.output_file}")
            print("\nYou can now use this JSON file in your downstream processes.")

        except Exception as e:
            print(f"\n❌ Recovery failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Recover insights from malformed Claude XML output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Recover XML and generate insights JSON
  python recovery.py --input problematic_xml_debug.txt --output 03_ai/recovered_insights.json

  # Use custom CSV for group size calculation
  python recovery.py --input problematic_xml_debug.txt --output 03_ai/insights.json --csv 01_in/HRA_data.csv

  # Dry run - just diagnose without fixing
  python recovery.py --input problematic_xml_debug.txt --dry-run

  # Recover company-specific failed output
  python recovery.py --input problematic_xml_debug.txt --output 03_ai/company/Company_68_insights.json

Typical workflow after AI processing fails:
  1. AI pipeline creates 'problematic_xml_debug.txt' when XML parsing fails
  2. Run: python recovery.py --input problematic_xml_debug.txt --dry-run
  3. Review the diagnosis
  4. Run: python recovery.py --input problematic_xml_debug.txt --output 03_ai/recovered.json
  5. Use the recovered insights JSON as normal
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        type=Path,
        help='Path to problematic XML file (usually problematic_xml_debug.txt)'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Path for output insights JSON file (required unless --dry-run)'
    )

    parser.add_argument(
        '--csv',
        type=Path,
        help='Path to CSV data file for group size calculation (default: 01_in/HRA_data.csv)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only diagnose issues without applying fixes or generating output'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.output:
        parser.error("--output is required unless using --dry-run")

    try:
        orchestrator = RecoveryOrchestrator(
            input_file=args.input,
            output_file=args.output if args.output else Path('dummy.json'),  # dummy for dry-run
            csv_path=args.csv,
            dry_run=args.dry_run
        )
        orchestrator.run()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
