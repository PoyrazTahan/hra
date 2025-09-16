# Column Relationship Analysis Implementation Plan

## Purpose & Scope

Create `05_column_relation_analysis.py` to discover **descriptive-to-descriptive relationships** in health data without focusing on target variables. Fill the gap left by target-driven scripts (02-04) by understanding how lifestyle, demographic, and behavioral factors correlate with each other.

## Key Requirements

### ✅ **What This Script Should Do:**
1. **Find lifestyle clustering patterns** - Which unhealthy behaviors cluster together?
2. **Discover demographic behavior differences** - How do age/gender groups differ in lifestyle?
3. **Identify surprising correlations** - Unexpected relationships between variables
4. **Generate LLM-ready insights** - Clear, actionable relationship patterns

### ❌ **What This Script Should NOT Do:**
- Target-driven analysis (health_risk_level prediction) - Scripts 02-04 handle this
- Class-based architecture - Keep it flat and functional
- Complex statistical modeling - Focus on interpretable relationships

## Implementation Strategy

### 1. **Column Configuration (Global Variables)**
```python
# Exclude ID columns and target variables
EXCLUSION_COLUMNS = ['_id', 'UserId', 'health_risk_level', 'Total_Health_Score']

# Lifestyle behavior cluster
LIFESTYLE_FACTORS = [
    'Data.smoking_status', 'Data.alcohol_consumption', 'Data.activity_level',
    'Data.sleep_quality', 'Data.daily_steps', 'Data.supplement_usage'
]

# Mental health & stress cluster
MENTAL_HEALTH_FACTORS = [
    'Data.stress_level_irritability', 'Data.depression_mood', 'Data.loneliness',
    'Data.perceived_health', 'Data.depression_anhedonia'
]

# Nutrition behavior cluster
NUTRITION_FACTORS = [
    'Data.fruit_veg_intake', 'Data.sugar_intake', 'Data.processed_food_intake', 'Data.water_intake'
]

# Core demographics
DEMOGRAPHIC_FACTORS = ['age_group', 'Data.gender', 'Data.has_children', 'bmi_category']

# Physical health descriptors
PHYSICAL_HEALTH_FACTORS = ['Data.physical_pain', 'Data.chronic_conditions_*']
```

### 2. **Core Analysis Functions (Flat Structure)**

#### **Function: `calculate_categorical_correlations()`**
- **Purpose**: Find relationships between categorical variables using Cramer's V
- **Logic**: Chi-square test + effect size calculation
- **Output**: Correlation matrix for categorical variables
- **Threshold**: Only report Cramer's V > 0.3 (medium+ effect size)

#### **Function: `analyze_lifestyle_clustering()`**
- **Purpose**: Find which lifestyle behaviors cluster together
- **Method**: Cross-tabulation analysis within lifestyle factors
- **Key Insight**: "People who smoke are X% more likely to have poor nutrition"
- **Focus**: Unhealthy behavior clustering vs healthy behavior clustering

#### **Function: `analyze_demographic_differences()`**
- **Purpose**: How do age/gender/family status affect lifestyle choices?
- **Method**: Group-wise proportion comparisons
- **Key Insights**:
  - "Young adults vs mature adults lifestyle differences"
  - "Males vs females stress coping patterns"
  - "Parents vs non-parents health behaviors"

#### **Function: `find_surprising_correlations()`**
- **Purpose**: Discover unexpected relationships across different factor groups
- **Method**: Cross-cluster correlation analysis
- **Examples**: Physical pain ↔ loneliness, Water intake ↔ activity level
- **Filter**: Only report correlations that are non-obvious and actionable

### 3. **Statistical Approach & Thresholds**

#### **For Categorical Variables:**
- **Cramer's V**: Measure association strength (0-1 scale)
  - 0.1-0.3: Small effect
  - 0.3-0.5: Medium effect ← **Report these**
  - 0.5+: Large effect ← **Highlight these**
- **Chi-square p-value**: Statistical significance (p < 0.05)

