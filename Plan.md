# LLM-Powered Health Insights Pipeline Plan

## Project Overview
This project transforms health risk analysis reports into actionable business insights using Claude CLI with XML-structured output. It takes unified analysis reports (generated from 6 statistical analysis scripts) and produces scored, translated insights for HR professionals in a single LLM call.

## Current State
- **Analysis Pipeline**: `main.py` generates unified reports in `02_out/` directory
  - Main report: `02_out/HRA_report.txt` (full dataset)
  - Company reports: `02_out/company/Company_X_report.txt` (30+ employee companies)
- **LLM Processing**: Currently manual, separate insight synthesis and translation steps
- **Output**: `insights.json` with English insights + Turkish translations + actionability scores

## Goal: Unified Claude-Optimized Processing Pipeline

Create a simple Claude CLI orchestrator that processes any analysis report and produces final insights in one step using XML structured output for maximum reliability.

### Input
- Any unified analysis report (main or company)
- Configurable input/output paths

### Output
- Final `insights.json` with English insights, Turkish translations, and actionability scores
- Ready for business consumption

## Implementation Design

### Directory Structure
```
prompts/
└── unified_processor.md       # XML-optimized system prompt (synthesis + translation)

05_llm_processing/
├── claude_processor.py        # Main orchestrator script
└── xml_parser.py             # XML to JSON parser
```

### Core Script: `claude_processor.py`

**Simple Command Interface:**
```bash
# Process main report
python 05_llm_processing/claude_processor.py

# Process specific report with custom output
python 05_llm_processing/claude_processor.py --input 02_out/company/Company_28_report.txt --output insights_company28.json

# Process with specific prompt
python 05_llm_processing/claude_processor.py --prompt prompts/unified_processor.md
```

**Default Behavior:**
- Input: `02_out/HRA_report.txt`
- Output: `insights.json`
- Prompt: `prompts/unified_processor.md`

### LLM Processing Flow

