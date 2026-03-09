from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- Semua Model yang Terdaftar ---")
for model in client.models.list():
    # Kita cetak nama dan semua kemampuan (capabilities) agar kita tahu model mana yang bisa dipakai
    print(f"Model: {model.name}")
    print(f"  - Supported methods: {model.supported_methods}")
    print("-" * 30)
