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
        return wrapped_xml

    def _parse_insights(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse individual insight elements from XML."""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML structure: {e}")

        insights = []
        for i, insight_elem in enumerate(root.findall('insight')):
            insight_data = self._parse_single_insight(insight_elem, i + 1)
            if insight_data:
                insights.append(insight_data)

        return insights

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