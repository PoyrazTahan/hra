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
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from xml_parser import XMLInsightParser


# Global Configuration
DEFAULT_PROMPT = 'ultrathink: Please follow the prompt in scripts/llm/prompts/unified_insights.md'
DEFAULT_TIMEOUT = 900  # 15 minutes in seconds (increased for thinking time)
CLAUDE_MODEL = 'sonnet'


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

    def call_claude_cli(self, prompt: str, report_content: str, log_file_path: str) -> tuple[str, str]:
        """
        Call Claude CLI with stream-json format to capture thinking process.

        Args:
            prompt: System prompt content
            report_content: Analysis report content
            log_file_path: Path to save complete stream-json log

        Returns:
            Tuple of (final_response, complete_thinking_content)
        """
        # Combine system prompt with report content
        full_prompt = f"{prompt}\n\n## Health Analysis Report to Process:\n\n{report_content}"

        print(f"Claude CLI Configuration:")
        print(f"  Model: {CLAUDE_MODEL}")
        print(f"  Timeout: {DEFAULT_TIMEOUT} seconds")
        print(f"  Input length: {len(full_prompt):,} characters")
        print(f"  Log file: {log_file_path}")
        print()
        print("Calling Claude CLI with stream-json (thinking process enabled)...")
        print("="*60)

        # Resolve claude command (handle aliases)
        import shutil
        claude_cmd = shutil.which('claude')
        if not claude_cmd:
            # Try common Claude installation paths
            possible_paths = [
                '/Users/dogapoyraztahan/.claude/local/claude',
                '/usr/local/bin/claude',
                '~/.claude/local/claude'
            ]
            for path in possible_paths:
                expanded_path = Path(path).expanduser()
                if expanded_path.exists():
                    claude_cmd = str(expanded_path)
                    break

        if not claude_cmd:
            raise FileNotFoundError("Claude CLI not found in PATH or common locations")

        try:
            # Start timing
            start_time = time.time()

            # Create log file and call Claude with stream-json
            with open(log_file_path, 'w') as log_file:
                process = subprocess.Popen([
                    claude_cmd,
                    '--print',
                    '--verbose',
                    '--model', CLAUDE_MODEL,
                    '--output-format', 'stream-json',
                    '--include-partial-messages',
                    '--dangerously-skip-permissions'
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
                )

                # Send input
                process.stdin.write(full_prompt)
                process.stdin.close()

                # Collect all stream json, thinking content, and final response
                final_response = ""
                complete_thinking = ""
                thinking_events = 0
                stream_lines = []

                # Stream output and save to log
                for line in iter(process.stdout.readline, ''):
                    if line.strip():
                        stream_lines.append(line)
                        log_file.write(line)  # Save to log file

                        try:
                            # Parse JSON line to extract content
                            json_data = json.loads(line.strip())

                            # Handle different event types
                            if json_data.get('type') == 'stream_event':
                                event = json_data.get('event', {})
                                if event.get('type') == 'content_block_delta':
                                    delta = event.get('delta', {})
                                    if delta.get('type') == 'text_delta':
                                        content = delta.get('text', '')
                                        print(content, end='', flush=True)  # Live stream to terminal
                                        final_response += content
                                    elif delta.get('type') == 'thinking_delta':
                                        thinking = delta.get('thinking', '')
                                        if thinking:
                                            complete_thinking += thinking
                                            thinking_events += 1

                                            # Show thinking progress every 10 events, not every chunk
                                            if thinking_events % 10 == 0:
                                                print(f"[Thinking Progress] {thinking_events} events, {len(complete_thinking):,} characters so far...", flush=True)
                                            elif thinking_events <= 3:
                                                print(f"[Thinking Started] Event {thinking_events}...", flush=True)
                                elif event.get('type') == 'content_block_start':
                                    content_block = event.get('content_block', {})
                                    if content_block.get('type') == 'text':
                                        content = content_block.get('text', '')
                                        if content:
                                            print(content, end='', flush=True)
                                            final_response += content

                        except json.JSONDecodeError:
                            # Handle non-JSON lines
                            print(line.rstrip())
                            final_response += line

                # Wait for process to complete and time it
                process.wait(timeout=DEFAULT_TIMEOUT)
                elapsed_time = time.time() - start_time

                print("\n" + "="*60)
                print(f"✅ Claude CLI completed in {elapsed_time:.2f} seconds")

                # Display thinking summary
                if complete_thinking:
                    print(f"💭 Thinking Summary: {thinking_events} events, {len(complete_thinking):,} characters")
                    print(f"📊 Thinking/Response ratio: {len(complete_thinking)/max(len(final_response), 1):.1f}:1")
                else:
                    print("💭 No thinking detected (baseline mode)")

                if process.returncode != 0:
                    stderr_output = process.stderr.read()
                    print(f"Claude CLI error: {stderr_output}")
                    raise subprocess.CalledProcessError(process.returncode, 'claude')

                return final_response.strip(), complete_thinking.strip()

        except subprocess.TimeoutExpired:
            elapsed_time = time.time() - start_time
            raise TimeoutError(
                f"Claude CLI timed out after {elapsed_time:.2f} seconds (limit: {DEFAULT_TIMEOUT}s). "
                f"Report may be too large."
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

        # Create log file path (same name as output but .log extension)
        log_file_path = self.output_file.parent / f"{self.output_file.stem}.log"

        # Call Claude CLI with stream-json logging
        claude_response, thinking_content = self.call_claude_cli(system_prompt, report_content, str(log_file_path))

        print("Parsing XML response...")

        # Parse XML from response
        parser = XMLInsightParser()
        insights_data = parser.parse_claude_response(claude_response)

        # Add metadata and thinking content
        insights_data.update({
            'source_report': str(self.input_file),
            'prompt_used': str(self.prompt_file),
            'processing_date': datetime.now().isoformat(),
            'claude_model': f'claude-{CLAUDE_MODEL}',
            'log_file': str(log_file_path),
            'thinking_content': thinking_content,
            'thinking_stats': {
                'thinking_characters': len(thinking_content),
                'thinking_enabled': len(thinking_content) > 0,
                'estimated_thinking_tokens': len(thinking_content) // 4
            }
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

        # Show thinking statistics
        thinking_stats = insights_data.get('thinking_stats', {})
        if thinking_stats.get('thinking_enabled'):
            print(f"💭 Thinking enabled: {thinking_stats.get('thinking_characters', 0):,} characters")
            print(f"🧠 Estimated thinking tokens: {thinking_stats.get('estimated_thinking_tokens', 0):,}")
        else:
            print("💭 No thinking detected (baseline mode)")

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
  python scripts/llm/claude_processor.py

  # Process specific company report
  python scripts/llm/claude_processor.py --input 02_out/company/Company_28_report.txt --output 03_ai/company/Company_28_report_insights.json

  # Use different prompt
  python scripts/llm/claude_processor.py --prompt scripts/llm/prompts/english_only.md --output insights_english.json
        """
    )

    parser.add_argument(
        '--input',
        default='02_out/HRA_report.txt',
        help='Path to input analysis report (default: 02_out/HRA_report.txt)'
    )

    parser.add_argument(
        '--output',
        default='03_ai/HRA_report_insights.json',
        help='Path for output insights JSON (default: 03_ai/HRA_report_insights.json)'
    )

    parser.add_argument(
        '--prompt',
        default='scripts/llm/prompts/unified_insights.md',
        help='Path to system prompt file (default: scripts/llm/prompts/unified_insights.md)'
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