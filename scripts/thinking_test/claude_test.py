#!/usr/bin/env python3
"""
Claude Code Thinking Mode Test Script

Tests different thinking levels to verify they produce different amounts of thinking.
Analyzes thinking output to validate thinking modes are working correctly.
"""

import json
import subprocess
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class ThinkingStats:
    """Statistics about thinking output for a test run."""
    mode: str
    total_thinking_chars: int
    thinking_events: int
    total_time: float
    first_thinking_time: float
    thinking_duration: float
    avg_thinking_length: float
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens_estimate: int = 0
    response_chars: int = 0
    thinking_to_response_ratio: float = 0.0

    def __str__(self) -> str:
        return (f"Mode: {self.mode}\n"
                f"  Total thinking characters: {self.total_thinking_chars:,}\n"
                f"  Thinking events: {self.thinking_events}\n"
                f"  Avg thinking per event: {self.avg_thinking_length:.1f} chars\n"
                f"  Response characters: {self.response_chars:,}\n"
                f"  Thinking/Response ratio: {self.thinking_to_response_ratio:.2f}x\n"
                f"  Estimated thinking tokens: {self.thinking_tokens_estimate:,}\n"
                f"  Total time: {self.total_time:.2f}s\n"
                f"  Time to first thinking: {self.first_thinking_time:.2f}s\n"
                f"  Thinking duration: {self.thinking_duration:.2f}s\n"
                f"  Thinking rate: {self.total_thinking_chars/max(self.thinking_duration, 0.1):.0f} chars/sec")


