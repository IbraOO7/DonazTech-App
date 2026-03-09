import os
import math
import json
from google import genai
from databases.config import SessionLocal
from databases.models.charity import Charity
from services.config import configs

client = genai.Client(api_key=configs.GEMINI_API_KEY)

def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371  
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def match_charity(user_query):
    db = SessionLocal()
    try:
        charities = db.query(Charity).all()
        charity_texts = "\n".join([f"ID: {c.id} | Nama: {c.name} | Deskripsi: {c.description}" for c in charities])
        prompt = f"""
        Berikut adalah daftar yayasan:
        {charity_texts}
        
        User mencari: "{user_query}"
        
        Pilih 1 yayasan yang paling cocok dan berikan alasan singkat. 
        Berikan format JSON: {{"id": 1, "alasan": "..."}}
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text 
    finally:
        db.close()

def match_charity_by_geo(user_lat, user_lng, user_query, radius_km=15):
    db = SessionLocal()
    try:
        user_lat, user_lng = float(user_lat), float(user_lng)
        all_charities = db.query(Charity).all()
        nearby_charities = []
        
        for c in all_charities:
            if c.lat is not None and c.lng is not None:
                dist = calculate_haversine(user_lat, user_lng, float(c.lat), float(c.lng))
                if dist <= radius_km:
                    nearby_charities.append({
                        "id": c.id,
                        "name": c.name,
                        "lat": float(c.lat),
                        "lng": float(c.lng),
                        "distance": round(dist, 2)
                    })

        return nearby_charities 

    except Exception as e:
        return []
    finally:
        db.close()