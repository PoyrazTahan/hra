# AI Processing Orchestration Plan

## Overview
Design a clean orchestration system to process multiple health analysis reports through Claude, maintaining clear separation between batch orchestration (`ai.py`) and individual file processing (`scripts/llm/claude_processor.py`).

## Current Structure Analysis

### Input Structure (02_out/)
```
02_out/
├── HRA_data_report.txt           # Main consolidated report
└── company/
    ├── Company_28_report.txt     # Individual company reports
    ├── Company_29_report.txt
    └── ...
```

### Target Output Structure (03_ai/)
```
03_ai/
├── HRA_data_report_insights.json       # Main insights
├── processing_summary.json             # Orchestration results
└── company/
    ├── Company_28_report_insights.json # Company-specific insights
    ├── Company_29_report_insights.json
    └── ...
```

## Architecture Design

### 1. Separation of Concerns

#### `ai.py` (Root Orchestrator) - Responsibilities:
- **File Discovery**: Scan input directory for all `.txt` files
- **Path Mapping**: Create corresponding output paths with proper directory structure
- **Batch Processing**: Orchestrate multiple claude_processor instances
- **Parallel Execution**: Optional parallel processing with worker pools
- **Progress Tracking**: Show overall progress (X of Y files completed)
- **Error Aggregation**: Collect and report failures across all files
- **Summary Reporting**: Generate processing statistics and results overview
- **Directory Management**: Ensure output directories exist

#### `scripts/llm/claude_processor.py` (File Processor) - Responsibilities:
- **Single File Processing**: Handle one input→output transformation
- **Claude CLI Interaction**: Manage subprocess communication
- **Thinking Capture**: Collect and process thinking content
- **XML Parsing**: Convert Claude response to structured data
- **Error Handling**: Handle individual file processing errors
- **Progress Display**: Show per-file processing progress

### 2. Argument Flow & API Design

#### Command Line Interface
```bash
# Basic usage - process all files in directory
python ai.py --input-dir 02_out --output-dir 03_ai

# Advanced options
python ai.py \
  --input-dir 02_out \
  --output-dir 03_ai \
  --prompt scripts/llm/prompts/unified_insights.md \
  --parallel \
  --max-workers 3 \
  --timeout 900 \
  --model sonnet \
  --thinking-mode ultrathink
```

#### API Design

```python
# ai.py - Orchestrator Class
class AIOrchestrator:
    def __init__(self,
                 input_dir: Path,
                 output_dir: Path,
                 prompt_file: Path,
                 parallel: bool = False,
                 max_workers: int = 3,
                 **processor_kwargs):
        """
        Initialize orchestrator with directories and processing options.

        Args:
            input_dir: Source directory (02_out/)
            output_dir: Target directory (03_ai/)
            prompt_file: Prompt file path
            parallel: Enable parallel processing
            max_workers: Number of concurrent workers
            **processor_kwargs: Pass-through args for ClaudeProcessor
        """

    def discover_files(self) -> List[Tuple[Path, Path, str]]:
        """
        Discover all .txt files and map to output paths.

        Returns:
            List of (input_path, output_path, file_type) tuples
        """

    def process_all(self) -> ProcessingSummary:
        """
        Orchestrate processing of all discovered files.

        Returns:
            Summary with success/failure statistics
        """

    def process_file(self, input_path: Path, output_path: Path) -> ProcessingResult:
        """Process single file using ClaudeProcessor."""

# claude_processor.py - Focused on single file
class ClaudeProcessor:
    def __init__(self,
                 input_file: str,
                 output_file: str,
                 prompt_file: str,
                 timeout: int = 900,
                 model: str = 'sonnet',
                 thinking_mode: str = 'think'):

    def process(self) -> ProcessingResult:
        """
        Main entry point for processing single file.

        Returns:
            Structured result with success/failure, metrics, thinking stats
        """
```

### 3. Data Flow Architecture

```
ai.py Flow:
1. Parse command line arguments
2. Discover all input files (*.txt in input_dir)
3. Map to output paths (preserve directory structure)
4. Create output directories
5. Process files (sequential or parallel)
6. Aggregate results
7. Generate summary report
8. Display final statistics

claude_processor.py Flow:
1. Validate input/output paths
2. Read report and prompt
3. Call Claude CLI with thinking
4. Capture response and thinking
5. Parse XML response
6. Save JSON with thinking content
7. Return processing result
```

### 4. Configuration Strategy

#### Shared Configuration
- Model selection (sonnet, opus)
- Timeout values
- Thinking modes
- Prompt file selection

#### Orchestrator-Specific Configuration
- Parallel processing settings
- Worker pool size
- Error retry policies
- Progress reporting verbosity

#### Processor-Specific Configuration
- Claude CLI parameters
- XML parsing options
- JSON output formatting

### 5. Error Handling Strategy

#### Orchestrator Level (ai.py):
- Continue processing other files if one fails
- Collect all errors for final reporting
- Retry failed files (optional)
- Generate partial results if some files succeed

#### Processor Level (claude_processor.py):
- Handle Claude CLI errors gracefully
- Validate input/output file accessibility
- Report detailed error information upward

### 6. Progress Tracking & Reporting

#### Orchestrator Progress:
```
AI Processing Progress: [██████████] 8/12 files completed (66.7%)
Currently processing: Company_31_report.txt
Estimated time remaining: 15 minutes
```

#### Per-File Progress:
```
Processing: Company_28_report.txt
[Thinking Progress] 45 events, 12,847 characters so far...
✅ Completed in 234.5s - 5,941 thinking chars, 1,485 estimated tokens
```

### 7. Output Structure

#### Processing Summary (03_ai/processing_summary.json):
```json
{
  "processing_date": "2025-01-25T10:30:00",
  "total_files": 12,
  "successful": 11,
  "failed": 1,
  "total_processing_time": "45:23",
  "thinking_stats": {
    "total_thinking_characters": 67834,
    "avg_thinking_per_file": 5667,
    "total_thinking_tokens": 16958
  },
  "files_processed": [...],
  "failures": [...]
}
```

## Implementation Strategy

### Phase 1: Create ai.py Orchestrator
- Implement file discovery and path mapping
- Basic sequential processing
- Error handling and reporting
- Progress tracking

### Phase 2: Enhance claude_processor.py
- Refactor to return structured results
- Improve error reporting
- Add configuration flexibility

### Phase 3: Add Parallel Processing
- Implement worker pool management
- Handle concurrent Claude CLI calls
- Manage resource usage

### Phase 4: Advanced Features
- Retry failed files
- Resume interrupted processing
- Configuration file support
- Advanced filtering options

## Benefits of This Architecture

1. **Clear Separation**: Orchestration vs. processing logic
2. **Scalability**: Easy to add parallel processing
3. **Maintainability**: Focused, single-responsibility modules
4. **Testability**: Each component can be tested independently
5. **Flexibility**: Easy to add new processing options
6. **Robustness**: Comprehensive error handling
7. **Visibility**: Clear progress tracking and reporting

## Example Usage Scenarios

```bash
# Process all files sequentially
python ai.py --input-dir 02_out --output-dir 03_ai

# Process with maximum thinking and parallel execution
python ai.py --input-dir 02_out --output-dir 03_ai --thinking-mode ultrathink --parallel --max-workers 2

# Process only main report (no company subdirectories)
python ai.py --input-dir 02_out --output-dir 03_ai --pattern "HRA_*.txt"

# Resume failed processing
python ai.py --input-dir 02_out --output-dir 03_ai --retry-failed
```

This architecture provides clean separation of concerns while maintaining flexibility for future enhancements and scaling.