class ClaudeThinkingTester:
    def __init__(self):
        self.claude_model = 'sonnet'
        self.timeout = 900  # 15 minutes - much more time for complex thinking
        self.claude_cmd = self._find_claude_command()

        # Test modes to compare - start with fewer for faster testing
        self.test_modes = [
            "baseline",      # No thinking keywords
            "think",         # Basic thinking (~4K tokens)
            "think harder",  # High thinking
            "ultrathink"     # Maximum thinking (~32K tokens)
        ]

    def _find_claude_command(self) -> str:
        """Find Claude CLI command in system."""
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

        return claude_cmd

    def create_complex_test_prompt(self, thinking_mode: str) -> str:
        """
        Create a complex prompt that requires significant thinking.
        This tests multi-step reasoning, planning, and analysis.
        """
        thinking_prefix = f"{thinking_mode}: " if thinking_mode != "baseline" else ""

        return f"""{thinking_prefix}You are tasked with designing a comprehensive disaster response system for a major metropolitan city. This system needs to handle multiple types of emergencies simultaneously while optimizing resource allocation.

## Challenge Requirements:

1. **Multi-Emergency Scenarios**: The system must handle:
   - Natural disasters (earthquakes, floods, hurricanes)
   - Man-made emergencies (fires, chemical spills, infrastructure failures)
   - Pandemic responses
   - Cyber security incidents affecting city infrastructure

2. **Resource Optimization**: You have limited resources:
   - 500 first responders (police, fire, medical)
   - 50 emergency vehicles
   - 10 emergency shelters (capacity 1000 each)
   - $50M emergency budget
   - 3 hospitals with 2000 total bed capacity

3. **Stakeholder Coordination**: Multiple agencies must work together:
   - City government
   - Federal agencies (FEMA, FBI, CDC)
   - Private companies (utilities, telecoms)
   - Non-profit organizations
   - International aid organizations

## Your Task:

Design a complete system architecture that addresses:

A) **Priority Matrix**: How do you decide resource allocation when multiple emergencies occur simultaneously?

B) **Communication Protocol**: How do all stakeholders stay coordinated without overwhelming communication channels?

C) **Scalability**: How does the system adapt when emergencies exceed available resources?

D) **Technology Integration**: What technologies enable real-time decision making?

E) **Recovery Planning**: How do you transition from emergency response to recovery and reconstruction?

F) **Budget Allocation**: Propose specific budget allocations across all system components.

G) **Training Program**: Design a comprehensive training program for all personnel.

H) **Performance Metrics**: How do you measure and improve system effectiveness?

## Constraints:

- Must work with existing city infrastructure
- Comply with federal regulations
- Operate 24/7 with minimal downtime
- Handle up to 5 simultaneous major incidents
- Response time goals: <5min for life-threatening, <15min for property damage
- Must be implementable within 18 months

Provide a detailed, comprehensive plan with specific implementation steps, timelines, and contingency measures. Consider edge cases and potential system failures.
"""

    def run_claude_test(self, thinking_mode: str) -> Tuple[str, ThinkingStats]:
        """
        Run Claude with specific thinking mode and collect detailed metrics.
        """
        prompt = self.create_complex_test_prompt(thinking_mode)
        log_file = Path(f"claude_test_{thinking_mode.replace(' ', '_')}_{int(time.time())}.log")

        print(f"\n{'='*60}")
        print(f"Testing mode: {thinking_mode.upper()}")
        print(f"Prompt length: {len(prompt):,} characters")
        print(f"Log file: {log_file}")
        print(f"{'='*60}")

        try:
            start_time = time.time()
            first_thinking_time = None
            thinking_start_time = None
            thinking_end_time = None

            total_thinking_chars = 0
            thinking_events = 0
            final_response = ""
            input_tokens = 0
            output_tokens = 0

            with open(log_file, 'w') as log:
                process = subprocess.Popen([
                    self.claude_cmd,
                    '--print',
                    '--verbose',
                    '--model', self.claude_model,
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

                # Send prompt
                process.stdin.write(prompt)
                process.stdin.close()

                # Stream and analyze output
                for line in iter(process.stdout.readline, ''):
                    if line.strip():
                        log.write(line)  # Save everything to log

                        try:
                            json_data = json.loads(line.strip())

                            # Track usage information
                            if json_data.get('type') == 'usage':
                                usage = json_data.get('usage', {})
                                input_tokens = usage.get('input_tokens', 0)
                                output_tokens = usage.get('output_tokens', 0)
                                print(f"\n[Usage] Input: {input_tokens:,} tokens, Output: {output_tokens:,} tokens")

                            # Track thinking events
                            elif json_data.get('type') == 'stream_event':
                                event = json_data.get('event', {})

                                if event.get('type') == 'content_block_delta':
                                    delta = event.get('delta', {})

                                    # Thinking delta
                                    if delta.get('type') == 'thinking_delta':
                                        thinking = delta.get('thinking', '')
                                        if thinking:
                                            thinking_events += 1
                                            total_thinking_chars += len(thinking)

                                            # Track timing
                                            if first_thinking_time is None:
                                                first_thinking_time = time.time() - start_time
                                                thinking_start_time = time.time()
                                            thinking_end_time = time.time()

                                            # Show progress with less verbose output for long thinking
                                            if thinking_events % 10 == 0:
                                                print(f"[Thinking Event {thinking_events}] {total_thinking_chars:,} chars so far...")
                                            elif thinking_events <= 5:
                                                print(f"[Thinking {thinking_events}] {thinking[:60]}..." if len(thinking) > 60 else f"[Thinking {thinking_events}] {thinking}")

                                    # Text delta
                                    elif delta.get('type') == 'text_delta':
                                        content = delta.get('text', '')
                                        final_response += content
                                        print(content, end='', flush=True)

                                elif event.get('type') == 'content_block_start':
                                    content_block = event.get('content_block', {})
                                    if content_block.get('type') == 'text':
                                        content = content_block.get('text', '')
                                        if content:
                                            final_response += content
                                            print(content, end='', flush=True)

                        except json.JSONDecodeError:
                            # Handle non-JSON output
                            print(line.rstrip())
                            final_response += line

                # Wait for completion
                process.wait(timeout=self.timeout)
                total_time = time.time() - start_time

                # Calculate stats
                if first_thinking_time is None:
                    first_thinking_time = 0
                    thinking_duration = 0
                else:
                    thinking_duration = thinking_end_time - thinking_start_time

                avg_thinking_length = total_thinking_chars / max(thinking_events, 1)

                # Estimate thinking tokens (roughly 4 chars per token for thinking)
                thinking_tokens_estimate = total_thinking_chars // 4

                # Calculate thinking to response ratio
                response_chars = len(final_response)
                thinking_to_response_ratio = total_thinking_chars / max(response_chars, 1)

                stats = ThinkingStats(
                    mode=thinking_mode,
                    total_thinking_chars=total_thinking_chars,
                    thinking_events=thinking_events,
                    total_time=total_time,
                    first_thinking_time=first_thinking_time,
                    thinking_duration=thinking_duration,
                    avg_thinking_length=avg_thinking_length,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    thinking_tokens_estimate=thinking_tokens_estimate,
                    response_chars=response_chars,
                    thinking_to_response_ratio=thinking_to_response_ratio
                )

                print(f"\n\n{'-'*40}")
                print(f"RESULTS FOR {thinking_mode.upper()}:")
                print(stats)
                print(f"Log saved: {log_file}")

                if process.returncode != 0:
                    stderr_output = process.stderr.read()
                    print(f"Warning - Claude CLI returned {process.returncode}: {stderr_output}")

                return final_response, stats

        except subprocess.TimeoutExpired:
            print(f"\nTimeout after {self.timeout} seconds for mode: {thinking_mode}")
            return "", ThinkingStats(thinking_mode, 0, 0, self.timeout, 0, 0, 0, 0, 0, 0, 0, 0)
        except Exception as e:
            print(f"Error testing mode {thinking_mode}: {e}")
            return "", ThinkingStats(thinking_mode, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    def run_comprehensive_test(self) -> Dict[str, ThinkingStats]:
        """Run tests for all thinking modes and compare results."""
        print("CLAUDE CODE THINKING MODE COMPREHENSIVE TEST")
        print(f"Testing {len(self.test_modes)} different modes")
        print(f"Model: {self.claude_model}")
        print(f"Timeout: {self.timeout}s per test")

        results = {}

        for mode in self.test_modes:
            try:
                response, stats = self.run_claude_test(mode)
                results[mode] = stats

                # Longer delay between tests to avoid rate limits and let system cool down
                print(f"\nWaiting 10 seconds before next test...")
                time.sleep(10)

            except KeyboardInterrupt:
                print(f"\nTest interrupted by user at mode: {mode}")
                break
            except Exception as e:
                print(f"Failed to test mode {mode}: {e}")
                continue

        return results

    def analyze_results(self, results: Dict[str, ThinkingStats]) -> None:
        """Analyze and display comparison of all test results."""
        print(f"\n{'='*80}")
        print("THINKING MODE ANALYSIS RESULTS")
        print(f"{'='*80}")

        if not results:
            print("No results to analyze!")
            return

        # Sort by total thinking characters
        sorted_results = sorted(results.items(), key=lambda x: x[1].total_thinking_chars)

        print("\n1. THINKING CHARACTER COUNT COMPARISON:")
        print(f"{'Mode':<15} {'Think Chars':<12} {'Events':<8} {'Est.Tokens':<10} {'Duration':<10} {'Ratio':<8} {'Total Time':<10}")
        print("-" * 85)

        for mode, stats in sorted_results:
            print(f"{mode:<15} {stats.total_thinking_chars:<12,} {stats.thinking_events:<8} "
                  f"{stats.thinking_tokens_estimate:<10,} {stats.thinking_duration:<10.2f}s "
                  f"{stats.thinking_to_response_ratio:<8.1f}x {stats.total_time:<10.2f}s")

        # Validation checks
        print(f"\n2. THINKING MODE VALIDATION:")

        baseline_chars = results.get('baseline', ThinkingStats('baseline', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)).total_thinking_chars

        expected_order = ['baseline', 'think', 'think harder', 'ultrathink']
        validation_passed = True

        for i in range(len(expected_order) - 1):
            current_mode = expected_order[i]
            next_mode = expected_order[i + 1]

            current_chars = results.get(current_mode, ThinkingStats(current_mode, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)).total_thinking_chars
            next_chars = results.get(next_mode, ThinkingStats(next_mode, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)).total_thinking_chars

            if current_chars <= next_chars:
                print(f"✅ {current_mode} ({current_chars:,}) <= {next_mode} ({next_chars:,})")
            else:
                print(f"❌ {current_mode} ({current_chars:,}) > {next_mode} ({next_chars:,}) - UNEXPECTED!")
                validation_passed = False

        print(f"\n3. OVERALL VALIDATION:")
        if validation_passed:
            print("✅ Thinking modes are working correctly - each level produces more thinking than the previous")
        else:
            print("❌ Thinking modes may not be working as expected - check individual results")

        # Performance comparison
        print(f"\n4. PERFORMANCE COMPARISON:")
        if 'ultrathink' in results and 'baseline' in results:
            ultra_stats = results['ultrathink']
            baseline_stats = results['baseline']

            thinking_multiplier = ultra_stats.total_thinking_chars / max(baseline_stats.total_thinking_chars, 1)
            time_multiplier = ultra_stats.total_time / max(baseline_stats.total_time, 1)

            print(f"Ultrathink vs Baseline:")
            print(f"  Thinking increase: {thinking_multiplier:.1f}x")
            print(f"  Time increase: {time_multiplier:.1f}x")
            print(f"  Thinking efficiency: {ultra_stats.total_thinking_chars/ultra_stats.total_time:.0f} chars/second")

        # Save detailed results
        results_file = Path(f"thinking_test_results_{int(time.time())}.json")
        with open(results_file, 'w') as f:
            json.dump({
                mode: {
                    'mode': stats.mode,
                    'total_thinking_chars': stats.total_thinking_chars,
                    'thinking_events': stats.thinking_events,
                    'total_time': stats.total_time,
                    'first_thinking_time': stats.first_thinking_time,
                    'thinking_duration': stats.thinking_duration,
                    'avg_thinking_length': stats.avg_thinking_length,
                    'input_tokens': stats.input_tokens,
                    'output_tokens': stats.output_tokens,
                    'thinking_tokens_estimate': stats.thinking_tokens_estimate,
                    'response_chars': stats.response_chars,
                    'thinking_to_response_ratio': stats.thinking_to_response_ratio
                }
                for mode, stats in results.items()
            }, f, indent=2)

        print(f"\nDetailed results saved to: {results_file}")


def main():
    """Main test execution."""
    try:
        tester = ClaudeThinkingTester()
        results = tester.run_comprehensive_test()
        tester.analyze_results(results)

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()