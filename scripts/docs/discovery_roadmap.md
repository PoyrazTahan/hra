# Discovery Tools Roadmap - Health Risk Assessment EDA

## Overview

This roadmap outlines advanced discovery tools to build on top of the existing `simple_eda.py` pipeline. Instead of pre-defining employee archetypes, these tools surface statistical anomalies and unexpected patterns for LLM interpretation and storytelling.

## Core Philosophy

**Discovery-First Approach**: Let the data reveal surprising patterns rather than imposing predetermined categories. Each tool outputs LLM-optimized insights with statistical confidence and contextual baselines.

## Tool Specifications

### 1. Statistical Surprise Detector

**Purpose**: Identifies subgroups where observed outcomes significantly differ from population expectations.

**Technical Approach**:
- Calculate expected rates for each outcome across demographic subgroups
- Measure deviation using standardized residuals from chi-square tests
- Flag subgroups with |standardized residual| > 2.0 (statistical surprise threshold)
- Rank surprises by effect size and sample size reliability

**Implementation Strategy**:
```python
def detect_statistical_surprises(df, outcome_vars, demographic_vars):
    surprises = []
    for outcome in outcome_vars:
        for demo in demographic_vars:
            contingency = pd.crosstab(df[demo], df[outcome])
            chi2, p, dof, expected = chi2_contingency(contingency)
            
            # Calculate standardized residuals
            std_residuals = (contingency - expected) / np.sqrt(expected)
            
            # Find cells with |residual| > 2.0
            surprise_cells = np.where(np.abs(std_residuals) > 2.0)
            
            for i, j in zip(*surprise_cells):
                # Extract surprise details and context
                surprises.append({
                    'subgroup': f"{demo}={contingency.index[i]}",
                    'outcome': f"{outcome}={contingency.columns[j]}",
                    'observed_rate': contingency.iloc[i,j] / contingency.iloc[i].sum(),
                    'expected_rate': expected[i,j] / contingency.iloc[i].sum(),
                    'surprise_magnitude': std_residuals.iloc[i,j],
                    'sample_size': contingency.iloc[i].sum()
                })
```

**LLM Output Format**:
```
STATISTICAL SURPRISES (Observed vs Expected):
- Underweight employees: 16.7% high risk (expected: 8.7%, magnitude: +3.2σ)
- Other gender: 23.5% high risk (expected: 8.7%, magnitude: +4.1σ)
- Pregnant + high stress: 89% moderate-high risk (expected: 33%, magnitude: +5.7σ)
```

### 2. Interaction Effect Scanner

**Purpose**: Discovers non-obvious combinations where variables amplify or suppress each other's effects.

**Technical Approach**:
- Systematic testing of 2-way and 3-way variable interactions
- Compare compound effects vs additive expectations
- Use log-linear models to detect interaction terms
- Focus on interactions with practical significance (effect size > 0.2)

**Implementation Strategy**:
```python
def scan_interaction_effects(df, variables, outcome):
    interactions = []
    
    # 2-way interactions
    for var1, var2 in combinations(variables, 2):
        # Create interaction term
        df['interaction'] = df[var1].astype(str) + "_X_" + df[var2].astype(str)
        
        # Test if interaction explains variance beyond main effects
        contingency = pd.crosstab(df['interaction'], df[outcome])
        
        # Calculate interaction strength vs main effects
        main_effect_strength = calculate_main_effects(var1, var2, outcome)
        interaction_strength = calculate_cramers_v(contingency)
        
        if interaction_strength > main_effect_strength + 0.1:  # Meaningful interaction
            interactions.append({
                'variables': f"{var1} × {var2}",
                'interaction_strength': interaction_strength,
                'top_combinations': get_top_risk_combinations(contingency)
            })
```

**LLM Output Format**:
```
INTERACTION DISCOVERIES:
- Stress × Sleep Quality: Combined effect 2.3x stronger than individual effects
  > "High stress + Poor sleep" = 67% high risk (vs 23% for high stress alone)
- Exercise × Nutrition: Protective interaction detected
  > "No exercise + Poor nutrition" = 34% high risk (vs 19% for no exercise alone)
```

### 3. Demographic Outlier Spotter

**Purpose**: Automatically finds small demographic segments with outsized health impacts.

