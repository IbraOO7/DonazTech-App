import requests
from ddgs import DDGS
from google import genai
from google.genai import types
from services.backgroundtasks.make_celery import app
from databases.config import SessionLocal
from services.ai_matchmaker import match_charity_by_geo
from databases.models.user import User
from databases.models.services import ZakatConsultation
from databases.models.charity import Charity
from google.genai.errors import ClientError 
from services.config import configs
from brevo import Brevo
from brevo.transactional_emails import (
    SendTransacEmailRequestSender,
    SendTransacEmailRequestToItem,
)
import traceback
import json

client = genai.Client(api_key=configs.GEMINI_API_KEY)

def web_search(query: str):
    try:
        enhanced_query = f"{query} address lat lng coordinates"
        with DDGS() as ddgs:
            results = list(ddgs.text(enhanced_query, max_results=3))
            return str(results)
    except Exception as e:
        return f"Gagal mencari: {str(e)}"

def get_gold_price():
    try:
        response = requests.get("https://api.logamulia.com/v1/price", timeout=5)
        return {"price": response.json().get('price', 1250000)}
    except Exception:
        return {"price": 1250000}

tools = [
    {
        "function_declarations": [
            {
                "name": "web_search",
                "description": "Mencari informasi terkini di internet.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {"query": {"type": "STRING"}},
                    "required": ["query"]
                }
            },
            {
                "name": "get_gold_price",
                "description": "Mengambil harga emas per gram terkini.",
                "parameters": {"type": "OBJECT", "properties": {}}
            }
        ]
    }
]

@app.task(name="process_zakat_ai")
def process_zakat_ai(consultation_id, user_query, lat=None, lng=None):
    db = SessionLocal()
    try:
        charities = match_charity_by_geo(lat, lng, user_query) if lat else []
        charity_str = json.dumps(charities) if charities else "Tidak ada yayasan terdekat."
        system_prompt = (
            "Anda adalah Konsultan Zakat Ahli. "
            "Data yayasan terdekat: {charities}. "
            "TUGAS: Berikan jawaban ringkas, padat, dan teknis (langsung ke perhitungan). "
            "WAJIB: Masukkan data yayasan tersebut ke dalam field JSON 'locations'. "
            "Format JSON murni tanpa markdown: {{\"jawaban\": \"string\", \"locations\": [...]}}"
        ).format(charities=charity_str)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            tools=tools,
            max_output_tokens=3000
        )
        
        # 3. Eksekusi Request Pertama
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_query,
            config=config
        )

        # 4. Handle Function Call (Web Search/Gold Price)
        if response.function_calls:
            call = response.function_calls[0]
            if call.name == "web_search":
                result = web_search(call.args.get('query', user_query))
            elif call.name == "get_gold_price":
                result = get_gold_price()
            else:
                result = "Tool tidak ditemukan"
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part.from_text(text=user_query)]),
                    response.candidates[0].content,
                    types.Content(role="function", parts=[
                        types.Part.from_function_response(name=call.name, response={"result": result})
                    ])
                ]
            )

        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        try:
            data = json.loads(raw_text)
            if 'zakat_calculation' in data:
                calc = data['zakat_calculation']
                text = f"**{calc.get('title', 'Perhitungan')}**<br>{calc.get('description')}<br><br>"
                text += f"Nisab: {calc.get('nisab_amount')}<br>Zakat: {calc.get('zakat_percentage')}<br><br>"
                text += f"Contoh: {calc.get('example_calculation')}"
                data['jawaban'] = text
            if 'locations' not in data or not data['locations']:
                data['locations'] = charities[:3]
            ai_text = json.dumps(data)
        except (json.JSONDecodeError, ValueError):
            ai_text = json.dumps({
                "jawaban": raw_text, 
                "locations": charities[:3]
            })

        # 6. Simpan ke Database
        consult = db.query(ZakatConsultation).filter(ZakatConsultation.id == consultation_id).first()
        if consult:
            consult.ai_response = ai_text
            db.commit()
            
        return ai_text
    
    except ClientError as e:
        if e.code == 429:
            consult = db.query(ZakatConsultation).get(consultation_id)
            if consult:
                consult.ai_response = json.dumps({"jawaban": "LIMIT_EXCEEDED", "locations": []})
                db.commit()
            return 

    except Exception as e:
        db.rollback()
        print(f"DEBUG FATAL ERROR: {traceback.format_exc()}")
        return json.dumps({"jawaban": "Maaf, sistem sedang sibuk.", "locations": []})
    finally:
        db.close()

@app.task(name="send_thank_you_email")
def send_thank_you_email(user_email, amount, category):
    client = Brevo(api_key=configs.API_KEY_BREVO)
    
    try:
        client.transactional_emails.send_transac_email(
            sender=SendTransacEmailRequestSender(
                email=configs.SMTP_EMAIL,
                name="DonazTech AI Team"
            ),
            to=[
                SendTransacEmailRequestToItem(
                    email=user_email,
                    name="Donatur"
                )
            ],
            subject="Jazakallah Khairan - Donasi Anda Telah Diterima",
            html_content=f"""
            <h1>Terima Kasih!</h1>
            <p>Alhamdulillah, donasi <b>{category}</b> Anda sebesar <b>Rp{amount:,}</b> telah kami terima.</p>
            <p>Semoga Allah SWT membalas kebaikan Anda dengan pahala yang berlipat ganda di bulan Ramadhan ini.</p>
            <br>
            <p>Salam hangat,<br>DonazTech AI Team</p>
            """
        )
        return True
    except Exception as e:
        print(f"Gagal mengirim email: {e}")
        return False
