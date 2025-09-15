# Health Risk Assessment Analysis Tools

## Tool Ecosystem Overview

This suite of analysis tools creates a **progressive discovery pipeline** for employee health risk data. Each tool builds upon the previous level of analysis, surfacing increasingly sophisticated patterns for LLM interpretation.

```
Foundation EDA → Statistical Surprises → Interaction Effects → Demographic Outliers → Compound Scoring
    Phase 1&2   →     Anomalies      →    Amplifiers    →   Micro-segments  →   Alternative Risk
```

**Analysis Philosophy**: Instead of predetermined categories, these tools surface **statistical surprises** and **unexpected patterns** that an LLM can interpret and transform into compelling insights for stakeholders.

---

## 1. Foundation EDA (`scripts/simple_eda.py`)

### Purpose
Provides comprehensive baseline statistics and cross-pattern analysis. Essential foundation that all other tools build upon.

### Key Arguments
```bash
# Complete statistical foundation
--phase 1          # 1D statistics for every variable
--phase 2          # Cross-pattern relationships  
--phase all        # Both phases (recommended for new datasets)
--verbose          # Detailed distribution outputs
```

### When to Use
- **First analysis** of any new dataset
- Before running any discovery tools
- When you need comprehensive data understanding

### Interpreting Results

**Interesting Patterns to Look For**:
- Variables with extreme distributions (>80% in one category)
- Chi-square effects >0.3 (strong relationships)
- Counterintuitive correlations (healthy behavior + high risk)
- Age-specific pattern differences

**Uninteresting/Ignore**:
- Weak correlations (<0.2 effect size)
- Expected relationships (age ↔ chronic conditions)
- Balanced distributions without clear patterns
- Very small cross-pattern sample sizes (<20)

**Drilling Deeper Strategy**:
After reviewing EDA output, identify 2-3 most surprising patterns and use them to form hypotheses for the discovery tools.

---

## 2. Statistical Surprise Detector (`scripts/statistical_surprise.py`)

### Purpose
Finds demographic and lifestyle subgroups where outcomes significantly differ from statistical expectations. Answers "which groups are surprisingly different?"

### Key Arguments
```bash
# Basic usage
--data path/to/data.csv

# Sensitivity control  
--min-sample 15        # Require 15+ employees per subgroup (reliability)
--threshold 2.0        # Require 2.0+ standard deviations (surprise level)

# Output control
--output surprises.json    # LLM-ready structured output
```

### When to Use
- After foundation EDA reveals intriguing demographic patterns
- When you want to quantify "how surprising" specific findings are
- To identify overlooked subgroups for intervention

### Interpreting Results

**Most Interesting Surprises**:
- **High magnitude** (>5.0σ): Extremely unexpected patterns
- **Large sample sizes** (>50): Reliable for business decisions  
- **Counterintuitive direction**: "Healthy" behaviors + high risk
- **Multiple related surprises**: Same subgroup appearing across outcomes

**Example Interesting Result**:
```
[DEMOGRAPHIC] underweight ↑
Outcome: high_risk in health_risk_level  
Rate: 16.7% (vs 8.7% population)
Magnitude: 3.2σ | Sample: 84 employees
```
**Why interesting**: Underweight typically associated with health, but shows nearly 2x risk rate with substantial sample size.

**Uninteresting/Ignore**:
- Small magnitudes (<2.0σ): Could be random variation
- Tiny samples (<15): Unreliable for conclusions
- Expected surprises: "Heavy smokers have high risk" (obvious)
- Single-occurrence patterns: Only one related surprise for a subgroup

**Drilling Deeper Strategy**:
- Use surprising demographic groups as `--include` filters for interaction scanner
- Investigate what lifestyle factors drive demographic surprises
- Look for compound effects using demographic outlier spotter

---

## 3. Interaction Scanner (`scripts/interaction_scanner.py`)

### Purpose
Discovers variable combinations where effects amplify, suppress, or create unexpected outcomes. Finds "1+1=5" synergistic effects and "1+1=0" protective combinations.

### Key Arguments & Modes
```bash
# Exploration mode - see the full landscape
--threshold 1.5        # Show 1.5x+ amplifications (many results)

# Hypothesis mode - test specific combinations  
--include stress_calm,smoking_status,age_group,health_risk_level
--threshold 2.5        # Higher threshold for cleaner results

# Report mode - only dramatic findings
--threshold 4.0        # Show 4x+ amplifications (few, extreme results)
--min-sample 20        # Higher reliability for business decisions
```