**Technical Approach**:
- Segment population by demographic combinations
- Flag segments with <5% population share but >2x risk rates
- Calculate risk ratios with confidence intervals
- Prioritize by both magnitude and reliability

**Implementation Strategy**:
```python
def spot_demographic_outliers(df, demographics, outcomes, min_sample_size=10):
    outliers = []
    
    # Generate all meaningful demographic combinations
    for demo_combo in generate_demographic_combinations(demographics):
        segment_filter = create_segment_filter(df, demo_combo)
        segment_size = segment_filter.sum()
        
        if segment_size >= min_sample_size:
            segment_df = df[segment_filter]
            
            for outcome in outcomes:
                risk_rate = calculate_risk_rate(segment_df, outcome)
                population_rate = calculate_risk_rate(df, outcome)
                risk_ratio = risk_rate / population_rate
                
                if risk_ratio > 2.0 and segment_size/len(df) < 0.05:  # Small but high-risk
                    outliers.append({
                        'segment': demo_combo,
                        'size_pct': segment_size/len(df)*100,
                        'risk_rate': risk_rate,
                        'risk_ratio': risk_ratio,
                        'outcome': outcome
                    })
```

### 4. Lifecycle Risk Transition Mapper

**Purpose**: Identifies when life stage transitions amplify health risks.

**Technical Approach**:
- Map risk progression across age groups
- Detect accelerated risk patterns at transition points
- Test for interaction between life stage and other factors

**Implementation Strategy**:
- Age group risk velocity analysis
- Children status × age interaction effects
- Career stage proxy analysis (using stress + activity patterns)

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
1. **Statistical Surprise Detector** - Builds directly on existing chi-square analysis
2. **Integration with simple_eda.py** - Add as `--phase 3` option
3. **LLM-optimized output formatting** - Structured insights with confidence scores

### Phase 2: Advanced Discovery (Week 2)
1. **Interaction Effect Scanner** - Systematic combination testing
2. **Demographic Outlier Spotter** - Micro-segment analysis
3. **Enhanced statistical rigor** - Multiple testing corrections, confidence intervals

### Phase 3: Lifecycle Analysis (Week 3)
1. **Transition Risk Mapper** - Age-based pattern evolution
2. **Compound scoring algorithms** - Multi-factor risk amplification
3. **Insight prioritization engine** - Rank discoveries by practical significance

## Technical Architecture

### Data Flow
```
Existing EDA Output → Discovery Tools → LLM-Ready Insights → Narrative Generation
     Phase 1&2      →   Phase 3      →   Structured JSON   →   HR Reports
```

### Output Structure for LLM Consumption
```json
{
  "statistical_surprises": [
    {
      "pattern": "Underweight employees show unexpectedly high risk",
      "magnitude": 3.2,
      "confidence": "high",
      "subgroup_size": 84,
      "comparison": "16.7% vs 8.7% population average"
    }
  ],
  "interaction_effects": [...],
  "demographic_outliers": [...],
  "actionable_insights": [
    {
      "insight": "Small demographic groups driving disproportionate risk",
      "evidence": ["Other gender: 2.7x risk", "Pregnant employees: 4.2x risk"],
      "sample_reliability": "medium"
    }
  ]
}
```

### Integration Points

**Extends current pipeline**:
- Phase 1: Existing 1D statistics (foundation)
- Phase 2: Existing cross-patterns (relationships)  
- **Phase 3**: New discovery tools (surprises and anomalies)
- **Phase 4**: LLM narrative generation (insights and stories)

**File Structure**:
```
scripts/
├── simple_eda.py           # Existing foundation
├── discovery_tools.py      # New statistical surprise tools
├── pattern_scanner.py      # Interaction and outlier detection
└── insight_formatter.py    # LLM-optimized output generation
```

## Success Metrics

**For Discovery Tools**:
- Number of statistically significant surprises detected
- Diversity of pattern types discovered
- Reliability of small-sample insights

**For LLM Consumption**:
- Clear insight categorization and prioritization
- Statistical confidence indicators
- Contextual comparisons for interpretation
- Structured format enabling narrative generation

## Next Steps

The most straightforward starting point is the **Statistical Surprise Detector** since it leverages your existing chi-square infrastructure but adds the "unexpectedness" layer that makes patterns LLM-worthy.

Should we begin implementing the Statistical Surprise Detector as a new phase in your existing pipeline?