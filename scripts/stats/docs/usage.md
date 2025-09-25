# Health Risk Assessment Analysis - LLM Usage Guide

## Current Analysis Status

**✅ Base Analysis Complete**: All foundation-level analyses have been automatically executed and saved in the `outputs/` folder. You have comprehensive statistical insights ready for review.

**Your Starting Point**: Read the analysis results to understand employee health patterns, then decide whether to drill deeper with focused analysis or synthesize insights into executive-ready reports.

---

## Step 1: Review Base Analysis Results

### Read Files in Order:
```
outputs/0_foundation_eda.txt        # Start here - complete statistical foundation
outputs/1_statistical_surprises.txt # Unexpected demographic/lifestyle patterns  
outputs/2_interaction_effects.txt   # Variable combinations that amplify risks
outputs/3_demographic_outliers.txt  # Small segments with disproportionate impacts
outputs/4_compound_scoring_additive.txt     # Alternative risk scoring validation
outputs/5_compound_scoring_interaction.txt  # Interaction-aware risk scoring
outputs/analysis_index.json        # Quick navigation and key statistics
```

### What to Look For While Reading:
- **Statistical surprises with high magnitude** (>3.0σ) and good sample sizes (>30)
- **Interaction amplifications >3x baseline** with clear patterns
- **Demographic outliers with >2.5x risk ratios** and actionable segment sizes
- **Compound scoring mismatches** indicating missing risk factors
- **Counterintuitive findings** that challenge health assumptions

---

## Step 2: Choose Your Next Action

You have **three paths** forward:

### Path A: Focused Analysis (Drill Deeper)
**When to choose**: You found 2-3 specific patterns that warrant deeper investigation

**Tools for focused drilling** (see `tools.md` for detailed usage):

#### **Hypothesis Testing with Interaction Scanner**
```bash
# Test specific variable interactions based on base findings
python scripts/interaction_scanner.py --include [variables_from_base] --threshold 3.0

# Examples based on typical base findings:
python scripts/interaction_scanner.py --include stress_calm,age_group,health_risk_level --threshold 2.5
python scripts/interaction_scanner.py --include smoking_status,alcohol_level,bmi_category --threshold 2.0
```

#### **Micro-Segment Investigation with Outlier Spotter**  
```bash
# Deep dive on specific demographics that showed anomalies
python scripts/demographic_outlier_spotter.py --focus [demographics] --min-risk-ratio 2.5

# Examples for common outliers:
python scripts/demographic_outlier_spotter.py --focus gender,has_children --min-risk-ratio 2.5
python scripts/demographic_outlier_spotter.py --focus age_group,bmi_category --max-size 3.0
```

#### **Alternative Risk Model Testing**
```bash
# Test specific factor groups based on base insights
python scripts/compound_risk_scorer.py --factors stress_factors,lifestyle_factors --method additive
python scripts/compound_risk_scorer.py --factors demographic_factors --method interaction-weighted
```

### Path B: Employee Archetype Creation (Clustering)
**When to choose**: You want to create comprehensive employee risk profiles and archetypes

**Manual Clustering Approach** (using existing tools):

#### Step 1: Identify Clustering Variables
```bash
# Review compound scorer high-impact factors
grep "Impact.*x baseline" outputs/4_compound_scoring_additive.txt

# Typical high-impact variables for clustering:
# - stress_calm, mood_positivity (perfect predictors)
# - smoking_status, chronic_conditions (strong amplifiers)  
# - age_group, bmi_category (demographic differentiators)
```

#### Step 2: Discover Natural Segments
```bash
# Find existing natural breakpoints in data
python scripts/demographic_outlier_spotter.py --focus stress_calm,smoking_status,age_group --min-risk-ratio 1.5

# Test key variable interactions for archetype boundaries
python scripts/interaction_scanner.py --include stress_calm,mood_positivity,smoking_status,age_group,health_risk_level --threshold 2.0
```

#### Step 3: Define Employee Archetypes
Based on discovery tool outputs, manually define 4-6 archetypes such as:
- **High-Stress Achievers**: High stress + good health behaviors + young/middle age
- **Lifestyle Risk Veterans**: Multiple risk factors + older age + chronic conditions
- **Wellness-Focused Workers**: Low stress + excellent health behaviors + protective factors
- **Hidden Risk Carriers**: Surprising combinations (excellent nutrition + high risk)

