# Interaction Scanner Migration Instructions

## Current Script Analysis

### What the script does:
The `interaction_scanner.py` discovers **variable combinations** that create unexpected health risk patterns by:

1. **Risk Amplification Detection**: Finds combinations where `1+1=5` (compound effects exceed individual effects)
2. **Protective Pattern Discovery**: Identifies combinations where `1+1=0` (factors cancel each other out)  
3. **Counterintuitive Insights**: Reveals combinations that defy common assumptions
4. **Statistical Validation**: Uses population baselines and sample size requirements for reliability

### Core Concept: Risk Amplification Factor
- **Baseline**: Population risk rate (e.g., 18.1% high risk)
- **Individual Factor**: "High stress" = 25% high risk = **1.4x amplification**
- **Combination**: "High stress + Young age" = 45% high risk = **2.5x amplification**
- **Insight**: The combination amplifies risk more than individual factors would predict

### Current Parameters:
- `--data`: Path to CSV data file  
- `--include`: Comma-separated variables to test (overrides everything else)
- `--exclude`: Comma-separated variables to exclude from testing
- `--threshold`: Risk amplification threshold (default: 1.5x)
- `--min-sample`: Minimum sample size for reliable patterns (default: 15)
- `--output`: Optional JSON output file
- `--verbose`: Detailed analysis steps

## Migration Requirements

### Key Issues to Fix:

1. **Wrong Column Names**: Expects simplified names but data has `Data.*` prefixed columns
2. **Class Structure**: Uses unnecessary class when functions would be simpler
3. **Limited Outcome Detection**: Only recognizes `health_risk_level` and `health_risk_score`
4. **Hardcoded Risk Logic**: Inflexible risk detection patterns

### Goals:
✅ **Use actual column names** - Work with real `Data.*` prefixed columns  
✅ **Remove class complexity** - Use simple functions  
✅ **Flexible outcome detection** - Auto-detect risk patterns in any outcome  
✅ **Complete variable coverage** - Include all 38 columns for comprehensive analysis  
✅ **Preserve analytical rigor** - Keep statistical validation and amplification logic  

## Strategic Analysis Workflow

### 🎯 **Phase 1: Broad Discovery** 
**Goal**: Understand the interaction landscape across all variables

```bash
# Cast a wide net to see all meaningful interactions
python interaction_scanner.py --data preprocessed_data/HRA_data.csv --threshold 1.5
```

**Expected Results**: 50-100+ interactions  
**Use**: Identify which variable pairs show the strongest effects  
**Focus**: Look for surprising amplifications above 2.0x  

### 🔍 **Phase 2: Hypothesis-Driven Investigation**
**Goal**: Test specific theories from Phase 1 discoveries

```bash
# Test stress-related amplifications
python interaction_scanner.py --data data.csv \
  --include Data.stress_level_irritability,Data.depression_mood,Data.loneliness,age_group,health_risk_level \
  --threshold 2.0

# Test lifestyle combination effects  
python interaction_scanner.py --data data.csv \
  --include Data.smoking_status,Data.alcohol_consumption,Data.activity_level,health_risk_level \
  --threshold 2.0

# Test demographic risk patterns
python interaction_scanner.py --data data.csv \
  --include age_group,Data.gender,Data.has_children,bmi_category,health_risk_level \
  --threshold 1.8
```

**Expected Results**: 10-30 focused interactions per run  
**Use**: Deep-dive into specific risk factor categories  
**Focus**: Understand which combinations within categories are most dangerous  

### 🎯 **Phase 3: Extreme Pattern Detection**
**Goal**: Find only the most dramatic risk amplifications

```bash
# Only show the most extreme interactions
python interaction_scanner.py --data data.csv --threshold 3.0 --min-sample 20

# Focus on chronic conditions amplification
python interaction_scanner.py --data data.csv \
  --include Data.chronic_conditions_diabetes,Data.chronic_conditions_heart_disease,age_group,health_risk_level \
  --threshold 4.0
```

**Expected Results**: 5-15 extreme interactions  
**Use**: Identify highest-priority intervention targets  
**Focus**: Combinations requiring immediate attention  

### 📊 **Phase 4: Protective Pattern Analysis**
**Goal**: Find combinations that unexpectedly reduce risk

```bash
# Look for protective effects (low threshold to catch subtle protection)
python interaction_scanner.py --data data.csv \
  --include Data.activity_level,Data.sleep_quality,Data.fruit_veg_intake,health_risk_level \
  --threshold 1.2

# Focus on mental health protective combinations
python interaction_scanner.py --data data.csv \
  --include Data.perceived_health,Data.loneliness,Data.stress_level_loc,health_risk_level \
  --threshold 1.3
```

