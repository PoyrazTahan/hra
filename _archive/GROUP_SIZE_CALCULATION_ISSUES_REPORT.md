# Group Size Calculation Issues Report

**Date:** 2025-10-01
**Project:** HRA (Health Risk Assessment)
**Component:** Group Size Calculator & AI Orchestrator

---

## Executive Summary

The group size calculation system has **two critical issues** causing incorrect population counts:

1. **Wrong CSV Used for Company Reports** - Company-specific reports use the main population CSV instead of company-specific CSVs
2. **AND vs OR Logic Mismatch** - Multiple tags from the same column create impossible conditions, resulting in zero population

**Impact:** 6 out of 16 insights (37.5%) in the main report show zero population when they should show hundreds of people.

---

## Issue #1: Wrong CSV for Company Reports

### Problem Description

All reports (main and company-specific) are using the same CSV file: `01_in/HRA_data.csv`

**Evidence:**

| Report | Expected CSV | Actual CSV Used | Expected Population | Actual Population |
|--------|-------------|-----------------|---------------------|-------------------|
| HRA_data_report.txt | 01_in/HRA_data.csv | 01_in/HRA_data.csv | 1,457 | ✅ 1,457 |
| Company_28_report.txt | 01_in/company/Company_28.csv | 01_in/HRA_data.csv | 798 | ❌ 1,457 |
| Company_40_report.txt | 01_in/company/Company_40.csv | 01_in/HRA_data.csv | 30 | ❌ 1,457 |

### Root Cause

**File:** `ai.py`
**Lines:** 48-52, 134

```python
# ai.py line 48-52
if csv_path:
    self.csv_path = csv_path
else:
    # Default to main CSV in 01_in
    self.csv_path = Path('01_in/HRA_data.csv')  # ❌ Always uses main CSV
```

```python
# ai.py line 134
processor = ClaudeProcessor(
    input_file=str(input_path),
    output_file=str(output_path),
    prompt_file=str(self.prompt_file),
    csv_path=str(self.csv_path) if self.csv_path else None  # ❌ Same CSV for all
)
```

The orchestrator sets `self.csv_path` once during initialization and reuses it for ALL files (main + companies).

### Impact

- Company insights show incorrect group sizes and percentages
- Target groups are calculated against wrong population baseline
- Business decisions may be based on incorrect data

### Solution

The `process_single_file()` method needs to determine the correct CSV based on the input file:

```python
def determine_csv_path(self, input_path: Path) -> Path:
    """Determine the correct CSV file based on input report path."""
    if 'company' in input_path.parts:
        # Extract company identifier from filename
        # Example: Company_28_report.txt -> Company_28.csv
        company_id = input_path.stem.replace('_report', '')
        csv_path = Path('01_in/company') / f"{company_id}.csv"
        if csv_path.exists():
            return csv_path

    # Default to main CSV
    return Path('01_in/HRA_data.csv')
```

---

## Issue #2: AND vs OR Logic Mismatch

### Problem Description

The `GroupSizeCalculator` uses **AND logic** to combine all tags, but Claude AI generates insights with **multiple values from the SAME column**, creating impossible conditions.

**Example:** Insight #4 has tags: `['no_exercise', 'very_low_steps', 'low_steps']`

This translates to:
```sql
WHERE A.activity_level = 'no_exercise'
  AND A.daily_steps = 'very_low_steps'
  AND A.daily_steps = 'low_steps'  -- ❌ IMPOSSIBLE! A column can't have two values
```

**Result:** 0 people (but should be ~857 people)

### Evidence: Zero-Population Insights

| Insight | Tags | Individual Sums | Combined Result | Issue |
|---------|------|-----------------|-----------------|-------|
| insight_04 | no_exercise, very_low_steps, low_steps | 385 + 472 = 857 | ❌ 0 | Same column: A.daily_steps |
| insight_05 | severe_anhedonia, always_lonely, persistent_sadness, frequent_sadness, often_lonely | 1,293 total | ❌ 0 | Mixed columns with same-column conflicts |
| insight_06 | very_poor_nutrition, poor_nutrition, excellent_nutrition, good_nutrition | 1,373 total | ❌ 0 | Same column: A.fruit_veg_intake |
| insight_10 | sometimes_irritated, often_irritated, frequently_irritated, sometimes_out_of_control, often_out_of_control | ~1,200+ total | ❌ 0 | Same column conflicts |
| insight_13 | insufficient_sleep, excessive_sleep, borderline_sleep, optimal_sleep | 1,397 total | ❌ 0 | Same column: A.sleep_quality |
| insight_16 | using_supplements, not_using_supplements | ~1,400 total | ❌ 0 | Same column: A.supplement_usage |

### Root Cause Analysis

**File:** `scripts/llm/group_size_calculator.py`
**Lines:** 144-148

```python
# Current implementation (AND logic only)
for column_name, tag_value in filters:
    filtered_df = filtered_df[filtered_df[column_name] == tag_value]  # ❌ AND between ALL
```

**The Conceptual Problem:**

Claude AI understands that insights can apply to **multiple groups** (OR logic):
- "People who have insufficient sleep OR excessive sleep both face similar risks"
- "Daily smokers OR occasional smokers should consider cessation programs"

But the calculator expects **intersection** (AND logic):
- "Find people who match ALL these specific conditions simultaneously"

### Detailed Example: Insight #4

