import sqlite3
import pandas as pd
from datetime import datetime
import json
import os

DB_NAME = "measurements_v3.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_alias TEXT NOT NULL,
            date TEXT NOT NULL,
            weight REAL,
            body_score INTEGER,
            bmi REAL,
            body_fat_percentage REAL,
            body_water_mass REAL,
            fat_mass REAL,
            bone_mineral_mass REAL,
            protein_mass REAL,
            muscle_mass REAL,
            muscle_percentage REAL,
            body_water_percentage REAL,
            protein_percentage REAL,
            bone_mineral_percentage REAL,
            skeletal_muscle_mass REAL,
            visceral_fat_rating INTEGER,
            basal_metabolic_rate INTEGER,
            waist_to_hip_ratio REAL,
            body_age INTEGER,
            fat_free_body_weight REAL,
            heart_rate INTEGER,
            raw_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_measurement(user_alias, data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract all values safely
    def get_val(key):
        return data.get(key, None)

    c.execute('''
        INSERT INTO measurements (
            user_alias, date, weight, body_score, bmi, body_fat_percentage, 
            body_water_mass, fat_mass, bone_mineral_mass, protein_mass, 
            muscle_mass, muscle_percentage, body_water_percentage, 
            protein_percentage, bone_mineral_percentage, skeletal_muscle_mass, 
            visceral_fat_rating, basal_metabolic_rate, waist_to_hip_ratio, 
            body_age, fat_free_body_weight, heart_rate, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_alias, date_str, get_val('weight'), get_val('body_score'), get_val('bmi'), 
        get_val('body_fat_percentage'), get_val('body_water_mass'), get_val('fat_mass'), 
        get_val('bone_mineral_mass'), get_val('protein_mass'), get_val('muscle_mass'), 
        get_val('muscle_percentage'), get_val('body_water_percentage'), get_val('protein_percentage'), 
        get_val('bone_mineral_percentage'), get_val('skeletal_muscle_mass'), get_val('visceral_fat_rating'), 
        get_val('basal_metabolic_rate'), get_val('waist_to_hip_ratio'), get_val('body_age'), 
        get_val('fat_free_body_weight'), get_val('heart_rate'), json.dumps(data)
    ))
    
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT DISTINCT user_alias FROM measurements ORDER BY user_alias')
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_user_data(user_alias):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM measurements WHERE user_alias = ? ORDER BY date ASC"
    df = pd.read_sql_query(query, conn, params=(user_alias,))
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df
