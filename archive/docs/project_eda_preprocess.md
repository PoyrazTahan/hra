# Heltia HRA - LLM EDA Preprocessing Strategy

## Project Overview

**Objective**: Transform verbose Turkish health assessment data into LLM-optimized format while preserving clinical semantic meaning for descriptive analysis.

**Data Source**: Heltia Health Risk Assessment (HRA) questionnaire responses
- Original: 1000+ employee health records
- Language: Turkish with standardized health terminology
- Structure: Mixed categorical ordinal/nominal and continuous variables

## Current Data Challenges

### Token Inefficiency Issues
```text
Original: "Çok düşük (çoğunlukla oturuyor veya uzanıyorum)"
Tokens: ~12-15 tokens for simple activity level
```

### Semantic Complexity
- Long descriptive Turkish phrases
- Embedded parenthetical explanations
- Inconsistent scaling across question types
- Cultural/linguistic context requirements

## Preprocessing Strategy

### 1. **Categorical Standardization Framework**

#### **Frequency/Intensity Scales**
**Original**: "Hiçbir zaman" → "Çoğu zaman" → "Her zaman"  
**Optimized**: `never | rarely | sometimes | often | always`

```json
{
  "standardization_map": {
    "frequency_5_point": {
      "Hiçbir zaman": "never",
      "Bazen": "rarely", 
      "Geçen zamanın yarısından azında": "sometimes",
      "Geçen zamanın yarısından fazlasında": "often",
      "Çoğu zaman": "mostly",
      "Her zaman": "always"
    }
  }
}
```

#### **Activity Levels**
**Original**: "Çok düşük (çoğunlukla oturuyor veya uzanıyorum)"  
**Optimized**: `sedentary // Mostly sitting/lying`

```json
{
  "activity_levels": {
    "Çok düşük": "sedentary",
    "Düşük": "low", 
    "Orta": "moderate",
    "Yüksek": "high",
    "Çok yüksek": "very_high"
  }
}
```

### 2. **Health-Specific Transformations**

#### **Smoking Status** (Token Reduction: 70%)
```json
{
  "smoking_mapping": {
    "original": "Sosyal içiciyim (haftada birkaç gün)",
    "optimized": "social_smoker",
    "context": "// Weekly social smoking",
    "risk_level": "moderate"
  }
}
```

#### **Water Intake** (Preserve Clinical Ranges)
```json
{
  "water_intake": {
    "1-2 bardak (200-400 ml)": "very_low // <400ml",
    "3-4 bardak (600-800 ml)": "low // 600-800ml", 
    "5-6 bardak (1000-1200 ml)": "moderate // 1000-1200ml",
    "7-8 bardak (1400-1600 ml)": "good // 1400-1600ml",
    "8 bardaktan fazla (+1600 ml)": "high // >1600ml"
  }
}
```

### 3. **Structured Output Format**

#### **Individual Record Structure**
```json
{
  "participant": {
    "id": "P001",
    "demographics": {
      "age": 35,
      "age_group": "young_adult", 
      "gender": "male",
      "has_children": true
    }
  },
  "health_profile": {
    "mental": {
      "sleep_quality": "good // Usually refreshed mornings",
      "stress_level": "moderate // Sometimes calm and relaxed", 
      "mood": "positive // Generally happy and cheerful"
    },
    "physical": {
      "activity": "moderate // Daily walking, home exercises",
      "height_cm": 175,
      "weight_kg": 75,
      "bmi": 24.5,
      "bmi_category": "normal"
    },
    "lifestyle": {
      "smoking": "never",
      "water_intake": "good", 
      "sugar_frequency": "sometimes",
      "supplements": true
    }
  },
  "risk_profile": {
    "mental_health_score": "moderate",
    "physical_activity_score": "good",
    "lifestyle_score": "good",
    "overall_risk": "low"
  }
}
```

### 4. **Token Optimization Results**

| Category | Original Tokens | Optimized Tokens | Reduction |
|----------|----------------|------------------|-----------|
| Activity Level | 15-20 | 3-5 | 75% |
| Frequency Scales | 8-12 | 2-3 | 70% |
| Smoking Status | 10-15 | 3-4 | 73% |
| Water Intake | 12-18 | 4-6 | 67% |
| **Overall Average** | **11-16** | **3-5** | **70%** |

