#!/usr/bin/env python3
"""
Extract insights and create comprehensive JSON + translation input.

Creates:
1. insights.json at project root with complete parsed data
2. translation_input.md in data folder for LLM
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse


class InsightExtractor:
    def __init__(self, source_file: str, data_dir: str):
        self.source_file = Path(source_file)
        self.data_dir = Path(data_dir)
        self.project_root = Path(__file__).parent.parent.parent  # Go up from scripts/
        self.insights = []

    def parse_insights(self) -> List[Dict[str, Any]]:
        """Parse XML insights and extract structured data."""
        if not self.source_file.exists():
            raise FileNotFoundError(f"Source file not found: {self.source_file}")

        content = self.source_file.read_text(encoding='utf-8')

        # Extract individual insights using regex
        insight_pattern = r'<insight>(.*?)</insight>'
        insight_matches = re.findall(insight_pattern, content, re.DOTALL)

        for i, insight_content in enumerate(insight_matches):
            insight_data = self._parse_single_insight(insight_content, i)
            if insight_data:
                self.insights.append(insight_data)

        return self.insights

    def _parse_single_insight(self, content: str, index: int) -> Dict[str, Any]:
        """Parse a single insight XML block."""
        insight = {
            'id': f"insight_{index + 1:02d}",
            'index': index + 1,
            'english': {},
            'turkish': {
                'message': None,
                'score': None
            }
        }

        # Extract each section
        sections = ['message', 'categories', 'health_tags', 'demographic_tags', 'proof']

        for section in sections:
            pattern = f'<{section}>(.*?)</{section}>'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                section_content = match.group(1).strip()

                # For list sections (categories, tags), extract items
                if section in ['categories', 'health_tags', 'demographic_tags']:
                    items = []
                    for line in section_content.split('\n'):
                        line = line.strip()
                        if line.startswith('- '):
                            items.append(line[2:])
                    insight[section] = items
                else:
                    # For message and proof, store in english section
                    insight['english'][section] = section_content
            else:
                # Handle missing sections
                if section in ['categories', 'health_tags', 'demographic_tags']:
                    insight[section] = []
                else:
                    insight['english'][section] = ""

        return insight

    def create_translation_input(self) -> str:
        """Create simple MD file for translation with <insight_tr> tags."""
        md_lines = []

        for insight in self.insights:
            message = insight['english'].get('message', '').strip()
            proof = insight['english'].get('proof', '').strip()

            # Combine message and proof with clear separation
            combined_content = []
            if message:
                combined_content.append(message)
            if proof:
                combined_content.append(f"\n**Supporting Evidence:**\n{proof}")

            content = '\n'.join(combined_content)

            if content.strip():
                md_lines.append(f"<insight_tr id=\"{insight['id']}\">")
                md_lines.append(content)
                md_lines.append("</insight_tr>")
                md_lines.append("")  # Empty line between insights

        return '\n'.join(md_lines)

    def save_outputs(self) -> None:
        """Save comprehensive insights.json and translation input MD."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create comprehensive insights JSON
        insights_data = {
            'source_file': str(self.source_file),
            'total_insights': len(self.insights),
            'extraction_date': None,  # Can be set by calling script
            'translation_date': None,  # Will be set when translation is merged
            'insights': self.insights
        }

        # Save comprehensive JSON at project root
        json_path = self.project_root / 'insights.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(insights_data, f, indent=2, ensure_ascii=False)

        # Save translation input MD in data folder
        translation_input = self.create_translation_input()
        md_path = self.data_dir / 'translation_input.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(translation_input)

        print(f"Created files:")
        print(f"  Main data: {json_path}")
        print(f"  Translation input: {md_path}")
        print(f"  Total insights: {len(self.insights)}")


def main():
    parser = argparse.ArgumentParser(description='Extract insights for Turkish translation')
    parser.add_argument('source_file', help='Path to source insights MD file')
    parser.add_argument('data_dir', help='Data directory for translation files')

    args = parser.parse_args()

    try:
        extractor = InsightExtractor(args.source_file, args.data_dir)
        extractor.parse_insights()
        extractor.save_outputs()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()