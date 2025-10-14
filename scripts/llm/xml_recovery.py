#!/usr/bin/env python3
"""
XML Recovery Tool - Fixes common Claude XML generation errors

This is a MANUAL recovery tool, separate from the main pipeline.
Use it when Claude generates malformed XML that can be heuristically fixed.

Usage:
    python scripts/llm/xml_recovery.py problematic_xml_debug.txt
    python scripts/llm/xml_recovery.py problematic_xml_debug.txt --output fixed.xml
    python scripts/llm/xml_recovery.py problematic_xml_debug.txt --dry-run
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


class XMLRecovery:
    """Recovers common XML structural errors using heuristics."""

    def __init__(self):
        self.fixes_applied = []
        self.warnings = []

    def diagnose(self, xml_content: str) -> List[str]:
        """
        Diagnose XML issues without fixing them.

        Returns:
            List of issues found
        """
        issues = []

        # Check for mismatched closing tags
        message_opens = xml_content.count('<message>')
        message_closes = xml_content.count('</message>')
        if message_opens != message_closes:
            issues.append(f"Mismatched <message> tags: {message_opens} opens, {message_closes} closes")

        summary_opens = xml_content.count('<summary_tr')
        summary_closes = xml_content.count('</summary_tr>')
        if summary_opens != summary_closes:
            issues.append(f"Mismatched <summary_tr> tags: {summary_opens} opens, {summary_closes} closes")

        # Check for common wrong closing tag patterns
        if '</summary_tr>' in xml_content:
            # Look for </summary_tr> that appears before any <summary_tr>
            lines = xml_content.split('\n')
            in_message = False
            for i, line in enumerate(lines):
                if '<message>' in line:
                    in_message = True
                if '</summary_tr>' in line and in_message and '</message>' not in xml_content[:xml_content.index(line)]:
                    issues.append(f"Line {i+1}: Found </summary_tr> inside <message> block (missing </message>)")
                if '</message>' in line:
                    in_message = False

        return issues

    def fix_mismatched_message_tags(self, xml_content: str) -> str:
        """
        Fix the specific case where </summary_tr> appears instead of </message>.

        Pattern we're fixing:
            <message>
            ...content...
            </summary_tr>  <-- WRONG! Should be </message>

            <summary_tr score="X">
            ...content...
            </summary_tr>
        """
        lines = xml_content.split('\n')
        fixed_lines = []
        fixes_made = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if we're at a misplaced </summary_tr>
            if '</summary_tr>' in line:
                # Look back to see if we're in an unclosed <message> block
                # and look ahead to see if next block starts with <summary_tr>

                # Look back for unclosed <message>
                has_unclosed_message = False
                for j in range(i-1, max(0, i-50), -1):
                    if '<message>' in fixed_lines[j]:
                        has_unclosed_message = True
                        break
                    if '</message>' in fixed_lines[j]:
                        break

                # Look ahead for <summary_tr> opening
                has_summary_ahead = False
                for j in range(i+1, min(len(lines), i+5)):
                    if '<summary_tr' in lines[j]:
                        has_summary_ahead = True
                        break

                # If we have unclosed message and summary ahead, this is likely the error
                if has_unclosed_message and has_summary_ahead:
                    # Replace </summary_tr> with </message>
                    fixed_line = line.replace('</summary_tr>', '</message>')
                    fixed_lines.append(fixed_line)
                    fixes_made += 1
                    self.fixes_applied.append(f"Line {i+1}: Replaced '</summary_tr>' with '</message>'")
                    i += 1
                    continue

            fixed_lines.append(line)
            i += 1

        if fixes_made > 0:
            print(f"✅ Applied {fixes_made} fixes for mismatched message tags")

        return '\n'.join(fixed_lines)

    def fix_unclosed_tags(self, xml_content: str) -> str:
        """
        Fix unclosed tags by counting opens/closes for each insight.

        This is a more general fix that handles various tag mismatch scenarios.
        """
        # Split into insight blocks
        insight_pattern = r'<insight>.*?</insight>'
        insights = re.findall(insight_pattern, xml_content, re.DOTALL)

        if not insights:
            # If no complete insights found, try to fix the wrapper
            if '<insights>' in xml_content and '</insights>' not in xml_content:
                xml_content += '\n</insights>'
                self.fixes_applied.append("Added missing </insights> closing tag")

            return xml_content

        # Check each insight for internal consistency
        fixed_insights = []
        for idx, insight in enumerate(insights):
            fixed_insight = insight

            # Check for missing </message>
            if '<message>' in insight and '</message>' not in insight:
                # Find where to insert it (before <summary_tr> or <categories>)
                if '<summary_tr' in insight:
                    fixed_insight = re.sub(r'(\n\s*)(<summary_tr)', r'\n</message>\1\2', fixed_insight)
                    self.fixes_applied.append(f"Insight #{idx+1}: Added missing </message> before <summary_tr>")
                elif '<categories>' in insight:
                    fixed_insight = re.sub(r'(\n\s*)(<categories>)', r'\n</message>\1\2', fixed_insight)
                    self.fixes_applied.append(f"Insight #{idx+1}: Added missing </message> before <categories>")

            fixed_insights.append(fixed_insight)

        # Reconstruct XML
        if '<insights>' in xml_content:
            result = '<insights>\n' + '\n'.join(fixed_insights) + '\n</insights>'
        else:
            result = '\n'.join(fixed_insights)

        return result

    def validate_fixed_xml(self, xml_content: str) -> Tuple[bool, List[str]]:
        """
        Validate that the fixed XML has balanced tags.

        Returns:
            (is_valid, list_of_remaining_issues)
        """
        issues = []

        # Check basic tag balance
        tags_to_check = [
            'insights', 'insight', 'message', 'summary_tr',
            'categories', 'health_tags', 'demographic_tags', 'proof'
        ]

        for tag in tags_to_check:
            open_count = len(re.findall(f'<{tag}[^>]*>', xml_content))
            close_count = xml_content.count(f'</{tag}>')

            if open_count != close_count:
                issues.append(f"Tag <{tag}>: {open_count} opens, {close_count} closes")

        return len(issues) == 0, issues

    def recover(self, xml_content: str) -> str:
        """
        Apply all recovery heuristics.

        Returns:
            Fixed XML content
        """
        print("Starting XML recovery...")
        print("=" * 60)

        # Diagnose first
        issues = self.diagnose(xml_content)
        if issues:
            print("\n🔍 Issues detected:")
            for issue in issues:
                print(f"  • {issue}")
        else:
            print("\n✅ No obvious issues detected")
            return xml_content

        print("\n🔧 Applying fixes...\n")

        # Apply fixes in order
        fixed_xml = xml_content

        # Fix 1: Mismatched message/summary_tr tags (most common)
        fixed_xml = self.fix_mismatched_message_tags(fixed_xml)

        # Fix 2: Unclosed tags
        fixed_xml = self.fix_unclosed_tags(fixed_xml)

        # Validate result
        print("\n" + "=" * 60)
        print("Validating fixed XML...")
        is_valid, remaining_issues = self.validate_fixed_xml(fixed_xml)

        if is_valid:
            print("✅ XML appears valid after fixes")
        else:
            print("⚠️  Some issues remain:")
            for issue in remaining_issues:
                print(f"  • {issue}")

        print("\n📋 Summary of fixes applied:")
        if self.fixes_applied:
            for fix in self.fixes_applied:
                print(f"  • {fix}")
        else:
            print("  No fixes were applied")

        return fixed_xml


def main():
    parser = argparse.ArgumentParser(
        description='Recover malformed XML from Claude output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze and fix problematic XML
  python scripts/llm/xml_recovery.py problematic_xml_debug.txt

  # Save fixed XML to specific file
  python scripts/llm/xml_recovery.py problematic_xml_debug.txt --output fixed.xml

  # Dry run - just diagnose, don't fix
  python scripts/llm/xml_recovery.py problematic_xml_debug.txt --dry-run
        """
    )

    parser.add_argument(
        'input_file',
        help='Path to problematic XML file (usually problematic_xml_debug.txt)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file for fixed XML (default: fixed_xml_output.xml)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only diagnose issues, do not apply fixes'
    )

    args = parser.parse_args()

    # Read input
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()

    print(f"📂 Input file: {input_path}")
    print(f"   Size: {len(xml_content):,} characters")

    # Process
    recovery = XMLRecovery()

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - Diagnosing only\n")
        issues = recovery.diagnose(xml_content)

        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  • {issue}")
            print("\nRun without --dry-run to apply fixes")
        else:
            print("✅ No obvious issues detected")

        sys.exit(0)

    # Apply recovery
    fixed_xml = recovery.recover(xml_content)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path('fixed_xml_output.xml')

    # Save result
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(fixed_xml)

    print(f"\n💾 Fixed XML saved to: {output_path}")
    print(f"   Size: {len(fixed_xml):,} characters")

    # Test if it can be parsed now
    print("\n🧪 Testing if fixed XML can be parsed...")
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(fixed_xml)
        print("✅ SUCCESS! Fixed XML is now parseable")
        print("\nYou can now use the fixed XML with:")
        print(f"  python scripts/llm/xml_parser.py {output_path} --output insights.json")
    except ET.ParseError as e:
        print(f"❌ FAILED: XML still has errors: {e}")
        print("\nThe automatic fixes could not fully resolve the issues.")
        print("Manual intervention may be required.")
        sys.exit(1)


if __name__ == '__main__':
    main()