**Optimized Single Claude CLI Call:**
1. **Read** the analysis report
2. **Apply** XML-optimized unified system prompt that handles:
   - Insight synthesis (extract 5-15 actionable insights)
   - Turkish translation + scoring (1-10 actionability scores)
   - XML structured output (Claude's trained strength)
3. **Parse** XML output to final JSON structure

**XML Output Strategy (Claude-Optimized):**
- Leverage Claude's specific training on XML tags for maximum reliability
- Single prompt combines insight synthesis + translation for efficiency
- XML structure provides deterministic parsing with error detection
- Higher token cost justified by production-grade reliability

### Key Design Principles

#### 1. Extreme Simplicity
- **Single script execution** - no complex workflows
- **Direct Claude CLI calls** - let LLM handle complexity
- **No error handling** - if Claude fails, we debug together
- **Linear processing** - no branching logic or state management

#### 2. Flexible Input/Output
- **Any report path** - main dataset or individual companies
- **Any output path** - configurable JSON destination
- **Prompt selection** - different prompts for different needs

#### 3. Claude-Optimized Approach
- **XML structured output** - leverages Claude's specific training advantages
- **Single LLM call** - synthesis + translation in one step for efficiency
- **Deterministic parsing** - robust XML extraction with error detection
- **Production reliability** - proven approach for agentic systems

## Technical Implementation

### Core Function
```python
def process_report_with_claude(input_file, output_file, prompt_file):
    """
    Process analysis report through Claude CLI to generate insights.

    Args:
        input_file: Path to unified analysis report
        output_file: Path for output insights.json
        prompt_file: XML-optimized system prompt for Claude
    """
    # Read report content
    # Read XML-optimized system prompt
    # Call Claude CLI with combined prompt + report
    # Parse Claude's XML response to JSON
    # Save to output file
```

### Claude CLI Integration
```bash
# XML-optimized Claude CLI call
claude_cli \
  --prompt-file prompts/unified_processor.md \
  --input-file 02_out/HRA_report.txt \
  --output-format xml \
  --max-tokens 8000
```

### XML System Prompt Design

**XML-Optimized Prompt Structure:**
1. **Context**: Health analysis report → business insights with XML output
2. **Task 1**: Extract 5-15 actionable insights with categories and tags
3. **Task 2**: Translate each insight to Turkish with business language
4. **Task 3**: Score each insight 1-10 for actionability and business value
5. **Output Format**: XML structure optimized for Claude's training

**Expected XML Output Format:**
```xml
<insights>
<insight id="insight_01">
<english>
<message>The dramatic gender skew in health survey participation reveals...</message>
<proof>Female participation: 650 employees (78.9%) vs Male participation: 164 employees (19.9%)</proof>
</english>
<turkish>
<message>Sağlık anketine katılımda görülen dramatik cinsiyet dengesizliği...</message>
<score>9</score>
</turkish>
<categories>health_conditions,lifestyle</categories>
<health_tags></health_tags>
<demographic_tags>female,male</demographic_tags>
</insight>
</insights>
```

## Expected Output Structure

```json
{
  "source_report": "02_out/HRA_report.txt",
  "processing_date": "2025-09-23T...",
  "total_insights": 12,
  "insights": [
    {
      "id": "insight_01",
      "english": {
        "message": "Insight explanation and recommendations...",
        "proof": "Statistical evidence and numbers..."
      },
      "turkish": {
        "message": "Turkish translation with business focus...",
        "score": 8
      },
      "categories": ["mental_health", "lifestyle"],
      "health_tags": ["daily_smoker", "persistent_sadness"],
      "demographic_tags": ["young_adult", "male"]
    }
  ]
}
```

## Usage Examples

### Process Main Dataset
```bash
python 05_llm_processing/claude_processor.py
# Input: 02_out/HRA_report.txt
# Output: insights.json
```

### Process Specific Company
```bash
python 05_llm_processing/claude_processor.py \
  --input 02_out/company/Company_28_report.txt \
  --output insights_company28.json
```

### Use Different Prompt
```bash
python 05_llm_processing/claude_processor.py \
  --prompt prompts/insight_synthesis.md \
  --output insights_english_only.json
```

## Integration with Analysis Pipeline

### Standalone Usage
```bash
# Run analysis pipeline
python main.py

# Process results with LLM
python 05_llm_processing/claude_processor.py
```

### Optional Future Integration
```bash
# Combined execution (future enhancement)
python main.py --process-insights
```

## Development Approach

### Phase 1: Core Implementation
1. **Create `claude_processor.py`** with basic CLI argument handling
2. **Design XML-optimized unified system prompt** combining synthesis + translation
3. **Implement Claude CLI integration** with XML output specification
4. **Create `xml_parser.py`** for robust XML → JSON conversion
5. **Test with main report** to verify complete workflow

### Phase 2: Enhancement
1. **Test with company reports** to ensure robustness across different data sizes
2. **Refine XML prompt** based on output quality and parsing reliability
3. **Add error detection** in XML parsing for production stability
4. **Document usage patterns** for different report types

### Success Criteria
- **Single command execution** produces complete insights.json with XML reliability
- **Claude XML optimization** - leverages Claude's specific training strengths
- **Deterministic parsing** - robust XML extraction with error detection
- **Configurable paths** allow processing any report type
- **Production reliability** - proven XML approach for agentic systems
- **Zero business logic** - simple orchestration, Claude does the intellectual work

## Key Benefits

1. **Claude-Optimized**: Leverages Claude's specific XML training for maximum reliability
2. **Production-Ready**: Uses proven XML approach from successful agentic systems
3. **Single LLM Call**: Synthesis + translation in one step for efficiency
4. **Deterministic**: Robust XML parsing prevents format-related failures
5. **Flexible**: Works with main dataset or individual company reports
6. **Research-Backed**: Based on 2024 findings about Claude XML performance

## Next Steps

1. **Implement** `claude_processor.py` with XML-optimized Claude CLI integration
2. **Create** `xml_parser.py` for deterministic XML → JSON conversion
3. **Design** unified XML system prompt combining synthesis + translation workflows
4. **Test** with `02_out/HRA_report.txt` to produce complete `insights.json`
5. **Validate** XML parsing reliability and output quality
6. **Document** usage patterns for different report types and prompt variations

This design leverages Claude's XML training strengths to handle the complex task of insight synthesis and translation in a single, reliable call, while keeping the orchestration code simple and focused on data flow rather than business logic.

## Technical Foundation

Based on 2024 research findings:
- **Claude XML Training**: Claude was specifically trained with XML tags, making it optimal for structured output
- **Production Reliability**: Agentic systems prefer XML for 89% success rates vs lower JSON performance
- **Token Efficiency**: Higher token cost justified by elimination of parsing errors and multi-step workflows
- **Deterministic Parsing**: XML provides built-in structure validation and error detection capabilities

The pipeline transforms complex health analysis reports into actionable business insights through a single, Claude-optimized XML processing step.