### When to Use

**Exploration Mode**: After EDA shows multiple interesting individual variables
**Hypothesis Mode**: When you suspect specific variables interact (stress + age, smoking + alcohol)  
**Report Mode**: For executive summaries focusing on most critical combinations

### Interpreting Results

**Most Interesting Interactions**:
- **High amplification** (>3x): Risk combinations worth urgent attention
- **Counterintuitive amplification**: "Healthy" factor + risk factor = extreme risk
- **Large sample protective effects**: Reliable "good combinations" to promote
- **Demographic-specific amplification**: Same interaction affects different groups differently

**Example Interesting Result**:
```
stress_calm × smoking_status → health_risk_level
• mostly_stressed + non_smoker: 100.0% (11.49x baseline, n=39)
```
**Why interesting**: Non-smoking is typically protective, but with high stress becomes perfect risk predictor. Suggests stress overwhelms other health behaviors.

**Uninteresting/Ignore**:
- Low amplification (<1.8x): Marginal effects
- Expected combinations: "Heavy smoker + heavy drinker = high risk" 
- Tiny sample sizes (<15): Unreliable patterns
- Perfect correlations from derived variables: BMI + weight interactions

**Drilling Deeper Strategy**:
- Use surprising interactions as basis for demographic outlier analysis
- Test if interactions hold across different age groups or demographics
- Investigate whether protective combinations can be promoted organization-wide

---

## 4. Demographic Outlier Spotter (`scripts/demographic_outlier_spotter.py`)

### Purpose
Identifies small demographic segments (<5% of population) with disproportionate health impacts. Finds "hidden populations" that might be overlooked in broad analysis.

### Key Arguments & Modes
```bash
# Standard outlier detection
--max-size 5.0         # Max 5% of population (small segment threshold)
--min-risk-ratio 1.5   # 1.5x+ population risk rate

# Focused demographic analysis
--focus age_group,gender,has_children
--min-risk-ratio 2.5   # Stricter outlier threshold

# High-reliability analysis
--min-sample 20        # Larger samples for business decisions
--max-size 3.0         # Smaller segments (more exclusive outliers)
```

### When to Use

**After surprise detection** reveals specific demographic anomalies
**For targeted program design** when you need to identify specific intervention populations
**For resource allocation** when you want to focus on high-impact small groups

### Interpreting Results

**Most Interesting Outliers**:
- **High risk ratio** (>3x): Small groups with massive risk concentration
- **Unexpected protection**: Groups that should be high risk but aren't  
- **Actionable size**: 10-50 employees (manageable for targeted interventions)
- **Clear distinctive characteristics**: Obvious lifestyle patterns explaining the outlier

**Example Interesting Result**:
```
• gender = other
  Segment size: 17 employees (1.7% of population)
  high_risk: 23.5% (vs 8.7% population)  
  Risk ratio: 2.7x | Difference: +14.8pp
  Distinctive: 23.5% mostly_stressed (+17.4pp vs population)
```
**Why interesting**: Small, actionable group with clear risk drivers and specific intervention opportunities.

**Uninteresting/Ignore**:
- **Expected outliers**: Seniors with more chronic conditions
- **Tiny samples** (<10): Unreliable for action
- **Marginal differences** (<20% rate difference): Limited practical impact
- **No distinctive characteristics**: Can't explain why they're different

**Drilling Deeper Strategy**:
- Use outlier segments as `--include` filters for interaction analysis
- Test if outlier patterns hold when you control for other variables
- Investigate if outliers represent early indicators of broader population trends

---

## 5. Compound Risk Scorer (`scripts/compound_risk_scorer.py`)

### Purpose
Creates alternative risk scoring that captures multi-factor patterns potentially missed by standard health_risk_score. Tests different approaches to combining risk factors.

### Key Arguments & Methods

**Additive Method**:
```bash
--method additive      # Average individual factor multipliers
--factors stress_factors,lifestyle_factors    # Focus on specific factor groups
```

**Interaction-Weighted Method**:
```bash
--method interaction-weighted    # Add bonuses for known interactions
--factors stress_factors,lifestyle_factors,demographic_factors
```

