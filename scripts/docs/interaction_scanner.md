# Interaction Scanner Documentation

## Overview

The Interaction Scanner (`scripts/interaction_scanner.py`) discovers variable combinations that create unexpected health risk patterns. It finds when employee characteristics interact to amplify or reduce health risks beyond what individual factors would predict.

## Core Concept: Risk Amplification

**Risk Amplification** = How much a combination increases risk compared to population baseline.

**Example**:

- Population baseline: 8.7% employees are high risk
- "High stress" alone: 15% high risk = **1.7x amplification**
- "High stress + Young age": 35% high risk = **4.0x amplification**
- "High stress + Excellent nutrition": 45% high risk = **5.2x amplification** (surprising!)

## What the Tool Finds

### Risk Amplifiers (1+1=5 effects)

Combinations where risks compound unexpectedly:

- "Mostly stressed + Non-smoker" = 100% high risk (11.5x baseline)
- "Underweight + High activity" = 67% high risk (7.7x baseline)

### Protective Combinations (1+1=0 effects)

Combinations that unexpectedly reduce risk:

- "Sometimes stressed + Regular exercise" = 0% high risk (full protection)
- "Social smoker + Good nutrition" = 2% high risk (4x protection)

### Counterintuitive Patterns

Combinations that defy common assumptions:

- "Excellent nutrition + High stress" = still 100% high risk (nutrition doesn't protect)
- "No exercise + Good sleep" = 0% high risk (sleep compensates for inactivity)

## Command Line Arguments

### Basic Usage

```bash
# Test all meaningful variables (default)
python scripts/interaction_scanner.py --data preprocessed_data/HRA_data.csv
```

### Variable Control

```bash
# Test specific variables only
--include stress_calm,smoking_status,age_group,health_risk_level

# Exclude specific variables (test everything else)
--exclude bmi,weight_kg,height_cm

# Exclude derived fields to focus on survey responses
--exclude bmi,bmi_category,health_risk_score,age_group
```

### Sensitivity Control

```bash
# Find more patterns (lower threshold)
--threshold 1.2    # Shows 1.2x+ amplifications (many results)

# Find only extreme patterns (higher threshold)
--threshold 3.0    # Shows 3x+ amplifications (few, dramatic results)

# Require larger sample sizes for reliability
--min-sample 20    # Need 20+ employees in each combination
```

### Output Control

```bash
# Save results for LLM processing
--output interactions.json

# See detailed analysis steps
--verbose
```

## Analytical Workflow

### Stage 1: Broad Discovery

**Goal**: Understand the interaction landscape

```bash
python scripts/interaction_scanner.py --threshold 1.5
```

**Outcome**: See all meaningful amplifications (100+ results)
**Use**: Identify which variable pairs are worth deeper investigation

### Stage 2: Focused Investigation

**Goal**: Test specific hypotheses from Stage 1

```bash
python scripts/interaction_scanner.py --include stress_calm,age_group,health_risk_level --threshold 2.5
```

**Outcome**: Detailed analysis of stress×age interactions (10-20 results)
**Use**: Understand how stress affects different age groups

### Stage 3: Extreme Pattern Detection

**Goal**: Find only the most dramatic interactions

```bash
python scripts/interaction_scanner.py --include stress_calm,mood_positivity,smoking_status,health_risk_level --threshold 4.0
```

**Outcome**: Only combinations with 4x+ risk amplification (5-10 results)
**Use**: Identify highest-priority intervention targets

## LLM Integration Strategy

### Step 1: LLM Reviews EDA Output

LLM reads `simple_eda_output.txt` and identifies:

- Variables with surprising individual patterns
- Demographic groups with outlier behavior
- Health factors with strong correlations

### Step 2: LLM Generates Hypotheses

Based on EDA review, LLM forms hypotheses like:

- "Stress seems to be the strongest predictor - what amplifies it?"
- "Underweight employees have high risk - what combinations make it worse?"
- "Pregnant employees show elevated risk - what specific factors drive this?"

### Step 3: LLM Runs Targeted Analysis

```bash
# Test stress amplification hypothesis
python scripts/interaction_scanner.py --include stress_calm,age_group,exercise_freq,health_risk_level

# Test underweight risk factors
python scripts/interaction_scanner.py --include bmi_category,nutrition_quality,exercise_freq,health_risk_level

# Test pregnancy risk drivers
python scripts/interaction_scanner.py --include has_children,stress_calm,sleep_duration,health_risk_level
```

### Step 4: LLM Creates Narrative

LLM transforms technical results into engaging insights:

- **Technical**: "mostly_stressed + young_adult = 100% high risk (11.5x baseline, n=23)"
- **Narrative**: "Every single young adult reporting high stress levels is classified as high health risk - a perfect storm combination affecting 23 employees"

## Argument Strategy Guide

### For Exploratory Analysis

- Use **default settings** or `--threshold 1.5` to see the full landscape
- Add `--verbose` to understand what's being tested
- Don't use include/exclude initially

### For Hypothesis Testing

- Use `--include` with 3-5 specific variables you want to test
- Increase `--threshold` to 2.0+ for cleaner results
- Focus on combinations that surprised you in broad analysis

### For Report Generation

- Use `--threshold 3.0+` for only the most dramatic findings
- Add `--output results.json` for LLM processing
- Use `--min-sample 20+` for higher reliability claims

### For Debugging/Understanding

- Add `--verbose` to see filtering decisions
- Lower `--threshold` to 1.2 to catch subtle patterns
- Use `--include` with just 2-3 variables for clearer output

## Output Interpretation

**High Amplification**: Combinations worth investigating for intervention
**Protective Patterns**: Combinations worth promoting as best practices
**Sample Sizes**: Larger samples (n=50+) are more reliable for business decisions
**Baseline Context**: Always compare to population baseline for meaningful interpretation