```
Insight: "Sedentary lifestyle is dangerous"
Tags: ['no_exercise', 'very_low_steps', 'low_steps']

Column Mapping:
- no_exercise       → A.activity_level = 'no_exercise'
- very_low_steps   → A.daily_steps = 'very_low_steps'
- low_steps        → A.daily_steps = 'low_steps'

Current Query (AND):
  Find people where:
    A.activity_level = 'no_exercise'
    AND A.daily_steps = 'very_low_steps'
    AND A.daily_steps = 'low_steps'       ← IMPOSSIBLE!

  Result: 0 people

Correct Query (OR for same column):
  Find people where:
    A.activity_level = 'no_exercise'
    AND (A.daily_steps = 'very_low_steps' OR A.daily_steps = 'low_steps')

  Expected Result: 857 people (or close)
```

---

## Proposed Solutions

### Solution A: Fix the Calculator (Smart OR Logic)

Modify `GroupSizeCalculator` to detect when multiple tags map to the same column and use OR logic:

```python
def calculate_group_size(self, health_tags, demographic_tags):
    all_tags = health_tags + demographic_tags

    # Group filters by column
    column_filters = {}
    for tag in all_tags:
        column, value = self.tag_to_column[tag]
        if column not in column_filters:
            column_filters[column] = []
        column_filters[column].append(value)

    # Apply filters with OR within columns, AND between columns
    filtered_df = self.df.copy()
    for column, values in column_filters.items():
        filtered_df = filtered_df[filtered_df[column].isin(values)]  # OR within column

    return len(filtered_df)
```

**Pros:**
- Maintains backward compatibility
- Fixes all zero-population issues automatically
- More intuitive behavior

**Cons:**
- Changes the fundamental logic (could affect existing insights)

### Solution B: Fix the Prompt (Prevent Multiple Tags from Same Column)

Update the Claude prompt to never generate multiple tags from the same column:

```markdown
IMPORTANT: Each insight should target a specific, measurable group.
- Use ONE value per health dimension
- DO NOT combine multiple values from the same category
- Example: Use 'very_low_steps' OR 'low_steps', not both
```

**Pros:**
- No code changes needed
- Forces more precise insights

**Cons:**
- Limits flexibility of insights
- May miss combined-group insights that are valuable

### Solution C: Hybrid Approach (Recommended)

1. **Fix the calculator** with smart OR logic (Solution A)
2. **Add validation** to warn when same-column tags are used
3. **Update prompt** to prefer single values but allow multiple when meaningful

---

## Recommendations

### Immediate Actions (Critical)

1. ✅ **Fix Issue #1**: Update `ai.py` to use company-specific CSVs
   - Priority: **HIGH**
   - Effort: 1-2 hours
   - Impact: Fixes incorrect population baselines

2. ✅ **Fix Issue #2**: Implement smart OR logic in calculator
   - Priority: **HIGH**
   - Effort: 2-3 hours
   - Impact: Fixes 37.5% of insights showing zero population

### Follow-up Actions

3. **Regenerate All Insights**: Re-run `ai.py` with fixes applied
   - Delete existing JSON outputs
   - Process all reports with correct CSVs and logic

4. **Add Validation**: Log warnings when unusual patterns detected
   ```python
   if len(column_filters[column]) > 3:
       print(f"⚠️  Warning: {len(column_filters[column])} values from {column}")
   ```

5. **Update Tests**: Add unit tests for group size calculator
   - Test single-column OR logic
   - Test multi-column AND logic
   - Test edge cases (empty tags, unknown tags)

---

## Testing Plan

After implementing fixes, verify:

1. **CSV Path Fix:**
   ```bash
   # Check that company reports use correct CSV
   python -c "
   import json
   with open('03_ai/company/Company_28_report_insights.json') as f:
       data = json.load(f)
       assert data['insights'][0]['target_group']['total_population'] == 798
   "
   ```

2. **OR Logic Fix:**
   ```bash
   # Verify insight_04 now has population
   python -c "
   import json
   with open('03_ai/HRA_data_report_insights.json') as f:
       data = json.load(f)
       insight_04 = [i for i in data['insights'] if i['id'] == 'insight_04'][0]
       assert insight_04['target_group']['size'] > 0
       print(f'insight_04 population: {insight_04[\"target_group\"][\"size\"]}')
   "
   ```

---

## Appendix: Data Analysis

### Current State

**Main Report (HRA_data_report_insights.json):**
- Total insights: 16
- Insights with zero population: 6 (37.5%)
- Insights with valid population: 10 (62.5%)

**Zero Population Insights:**
| ID | Health Tags Count | Root Cause |
|----|------------------|------------|
| insight_04 | 3 | Same-column tags (A.daily_steps) |
| insight_05 | 5 | Multiple same-column conflicts |
| insight_06 | 4 | Same-column tags (A.fruit_veg_intake) |
| insight_10 | 5 | Same-column tags (A.stress_level_*) |
| insight_13 | 4 | Same-column tags (A.sleep_quality) |
| insight_16 | 2 | Mutually exclusive tags |

### Expected Impact After Fixes

**Insight #4 Example:**
- Current: 0 people (0.0%)
- Expected: ~700-850 people (~50-60%)
- Tags will match: People with no_exercise OR low activity levels

**Insight #6 Example:**
- Current: 0 people (0.0%)
- Expected: ~1,300+ people (~90%)
- Tags will match: People across nutrition spectrum

---

## Conclusion

Both issues are **critical** and **fixable** with modest development effort. The fixes will:

1. ✅ Correct company-specific population calculations
2. ✅ Eliminate impossible zero-population conditions
3. ✅ Restore 37.5% of insights to useful state
4. ✅ Make the system more intuitive and maintainable

**Estimated Total Effort:** 4-6 hours (including testing and regeneration)

**Recommended Timeline:**
- Day 1: Implement fixes + unit tests
- Day 2: Regenerate all insights + validate results
- Day 3: Update documentation + deploy

---

**Report Generated:** 2025-10-01
**Author:** Claude Code Analysis
**Contact:** See git commit history for maintainer
