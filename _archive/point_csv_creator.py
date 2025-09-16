import csv
import json
import re

def find_english_translation(turkish_answer, slug, value_mappings):
    """Find English translation for Turkish answer based on question slug"""
    # Try to find mapping for this specific slug
    if slug in value_mappings and 'mappings' in value_mappings[slug]:
        if turkish_answer in value_mappings[slug]['mappings']:
            return value_mappings[slug]['mappings'][turkish_answer]
    
    # If no direct mapping found, search all categories as fallback
    for category, data in value_mappings.items():
        if 'mappings' in data:
            for turkish, english in data['mappings'].items():
                if turkish == turkish_answer:
                    return english
    
    return ""  # Return empty string if no translation found

def parse_csv_and_create_points():
    # Read the questions CSV
    questions_data = []
    with open('questions/HRA_Questions_added.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions_data.append(row)
    
    # Read value mappings
    with open('mappings/value_mappings.json', 'r', encoding='utf-8') as f:
        value_mappings = json.load(f)
    
    # Process the data to create points.csv
    points_data = []
    
    for row in questions_data:
        slug = row['Slug']
        possible_answers = row['PossibleAnswers'].strip()
        scores = row['Score'].strip()
        
        if not possible_answers or not scores:
            continue
            
        # Split answers and scores by newlines
        answers = [answer.strip() for answer in possible_answers.split('\n') if answer.strip()]
        score_lines = [score.strip() for score in scores.split('\n') if score.strip()]
        
        # Extract numeric scores from score lines (remove * prefix)
        numeric_scores = []
        for score_line in score_lines:
            if score_line.startswith('*'):
                try:
                    numeric_score = float(score_line[1:].strip())
                    numeric_scores.append(numeric_score)
                except ValueError:
                    continue
        
        # Match answers with scores
        for i, answer in enumerate(answers):
            if i < len(numeric_scores):
                score = numeric_scores[i]
                english_answer = find_english_translation(answer, slug, value_mappings)
                points_data.append({
                    'slug': slug,
                    'PossibleAnswer': answer,
                    'PossibleAnswerEnglish': english_answer,
                    'Score': score
                })
    
    # Write to points.csv
    with open('points.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['slug', 'PossibleAnswer', 'PossibleAnswerEnglish', 'Score']
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(points_data)
    
    print(f"Created points.csv with {len(points_data)} entries")
    
    # Print a sample of the data for verification
    print("\nFirst 10 entries:")
    for i, point in enumerate(points_data[:10]):
        print(f"{i+1}. {point}")

if __name__ == "__main__":
    parse_csv_and_create_points()