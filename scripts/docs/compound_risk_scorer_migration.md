# Compound Risk Scorer Migration Instructions

## Current Script Analysis

### What the script does:
The `compound_risk_scorer.py` creates alternative risk scoring mechanisms that go beyond the standard health risk score by:

1. **Risk Factor Analysis**: Groups variables into logical categories (stress, lifestyle, demographics, health, behavior)
2. **Individual Risk Weights**: Calculates risk multipliers for each factor value based on how it correlates with actual health outcomes
3. **Compound Scoring**: Creates new risk scores using two methods:
   - **Additive**: Simple average of all factor risk multipliers  
   - **Interaction-weighted**: Additive score + bonuses for known high-risk combinations
4. **Performance Evaluation**: Tests how well the compound scores predict actual health risk levels
5. **Outlier Detection**: Finds cases where compound score disagrees with actual risk (over/under-estimates)

### Current Parameters:
- `--data`: Path to CSV data file
- `--method`: `additive` (default) or `interaction-weighted` 
- `--factors`: Focus on specific factor groups (stress,lifestyle,demographics,health,behavior)
- `--min-sample`: Minimum sample size for factor analysis (default: 15)
- `--output`: Optional JSON output file
- `--verbose`: Detailed output

### Key Issues to Fix:

1. **Wrong Column Names**: Script expects simplified names like `stress_calm`, `mood_positivity` but data has `Data.stress_level_irritability`, `Data.depression_mood`

2. **Missing Variables**: Only defines ~20 factor variables but data has 25+ lifestyle/health variables

3. **Hardcoded Factor Groups**: Uses fixed lists instead of auto-discovering from actual data

4. **Class-based Structure**: Uses unnecessary class when simple functions would work

## Migration Requirements

### Goals:
✅ **Keep it simple** - Remove class, use functions  
✅ **Use actual column names** - Work with real `Data.*` prefixed columns  
✅ **Include all variables** - Use all 25+ available lifestyle/health factors  
✅ **Configurable** - Column mappings at top for easy changes  
✅ **Same functionality** - Preserve both scoring methods and evaluation  

### New Structure:

```python
# Configuration section at top
DEMOGRAPHIC_FACTORS = ['age_group', 'Data.gender', 'Data.has_children', 'bmi_category']
LIFESTYLE_FACTORS = ['Data.smoking_status', 'Data.alcohol_consumption', ...]
STRESS_FACTORS = ['Data.stress_level_irritability', 'Data.depression_mood', ...]
# ... etc for all factor groups

# Simple functions instead of class
def load_and_validate_data(data_path)
def calculate_factor_weights(df, factor_groups, min_sample)
def create_additive_score(df, factor_weights)
def create_interaction_weighted_score(df, factor_weights)
def evaluate_score_performance(df, scores, method)
def find_score_outliers(df, scores, method)
def print_results(evaluation, outliers, factor_weights)
```

### Implementation Steps:

1. **Update Factor Groups**: 
   - Map to actual column names from the data
   - Include all chronic conditions, lifestyle variables, mental health factors
   - Group logically (demographics, lifestyle, mental_health, chronic_conditions, behavior)

2. **Simplify Structure**:
   - Remove class, use standalone functions
   - Single main() function that orchestrates the analysis
   - Clear separation between data processing and output

3. **Fix Column Name Issues**:
   - Update all hardcoded column references to match actual data
   - Use `find_available_columns()` helper to gracefully handle missing columns
   - Print clear warnings when expected columns aren't found

4. **Preserve Core Logic**:
   - Keep the risk multiplier calculation (rate vs population baseline)
   - Keep both additive and interaction-weighted methods
   - Keep the performance evaluation metrics (precision, recall)
   - Keep outlier detection for over/under-estimated risk

5. **Enhance Output**:
   - Clear sections for factor weights, compound scores, evaluation
   - Better formatting for interpretation
   - Optional JSON export for programmatic use

### Expected Output:
The new script should produce the same analysis but with:
- All actual data columns included in factor analysis
- Clear factor group organization  
- Both scoring methods working correctly
- Performance evaluation showing prediction accuracy
- Outlier analysis highlighting surprising cases
- Easy configurability for different datasets

### Key Functions to Implement:

1. `calculate_individual_risk_weights()` - Core risk multiplier calculation
2. `create_additive_compound_score()` - Simple averaging method
3. `create_interaction_weighted_score()` - Amplification bonuses method  
4. `evaluate_compound_score_performance()` - Precision/recall analysis
5. `find_score_outliers()` - Prediction disagreement analysis

The migrated script should maintain the same statistical rigor while being more maintainable and working with the actual dataset structure.