#!/usr/bin/env python3
"""
Merge Turkish translations into insights.json.

Updates the main insights.json file with Turkish translations and scores.
"""

import re
import json
import sys
from pathlib import Path
import argparse
from datetime import datetime
from typing import Dict, Any


class TranslationMerger:
    def __init__(self, turkish_file: str):
        self.turkish_file = Path(turkish_file)
        self.project_root = Path(__file__).parent.parent.parent  # Go up from scripts/
        self.insights_file = self.project_root / 'insights.json'
        self.insights_data = None
        self.translations = {}

    def load_insights_data(self) -> None:
        """Load the main insights.json file."""
        if not self.insights_file.exists():
            raise FileNotFoundError(f"Insights file not found: {self.insights_file}")

        with open(self.insights_file, 'r', encoding='utf-8') as f:
            self.insights_data = json.load(f)

    def parse_turkish_translations(self) -> None:
        """Parse Turkish translations from MD file."""
        if not self.turkish_file.exists():
            raise FileNotFoundError(f"Turkish file not found: {self.turkish_file}")

        content = self.turkish_file.read_text(encoding='utf-8')

        # Extract <insight_tr> tags with id, score, and content
        insight_pattern = r'<insight_tr id="([^"]+)"(?:\s+score="([^"]+)")?(.*?)</insight_tr>'
        matches = re.findall(insight_pattern, content, re.DOTALL)

        for insight_id, score, turkish_content in matches:
            self.translations[insight_id] = {
                'message': turkish_content.strip(),
                'score': int(score) if score else None
            }

        print(f"Parsed {len(self.translations)} Turkish translations")

    def update_insights_data(self) -> None:
        """Update insights data with Turkish translations."""
        if not self.insights_data:
            raise ValueError("Insights data not loaded")

        updated_count = 0

        for insight in self.insights_data['insights']:
            insight_id = insight['id']

            if insight_id in self.translations:
                translation = self.translations[insight_id]
                insight['turkish']['message'] = translation['message']
                insight['turkish']['score'] = translation['score']
                updated_count += 1

        # Update metadata
        self.insights_data['translation_date'] = datetime.now().isoformat()

        print(f"Updated {updated_count} insights with Turkish translations")

        # Check for missing translations
        missing_ids = []
        for insight in self.insights_data['insights']:
            if insight['id'] not in self.translations:
                missing_ids.append(insight['id'])

        if missing_ids:
            print(f"Missing translations for: {missing_ids}")

    def save_insights_data(self) -> None:
        """Save the updated insights.json file."""
        with open(self.insights_file, 'w', encoding='utf-8') as f:
            json.dump(self.insights_data, f, indent=2, ensure_ascii=False)

        print(f"Updated insights data: {self.insights_file}")

        # Print summary
        total_insights = self.insights_data['total_insights']
        translated_count = len(self.translations)

        print(f"Total insights: {total_insights}")
        print(f"Translated insights: {translated_count}")

        # Show score distribution
        scores = [insight['turkish']['score'] for insight in self.insights_data['insights']
                 if insight['turkish']['score'] is not None]

        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"Average insight score: {avg_score:.1f}")
            print(f"Score range: {min(scores)}-{max(scores)}")

    def run(self) -> None:
        """Execute the merge process."""
        self.load_insights_data()
        self.parse_turkish_translations()
        self.update_insights_data()
        self.save_insights_data()


def main():
    parser = argparse.ArgumentParser(description='Merge Turkish translations into insights.json')
    parser.add_argument('turkish_file', help='Path to Turkish translations MD file')

    args = parser.parse_args()

    try:
        merger = TranslationMerger(args.turkish_file)
        merger.run()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()