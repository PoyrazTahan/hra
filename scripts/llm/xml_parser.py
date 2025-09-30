#!/usr/bin/env python3
"""
XML parser for Claude insights responses.

Parses XML-structured insights from Claude and converts to JSON format
compatible with the existing insights.json structure.
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional


class XMLInsightParser:
    def __init__(self):
        self.insights = []

    def parse_claude_response(self, claude_output: str) -> Dict[str, Any]:
        """
        Parse Claude's XML response and convert to structured JSON.

        Args:
            claude_output: Raw text output from Claude containing XML insights

        Returns:
            Dict with structured insights data
        """
        # Clean the output to extract just the XML content
        xml_content = self._extract_xml_content(claude_output)

        # Parse individual insights
        insights = self._parse_insights(xml_content)

        return {
            'total_insights': len(insights),
            'insights': insights
        }

    def _extract_xml_content(self, text: str) -> str:
        """
        Extract XML content from Claude's response, handling potential
        markdown formatting or extra text around the XML.
        """
        # Remove markdown code blocks if present
        text = re.sub(r'```xml\n?', '', text)
        text = re.sub(r'```\n?', '', text)

        # Find all <insight>...</insight> blocks
        insight_pattern = r'<insight>.*?</insight>'
        insight_matches = re.findall(insight_pattern, text, re.DOTALL)

        if not insight_matches:
            # Save Claude's full response for debugging
            with open('claude_debug_response.txt', 'w', encoding='utf-8') as f:
                f.write(text)
            raise ValueError(
                f"No valid <insight> tags found in Claude's response. "
                f"Response length: {len(text)} chars. "
                f"Full response saved to 'claude_debug_response.txt' for debugging."
            )

        # Wrap insights in a root element for valid XML
        wrapped_xml = '<insights>\n' + '\n'.join(insight_matches) + '\n</insights>'

        # IMPORTANT: Escape XML special characters before parsing
        wrapped_xml = self._fix_xml_escaping(wrapped_xml)

        return wrapped_xml

    def _parse_insights(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse individual insight elements from XML."""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            # Enhanced debugging for XML parse errors
            print(f"\n❌ XML Parse Error: {e}")

            # Save the problematic XML for debugging
            with open('problematic_xml_debug.txt', 'w', encoding='utf-8') as f:
                f.write(xml_content)

            # Try to show context around the error
            error_str = str(e)
            if 'line' in error_str and 'column' in error_str:
                import re
                line_match = re.search(r'line (\d+)', error_str)
                col_match = re.search(r'column (\d+)', error_str)

                if line_match and col_match:
                    error_line = int(line_match.group(1))
                    error_col = int(col_match.group(1))

                    lines = xml_content.split('\n')
                    print(f"\nProblematic area around line {error_line}, column {error_col}:")

                    # Show context: 2 lines before and after the error
                    start_line = max(0, error_line - 3)
                    end_line = min(len(lines), error_line + 2)

                    for i in range(start_line, end_line):
                        line_num = i + 1
                        line_content = lines[i] if i < len(lines) else ""
                        marker = " --> " if line_num == error_line else "     "
                        print(f"{marker}Line {line_num:3d}: {line_content}")

                        # Show column indicator for error line
                        if line_num == error_line and error_col <= len(line_content):
                            print(f"          {' ' * (error_col - 1)}^-- Error here")

            raise ValueError(f"Invalid XML structure: {e}. Problematic XML saved to 'problematic_xml_debug.txt'")

        return self._extract_insights_from_root(root)

    def _extract_insights_from_root(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract insights from parsed XML root element."""
        insights = []
        for i, insight_elem in enumerate(root.findall('insight')):
            insight_data = self._parse_single_insight(insight_elem, i + 1)
            if insight_data:
                insights.append(insight_data)

        return insights

    def _fix_xml_escaping(self, xml_content: str) -> str:
        """Fix common XML character escaping issues."""
        import re

        # More precise tag pattern: matches proper XML tags only (starting with < and letter/slash)
        tag_pattern = r'</?[a-zA-Z_][a-zA-Z0-9_]*(?:\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*"[^"]*")*\s*/?>'

        # Find all tags and their positions
        tag_matches = list(re.finditer(tag_pattern, xml_content))

        if not tag_matches:
            # No tags found, just escape everything
            result = xml_content
            result = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', r'&amp;', result)
            result = result.replace('<', '&lt;')
            result = result.replace('>', '&gt;')
            return result

        # Build result by escaping text between tags
        result = []
        last_end = 0

        for match in tag_matches:
            # Get text before this tag
            text_before = xml_content[last_end:match.start()]

            # Escape special characters in text
            text_before = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', r'&amp;', text_before)
            text_before = text_before.replace('<', '&lt;')
            text_before = text_before.replace('>', '&gt;')

            result.append(text_before)
            result.append(match.group(0))  # Add the tag as-is

            last_end = match.end()

        # Don't forget text after the last tag
        text_after = xml_content[last_end:]
        text_after = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', r'&amp;', text_after)
        text_after = text_after.replace('<', '&lt;')
        text_after = text_after.replace('>', '&gt;')
        result.append(text_after)

        return ''.join(result)

    def _parse_single_insight(self, insight_elem: ET.Element, index: int) -> Dict[str, Any]:
        """Parse a single insight XML element."""
        insight = {
            'id': f"insight_{index:02d}",
            'index': index,
            'english': {},
            'turkish': {}
        }

        # Extract message (English)
        message_elem = insight_elem.find('message')
        if message_elem is not None:
            insight['english']['message'] = self._clean_text(message_elem.text or '')

        # Extract proof (English)
        proof_elem = insight_elem.find('proof')
        if proof_elem is not None:
            insight['english']['proof'] = self._clean_text(proof_elem.text or '')

        # Extract Turkish summary with score
        summary_tr_elem = insight_elem.find('summary_tr')
        if summary_tr_elem is not None:
            insight['turkish']['message'] = self._clean_text(summary_tr_elem.text or '')
            # Extract score from attribute
            score_attr = summary_tr_elem.get('score')
            if score_attr:
                try:
                    insight['turkish']['score'] = int(score_attr)
                except ValueError:
                    insight['turkish']['score'] = None
            else:
                insight['turkish']['score'] = None

        # Extract categories
        categories_elem = insight_elem.find('categories')
        insight['categories'] = self._parse_list_element(categories_elem)

        # Extract health tags
        health_tags_elem = insight_elem.find('health_tags')
        insight['health_tags'] = self._parse_list_element(health_tags_elem)

        # Extract demographic tags
        demographic_tags_elem = insight_elem.find('demographic_tags')
        insight['demographic_tags'] = self._parse_list_element(demographic_tags_elem)

        return insight

    def _parse_list_element(self, list_elem: Optional[ET.Element]) -> List[str]:
        """Parse list elements (categories, tags) that may contain bullet points."""
        if list_elem is None or not list_elem.text:
            return []

        items = []
        text = list_elem.text.strip()

        # Split by lines and extract items
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                items.append(line[2:].strip())
            elif line and not line.startswith('-'):
                # Single item without bullet
                items.append(line)

        return items

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""

        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text.strip())
        text = re.sub(r'[ \t]+', ' ', text)

        return text

    def validate_insights(self, insights: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Validate parsed insights and return any issues found.

        Returns:
            Dict with lists of validation errors and warnings
        """
        errors = []
        warnings = []

        for i, insight in enumerate(insights):
            insight_id = insight.get('id', f'insight_{i+1}')

            # Check required fields
            if not insight.get('english', {}).get('message'):
                errors.append(f"{insight_id}: Missing English message")

            if not insight.get('turkish', {}).get('message'):
                warnings.append(f"{insight_id}: Missing Turkish translation")

            # Check score
            turkish_score = insight.get('turkish', {}).get('score')
            if turkish_score is not None:
                if not isinstance(turkish_score, int) or not (1 <= turkish_score <= 10):
                    errors.append(f"{insight_id}: Invalid score {turkish_score} (must be 1-10)")

            # Check categories
            categories = insight.get('categories', [])
            if not categories:
                warnings.append(f"{insight_id}: No categories specified")

        return {
            'errors': errors,
            'warnings': warnings
        }


def main():
    """CLI interface for testing the parser."""
    import argparse

    parser = argparse.ArgumentParser(description='Test XML insight parser')
    parser.add_argument('xml_file', help='Path to XML file to parse')
    parser.add_argument('--output', help='Output JSON file path')

    args = parser.parse_args()

    try:
        with open(args.xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        parser = XMLInsightParser()
        result = parser.parse_claude_response(xml_content)

        # Validate results
        validation = parser.validate_insights(result['insights'])

        print(f"Parsed {result['total_insights']} insights")

        if validation['errors']:
            print(f"\nErrors:")
            for error in validation['errors']:
                print(f"  - {error}")

        if validation['warnings']:
            print(f"\nWarnings:")
            for warning in validation['warnings']:
                print(f"  - {warning}")

        if args.output:
            import json
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nSaved to: {args.output}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()