**Factor Groups Available**:
- `stress_factors`: stress_calm, mood_positivity, depression_*
- `lifestyle_factors`: smoking, alcohol, exercise, nutrition, sleep  
- `demographic_factors`: age_group, gender, has_children, BMI
- `health_factors`: chronic_conditions, pain_level, health_perception
- `behavior_factors`: water, sugar, processed_food, supplements, steps

### When to Use

**Additive Method**: When you want to understand individual factor contributions clearly
**Interaction-Weighted**: When previous tools showed strong interaction effects
**Factor-Focused Analysis**: When you want to test specific risk theories (stress-only, lifestyle-only)

### Interpreting Results

**Most Interesting Findings**:
- **Perfect predictors**: Factors with 2.5x+ impact and 100% precision
- **Scoring mismatches**: Low compound score + actual high risk (hidden risk factors)
- **Threshold performance**: High precision + high recall combinations
- **Factor group differences**: Stress factors vs lifestyle factors impact

**Example Interesting Result**:
```
Threshold 1.5x: Flags 240 employees (24.0%)
Precision: 100.0% elevated risk | Recall: 71.2% elevated risk

Underestimated Risk Case:
• Compound score: 1.21 | Actual: high_risk  
  Profile: middle_adult, female, has_children, obese
```
**Why interesting**: Compound model missed a high-risk employee, suggesting hidden risk factors not captured in current scoring approach.

**Uninteresting/Ignore**:
- **Perfect correlations**: Score perfectly matches existing health_risk_score
- **Poor performance**: Low precision (<70%) or low recall (<50%)
- **Expected high-impact factors**: Stress having highest weight (obvious from EDA)
- **Uniform scoring**: All employees get similar compound scores

**Drilling Deeper Strategy**:
- Investigate underestimated cases: What factors are missing from compound model?
- Test alternative factor groupings: Does demographics-only scoring work better?
- Use mismatched predictions to identify new variables to collect

---

## Tool Selection Strategy

### For Initial Data Exploration
```bash
# Start here - always
python scripts/simple_eda.py --phase all --verbose

# Then identify 2-3 most surprising patterns and run:
python scripts/statistical_surprise.py --threshold 2.5
```

### For Hypothesis-Driven Analysis
```bash
# Form hypothesis from EDA: "Stress + age might interact"
python scripts/interaction_scanner.py --include stress_calm,age_group,health_risk_level --threshold 2.0

# Drill deeper: "Young adults with stress seem high risk - what characterizes them?"
python scripts/demographic_outlier_spotter.py --focus age_group,stress_calm --min-risk-ratio 2.0
```

### For Alternative Risk Perspectives
```bash
# Question: "Is our current risk score missing anything?"
python scripts/compound_risk_scorer.py --method additive --factors stress_factors,lifestyle_factors

# Follow-up: "What about interaction effects?"
python scripts/compound_risk_scorer.py --method interaction-weighted
```

## LLM Interpretation Guidelines

### What Makes Results LLM-Worthy

**Statistical Confidence**:
- Magnitude >2.5σ (surprises), >3x amplification (interactions), >2x risk ratio (outliers)
- Sample sizes >20 for business relevance
- Multiple related patterns supporting the same insight

**Practical Significance**:
- Actionable population sizes (10-100 employees for interventions)
- Clear rate differences (>15 percentage points)
- Counterintuitive findings that challenge assumptions

**Narrative Potential**:
- Clear cause-effect relationships
- Surprising combinations ("excellent nutrition + high risk")
- Perfect or near-perfect predictions (100% risk rates)

### What to Ignore as Uninteresting

**Statistical Noise**:
- Low magnitudes (<1.5σ, <1.8x amplification, <1.5x risk ratio)
- Tiny samples (<10 employees)
- Inconsistent patterns across similar analyses

**Expected Relationships**:
- Obvious correlations (smoking → health risk)
- Derived variable relationships (BMI ↔ weight)
- Monotonic age trends (older → more chronic conditions)

**Unreliable Patterns**:
- Single-occurrence anomalies
- Extreme outliers with no explaining characteristics
- Perfect correlations from data generation artifacts

## Progressive Analysis Workflow

### Stage 1: Foundation Discovery
```bash
# Understand the landscape
python scripts/simple_eda.py --phase all
python scripts/statistical_surprise.py --threshold 2.0
```
**Goal**: Identify 3-5 most surprising demographic or lifestyle patterns

### Stage 2: Interaction Investigation  
```bash
# Test specific hypotheses from Stage 1
python scripts/interaction_scanner.py --include [surprising_variables] --threshold 2.5
```
**Goal**: Understand how surprising patterns amplify through combinations

