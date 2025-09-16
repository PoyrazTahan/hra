#!/usr/bin/env python3
"""
Health Risk Assessment Dummy Data Generator for Heltia
Generates realistic dummy data for 1000 employees with anomalies and edge cases
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_correlated_demographics():
    """Generate correlated demographic data"""
    demographics = []
    
    for i in range(1000):
        # Generate age with realistic distribution
        age = int(np.random.normal(35, 12))
        age = max(18, min(65, age))  # Clamp between 18-65
        
        # Gender distribution
        gender_weights = [0.45, 0.45, 0.08, 0.02]  # Erkek, Kadın, Belirtmek istemiyorum, Diğer
        gender = np.random.choice(['Erkek', 'Kadın', 'Belirtmek istemiyorum', 'Diğer'], p=gender_weights)
        
        # Children status correlated with age
        if age < 25:
            has_children_prob = 0.15
        elif age < 30:
            has_children_prob = 0.35
        elif age < 40:
            has_children_prob = 0.65
        else:
            has_children_prob = 0.75
            
        # Special case: pregnancy only for women
        if gender == 'Kadın' and age < 45 and random.random() < 0.03:
            has_children = 'Hamileyim'
        else:
            has_children = np.random.choice(['Hayır', 'Evet'], 
                                          p=[1-has_children_prob, has_children_prob])
        
        demographics.append({
            'age': age,
            'gender': gender,
            'has_children': has_children
        })
    
    return demographics

def generate_physical_metrics(demographics):
    """Generate height and weight with realistic distributions"""
    physical_data = []
    
    for demo in demographics:
        gender = demo['gender']
        age = demo['age']
        
        # Height distribution by gender
        if gender == 'Erkek':
            height = int(np.random.normal(175, 8))
            height = max(150, min(200, height))
        else:  # Kadın or other
            height = int(np.random.normal(162, 7))
            height = max(140, min(185, height))
        
        # Weight correlated with height and age
        bmi_mean = 24 + (age - 30) * 0.1  # Slight increase with age
        bmi = np.random.normal(bmi_mean, 4)
        bmi = max(16, min(45, bmi))  # Realistic BMI range
        
        weight = int(bmi * (height/100)**2)
        
        physical_data.append({
            'height': height,
            'weight': weight
        })
    
    return physical_data

def generate_mental_health_scores():
    """Generate correlated mental health responses"""
    mental_data = []
    
    frequency_options = ['Hiçbir zaman', 'Bazen', 'Geçen zamanın yarısından azında', 
                        'Geçen zamanın yarısından fazlasında', 'Çoğu zaman', 'Her zaman']
    
    for i in range(1000):
        # Create a base mental health score (0-1)
        mental_health_base = np.random.beta(2, 1.5)  # Slightly skewed toward better health
        
        # Sleep quality (inverse correlation with stress)
        sleep_index = int(mental_health_base * 5)
        sleep_quality = frequency_options[sleep_index]
        
        # Stress level (inverse of mental health)
        stress_index = int((1 - mental_health_base) * 5)
        stress_level = frequency_options[stress_index]
        
        # Mood level (correlated with mental health)
        mood_index = int(mental_health_base * 5)
        mood_level = frequency_options[mood_index]
        
        mental_data.append({
            'sleep_quality': sleep_quality,
            'stress_level': stress_level,
            'mood_level': mood_level
        })
    
    return mental_data

def generate_activity_and_nutrition(demographics, physical_data):
    """Generate activity and nutrition data with correlations"""
    lifestyle_data = []
    
    activity_levels = [
        'Çok düşük (çoğunlukla oturuyor veya uzanıyorum)',
        'Düşük (kısa mesafeleri yürüyor, ara sıra ayakta duruyorum)',
        'Orta (her gün düzenli yürüyüş veya basit ev egzersizleri yapıyorum)',
        'Yüksek (işe-okula yürüyor, merdiven kullanıyor, hobi olarak spor yapıyorum)',
        'Çok yüksek (düzenli yoğun egzersiz veya spor yapıyorum)'
    ]
    
    sugar_frequency = ['Hiç', '1-2 gün', '3-4 gün', '5-6 gün', 'Her gün']
    water_intake = ['1-2 bardak (200-400 ml)', '3-4 bardak (600-800 ml)', 
                   '5-6 bardak (1000-1200 ml)', '7-8 bardak (1400-1600 ml)', 
                   '8 bardaktan fazla (+1600 ml)']
    
    for i, (demo, physical) in enumerate(zip(demographics, physical_data)):
        age = demo['age']
        bmi = physical['weight'] / (physical['height']/100)**2
        
        # Activity level correlated with age and BMI
        if age < 30 and bmi < 25:
            activity_prob = [0.05, 0.15, 0.30, 0.35, 0.15]
        elif bmi > 30:
            activity_prob = [0.25, 0.35, 0.25, 0.10, 0.05]
        else:
            activity_prob = [0.10, 0.25, 0.35, 0.25, 0.05]
            
        activity_level = np.random.choice(activity_levels, p=activity_prob)
        
        # Sugar intake (inverse correlation with activity)
        if 'Çok yüksek' in activity_level:
            sugar_prob = [0.30, 0.40, 0.20, 0.08, 0.02]
        elif 'Çok düşük' in activity_level:
            sugar_prob = [0.05, 0.20, 0.30, 0.30, 0.15]
        else:
            sugar_prob = [0.15, 0.30, 0.30, 0.20, 0.05]
            
        sugar_intake = np.random.choice(sugar_frequency, p=sugar_prob)
        
        # Water intake (correlated with activity)
        if 'yüksek' in activity_level.lower():
            water_prob = [0.05, 0.15, 0.25, 0.35, 0.20]
        else:
            water_prob = [0.15, 0.25, 0.30, 0.20, 0.10]
            
        water_level = np.random.choice(water_intake, p=water_prob)
        
        lifestyle_data.append({
            'activity_level': activity_level,
            'sugar_intake': sugar_intake,
            'water_intake': water_level
        })
    
    return lifestyle_data

def generate_smoking_and_supplements(demographics):
    """Generate smoking and supplement usage"""
    habits_data = []
    
    smoking_options = ['Hayır', 'Sosyal içiciyim (haftada birkaç gün)', 
                      'Günde 3-4 tane', 'Günde yarım paket', 
                      'Günde 1 paket', 'Günde 1 paketten fazla']
    supplement_options = ['Hayır', 'Evet']
    
    for demo in demographics:
        age = demo['age']
        gender = demo['gender']
        
        # Smoking correlated with age and gender
        if age < 25:
            smoking_prob = [0.70, 0.20, 0.05, 0.03, 0.015, 0.005]
        elif age > 50:
            smoking_prob = [0.60, 0.15, 0.10, 0.08, 0.06, 0.01]
        else:
            smoking_prob = [0.65, 0.18, 0.08, 0.05, 0.03, 0.01]
            
        smoking_status = np.random.choice(smoking_options, p=smoking_prob)
        
        # Supplement usage (higher in women and older adults)
        if gender == 'Kadın' and age > 40:
            supplement_prob = 0.7
        elif age > 50:
            supplement_prob = 0.6
        else:
            supplement_prob = 0.4
            
        supplement_usage = np.random.choice(supplement_options, 
                                          p=[1-supplement_prob, supplement_prob])
        
        habits_data.append({
            'smoking_status': smoking_status,
            'supplement_usage': supplement_usage
        })
    
    return habits_data

def add_anomalies_and_edge_cases(data_df):
    """Add realistic anomalies and edge cases to the dataset"""
    anomaly_indices = random.sample(range(len(data_df)), 50)  # 5% anomalies
    
    for idx in anomaly_indices:
        anomaly_type = random.choice(['extreme_bmi', 'contradiction', 'extreme_age', 'unusual_habits'])
        
        if anomaly_type == 'extreme_bmi':
            # Create extreme BMI cases
            data_df.loc[idx, 'weight'] = random.choice([40, 45, 150, 160])  # Very low or very high
            
        elif anomaly_type == 'contradiction':
            # High activity but poor health indicators
            data_df.loc[idx, 'activity_level'] = 'Çok yüksek (düzenli yoğun egzersiz veya spor yapıyorum)'
            data_df.loc[idx, 'sugar_intake'] = 'Her gün'
            data_df.loc[idx, 'smoking_status'] = 'Günde 1 paket'
            
        elif anomaly_type == 'extreme_age':
            # Very young or old employees
            data_df.loc[idx, 'age'] = random.choice([18, 19, 62, 65])
            
        elif anomaly_type == 'unusual_habits':
            # Unusual combinations
            data_df.loc[idx, 'water_intake'] = '1-2 bardak (200-400 ml)'
            data_df.loc[idx, 'activity_level'] = 'Çok yüksek (düzenli yoğun egzersiz veya spor yapıyorum)'
    
    # Add some missing data (realistic scenario)
    missing_indices = random.sample(range(len(data_df)), 20)  # 2% missing data
    missing_columns = ['height', 'weight', 'water_intake']
    
    for idx in missing_indices:
        col = random.choice(missing_columns)
        data_df.loc[idx, col] = np.nan
    
    return data_df

def generate_additional_questions_data():
    """Generate data for additional questions from HRA_Questions_added.csv"""
    additional_data = []
    
    # Perceived health
    perceived_health_options = ['Hiç iyi hissetmiyorum', 'Pek iyi hissetmiyorum', 
                               'Ne iyi ne kötü', 'Oldukça iyi hissediyorum', 
                               'Çok iyi ve zinde hissediyorum']
    
    # Depression indicators
    depression_options = ['Hiç yaşamadım', 'Ara sıra', 'Çoğu gün', 'Neredeyse her gün']
    
    # Stress indicators  
    stress_options = ['Hiçbir zaman', 'Neredeyse hiçbir zaman', 'Bazen', 
                     'Oldukça sık', 'Çok sık']
    
    # Loneliness
    loneliness_options = ['Hiçbir zaman', 'Nadiren', 'Ara sıra', 'Bazen', 'Sık sık / Her zaman']
    
    # Sleep hours
    sleep_hours_options = ['6 saatten az', '6-7 saat', '7-9 saat', '9-10 saat', '10 saatten fazla']
    
    # Exercise frequency
    exercise_options = ['Hiç yapmıyorum', 'Haftada 1 gün', 'Haftada 2–3 gün', 
                       'Haftada 4–5 gün', 'Haftada 5 günden fazla']
    
    # Daily steps
    steps_options = ['2.500 adımdan az', '2.500 - 5.000 adım', '5.000 - 7.500 adım', 
                    '7.500 -10.000 adım', '10.000\'dan fazla']
    
    # Physical pain
    pain_options = ['Hiç ağrım olmadı', 'Ağrım günlük işlerimi etkilemedi', 
                   'Ağrım günlük işlerimi biraz etkiledi', 
                   'Ağrım günlük işlerimi orta derecede etkiledi', 
                   'Ağrım günlük işlerimi belirgin şekilde etkiledi', 
                   'Ağrım günlük işlerimi ciddi şekilde kısıtladı']
    
    # Fruit/vegetable intake
    fruit_veg_options = ['Günde 1 porsiyondan az veya hiç', 'Günde 1-2 porsiyon', 
                        'Günde 3 porsiyon', 'Günde 4 porsiyon', 'Günde 5 porsiyondan fazla']
    
    # Weekly frequency options
    weekly_freq_options = ['Haftada1 veya hiç', 'Haftada 2', 'Haftada 3', 
                          'Haftada 4', 'Haftada 5 veya daha fazla']
    
    # Alcohol consumption
    alcohol_options = ['Hiç içmiyorum', '1–6 kadeh', '7–9 kadeh', '10–20 kadeh', 
                      '21–30 kadeh', '31–50 kadeh', '50+ kadeh']
    
    # Smoking status (expanded)
    smoking_expanded = ['Hiç kullanmadım', 'Uzun zaman önce bıraktım', 
                       'Sosyal içiciyim, bazen kullanıyorum', 'Sık sık kullanıyorum', 
                       'Her gün kullanıyorum']
    
    # Chronic conditions
    chronic_conditions = ['Hayır yok', 'Diabet', 'Tiroid', 'Böbrek', 'Kalp', 
                         'Obezite', 'Hipertansiyon', 'Kanser', 'Diğer']
    
    for i in range(1000):
        # Create correlations based on existing mental health data
        mental_health_score = random.random()
        
        # Perceived health
        if mental_health_score > 0.8:
            perceived_health = np.random.choice(perceived_health_options, 
                                              p=[0.02, 0.08, 0.15, 0.35, 0.40])
        elif mental_health_score < 0.3:
            perceived_health = np.random.choice(perceived_health_options, 
                                              p=[0.25, 0.35, 0.25, 0.10, 0.05])
        else:
            perceived_health = np.random.choice(perceived_health_options, 
                                              p=[0.05, 0.15, 0.35, 0.35, 0.10])
        
        # Depression indicators (correlated)
        if mental_health_score < 0.3:
            depression_anhedonia = np.random.choice(depression_options, p=[0.20, 0.30, 0.30, 0.20])
            depression_mood = np.random.choice(depression_options, p=[0.15, 0.35, 0.30, 0.20])
        else:
            depression_anhedonia = np.random.choice(depression_options, p=[0.60, 0.30, 0.08, 0.02])
            depression_mood = np.random.choice(depression_options, p=[0.65, 0.25, 0.08, 0.02])
        
        additional_data.append({
            'perceived_health': perceived_health,
            'depression_anhedonia': depression_anhedonia,
            'depression_mood': depression_mood,
            'stress_level_irritability': np.random.choice(stress_options),
            'stress_level_loc': np.random.choice(stress_options),
            'loneliness': np.random.choice(loneliness_options),
            'sleep_hours': np.random.choice(sleep_hours_options),
            'activity_level': np.random.choice(exercise_options),
            'daily_steps': np.random.choice(steps_options),
            'physical_pain': np.random.choice(pain_options),
            'fruit_veg_intake': np.random.choice(fruit_veg_options),
            'processed_food_intake': np.random.choice(weekly_freq_options),
            'alcohol_consumption': np.random.choice(alcohol_options),
            'smoking_status_expanded': np.random.choice(smoking_expanded),
            'chronic_conditions': np.random.choice(chronic_conditions)
        })
    
    return additional_data

def main():
    print("Generating Heltia HRA Dummy Data...")
    
    # Generate all data components
    demographics = generate_correlated_demographics()
    physical_data = generate_physical_metrics(demographics)
    mental_data = generate_mental_health_scores()
    lifestyle_data = generate_activity_and_nutrition(demographics, physical_data)
    habits_data = generate_smoking_and_supplements(demographics)
    additional_data = generate_additional_questions_data()
    
    # Create DataFrame
    data = []
    for i in range(1000):
        user_id = str(uuid.uuid4())[:24]  # MongoDB-style ID
        record_id = str(uuid.uuid4())[:24]
        
        record = {
            '_id': record_id,
            'UserId': user_id,
            **demographics[i],
            **physical_data[i],
            **mental_data[i],
            **lifestyle_data[i],
            **habits_data[i],
            **additional_data[i]
        }
        data.append(record)
    
    df = pd.DataFrame(data)
    
    # Add anomalies
    df = add_anomalies_and_edge_cases(df)
    
    # Reorder columns to match existing data structure
    column_order = ['_id', 'UserId', 'sleep_quality', 'activity_level', 'water_intake', 
                   'height', 'has_children', 'stress_level', 'sugar_intake', 'weight', 
                   'smoking_status', 'mood_level', 'gender', 'supplement_usage', 'age']
    
    # Add additional columns
    additional_cols = [col for col in df.columns if col not in column_order]
    final_column_order = column_order + additional_cols
    
    df = df[final_column_order]
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"HRA_dummy_data_{timestamp}.csv"
    df.to_csv(filename, index=False)
    
    print(f"✅ Generated {len(df)} records with realistic correlations and anomalies")
    print(f"📁 Saved as: {filename}")
    print(f"🔍 Dataset includes:")
    print(f"   - {len([x for x in df['gender'] if x == 'Erkek'])} men, {len([x for x in df['gender'] if x == 'Kadın'])} women")
    print(f"   - Age range: {df['age'].min()}-{df['age'].max()} years")
    print(f"   - BMI range: {(df['weight']/(df['height']/100)**2).min():.1f}-{(df['weight']/(df['height']/100)**2).max():.1f}")
    print(f"   - Missing data points: {df.isnull().sum().sum()}")
    print(f"   - Includes realistic anomalies and edge cases")
    
    # Display sample data
    print("\n📊 Sample records:")
    print(df[['age', 'gender', 'height', 'weight', 'activity_level', 'smoking_status']].head())
    
    return df

if __name__ == "__main__":
    dummy_data = main()