**Expected Results**: 20-40 interactions with protective patterns  
**Use**: Identify best practices and protective behaviors to promote  
**Focus**: Combinations where amplification < 0.8x (protective effects)  

## Critical Parameter Combinations for Comprehensive Exploration

### 1. **Maximum Coverage Runs**
```bash
# Full dataset exploration (will take time but comprehensive)
python interaction_scanner.py --data data.csv --threshold 1.5 --output full_interactions.json

# Exclude only ID fields for complete analysis  
python interaction_scanner.py --data data.csv --exclude _id,UserId --threshold 1.6
```

### 2. **Category-Focused Deep Dives**
```bash
# Mental Health Interactions
python interaction_scanner.py --data data.csv \
  --include Data.stress_level_irritability,Data.depression_anhedonia,Data.depression_mood,Data.loneliness,Data.perceived_health,health_risk_level \
  --threshold 1.8

# Physical Health & Lifestyle  
python interaction_scanner.py --data data.csv \
  --include Data.activity_level,Data.daily_steps,Data.sleep_quality,Data.physical_pain,bmi_category,health_risk_level \
  --threshold 1.7

# Substance Use Patterns
python interaction_scanner.py --data data.csv \
  --include Data.smoking_status,Data.alcohol_consumption,age_group,Data.gender,health_risk_level \
  --threshold 2.0

# Nutrition & Wellness
python interaction_scanner.py --data data.csv \
  --include Data.fruit_veg_intake,Data.sugar_intake,Data.processed_food_intake,Data.water_intake,health_risk_level \
  --threshold 1.9
```

### 3. **High-Confidence Runs** 
```bash
# Large sample sizes for business decisions
python interaction_scanner.py --data data.csv --min-sample 25 --threshold 2.0

# Only the most reliable extreme patterns
python interaction_scanner.py --data data.csv --min-sample 30 --threshold 3.0
```

## New Structure Design

### Configuration Section:
```python
# Outcome columns (in order of preference)
OUTCOME_COLUMNS = ['health_risk_level', 'Total_Health_Score', 'health_risk_score']

# Auto-exclude patterns (ID fields, etc.)  
AUTO_EXCLUDE_PATTERNS = ['id', 'record', 'user']

# Risk detection patterns for different outcome types
RISK_PATTERNS = {
    'categorical': ['high_risk', 'severe', 'extreme'],
    'numeric_high': lambda x: x >= np.percentile(x, 75),  # Top quartile
    'numeric_low': lambda x: x <= np.percentile(x, 25)    # Bottom quartile  
}
```

### Key Functions:
```python
def load_and_validate_data(data_path)
def filter_variables(df, include_vars, exclude_vars) 
def calculate_baseline_risk_rate(df, outcome_col)
def test_variable_pair_interaction(df, var1, var2, outcome_col, threshold, min_sample)
def analyze_all_interactions(df, predictor_vars, outcome_vars, threshold, min_sample)
def categorize_interactions(interactions)  # Amplifiers vs Protective
def print_human_readable_report(interactions)
def save_json_output(interactions, output_path)
```

## Expected Migration Outcomes

### Enhanced Capabilities:
- **Complete Variable Coverage**: All 38 columns analyzed vs limited subset  
- **Flexible Risk Detection**: Works with any outcome pattern vs hardcoded logic
- **Better Error Handling**: Clear messages when no patterns found
- **Improved Output**: Clearer categorization of amplification vs protection

### Maintained Functionality:
- **Statistical Rigor**: Same amplification calculations and sample size requirements
- **Multiple Output Formats**: Human-readable + JSON for LLM processing
- **Parameter Flexibility**: Include/exclude filtering and threshold tuning
- **Baseline Comparison**: All patterns compared to population baseline

### Performance Expectations:
- **Broad Discovery**: ~100 interactions found across 38 variables
- **Focused Analysis**: ~20 interactions per category focus
- **Extreme Patterns**: ~10 interactions above 3.0x amplification  
- **Processing Time**: 30-60 seconds for full analysis vs 5-10 seconds for focused

## Migration Success Criteria

✅ **Completeness**: Analyzes all available columns without hardcoded limitations  
✅ **Accuracy**: Produces same statistical results as original for equivalent inputs  
✅ **Usability**: Clear parameter combinations for different analysis needs  
✅ **Extensibility**: Easy to modify for new outcome types or risk patterns  
✅ **Performance**: Handles full dataset analysis without breaking  

The migrated script should enable comprehensive interaction discovery across the entire dataset while maintaining the statistical rigor needed for reliable business insights.