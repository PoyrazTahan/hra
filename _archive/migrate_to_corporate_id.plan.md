# Migration Plan: SponsorId → CorporateId

**Date:** 2025-10-22
**Status:** Planning
**Decision:** Clean break from SponsorId, use CorporateId as primary key

---

## Executive Summary

Migrate from SponsorId-based company grouping to CorporateId/CorporateName from source CSV data. This eliminates the need to maintain the company mapping in `value_mappings.json` and provides more meaningful company identifiers.

### Key Decisions
- ✅ **Primary Key:** CorporateId (stable, unique)
- ✅ **File Naming:** `Corporate_{corporateId}_{sanitizedName}.csv`
- ✅ **#N/A Handling:** Group into "Unknown_Company"
- ✅ **Compatibility:** Clean break - remove SponsorId mapping logic

---

## Current State Analysis

### Data Sources
| File | Location | Contains |
|------|----------|----------|
| Old CSV | `00_init_data/HRA_Answers_tab_with_company.csv` | SponsorId only |
| New CSV | `00_init_data/HRA_data.csv` | SponsorId + CorporateId + CorporateName |
| Mapping | `00_init_data/mappings/value_mappings.json` | SponsorId → "Company_X" mapping |

### Current File Naming Pattern
```
01_in/company/Company_1.csv
01_in/company/Company_10.csv
01_in/company/Company_28.csv
...
```

### New File Naming Pattern
```
01_in/company/Corporate_68e6d330_Heltia.csv
01_in/company/Corporate_[id]_[name].csv
01_in/company/Unknown_Company.csv  (for #N/A records)
```

---

## Migration Strategy

### Phase 1: Data Preparation ✅
**Goal:** Ensure new CSV has required columns

- [x] Verify `HRA_data.csv` has CorporateId and CorporateName columns
- [x] Analyze data quality:
  - Check for NULL/empty CorporateId values → Found: #N/A values exist
  - Check for duplicate CorporateId → To verify
  - Check CorporateId-CorporateName consistency → To verify

### Phase 2: Code Changes 🔄
**Goal:** Update preprocessing and analysis scripts

#### 2.1 Update `csv_preprocessor.py`
**File:** `00_init_data/csv_preprocessor.py`

**Changes Required:**
1. **Update INPUT_FILE reference**
   - Change: `INPUT_FILE = "00_init_data/HRA_Answers_tab_with_company.csv"`
   - To: `INPUT_FILE = "00_init_data/HRA_data.csv"`

2. **Remove SponsorId mapping function**
   - Remove: `map_sponsor_to_company()` function (lines 25-30)
   - Remove: SponsorId mapping logic from `value_mappings.json` loading

3. **Add CorporateName sanitization**
   ```python
   def sanitize_company_name(name):
       """Sanitize company name for use in file paths."""
       if pd.isna(name) or name == '#N/A':
           return 'Unknown_Company'
       # Remove special characters, spaces → underscores
       sanitized = re.sub(r'[^\w\s-]', '', str(name))
       sanitized = re.sub(r'[\s-]+', '_', sanitized)
       return sanitized.strip('_')
   ```

4. **Update company grouping logic**
   - Current: Groups by `SponsorId`, maps to generic names
   - New: Group by `CorporateId`, use actual `CorporateName`

   ```python
   def save_company_specific_data(df):
       """Save company-specific CSV files using CorporateId."""
       # Check for required columns
       if 'CorporateId' not in df.columns or 'CorporateName' not in df.columns:
           print("Warning: CorporateId/CorporateName columns not found")
           return

       os.makedirs(COMPANY_OUTPUT_DIR, exist_ok=True)

       # Handle #N/A values - group together
       na_mask = df['CorporateId'].isna() | (df['CorporateId'] == '#N/A')
       if na_mask.any():
           unknown_df = df[na_mask].copy()
           unknown_file = os.path.join(COMPANY_OUTPUT_DIR, "Unknown_Company.csv")
           unknown_df.to_csv(unknown_file, index=False)
           print(f"Saved {len(unknown_df)} records for Unknown_Company to {unknown_file}")

       # Process known companies
       valid_df = df[~na_mask].copy()

       for corporate_id in valid_df['CorporateId'].unique():
           if pd.notna(corporate_id):
               company_df = valid_df[valid_df['CorporateId'] == corporate_id].copy()

               # Get company name (should be consistent per CorporateId)
               corporate_name = company_df['CorporateName'].iloc[0]
               sanitized_name = sanitize_company_name(corporate_name)

               # Create filename: Corporate_{id_prefix}_{sanitized_name}.csv
               id_prefix = str(corporate_id)[:8]  # First 8 chars of ID
               company_file_name = f"Corporate_{id_prefix}_{sanitized_name}.csv"
               company_file = os.path.join(COMPANY_OUTPUT_DIR, company_file_name)

               company_df.to_csv(company_file, index=False)
               print(f"Saved {len(company_df)} records for {corporate_name} (ID: {corporate_id}) to {company_file}")
   ```

