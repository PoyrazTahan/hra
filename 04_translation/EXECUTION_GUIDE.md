# Turkish Translation Execution Guide

## Super Simple 3-Step Process

This guide provides a streamlined workflow to translate health risk analysis insights from English to Turkish with insight scoring. The main output is a comprehensive `insights.json` file at the project root.

## Prerequisites

- Python 3.7+ installed
- Latest English insights file in `03_answers/` folder
- Access to an LLM for translation

## Step-by-Step Execution

### Step 1: Extract and Create JSON

Extract insights and create the main data structure:

```bash
cd /Users/dogapoyraztahan/heltia/hra

# Extract from source file
python 04_translation/scripts/extract_text.py 03_answers/answer_800_try3.md 04_translation/data/

# This creates:
# - insights.json (at project root - main data file)
# - 04_translation/data/translation_input.md (for LLM)
```

**What this does**:
- Parses XML insights completely (message, proof, categories, tags)
- Creates comprehensive `insights.json` at project root with all data
- Creates simple `translation_input.md` with `<insight_tr>` tags for translation

### Step 2: Translate with LLM and Scoring

Translate using the prepared input:

1. **Read guidelines**: `04_translation/prompts/turkish_translation_prompt.md`
2. **Use input file**: `04_translation/data/translation_input.md`
3. **Provide this prompt to your LLM**:

```
Please translate and score these health insights from English to Turkish following the guidelines. For each insight:

1. Translate content naturally into business-appropriate Turkish
2. Preserve ALL statistical data exactly (percentages, ratios, sample sizes)
3. Score each insight 1-10 based on actionability and business value
4. Output in <insight_tr> format with scoring

[Paste content from translation_input.md here]
```

4. **Save LLM output** to: `04_translation/data/turkish_output.md`

### Step 3: Update Main JSON

Merge Turkish translations back into the main data file:

```bash
python 04_translation/scripts/merge_translations.py 04_translation/data/turkish_output.md

# This updates: insights.json (at project root)
```

**What this does**:
- Updates `insights.json` with Turkish translations and scores
- Adds timestamp metadata
- Shows score distribution summary

## Output Structure

Your main data file `insights.json` contains:

```json
{
  "source_file": "03_answers/answer_800_try3.md",
  "total_insights": 15,
  "extraction_date": null,
  "translation_date": "2024-09-21T...",
  "insights": [
    {
      "id": "insight_01",
      "index": 1,
      "categories": ["mental_health", "lifestyle"],
      "health_tags": ["daily_smoker", "frequent_sadness"],
      "demographic_tags": ["female", "young_adult"],
      "english": {
        "message": "Original English message...",
        "proof": "Statistical evidence..."
      },
      "turkish": {
        "message": "Turkish translation...",
        "score": 8
      }
    }
  ]
}
```

## Working Files

The data folder contains temporary working files:

```
04_translation/data/
├── translation_input.md     # LLM input
└── turkish_output.md       # LLM output
```

## Integration with main.py

Simple command-line integration:

```python
import subprocess

# Step 1: Extract
subprocess.run([
    'python', '04_translation/scripts/extract_text.py',
    'source_file.md',
    '04_translation/data/'
])

# Step 3: Merge (after manual translation)
subprocess.run([
    'python', '04_translation/scripts/merge_translations.py',
    '04_translation/data/turkish_output.md'
])
```

## Quick Automation Script

Create `translate_latest.sh` for regular use:

```bash
#!/bin/bash
# Find latest answer file
LATEST_FILE=$(ls -t 03_answers/answer_*.md | head -1)
DATA_DIR="04_translation/data"

echo "Processing: $LATEST_FILE"

# Step 1: Extract
python 04_translation/scripts/extract_text.py "$LATEST_FILE" "$DATA_DIR/"

echo "Created:"
echo "  Main data: insights.json"
echo "  Translation input: $DATA_DIR/translation_input.md"
echo ""
echo "Next steps:"
echo "1. Translate using prompt: 04_translation/prompts/turkish_translation_prompt.md"
echo "2. Save to: $DATA_DIR/turkish_output.md"
echo "3. Run: python 04_translation/scripts/merge_translations.py $DATA_DIR/turkish_output.md"
```

## Success Criteria

Your translation is successful when:

1. **insights.json updated** with Turkish translations and scores
2. **Statistical data preserved** exactly in Turkish content
3. **Insights scored 1-10** reflecting business actionability
4. **Categories and tags unchanged** in JSON structure
5. **Score distribution shown** (average, range)

## What Makes This System Ultra-Simple

- **Single source of truth**: insights.json contains everything
- **Only 2 scripts**: extract → merge
- **Manual control**: You handle translation quality and scoring
- **JSON output**: Easy integration with any system
- **No complexity**: Trust your LLM, review the JSON

The insights.json file becomes your complete dataset with both English and Turkish content, ready for analysis, reporting, or integration into other systems.