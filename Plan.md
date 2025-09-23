# Health Risk Assessment Multi-Company Pipeline Plan

## Project Overview
This project analyzes employee health risk assessment data using 6 analysis scripts that generate unified reports. Currently processes a single dataset, but needs to be extended to handle multiple company datasets.

## Current Architecture
- **Input**: `01_in/HRA_data.csv` (main dataset with all employees)
- **Company Data**: `01_in/company/Company_X.csv` (121 individual company subsets)
- **Scripts**: 6 analysis scripts in `_scripts/` directory
- **Output**: Single unified report combining all 6 analyses
- **Configuration**: Column definitions centralized in `_scripts/categories.py`

## Task: Multi-Company Pipeline

### Goal
Create a pipeline that generates:
1. **Main Report**: `02_out/HRA_report.txt` (analysis of full dataset)
2. **Company Reports**: `02_out/company/CompanyX_report.txt` (individual company analyses)

### Requirements
- Only process companies with **30+ employee records**
- Each report uses the same 6-analysis format as current pipeline
- Maintain existing unified report structure for consistency
- Use same fail-fast error handling (stop on any script failure)

## Implementation Plan

### Step 1: Company Filtering
```python
# Scan 01_in/company/*.csv files
# Count records in each (exclude header)
# Keep only companies with 30+ records
# Log which companies are eligible vs excluded
```

### Step 2: Directory Structure Setup
```python
# Create 02_out/ directory
# Create 02_out/company/ subdirectory
# Clear any existing files
```

### Step 3: Main Dataset Analysis
```python
# Run existing pipeline on 01_in/HRA_data.csv
# Output to 02_out/HRA_report.txt
# Use current main.py logic exactly
```

### Step 4: Company-Specific Analysis
```python
# For each eligible company CSV:
#   - Run same 6-script pipeline
#   - Output to 02_out/company/CompanyX_report.txt
#   - Use company name from filename
#   - Same unified report format
```

### Step 5: Summary Logging
```python
# Log total companies processed
# Log companies excluded (< 30 records)
# Log any failures
# Provide final summary
```

## Technical Approach

### Option A: Extend main.py (RECOMMENDED)
- Add `--mode` parameter: `full` or `company`
- Add `--company-filter` flag to process only 30+ record companies
- Reuse all existing logic, just change input/output paths
- Keep it simple and linear

### Option B: New orchestrator script
- Create `multi_main.py` that calls existing `main.py` multiple times
- Risk: Duplicate code and harder to maintain

## Best Practices for Implementation

### Keep It Simple
- **Linear flow**: Process main dataset first, then companies one by one
- **No complex error handling**: Use existing fail-fast approach
- **No nested try/catch blocks**: Let errors bubble up naturally
- **Straightforward file operations**: Simple read/write, no fancy I/O

### Code Organization
- **Reuse existing functions**: Don't reinvent main.py logic
- **Single responsibility**: Each function does one clear thing
- **Clear naming**: `process_main_dataset()`, `process_company_dataset()`
- **Minimal parameters**: Pass only what's needed

### File Handling
- **Absolute paths**: Always use full paths, avoid relative path issues
- **Simple file operations**: Basic read/write, no streaming or chunking
- **Clear naming convention**: `CompanyX_report.txt` where X is company number
- **Overwrite existing**: Don't append, always create fresh reports

### Error Management
- **Fail fast**: Stop immediately on any script failure
- **Clear error messages**: Show which company/script failed
- **Cleanup on failure**: Remove partial files
- **Log everything**: What's being processed, what succeeded/failed

## Expected Output Structure
```
02_out/
├── HRA_report.txt                 # Main dataset analysis
└── company/
    ├── Company_10_report.txt      # Only companies with 30+ records
    ├── Company_1_report.txt
    ├── Company_112_report.txt
    ├── Company_2_report.txt
    ├── Company_66_report.txt
    └── Company_99_report.txt
```

## Data Flow
1. **Input**: 121 company CSVs + 1 main CSV
2. **Filter**: Identify 6 companies with 30+ records
3. **Process Main**: `01_in/HRA_data.csv` → `02_out/HRA_report.txt`
4. **Process Companies**: Each eligible CSV → `02_out/company/CompanyX_report.txt`
5. **Summary**: Log processing results

## Key Considerations
- **Column Alignment**: All scripts use `_scripts/categories.py` for consistent column definitions
- **Same Analysis**: Each company report has identical structure to main report
- **Performance**: Process companies sequentially (simple, predictable)
- **Validation**: Verify each company CSV has required columns before processing
- **Naming**: Extract company name/number from filename for report naming

## Success Criteria
- Main dataset report generated successfully
- Only eligible companies (30+ records) get individual reports
- All reports use identical unified format
- Clear logging of what was processed/skipped
- Fail-fast behavior on any errors
- No complex code patterns or nested error handling

## Next Steps
1. Implement company filtering logic
2. Extend main.py with multi-dataset capability
3. Test with small subset of companies
4. Run full pipeline on all eligible companies
5. Verify output format consistency