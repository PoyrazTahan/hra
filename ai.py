#!/usr/bin/env python3
"""
AI Processing Orchestrator

Discovers all .txt files in input directory and processes them through Claude
to generate insights, maintaining proper directory structure in output.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time
from datetime import datetime

# Import the claude processor
sys.path.append(str(Path(__file__).parent / 'scripts' / 'llm'))
from claude_processor import ClaudeProcessor


@dataclass
class ProcessingResult:
    """Result of processing a single file."""
    input_file: Path
    output_file: Path
    success: bool
    processing_time: float
    error_message: str = ""
    thinking_chars: int = 0


class AIOrchestrator:
    """Orchestrates AI processing across multiple health analysis reports."""

    def __init__(self, input_dir: Path, output_dir: Path, main_only: bool = False, parallel: bool = False, max_workers: int = 3, csv_path: Path = None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.main_only = main_only
        self.parallel = parallel
        self.max_workers = max_workers

        # Fixed prompt file path - internal to processor
        self.prompt_file = Path('scripts/llm/prompts/unified_insights.md')

        # CSV path for group size calculation
        if csv_path:
            self.csv_path = csv_path
        else:
            # Default to main CSV in 01_in
            self.csv_path = Path('01_in/HRA_data.csv')

        # Validate directories
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")

        if not self.prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_file}")

        if not self.csv_path.exists():
            print(f"⚠️  Warning: CSV file not found at {self.csv_path}")
            print("   Group size calculation will be skipped.")
            self.csv_path = None

    def discover_files(self) -> List[Tuple[Path, Path]]:
        """
        Discover all .txt files and map to output paths.

        Returns:
            List of (input_path, output_path) tuples
        """
        files = []

        # Always process main report if it exists
        main_report = self.input_dir / 'HRA_data_report.txt'
        if main_report.exists():
            output_path = self.output_dir / 'HRA_data_report_insights.json'
            files.append((main_report, output_path))
            print(f"Found main report: {main_report}")

        # Process company reports unless main-only flag is set
        if not self.main_only:
            company_dir = self.input_dir / 'company'
            if company_dir.exists():
                company_files = list(company_dir.glob('*.txt'))
                print(f"Found {len(company_files)} company reports in {company_dir}")

                for company_file in company_files:
                    # Convert Company_28_report.txt -> Company_28_report_insights.json
                    output_name = company_file.stem + '_insights.json'
                    output_path = self.output_dir / 'company' / output_name
                    files.append((company_file, output_path))

        return files

    def create_output_dirs(self, file_pairs: List[Tuple[Path, Path]]) -> None:
        """Ensure all output directories exist."""
        dirs_to_create = set()

        for _, output_path in file_pairs:
            dirs_to_create.add(output_path.parent)

        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Ensured directory exists: {dir_path}")

    def process_single_file(self, input_path: Path, output_path: Path) -> ProcessingResult:
        """Process a single file using ClaudeProcessor."""
        start_time = time.time()

        try:
            # Ensure output directory exists before processing
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create processor and run it
            processor = ClaudeProcessor(
                input_file=str(input_path),
                output_file=str(output_path),
                prompt_file=str(self.prompt_file),
                csv_path=str(self.csv_path) if self.csv_path else None
            )

            print(f"\n🔄 Starting: {input_path.name}")

            # Process the file
            processor.run()

            processing_time = time.time() - start_time

            # Try to get thinking stats from the output file if it was created
            thinking_chars = 0
            if output_path.exists():
                try:
                    import json
                    with open(output_path, 'r') as f:
                        data = json.load(f)
                        thinking_stats = data.get('thinking_stats', {})
                        thinking_chars = thinking_stats.get('thinking_characters', 0)
                except:
                    pass  # If we can't read thinking stats, that's ok

            print(f"✅ Completed: {input_path.name} in {processing_time:.1f}s")

            return ProcessingResult(
                input_file=input_path,
                output_file=output_path,
                success=True,
                processing_time=processing_time,
                thinking_chars=thinking_chars
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Failed to process {input_path.name}: {str(e)}"
            print(f"❌ {error_msg}")

            return ProcessingResult(
                input_file=input_path,
                output_file=output_path,
                success=False,
                processing_time=processing_time,
                error_message=error_msg
            )

    def process_all_sequential(self, file_pairs: List[Tuple[Path, Path]]) -> List[ProcessingResult]:
        """Process files one by one sequentially."""
        results = []

        for i, (input_path, output_path) in enumerate(file_pairs, 1):
            print(f"\n📊 Processing file {i}/{len(file_pairs)}")
            result = self.process_single_file(input_path, output_path)
            results.append(result)

        return results

    def process_all_parallel(self, file_pairs: List[Tuple[Path, Path]]) -> List[ProcessingResult]:
        """Process files in parallel using thread pool."""
        results = []

        print(f"🚀 Processing {len(file_pairs)} files in parallel (max {self.max_workers} workers)")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_single_file, input_path, output_path): (input_path, output_path)
                for input_path, output_path in file_pairs
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_file):
                completed += 1
                input_path, output_path = future_to_file[future]

                try:
                    result = future.result()
                    results.append(result)
                    print(f"📊 Progress: {completed}/{len(file_pairs)} files completed")
                except Exception as e:
                    error_result = ProcessingResult(
                        input_file=input_path,
                        output_file=output_path,
                        success=False,
                        processing_time=0,
                        error_message=f"Parallel execution error: {str(e)}"
                    )
                    results.append(error_result)

        return results

    def print_summary(self, results: List[ProcessingResult], total_time: float) -> None:
        """Print final processing summary."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        print(f"\n{'='*80}")
        print(f"🎯 AI PROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"📈 Total files: {len(results)}")
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"⏱️  Total time: {total_time:.1f} seconds")

        if successful:
            avg_time = sum(r.processing_time for r in successful) / len(successful)
            total_thinking = sum(r.thinking_chars for r in successful)
            print(f"📊 Average processing time: {avg_time:.1f}s per file")
            print(f"🧠 Total thinking characters: {total_thinking:,}")

        if failed:
            print(f"\n❌ FAILED FILES:")
            for result in failed:
                print(f"  • {result.input_file.name}: {result.error_message}")

        print(f"\n📁 Output directory: {self.output_dir}")

    def run(self) -> None:
        """Execute the complete orchestration process."""
        start_time = time.time()

        print(f"🚀 AI Processing Orchestrator Starting")
        print(f"📂 Input directory: {self.input_dir}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🎯 Mode: {'Main report only' if self.main_only else 'All reports (main + companies)'}")
        print(f"⚡ Execution: {'Parallel' if self.parallel else 'Sequential'}")
        if self.parallel:
            print(f"👥 Max workers: {self.max_workers}")

        try:
            # Discover files to process
            file_pairs = self.discover_files()

            if not file_pairs:
                print("❌ No .txt files found to process!")
                return

            print(f"\n📋 Found {len(file_pairs)} files to process")

            # Create output directories
            self.create_output_dirs(file_pairs)

            # Process files
            if self.parallel:
                results = self.process_all_parallel(file_pairs)
            else:
                results = self.process_all_sequential(file_pairs)

            # Show summary
            total_time = time.time() - start_time
            self.print_summary(results, total_time)

        except Exception as e:
            print(f"❌ Orchestration failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='AI Processing Orchestrator - Process health analysis reports through Claude',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all files (main + companies)
  python ai.py --input-dir 02_out --output-dir 03_ai

  # Process only main report
  python ai.py --input-dir 02_out --output-dir 03_ai --main-only

  # Process with parallel execution
  python ai.py --input-dir 02_out --output-dir 03_ai --parallel --max-workers 2
        """
    )

    parser.add_argument(
        '--input-dir',
        type=Path,
        default=Path('02_out'),
        help='Input directory containing .txt reports (default: 02_out)'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('03_ai'),
        help='Output directory for generated insights (default: 03_ai)'
    )

    parser.add_argument(
        '--main-only',
        action='store_true',
        help='Process only HRA_data_report.txt (skip company reports)'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Enable parallel processing of files'
    )

    parser.add_argument(
        '--max-workers',
        type=int,
        default=3,
        help='Maximum number of parallel workers (default: 3)'
    )

    parser.add_argument(
        '--csv',
        type=Path,
        help='Path to CSV data file for group size calculation (default: 01_in/HRA_data.csv)'
    )

    args = parser.parse_args()

    try:
        orchestrator = AIOrchestrator(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            main_only=args.main_only,
            parallel=args.parallel,
            max_workers=args.max_workers,
            csv_path=args.csv
        )
        orchestrator.run()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()