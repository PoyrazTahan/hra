#!/usr/bin/env python3
"""
Simple CSV preprocessor for HRA data
Processes raw data, creates one-hot encoding, calculates scores and derived features
"""

import pandas as pd
import json
import os

# Configuration
INPUT_FILE = "HRA_Answers_tab.csv"
OUTPUT_FILE = "../preprocessed_data/HRA_data.csv"
MAPPINGS_FILE = "mappings/value_mappings.json"

def load_mappings():
    """Load value mappings"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mappings_path = os.path.join(script_dir, MAPPINGS_FILE)
    
    with open(mappings_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def process_single_selection(df, column_name, mappings):
    """Process SingleSelection fields"""
    field_info = mappings[column_name]
    if 'english' in field_info['mappings']:
        english_map = field_info['mappings']['english']
        df[column_name] = df[column_name].map(
            lambda x: english_map.get(str(x).strip(), str(x).lower().replace(' ', '_'))
        )

def process_multi_selection(df, column_name, mappings):
    """Process MultiSelection fields with meaningful string values"""
    field_info = mappings[column_name]
    if 'english' not in field_info['mappings']:
        return

    english_map = field_info['mappings']['english']
    binary_values = field_info['mappings']['binary_values']
    baseline_options = ['Hayır yok']  # Exclude baseline

    # Create columns for non-baseline options with meaningful string values
    for turkish_option, english_name in english_map.items():
        if turkish_option not in baseline_options:
            new_col_name = f"{english_name}_status"

            has_value = binary_values[turkish_option]['1']
            no_value = binary_values[turkish_option]['0']

            # Check if option is selected and assign meaningful string
            df[new_col_name] = df[column_name].apply(
                lambda x: has_value if is_option_selected(x, turkish_option) else no_value
            )

    # Remove original column
    df.drop(columns=[column_name], inplace=True)

def is_option_selected(value, option):
    """Check if option is selected in multi-choice answer"""
    if pd.isna(value):
        return False
    
    value_str = str(value).strip()
    if value_str.startswith('[') and value_str.endswith(']'):
        selected_options = [opt.strip() for opt in value_str[1:-1].split(',')]
        return option in selected_options
    return False

def process_free_form(df, column_name):
    """Process FreeForm fields (convert to numeric)"""
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')

def calculate_bmi(df):
    """Calculate BMI and categories"""
    if 'Data.height' in df.columns and 'Data.weight' in df.columns:
        height_m = df['Data.height'] / 100
        df['bmi'] = (df['Data.weight'] / (height_m ** 2)).round(2)
        df['bmi_category'] = pd.cut(df['bmi'], 
                                   bins=[0, 18.5, 25, 30, float('inf')],
                                   labels=['underweight', 'normal_weight', 'overweight', 'obese'])

def calculate_age_groups(df):
    """Calculate age groups"""
    if 'Data.age' in df.columns:
        df['age_group'] = pd.cut(df['Data.age'],
                                bins=[0, 25, 35, 45, 55, 100],
                                labels=['young', 'young_adult', 'middle_adult', 'mature', 'senior'])

def calculate_risk_levels(df):
    """Calculate health risk levels"""
    if 'Total_Health_Score' in df.columns:
        df['health_risk_level'] = pd.cut(df['Total_Health_Score'],
                                        bins=[0, 25, 50, 75, 100],
                                        labels=['very_high_risk', 'high_risk', 'moderate_risk', 'low_risk'],
                                        include_lowest=True)

def main():
    print("Processing HRA data...")
    
    # Load data and mappings
    df = pd.read_csv(INPUT_FILE)
    mappings = load_mappings()
    
    print(f"Loaded {len(df)} records")
    
    # Rename Total_Score to Total_Health_Score
    if 'Total_Score' in df.columns:
        df['Total_Health_Score'] = df['Total_Score']
        df.drop(columns=['Total_Score'], inplace=True)
    
    # Process each column based on its type
    for column_name in list(df.columns):
        if column_name.startswith('Data.') and column_name in mappings:
            field_info = mappings[column_name]
            answer_field = field_info['answer_field']
            
            if answer_field == 'SingleSelection':
                process_single_selection(df, column_name, mappings)
            elif answer_field == 'MultiSelection':
                process_multi_selection(df, column_name, mappings)
            elif answer_field == 'FreeForm':
                process_free_form(df, column_name)
    
    # Calculate derived features
    calculate_bmi(df)
    calculate_age_groups(df)
    calculate_risk_levels(df)
    
    # Save processed data
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved processed data to {OUTPUT_FILE}")
    print(f"Final dataset: {len(df)} records, {len(df.columns)} columns")

if __name__ == "__main__":
    main()