### Stage 3: Micro-Segment Focus
```bash
# Deep dive on specific populations
python scripts/demographic_outlier_spotter.py --focus [key_demographics] --min-risk-ratio 2.5
```
**Goal**: Identify actionable intervention targets

### Stage 4: Alternative Scoring
```bash
# Test if current risk model is complete
python scripts/compound_risk_scorer.py --method additive --factors [relevant_groups]
```
**Goal**: Validate existing risk assessment or identify missing factors

## LLM Analysis Decision Tree

### When Results Are Worth Investigating Further

**Strong Signal Indicators**:
- Multiple tools show related patterns for same subgroup
- High statistical confidence + large practical impact
- Counterintuitive findings that challenge assumptions
- Clear intervention opportunities

**Example Decision Logic**:
1. **EDA shows**: "Underweight employees have surprisingly high risk"
2. **Surprise detector confirms**: "16.7% vs 8.7% population (3.2σ magnitude)"
3. **Interaction scanner reveals**: "Underweight + excellent health perception = 30% high risk"
4. **Outlier spotter explains**: "40% don't exercise despite health perception"
5. **LLM conclusion**: Strong intervention signal with clear action path

### When to Stop Investigation

**Weak Signal Indicators**:
- Pattern appears in only one tool
- Small sample sizes across all analyses  
- No clear explaining characteristics
- Expected relationships without surprises

**Example Stop Logic**:
1. **EDA shows**: "Moderate correlation between exercise and BMI"
2. **Other tools**: No surprising amplifications or outliers
3. **LLM conclusion**: Expected relationship, not worth detailed narrative

## Advanced Usage Patterns

### Hypothesis Chain Testing
```bash
# Chain 1: Stress hypothesis
python scripts/statistical_surprise.py --threshold 2.5 | grep stress
python scripts/interaction_scanner.py --include stress_calm,mood_positivity,health_risk_level
python scripts/demographic_outlier_spotter.py --focus age_group,gender | grep stressed

# Chain 2: Lifestyle combination hypothesis  
python scripts/interaction_scanner.py --include smoking_status,alcohol_level,exercise_freq
python scripts/compound_risk_scorer.py --factors lifestyle_factors --method interaction-weighted
```

### Validation Cross-Checking
```bash
# Validate outlier with interaction analysis
python scripts/demographic_outlier_spotter.py --focus gender --min-risk-ratio 2.5
python scripts/interaction_scanner.py --include gender,stress_calm,health_risk_level

# Cross-validate compound scoring
python scripts/compound_risk_scorer.py --method additive 
python scripts/compound_risk_scorer.py --method interaction-weighted
```

### Progressive Refinement
```bash
# Broad discovery → focused analysis → micro-targeting
python scripts/statistical_surprise.py --threshold 2.0    # Find broad surprises
python scripts/interaction_scanner.py --include [surprise_vars] --threshold 3.0    # Focus on strongest
python scripts/demographic_outlier_spotter.py --focus [interaction_vars] --min-risk-ratio 3.0    # Micro-target
```

## Output Quality Indicators

### High-Quality LLM Inputs
- **Clear magnitude indicators**: 3.2σ, 11.5x, 2.7x risk ratio
- **Contextual comparisons**: Always vs population baseline
- **Sample size transparency**: (n=39), (n=84) for reliability assessment
- **Multiple supporting analyses**: Same pattern across different tools

### Red Flags for LLM Interpretation
- **Missing baselines**: Raw percentages without population comparison
- **Unclear sample sizes**: No reliability indicators
- **Isolated findings**: Pattern appears in only one analysis
- **Perfect correlations**: Likely derived variable relationships

## Tool Combination Strategies

### For Maximum Discovery
Run all tools in sequence with moderate thresholds to build comprehensive pattern map.

### For Focused Investigation  
Use `--include`/`--focus` filters across tools to drill deep on specific hypotheses.

### For Executive Reporting
Use high thresholds (3x+, 3.0σ+) to surface only most dramatic, reliable findings.

### For Intervention Planning
Focus on actionable segments (10-50 employees) with clear risk drivers and intervention pathways.

---

**Remember**: These tools surface patterns for LLM interpretation, not final answers. The goal is providing rich, statistically-grounded material for creating compelling, actionable insights about employee health risks.