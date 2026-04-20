import os
from dotenv import load_dotenv
import json
import base64
import requests

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

def extract_health_data_from_image(image_path: str):
    """
    Calls Gemini API via direct REST request to extract health metrics.
    """
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    try:
        # Read and encode image
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        prompt = (
            "Analyze this Xiaomi body composition test result image. "
            "Extract all the values as numbers (floats). "
            "If a value is missing or you cannot read it confidently, set it to 0. "
            "Do not include units, just the numeric values. "
            "Return ONLY a valid JSON dictionary with these EXACT keys (and no others): "
            "body_weight, body_score, bmi, body_fat_percentage, body_water_mass, "
            "fat_mass, bone_mineral_mass, protein_mass, muscle_mass, muscle_percentage, "
            "body_water_percentage, protein_percentage, bone_mineral_percentage, "
            "skeletal_muscle_mass, visceral_fat_rating, basal_metabolic_rate, "
            "estimated_waist_to_hip_ratio, body_age, fat_free_body_weight, heart_rate."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": encoded_string
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print("Gemini API Error:", response.text)
            return None
            
        result_json = response.json()
        
        try:
            text = result_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            print("Unexpected response structure:", result_json)
            return None
            
        data = json.loads(text)
        
        required_keys = [
            "body_weight", "body_score", "bmi", "body_fat_percentage", "body_water_mass",
            "fat_mass", "bone_mineral_mass", "protein_mass", "muscle_mass", "muscle_percentage",
            "body_water_percentage", "protein_percentage", "bone_mineral_percentage",
            "skeletal_muscle_mass", "visceral_fat_rating", "basal_metabolic_rate",
            "estimated_waist_to_hip_ratio", "body_age", "fat_free_body_weight", "heart_rate"
        ]
        
        final_data = {}
        for key in required_keys:
            val = data.get(key)
            try:
                final_data[key] = float(val) if val is not None else 0.0
            except:
                final_data[key] = 0.0
                
        return final_data

    except Exception as e:
        print(f"Error during extraction: {e}")
        return None
