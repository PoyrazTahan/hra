#!/usr/bin/env python3
"""
Simple CSV preprocessor for HRA data
Processes raw data, creates one-hot encoding, calculates scores and derived features
"""

import pandas as pd
import json
import os
import re

# Configuration
INPUT_FILE = "00_init_data/HRA_data.csv"
OUTPUT_FILE = "./01_in/HRA_data.csv"
COMPANY_OUTPUT_DIR = "./01_in/company/"
MAPPINGS_FILE = "mappings/value_mappings.json"

def load_mappings():
    """Load value mappings"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mappings_path = os.path.join(script_dir, MAPPINGS_FILE)

    with open(mappings_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def sanitize_company_name(name):
    """Sanitize company name for use in file paths."""
    if pd.isna(name) or str(name).strip() in ['#N/A', '']:
        return 'Unknown_Company'
    # Remove special characters, convert spaces to underscores
    sanitized = re.sub(r'[^\w\s-]', '', str(name))
    sanitized = re.sub(r'[\s-]+', '_', sanitized)
    return sanitized.strip('_')


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

def process_multi_selection_new_format(df, column_prefix, mappings):
    """Process MultiSelection fields in new format (A.chronic_conditions.0, A.chronic_conditions.1, etc.)"""
    base_column = column_prefix.split('.')[0] + '.' + column_prefix.split('.')[1]

    if base_column not in mappings:
        return

    field_info = mappings[base_column]
    if 'english' not in field_info['mappings']:
        return

    english_map = field_info['mappings']['english']
    binary_values = field_info['mappings']['binary_values']
    baseline_options = ['Hayır yok']  # Exclude baseline

    # Find all chronic condition columns
    chronic_columns = [col for col in df.columns if col.startswith(column_prefix)]

    # Combine all chronic condition values into a list for each row
    def combine_conditions(row):
        conditions = []
        for col in chronic_columns:
            if pd.notna(row[col]) and str(row[col]).strip():
                conditions.append(str(row[col]).strip())
        return conditions

    combined_conditions = df[chronic_columns].apply(combine_conditions, axis=1)

    # Create columns for non-baseline options with meaningful string values
    for turkish_option, english_name in english_map.items():
        if turkish_option not in baseline_options:
            new_col_name = f"{english_name}_status"

            has_value = binary_values[turkish_option]['1']
            no_value = binary_values[turkish_option]['0']

            # Check if option is selected and assign meaningful string
            df[new_col_name] = combined_conditions.apply(
                lambda conditions: has_value if turkish_option in conditions else no_value
            )

    # Remove original columns
    df.drop(columns=chronic_columns, inplace=True)

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

def calculate_bmi_category(df):
    """Calculate BMI categories from existing A.bmi column"""
    bmi_col = 'A.bmi'

    if bmi_col in df.columns:
        # Use existing A.bmi column instead of calculating
        df['bmi_category'] = pd.cut(df[bmi_col],
                                   bins=[0, 18.5, 25, 30, float('inf')],
                                   labels=['underweight', 'normal_weight', 'overweight', 'obese'])
        print(f"Created bmi_category from existing {bmi_col} column")
    else:
        print(f"Warning: {bmi_col} column not found, bmi_category not created")

def calculate_age_groups(df):
    """Calculate age groups"""
    age_col = 'A.age' if 'A.age' in df.columns else 'Data.age'

    if age_col in df.columns:
        df['age_group'] = pd.cut(df[age_col],
                                bins=[0, 25, 35, 45, 55, 100],
                                labels=['young', 'young_adult', 'middle_adult', 'mature', 'senior'])

def calculate_risk_levels(df):
    """Calculate health risk levels"""
    total_score_col = None
    if 'Evaluation.TotalScore' in df.columns:
        total_score_col = 'Evaluation.TotalScore'
    elif 'Total_Health_Score' in df.columns:
        total_score_col = 'Total_Health_Score'

    if total_score_col:
        df['health_risk_level'] = pd.cut(df[total_score_col],
                                        bins=[0, 25, 50, 75, 100],
                                        labels=['very_high_risk', 'high_risk', 'moderate_risk', 'low_risk'],
                                        include_lowest=True)

def save_company_specific_data(df):
    """Save company-specific CSV files using CorporateId and CorporateName"""
    # Check for required columns
    if 'CorporateId' not in df.columns or 'CorporateName' not in df.columns:
        print("Warning: CorporateId/CorporateName columns not found. Skipping company-specific data generation.")
        return

    # Create company output directory
    os.makedirs(COMPANY_OUTPUT_DIR, exist_ok=True)

    # Handle #N/A or missing values - group together as Unknown_Company
    na_mask = df['CorporateId'].isna() | (df['CorporateId'] == '#N/A') | (df['CorporateId'].astype(str).str.strip() == '#N/A')
    if na_mask.any():
        unknown_df = df[na_mask].copy()
        unknown_file = os.path.join(COMPANY_OUTPUT_DIR, "Unknown_Company.csv")
        unknown_df.to_csv(unknown_file, index=False)
        print(f"Saved {len(unknown_df)} records for Unknown_Company to {unknown_file}")

    # Process known companies
    valid_df = df[~na_mask].copy()

    for corporate_id in valid_df['CorporateId'].unique():
        if pd.notna(corporate_id):
            company_df = valid_df[valid_df['CorporateId'] == corporate_id].copy()

            # Get company name (should be consistent per CorporateId)
            corporate_name = company_df['CorporateName'].iloc[0]
            sanitized_name = sanitize_company_name(corporate_name)

            # Create filename: Corporate_{full_id}_{sanitized_name}.csv
            company_file_name = f"Corporate_{corporate_id}_{sanitized_name}.csv"
            company_file = os.path.join(COMPANY_OUTPUT_DIR, company_file_name)

            company_df.to_csv(company_file, index=False)
            print(f"Saved {len(company_df)} records for {corporate_name} (ID: {corporate_id}) to {company_file}")

def main():
    print("Processing HRA data...")
    
    # Load data and mappings
    df = pd.read_csv(INPUT_FILE)
    mappings = load_mappings()
    
    print(f"Loaded {len(df)} records")
    
    # Keep Evaluation columns as target variables
    evaluation_columns = [col for col in df.columns if col.startswith('Evaluation.')]

    # Process each column based on its type
    for column_name in list(df.columns):
        if column_name.startswith('A.') and column_name in mappings:
            field_info = mappings[column_name]
            answer_field = field_info['answer_field']

            if answer_field == 'SingleSelection':
                process_single_selection(df, column_name, mappings)
            elif answer_field == 'FreeForm':
                process_free_form(df, column_name)

    # Handle chronic conditions separately (new format)
    if any(col.startswith('A.chronic_conditions.') for col in df.columns):
        process_multi_selection_new_format(df, 'A.chronic_conditions.', mappings)

    # Remove timestamp columns but keep ID columns for tracking
    columns_to_remove = ['CompletedDate']
    for col in columns_to_remove:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)
    
    # Calculate derived features
    calculate_bmi_category(df)
    calculate_age_groups(df)
    calculate_risk_levels(df)
    
    # Create output directory
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Save complete processed data
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved processed data to {OUTPUT_FILE}")
    print(f"Final dataset: {len(df)} records, {len(df.columns)} columns")

    # Save company-specific data
    save_company_specific_data(df)
    print(f"Saved company-specific data to {COMPANY_OUTPUT_DIR}")

if __name__ == "__main__":
    main()