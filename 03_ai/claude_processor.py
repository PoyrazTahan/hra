#!/usr/bin/env python3
"""
Unified Claude-powered health insights processor.

Processes health analysis reports through Claude CLI to generate insights
with English analysis and Turkish translations in a single call.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from xml_parser import XMLInsightParser


class ClaudeProcessor:
    def __init__(self, input_file: str, output_file: str, prompt_file: str):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.prompt_file = Path(prompt_file)
        self.project_root = Path(__file__).parent.parent

        # Validate inputs
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        if not self.prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_file}")

    def read_report(self) -> str:
        """Read the analysis report content."""
        return self.input_file.read_text(encoding='utf-8')

    def read_prompt(self) -> str:
        """Read the system prompt content."""
        return self.prompt_file.read_text(encoding='utf-8')

    def call_claude_cli(self, prompt: str, report_content: str) -> str:
        """
        Call Claude CLI with the combined prompt and report content.

        Uses subprocess to call the claude command with the unified prompt.
        """
        # Combine system prompt with report content
        full_prompt = f"{prompt}\n\n## Health Analysis Report to Process:\n\n{report_content}"

        try:
            # Call Claude CLI with correct options
            result = subprocess.run([
                'claude',
                '--print',
                '--model', 'sonnet',
                '--dangerously-skip-permissions'
            ],
            input=full_prompt,
            text=True,
            capture_output=True,
            check=True,
            timeout=300  # 5 minute timeout
            )

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise TimeoutError(
                f"Claude CLI timed out after 5 minutes. Report may be too large. "
                f"Try chunking the input or using a smaller report."
            )
        except subprocess.CalledProcessError as e:
            print(f"Claude CLI error: {e}")
            print(f"Error output: {e.stderr}")
            raise
        except FileNotFoundError:
            raise FileNotFoundError(
                "Claude CLI not found. Please install Claude CLI and ensure it's in your PATH."
            )

    def process_report(self) -> Dict[str, Any]:
        """
        Main processing function that orchestrates the entire workflow.

        Returns:
            Dict with processed insights data
        """
        print(f"Processing report: {self.input_file}")
        print(f"Using prompt: {self.prompt_file}")

        # Read inputs
        report_content = self.read_report()
        system_prompt = self.read_prompt()

        print("Calling Claude CLI...")

        # Get Claude's response
        claude_response = self.call_claude_cli(system_prompt, report_content)

        print("Parsing XML response...")

        # Parse XML to structured data
        parser = XMLInsightParser()
        insights_data = parser.parse_claude_response(claude_response)

        # Add metadata
        insights_data.update({
            'source_report': str(self.input_file),
            'prompt_used': str(self.prompt_file),
            'processing_date': datetime.now().isoformat(),
            'claude_model': 'claude-3-5-sonnet-20241022'
        })

        return insights_data

    def save_results(self, insights_data: Dict[str, Any]) -> None:
        """Save the processed insights to JSON file."""
        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(insights_data, f, indent=2, ensure_ascii=False)

        print(f"Saved insights: {self.output_file}")
        print(f"Total insights: {insights_data.get('total_insights', 0)}")

        # Show score distribution if available
        insights = insights_data.get('insights', [])
        scores = [
            insight.get('turkish', {}).get('score')
            for insight in insights
            if insight.get('turkish', {}).get('score') is not None
        ]

        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"Average Turkish score: {avg_score:.1f}")
            print(f"Score range: {min(scores)}-{max(scores)}")

    def run(self) -> None:
        """Execute the complete processing pipeline."""
        try:
            insights_data = self.process_report()
            self.save_results(insights_data)
            print("Processing completed successfully!")

        except Exception as e:
            print(f"Processing failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Process health analysis reports with Claude CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process main report with default settings
  python 03_ai/claude_processor.py

  # Process specific company report
  python 03_ai/claude_processor.py --input 02_out/company/Company_28_report.txt --output insights_company28.json

  # Use different prompt
  python 03_ai/claude_processor.py --prompt 03_ai/prompts/english_only.md --output insights_english.json
        """
    )

    parser.add_argument(
        '--input',
        default='02_out/HRA_report.txt',
        help='Path to input analysis report (default: 02_out/HRA_report.txt)'
    )

    parser.add_argument(
        '--output',
        default='insights.json',
        help='Path for output insights JSON (default: insights.json)'
    )

    parser.add_argument(
        '--prompt',
        default='03_ai/prompts/unified_insights.md',
        help='Path to system prompt file (default: 03_ai/prompts/unified_insights.md)'
    )

    args = parser.parse_args()

    try:
        processor = ClaudeProcessor(args.input, args.output, args.prompt)
        processor.run()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()