5. **Update main() function**
   - Remove `mappings` parameter from `save_company_specific_data(df, mappings)` call
   - Change to: `save_company_specific_data(df)`

6. **Optional: Keep CorporateId in company files**
   - Don't drop CorporateId column (for reference)

#### 2.2 Update `analysis.py`
**File:** `analysis.py`

**Changes Required:**
1. **Update company file discovery pattern**
   - Current: `company_dir.glob("Company_*.csv")`
   - New: `company_dir.glob("Corporate_*.csv")` + `Unknown_Company.csv`

   ```python
   # In main() function, around line 248
   for company_file in sorted(company_dir.glob("Corporate_*.csv")):
       company_name = company_file.stem  # e.g., "Corporate_68e6d330_Heltia"
       company_output_file = company_output_dir / f"{company_name}_report.txt"
       # ... rest of processing

   # Also check for Unknown_Company.csv
   unknown_file = company_dir / "Unknown_Company.csv"
   if unknown_file.exists():
       output_file = company_output_dir / "Unknown_Company_report.txt"
       success = process_dataset(unknown_file, output_file, "Unknown_Company")
   ```

#### 2.3 Update `ai.py`
**File:** `ai.py`

**Changes Required:**
1. **Update company file discovery**
   - Current: Looks for company reports matching pattern
   - New: Update to match new naming convention

   ```python
   # In AIOrchestrator.discover_files() method, around line 86
   company_files = list(company_dir.glob('Corporate_*_report.txt'))
   # Also check for Unknown_Company_report.txt
   unknown_report = company_dir / 'Unknown_Company_report.txt'
   if unknown_report.exists():
       company_files.append(unknown_report)
   ```

2. **Update CSV path determination**
   - In `determine_csv_path()` method (line 108)
   - Update to look for `Corporate_*` pattern instead of `Company_*`

#### 2.4 Update `value_mappings.json`
**File:** `00_init_data/mappings/value_mappings.json`

**Changes Required:**
1. **Remove SponsorId mapping section**
   - Remove the entire `"SponsorId": {...}` key-value pair
   - Keep all other question mappings (A.perceived_health, etc.)

2. **Backup first**
   ```bash
   cp 00_init_data/mappings/value_mappings.json 00_init_data/mappings/value_mappings.json.backup
   ```

---

## Testing Strategy

### Pre-Migration Tests
1. **Data Validation**
   ```bash
   # Check CorporateId uniqueness and consistency
   python -c "
   import pandas as pd
   df = pd.read_csv('00_init_data/HRA_data.csv')

   # CorporateId stats
   print('Total records:', len(df))
   print('Unique CorporateIds:', df['CorporateId'].nunique())
   print('Records with #N/A CorporateId:', df['CorporateId'].isna().sum() + (df['CorporateId'] == '#N/A').sum())

   # Check consistency (each CorporateId should map to one CorporateName)
   id_name_map = df[['CorporateId', 'CorporateName']].drop_duplicates()
   duplicates = id_name_map['CorporateId'].value_counts()[lambda x: x > 1]
   if len(duplicates) > 0:
       print('⚠️  WARNING: Inconsistent CorporateId → CorporateName mappings:')
       print(duplicates)
   else:
       print('✅ CorporateId → CorporateName mapping is consistent')
   "
   ```

### Migration Tests
1. **Test preprocessing with new code**
   ```bash
   # Backup existing processed data
   mv 01_in 01_in_backup

   # Run new preprocessing
   python 00_init_data/csv_preprocessor.py

   # Verify output
   ls -la 01_in/company/
   ```

2. **Verify file structure**
   - Check that files follow `Corporate_{id}_{name}.csv` pattern
   - Verify Unknown_Company.csv exists if there are #N/A records
   - Spot-check a few files for data integrity

3. **Test analysis pipeline**
   ```bash
   # Test main dataset only first
   python analysis.py --main-only

   # Then test with companies
   python analysis.py
   ```

4. **Test AI pipeline**
   ```bash
   python ai.py --main-only
   python ai.py  # full run
   ```

### Post-Migration Validation
1. **Compare record counts**
   - Old system: Sum of Company_*.csv records
   - New system: Sum of Corporate_*.csv + Unknown_Company.csv records
   - Should be identical

2. **Verify analysis outputs**
   - Check that all expected company reports are generated
   - Verify no empty or corrupted reports

3. **Spot-check AI insights**
   - Verify company names appear correctly in insights JSON
   - Check that group sizes are calculated correctly

---

## Rollback Plan

If migration fails:

1. **Restore old preprocessing**
   ```bash
   git checkout 00_init_data/csv_preprocessor.py
   git checkout analysis.py
   git checkout ai.py
   ```

2. **Restore processed data**
   ```bash
   rm -rf 01_in
   mv 01_in_backup 01_in
   ```

3. **Restore value_mappings.json**
   ```bash
   cp 00_init_data/mappings/value_mappings.json.backup 00_init_data/mappings/value_mappings.json
   ```

---

## Migration Checklist

### Pre-Migration
- [ ] Backup current codebase: `git commit -am "Pre-migration checkpoint"`
- [ ] Backup value_mappings.json
- [ ] Backup 01_in directory: `mv 01_in 01_in_backup`
- [ ] Run data validation script (see Testing Strategy)
- [ ] Document any data quality issues found

### Code Changes
- [ ] Update `csv_preprocessor.py`
  - [ ] Change INPUT_FILE to HRA_data.csv
  - [ ] Add sanitize_company_name() function
  - [ ] Remove map_sponsor_to_company() function
  - [ ] Update save_company_specific_data() function
  - [ ] Remove mappings parameter from function call
- [ ] Update `analysis.py`
  - [ ] Change glob pattern to "Corporate_*.csv"
  - [ ] Add handling for Unknown_Company.csv
- [ ] Update `ai.py`
  - [ ] Update discover_files() method
  - [ ] Update determine_csv_path() method
- [ ] Update `value_mappings.json`
  - [ ] Remove SponsorId section
  - [ ] Validate JSON structure

### Testing
- [ ] Run preprocessing: `python 00_init_data/csv_preprocessor.py`
- [ ] Verify file names and structure
- [ ] Run analysis (main only): `python analysis.py --main-only`
- [ ] Run analysis (full): `python analysis.py`
- [ ] Verify all company reports generated
- [ ] Run AI processing (main only): `python ai.py --main-only`
- [ ] Run AI processing (full): `python ai.py`
- [ ] Compare record counts (old vs new)
- [ ] Spot-check outputs for correctness

### Post-Migration
- [ ] Commit changes: `git commit -am "Migrate to CorporateId-based grouping"`
- [ ] Tag release: `git tag -a v2.0-corporate-id -m "Migration to CorporateId"`
- [ ] Update documentation (README, if exists)
- [ ] Clean up old backup: `rm -rf 01_in_backup` (only after confirming success)
- [ ] Archive old mapping: `mv value_mappings.json.backup _archive/`

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| CorporateId-CorporateName inconsistency | Medium | High | Run validation script before migration |
| Many #N/A records affecting analysis | Medium | Medium | Check #N/A count beforehand, acceptable if small % |
| File naming conflicts (special chars) | Low | Medium | Robust sanitization function with tests |
| Breaking downstream systems | Low | High | Clean break - no partial migration |
| Data loss during migration | Low | High | Full backup before starting |

---

## Notes

### Design Decisions

1. **Why CorporateId prefix in filename?**
   - Uniqueness guarantee (company names may not be unique)
   - Easy programmatic parsing
   - Human-readable balance

2. **Why not use full CorporateId?**
   - Very long filenames (24+ chars)
   - First 8 chars provide sufficient uniqueness for visual identification
   - Full ID is still in the CSV data itself

3. **Why create Unknown_Company group?**
   - Preserves all data for main analysis
   - Allows investigation of untagged records
   - Better than silently dropping data

4. **Why clean break from SponsorId?**
   - Simplifies codebase (no dual-path logic)
   - Clearer ownership of data structure
   - Easier to maintain going forward

### Future Considerations

1. **Multiple data sources:** If you add more CSVs in future, ensure they all have CorporateId/CorporateName
2. **Company name changes:** CorporateId remains stable, only sanitized name in filename changes
3. **Mergers/acquisitions:** May need to handle CorporateId remapping if companies merge
4. **Historical analysis:** Old Company_X naming is gone, need to map old reports to new IDs if comparing

---

## Questions for Final Review

Before proceeding with migration, confirm:

1. ✅ Is the new CSV (`HRA_data.csv`) the authoritative source going forward?
2. ✅ Are there any other scripts/tools that depend on the Company_X naming pattern?
3. ✅ Do we need to preserve any historical analysis with the old naming scheme?
4. ✅ Is there a data dictionary for CorporateId/CorporateName? (to understand their semantics)
5. ⚠️  Should we validate that SponsorId and CorporateId have expected relationships? (superset/subset)

---

## Timeline Estimate

- **Code changes:** 1-2 hours
- **Testing:** 1-2 hours
- **Full pipeline run:** 30-60 minutes (depends on data size)
- **Validation & verification:** 30 minutes

**Total:** 3-5 hours for safe, methodical migration

---

**Document Version:** 1.0
**Last Updated:** 2025-10-22
**Owner:** Dogapoyraz Tahan