#### Step 4: Validate and Profile Archetypes
```bash
# For each defined archetype, validate using focused analysis:
python scripts/interaction_scanner.py --include [archetype_variables] --threshold 2.5
python scripts/demographic_outlier_spotter.py --focus [archetype_demographics] --min-risk-ratio 2.0
```

### Path C: Insight Synthesis (Executive Report)
**When to choose**: Base analysis revealed clear patterns sufficient for stakeholder insights

**Create executive summary focusing on**:
- **Top 3-5 most surprising findings** with business implications
- **Actionable micro-segments** for intervention programs  
- **Risk amplification patterns** worth addressing
- **Protective combinations** worth promoting
- **Employee archetype summaries** if clustering was performed
- **Clear narratives** that translate statistics into compelling employee stories

---

## Decision Framework

### Choose **Focused Analysis** (Path A) if:
- **Multiple related anomalies**: Same variables appearing across different analyses
- **Counterintuitive patterns**: Findings that challenge health assumptions
- **Actionable segments identified**: 10-50 employee groups with clear intervention opportunities
- **Strong amplification effects**: >5x baseline amplifications worth understanding better

### Choose **Employee Archetype Creation** (Path B) if:
- **Comprehensive employee profiling needed**: Stakeholders want to understand distinct employee types
- **Multiple risk factors cluster together**: Discovery tools show variables that naturally group
- **Intervention program design**: Need clearly defined target populations for wellness programs
- **Complex patterns require simplification**: Too many individual findings need organizing into coherent profiles

### Choose **Insight Synthesis** (Path C) if:
- **Clear story emerges**: Base analysis provides sufficient evidence for compelling narratives
- **Executive reporting needed**: Stakeholders want actionable insights, not more statistics
- **Intervention priorities clear**: You can identify top 3-5 employee health priorities
- **Limited drilling value**: Additional analysis unlikely to change conclusions

---

## Report Synthesis Guidelines

When creating executive insights, focus on:

### **High-Impact Findings**
- **Perfect predictors**: Variables with 100% accuracy (e.g., "Every highly stressed employee is high-risk")
- **Hidden populations**: Small segments with major risk concentration (e.g., "1.7% of workforce accounts for 23.5% of high-risk cases")
- **Counterintuitive patterns**: Findings that surprise (e.g., "Employees with excellent nutrition still show high risk when stressed")

### **Actionable Insights**
- **Intervention targets**: Specific demographic segments (10-100 employees) with clear risk drivers
- **Program opportunities**: Protective combinations that can be promoted organization-wide
- **Resource allocation**: Where limited wellness resources would have maximum impact

### **Compelling Narratives**
Transform statistical findings into stories:
- **Technical**: "mostly_stressed employees show 100% high risk (24.18σ magnitude, n=61)"
- **Narrative**: "Every single employee reporting high stress levels is classified as high health risk - a perfect storm pattern affecting 61 employees across all demographics"

### **Business Context**
- **Population impact**: How many employees are affected
- **Risk magnitudes**: How much higher than normal (2x, 5x, 10x)
- **Intervention feasibility**: Whether findings suggest clear action paths
- **Cost implications**: Resource requirements for addressing identified risks

---

## Example Follow-Up Scenarios

### Scenario 1: Stress Dominates Everything
**Base findings**: Stress appears in top 5 surprises, all interactions, multiple outliers
**Next action**: Deep dive with interaction scanner
```bash
python scripts/interaction_scanner.py --include stress_calm,mood_positivity,age_group,health_risk_level --threshold 2.5
```

### Scenario 2: Multiple Demographic Anomalies  
**Base findings**: Gender, pregnancy, BMI outliers with different patterns
**Next action**: Targeted demographic investigation
```bash
python scripts/demographic_outlier_spotter.py --focus gender,has_children,bmi_category --min-risk-ratio 2.0
```

### Scenario 3: Clear Executive Story
**Base findings**: Obvious patterns, strong amplifications, clear intervention targets
**Next action**: Synthesize report focusing on top 3-5 actionable insights with business impact

---

## Key Resources

- **Detailed tool usage**: Read `tools.md` for comprehensive argument explanations and interpretation guidelines
- **Analysis philosophy**: Review `discovery_roadmap.md` for strategic approach understanding
- **Technical implementation**: Check individual scripts for advanced customization options

---

## Your Mission

Transform statistical discoveries into actionable employee health insights that drive meaningful wellness program improvements. Whether through deeper analysis or executive synthesis, your goal is creating compelling, evidence-based narratives that help stakeholders understand and act on employee health patterns.

**Start by reading the base analysis results, then choose your path forward.**