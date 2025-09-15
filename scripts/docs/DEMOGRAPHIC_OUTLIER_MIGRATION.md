# Demographic Outlier Spotter Migration Instructions

## Current Script Analysis

### What the script does:
The `demographic_outlier_spotter.py` script identifies **small demographic segments** (<5% of population) with **disproportionate health impacts**. It finds "hidden populations" that might be overlooked in broad analysis but show significantly different health risk patterns.

### Core Functionality:
1. **Single-variable outlier detection**: Tests each demographic variable individually against health outcomes
2. **Two-variable outlier detection**: Tests combinations of demographic variables  
3. **Statistical validation**: Uses risk ratios and minimum sample sizes to validate findings
4. **Outlier categorization**: Classifies as "ELEVATED" risk or "PROTECTED" segments
5. **Detailed reporting**: Provides human-readable analysis with statistical context

### Key Parameters:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `--max-size` | 5.0 | Maximum segment size as % of population (outliers must be small) |
| `--min-risk-ratio` | 1.5 | Minimum risk ratio to flag as outlier (1.5x = 50% higher risk) |
| `--min-sample` | 10 | Minimum sample size for reliable analysis (avoid tiny groups) |
| `--focus` | None | Comma-separated list to focus analysis on specific demographics |
| `--verbose` | False | Show detailed analysis including segment characteristics |

### Current Issues:
1. **Class-based complexity** - Uses unnecessary class structure  
2. **Hardcoded column names** - Expects `health_risk_score` but data has `Total_Health_Score`
3. **Limited demographic variables** - Only looks at 7 basic demographics
4. **KeyError bug** - Fixed in our earlier work but shows fragility

## Migration Goals

### Primary Objective:
Create a **simple, functional script** that identifies small demographic segments with unusual health patterns, making it easy to spot intervention opportunities.

### Key Requirements:
- **No classes** - Use simple functions
- **All demographic variables** - Include all `Data.*` columns from actual dataset
- **Configurable column mappings** - Easy to modify for different datasets
- **Clear output** - Actionable insights for stakeholders
- **Robust error handling** - Graceful handling of missing data/columns

## Implementation Strategy

### 1. Column Configuration
```python
# Outcome columns (health metrics to analyze)
OUTCOME_COLUMNS = ['health_risk_level', 'Total_Health_Score']

# Core demographic segmentation variables  
DEMOGRAPHIC_VARIABLES = ['age_group', 'Data.gender', 'Data.has_children', 'bmi_category']

# Lifestyle variables that can create demographic segments
LIFESTYLE_DEMOGRAPHICS = [
    'Data.smoking_status', 'Data.stress_level_irritability', 'Data.activity_level',
    'Data.sleep_quality', 'Data.perceived_health'
]

# Chronic conditions as demographic indicators
CHRONIC_CONDITION_DEMOGRAPHICS = [
    'Data.chronic_conditions_diabetes', 'Data.chronic_conditions_obesity',
    'Data.chronic_conditions_hypertension'
]
```

### 2. Core Functions Structure
```python
def find_single_variable_outliers(df, demographic_vars, outcome_vars, max_size_pct, min_risk_ratio, min_sample):
    """Find outliers in individual demographic variables"""
    
def find_two_variable_outliers(df, demographic_vars, outcome_vars, max_size_pct, min_risk_ratio, min_sample):
    """Find outliers in demographic combinations (limit combinations to avoid explosion)"""

def calculate_risk_metrics(segment_df, population_df, outcome_col):
    """Calculate risk ratios, rates, and statistical significance"""

def generate_outlier_insights(outliers):
    """Generate structured insights from outliers"""

def print_outlier_report(insights):
    """Human-readable report of findings"""
```

### 3. Analysis Logic

#### Single Variable Analysis:
- For each demographic variable (age_group, Data.gender, etc.)
- For each outcome (health_risk_level, Total_Health_Score)  
- Calculate segment size, risk rate, and population risk rate
- Flag if: segment size ≤ max_size AND risk_ratio ≥ min_risk_ratio AND sample ≥ min_sample

#### Two Variable Analysis:
- Test key combinations (age × gender, age × BMI, gender × chronic conditions)
- Avoid combinatorial explosion by focusing on meaningful pairs
- Apply same outlier detection criteria

#### Risk Metrics:
```python
# For categorical outcomes (health_risk_level)
risk_rate = (segment_df[outcome] == 'high_risk').mean()
population_rate = (df[outcome] == 'high_risk').mean() 
risk_ratio = risk_rate / population_rate

# For numeric outcomes (Total_Health_Score)  
# Use quartile-based analysis: top/bottom quartile rates
```

### 4. Output Format

#### Expected Output Structure:
```
DEMOGRAPHIC OUTLIER ANALYSIS REPORT
================================================================================

OUTLIER DETECTION SUMMARY:
Total outlier segments found: 15
Max segment size: 5.0% of population
Min risk ratio: 1.5x population average
Elevated risk segments: 12
Protected segments: 3

HIGHEST RISK DEMOGRAPHIC OUTLIERS
------------------------------------------------------------

• Data.gender = other
  Segment size: 17 employees (7.3% of population) 
  high_risk rate: 35.3% (vs 19.4% population)
  Risk ratio: 1.8x | Sample size: 17

• age_group = mature + Data.chronic_conditions_diabetes = 1
  Segment size: 3 employees (1.3% of population)
  high_risk rate: 100.0% (vs 19.4% population)  
  Risk ratio: 5.2x | Sample size: 3
```

### 5. Key Differences from Original

| Aspect | Original Script | New Script |
|--------|----------------|------------|
| **Structure** | Class-based (200+ lines) | Function-based (~150 lines) |
| **Columns** | Hardcoded 7 variables | All 25+ demographic variables |
| **Column Names** | Expected `health_risk_score` | Uses actual `Total_Health_Score` |
| **Combinations** | All possible pairs | Strategic key pairs only |
| **Output** | Complex nested reports | Clear actionable insights |
| **Configuration** | Buried in class methods | Top-level constants |

### 6. Success Criteria

The migrated script should:
- ✅ **Find actionable segments**: 10-50 employee groups with clear intervention opportunities  
- ✅ **Handle all data columns**: Use actual column names from dataset
- ✅ **Avoid analysis paralysis**: Focus on highest-impact outliers
- ✅ **Provide clear insights**: "X% of employees in Y demographic have Z risk"
- ✅ **Run reliably**: No crashes on missing columns or edge cases

### 7. Testing Validation

After migration, verify:
- Script runs without errors on actual data
- Finds meaningful outliers (not statistical noise)
- Output is interpretable by non-technical stakeholders  
- Performance is reasonable (completes in <30 seconds)
- Handles edge cases (no outliers found, single-value columns)

### 8. Parameter Tuning Guidelines

| Use Case | max-size | min-risk-ratio | min-sample |
|----------|----------|---------------|-------------|
| **Broad discovery** | 10.0 | 1.3 | 5 |
| **Standard analysis** | 5.0 | 1.5 | 10 |  
| **High-confidence only** | 3.0 | 2.0 | 20 |
| **Micro-targeting** | 2.0 | 2.5 | 15 |

The goal is identifying **"hidden populations"** - small but high-impact employee segments that warrant targeted wellness interventions.