### 5. **Semantic Preservation Strategies**

#### **Contextual Comments**
- Use `//` comments for clinical context
- Include original units/ranges where critical
- Maintain severity/frequency relationships

#### **Hierarchical Grouping**
```json
{
  "mental_health": {
    "depression_risk": {
      "anhedonia": "low // Rarely lacks enjoyment", 
      "mood": "stable // Sometimes feels down",
      "severity": "minimal"
    },
    "stress_indicators": {
      "irritability": "moderate",
      "control": "good",
      "frequency": "sometimes"
    }
  }
}
```

### 6. **Quality Control Framework**

#### **Validation Rules**
1. **Logical Consistency**: High activity ↔ Good water intake
2. **Missing Data Handling**: `"unknown"` with reason codes
3. **Range Validation**: BMI, age, consumption within realistic bounds
4. **Cross-field Relationships**: Pregnancy status vs gender/age

#### **Clinical Accuracy**
- Maintain WHO/medical standard categorizations
- Preserve risk factor relationships
- Include population benchmark context

### 7. **LLM Analysis Optimization**

#### **Question-Specific Formatting**
```json
{
  "analysis_context": {
    "population": "Turkish corporate employees",
    "age_range": "18-65",
    "sample_size": 1000,
    "collection_period": "2024-2025"
  },
  "key_metrics": [
    "mental_health_prevalence",
    "lifestyle_risk_factors", 
    "physical_activity_patterns",
    "nutrition_quality_indicators"
  ]
}
```

#### **Anomaly Detection Tags**
```json
{
  "flags": {
    "extreme_bmi": ["P034", "P127"], 
    "contradictory_patterns": ["P089"], // High activity + poor habits
    "missing_critical_data": ["P156"]
  }
}
```

### 8. **Implementation Pipeline**

#### **Stage 1: Data Cleaning**
1. Handle Turkish character encoding
2. Standardize missing value representations
3. Validate data type consistency

#### **Stage 2: Semantic Mapping**
1. Apply categorical transformations
2. Generate derived metrics (BMI, risk scores)
3. Create hierarchical groupings

#### **Stage 3: Optimization**
1. Apply token reduction strategies
2. Add contextual metadata
3. Generate analysis-ready JSON

#### **Stage 4: Validation**
1. Health expert review of mappings
2. LLM comprehension testing
3. Statistical distribution validation

### 9. **Expected Outcomes**

#### **Token Efficiency**
- **70% reduction** in average tokens per record
- **Maintained semantic accuracy** for clinical analysis
- **Improved LLM comprehension** through structured format

#### **Analytical Benefits**
- Faster LLM processing and lower costs
- Consistent cross-record comparisons
- Enhanced pattern recognition capabilities
- Preserved clinical interpretability

#### **Scalability**
- Standardized preprocessing pipeline for new data
- Language-agnostic transformation framework
- Adaptable to additional health questionnaires

### 10. **Quality Metrics**

#### **Success Criteria**
1. **Token Reduction**: ≥65% while preserving meaning
2. **Clinical Accuracy**: 95%+ expert validation score
3. **LLM Comprehension**: Consistent analysis across models
4. **Processing Speed**: <500ms per 1000 records

#### **Monitoring KPIs**
- Preprocessing pipeline error rates
- Semantic drift detection over time
- Cross-model analysis consistency
- Expert validation scores

---

## Implementation Notes

### **Priority Order**
1. Core demographics and physical metrics (immediate impact)
2. Mental health indicators (clinical importance)
3. Lifestyle factors (risk correlation)
4. Extended questionnaire items (comprehensive analysis)

### **Rollout Strategy**
1. **Phase 1**: Implement on dummy data, validate with sample
2. **Phase 2**: Process full dataset, A/B test with original
3. **Phase 3**: Deploy to production EDA pipeline
4. **Phase 4**: Continuous monitoring and optimization

---
*Project Document | Version 1.0 | Heltia HRA Team*  
*Optimized for Turkish health data → LLM analysis pipeline*