#### **For Mixed Analysis:**
- **Proportion differences**: ≥15 percentage point differences
- **Sample size**: Minimum 10 per cell for stable estimates
- **Effect magnitude**: Focus on actionable differences (not just statistical significance)

### 4. **Output Structure & LLM Optimization**

```
COLUMN RELATIONSHIP ANALYSIS REPORT
================================================================================

LIFESTYLE CLUSTERING PATTERNS
------------------------------------------------------------
• Strong Clustering: Smoking ↔ Poor Nutrition (Cramer's V = 0.42)
  - Daily smokers: 73% poor nutrition vs 31% population
  - Never smokers: 18% poor nutrition vs 31% population
  - Insight: Smoking and poor nutrition cluster as "unhealthy lifestyle"

• Mental Health Clustering: Stress ↔ Depression ↔ Loneliness (V = 0.38)
  - High stress individuals: 67% also report depression, 52% loneliness
  - Population baseline: 23% depression, 18% loneliness
  - Insight: Mental health factors strongly cluster together

DEMOGRAPHIC BEHAVIOR DIFFERENCES
------------------------------------------------------------
• Age Group Lifestyle Patterns:
  - Young adults: 67% poor sleep, 45% no exercise
  - Mature adults: 23% poor sleep, 28% no exercise
  - Key difference: Young adults sacrifice sleep and exercise

• Gender Coping Patterns:
  - Females: 3x more likely to report loneliness (42% vs 14%)
  - Males: 2x more likely to use alcohol coping (38% vs 19%)
  - Insight: Different stress expression patterns by gender

SURPRISING CORRELATIONS
------------------------------------------------------------
• Physical Pain ↔ Social Isolation (Cramer's V = 0.35)
  - People with moderate+ pain: 58% report loneliness
  - Population baseline: 18% loneliness
  - Insight: Physical pain strongly correlates with social isolation

• Water Intake ↔ Activity Level (V = 0.31)
  - Daily exercisers: 78% high water intake
  - No exercise group: 23% high water intake
  - Insight: Hydration behavior tracks with physical activity
```

## 5. **Implementation Considerations**

### **Statistical Robustness:**
- **Handle small cells**: Skip analysis when expected cell count < 5
- **Multiple comparisons**: Focus on effect sizes, not just p-values
- **Missing data**: Use pairwise deletion for each relationship test

### **Avoid Common Pitfalls:**
1. **Correlation ≠ Causation**: Label as "associations" not "causes"
2. **Simpson's Paradox**: Don't over-interpret aggregate correlations
3. **Selection Bias**: Acknowledge this is observational data
4. **Cherry-picking**: Report systematic findings, not isolated strong correlations

### **Performance Considerations:**
- **Limit combinations**: Focus on within-cluster and cross-cluster analysis
- **Efficient computation**: Use pandas crosstab for categorical analysis
- **Memory usage**: Process correlations in chunks if needed

## 6. **Expected Value & Validation**

### **Success Criteria:**
- **Actionable insights**: Findings that inform wellness program design
- **Non-obvious patterns**: Relationships not captured by other scripts
- **Interpretable results**: Clear narrative for LLM consumption
- **Statistical validity**: Robust findings with appropriate effect sizes

### **Quality Checks:**
- **Face validity**: Do the relationships make intuitive sense?
- **Effect magnitude**: Are the differences practically significant?
- **Sample sufficiency**: Are the findings based on adequate sample sizes?
- **Consistency**: Do patterns hold across different demographic groups?

## 7. **Differences from Existing Scripts**

| **Aspect** | **Script 01 (EDA)** | **Scripts 02-04** | **Script 05 (This)** |
|------------|---------------------|-------------------|----------------------|
| **Focus** | Individual variable distributions | Target prediction | Variable-to-variable relationships |
| **Method** | Descriptive statistics | Risk ratio analysis | Correlation & clustering analysis |
| **Output** | Column summaries | Risk segments | Relationship patterns |
| **Purpose** | Data understanding | Intervention targeting | Behavioral insights |

This script fills the critical gap of understanding **how descriptive factors relate to each other**, providing the foundation for understanding employee behavior patterns independent of health outcomes.