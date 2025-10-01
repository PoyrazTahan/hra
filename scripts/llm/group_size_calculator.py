#!/usr/bin/env python3
"""
Group Size Calculator for Health Insights

Calculates the actual number of employees represented by each insight
based on health_tags and demographic_tags using the source CSV data.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class GroupSizeCalculator:
    """Calculate target group sizes for insights based on CSV data filtering."""

    def __init__(self, csv_path: str, mappings_path: str = None):
        """
        Initialize calculator with CSV data and value mappings.

        Args:
            csv_path: Path to the preprocessed CSV data
            mappings_path: Path to value_mappings.json (optional, uses default if not provided)
        """
        self.csv_path = Path(csv_path)
        self.df = pd.read_csv(self.csv_path)

        # Load value mappings
        if mappings_path is None:
            mappings_path = Path(__file__).parent.parent.parent / "00_init_data" / "mappings" / "value_mappings.json"
        else:
            mappings_path = Path(mappings_path)

        with open(mappings_path, 'r') as f:
            self.value_mappings = json.load(f)

        # Build reverse mapping: tag → (column_name, tag_value)
        self.tag_to_column = self._build_tag_to_column_mapping()

    def _build_tag_to_column_mapping(self) -> Dict[str, Tuple[str, str]]:
        """
        Build reverse mapping from tag values to (column_name, value).

        Returns:
            Dict mapping tag → (column_name, tag_value)
            Example: "daily_smoker" → ("A.smoking_status", "daily_smoker")
        """
        tag_map = {}

        for column_name, config in self.value_mappings.items():
            # Skip non-health columns
            if column_name in ['SponsorId']:
                continue

            mappings = config.get('mappings', {})

            # Handle regular english mappings
            if 'english' in mappings:
                for original_value, tag_value in mappings['english'].items():
                    tag_map[tag_value] = (column_name, tag_value)

            # Handle binary_values for chronic conditions
            if 'binary_values' in mappings:
                for condition, binary_map in mappings['binary_values'].items():
                    for status, tag_value in binary_map.items():
                        # Map to the status column (e.g., diabetes_status)
                        if condition == 'Diabet':
                            column = 'diabetes_status'
                        elif condition == 'Tiroid':
                            column = 'thyroid_disorder_status'
                        elif condition == 'Böbrek':
                            column = 'kidney_disease_status'
                        elif condition == 'Kalp':
                            column = 'heart_disease_status'
                        elif condition == 'Obezite':
                            column = 'obesity_status'
                        elif condition == 'Hipertansiyon':
                            column = 'hypertension_status'
                        elif condition == 'Kanser':
                            column = 'cancer_status'
                        elif condition == 'Diğer':
                            column = 'other_condition_status'
                        else:
                            continue

                        # Map the tag to the status column
                        tag_map[tag_value] = (column, tag_value)

        # Handle bmi_category separately (computed column)
        # These are created during preprocessing
        for bmi_tag in ['underweight', 'normal_weight', 'overweight', 'obese']:
            tag_map[bmi_tag] = ('bmi_category', bmi_tag)

        return tag_map

    def calculate_group_size(
        self,
        health_tags: List[str],
        demographic_tags: List[str]
    ) -> Dict[str, any]:
        """
        Calculate the size of the target group defined by tags.

        Args:
            health_tags: List of health-related tags
            demographic_tags: List of demographic tags

        Returns:
            Dict with:
                - size: Number of employees matching all tags (AND logic)
                - percentage: Percentage of total population
                - filters_applied: List of (column, value) filters used
                - total_population: Total number of employees in dataset
        """
        # Combine all tags
        all_tags = health_tags + demographic_tags

        if not all_tags:
            return {
                'size': len(self.df),
                'percentage': 100.0,
                'filters_applied': [],
                'total_population': len(self.df),
                'note': 'No filters applied - represents entire population'
            }

        # Build filters grouped by column
        # Key insight: Use OR logic within same column, AND logic between columns
        column_filters = {}
        unknown_tags = []

        for tag in all_tags:
            if tag in self.tag_to_column:
                column_name, tag_value = self.tag_to_column[tag]

                # Check if column exists in dataframe
                if column_name in self.df.columns:
                    if column_name not in column_filters:
                        column_filters[column_name] = []
                    column_filters[column_name].append(tag_value)
                else:
                    unknown_tags.append(f"{tag} (column {column_name} not found)")
            else:
                unknown_tags.append(tag)

        # Apply filters: OR within column, AND between columns
        filtered_df = self.df.copy()

        for column_name, tag_values in column_filters.items():
            # Use .isin() for OR logic within the same column
            filtered_df = filtered_df[filtered_df[column_name].isin(tag_values)]

        # Calculate results
        group_size = len(filtered_df)
        total_population = len(self.df)
        percentage = (group_size / total_population * 100) if total_population > 0 else 0.0

        # Build human-readable filter descriptions
        filters_applied = []
        for column_name, tag_values in column_filters.items():
            if len(tag_values) == 1:
                filters_applied.append(f"{column_name}={tag_values[0]}")
            else:
                # Multiple values from same column - show as OR
                values_str = " OR ".join(tag_values)
                filters_applied.append(f"{column_name} IN ({values_str})")

        result = {
            'size': int(group_size),
            'percentage': round(percentage, 2),
            'filters_applied': filters_applied,
            'total_population': int(total_population)
        }

        if unknown_tags:
            result['unknown_tags'] = unknown_tags

        return result

    def calculate_sizes_for_insights(self, insights: List[Dict]) -> List[Dict]:
        """
        Calculate group sizes for all insights and add to each insight.

        Args:
            insights: List of insight dictionaries

        Returns:
            List of insights with added 'target_group' field
        """
        for insight in insights:
            health_tags = insight.get('health_tags', [])
            demographic_tags = insight.get('demographic_tags', [])

            group_info = self.calculate_group_size(health_tags, demographic_tags)

            # Add to insight
            insight['target_group'] = group_info

        return insights


def main():
    """CLI interface for testing the calculator."""
    import argparse

    parser = argparse.ArgumentParser(description='Calculate group sizes for health insights')
    parser.add_argument('csv_path', help='Path to the CSV data file')
    parser.add_argument('--health-tags', nargs='*', default=[], help='Health tags to filter by')
    parser.add_argument('--demographic-tags', nargs='*', default=[], help='Demographic tags to filter by')

    args = parser.parse_args()

    calculator = GroupSizeCalculator(args.csv_path)
    result = calculator.calculate_group_size(args.health_tags, args.demographic_tags)

    print("\nGroup Size Calculation Results:")
    print("=" * 60)
    print(f"Target group size: {result['size']} employees")
    print(f"Percentage of population: {result['percentage']}%")
    print(f"Total population: {result['total_population']}")
    print(f"\nFilters applied (AND logic):")
    for filter_str in result['filters_applied']:
        print(f"  - {filter_str}")

    if 'unknown_tags' in result:
        print(f"\n⚠️  Unknown tags (not mapped):")
        for tag in result['unknown_tags']:
            print(f"  - {tag}")


if __name__ == '__main__':
    main()