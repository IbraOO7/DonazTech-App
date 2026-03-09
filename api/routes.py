from gevent import monkey
monkey.patch_all()

import requests
import json
from flask import request, Blueprint, render_template, jsonify
from functools import wraps
from flask_restx import Namespace, Resource, fields
from databases.config import SessionLocal
from databases.models.services import Donation, ZakatConsultation
from api import api
from services.backgroundtasks.tasks import process_zakat_ai, send_thank_you_email
from services.ai_matchmaker import match_charity_by_geo, match_charity
from databases.models.charity import Charity
from databases.models.user import User
from services.config import configs
import jwt
import datetime
import logging


ns = Namespace('v1', description='DonazTech Main API')

routing = Blueprint('app_route', __name__, template_folder='templates')

zakat_input = api.model('ZakatAI', {
    'query': fields.String(required=True, example="Gaji saya 10jt per bulan, berapa zakat profesinya?")
})

match_input = api.model('MatchInput', {
    'query': fields.String(required=True, example="Saya ingin donasi untuk anak yatim."),
    'lat': fields.Float(required=False, example=-6.2345),
    'lng': fields.Float(required=False, example=106.8500)
})

donation_input = api.model('Donation', {
    'email': fields.String(required=True),
    'amount': fields.Float(required=True),
    'category': fields.String(required=True, enum=['Zakat', 'Sedekah', 'Wakaf'])
})

def get_fallback_charities():
    try:
        charities = Charity.query.limit(5).all()
        return [{"name": c.name, "lat": c.lat, "lng": c.lng} for c in charities]
    except:
        return []

@routing.route("/")
def index():
    return render_template("index.html")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
        
        if not token:
            return {"error": "Token tidak ditemukan"}, 401

        try:
            data = jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
            email_user = data['email']
        except Exception as e:
            return {"error": "Token tidak valid"}, 401
        return f(*args, current_user_email=email_user, **kwargs)
    return decorated

@ns.route('/login')
class Login(Resource):
    def post(self):
        data = request.json
        email = data.get('email')
        password = data.get('password')
        if not email:
            return {"error": "Email diperlukan"}, 400
        payload = {
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        token = jwt.encode(payload, configs.SECRET_KEY, algorithm='HS256')

        return {
            "message": "Login berhasil",
            "token": token,
            "user": {"email": email}
        }, 200

@ns.route('/charity/match')
class CharityMatch(Resource):
    @ns.expect(match_input)
    def post(self):
        data = request.json
        user_query = data.get('query')
        lat = data.get('lat')
        lng = data.get('lng')

        try:
            if lat is not None and lng is not None:
                nearby = match_charity_by_geo(lat, lng, user_query)
                
                if nearby:
                    return {"results": nearby, "message": "Yayasan ditemukan di sekitar Anda"}, 200
                else:
                    return {"results": [], "message": "Tidak ada yayasan dalam radius 10km"}, 200
            else:
                raw_response = match_charity(user_query)
                return {"match": raw_response}, 200
                
        except Exception as e:
            print(f"[!] Critical Error in CharityMatch: {str(e)}")
            return {"error": "Terjadi kesalahan internal saat mencari yayasan"}, 500

@ns.route('/zakat/consult')
class ZakatAI(Resource):
    @ns.expect(zakat_input)
    def post(self):
        data = request.json
        user_query = data.get('query')
        lat = data.get('lat', None)
        lng = data.get('lng', None)
        
        if not user_query:
            return {"error": "Query tidak boleh kosong"}, 400
            
        db = SessionLocal()
        try:
            new_consult = ZakatConsultation(query=user_query)
            db.add(new_consult)
            db.commit()
            process_zakat_ai.delay(new_consult.id, user_query, lat=lat, lng=lng)
            
            return {"message": "AI sedang memproses...", "id": new_consult.id}, 202
        except Exception as e:
            db.rollback()
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                logging.warning("AI Rate limit hit!")
                return {"error": "Sesi Token AI telah habis, silakan kembali dalam 24 jam."}, 429
            return {"error": "Gagal menginisiasi proses AI"}, 500
        finally:
            db.close()

@ns.route('/zakat/status/<int:consult_id>')
class ZakatStatus(Resource):
    def get(self, consult_id):
        db = SessionLocal()
        try:
            consult = db.query(ZakatConsultation).filter(ZakatConsultation.id == consult_id).first()
            if not consult:
                return {"error": "Konsultasi tidak ditemukan"}, 404
            
            if consult.ai_response:
                try:
                    data = json.loads(consult.ai_response)
                    jawaban = data.get("jawaban") or data.get("response") or str(data)
                    
                    return {
                        "status": "completed",
                        "response": jawaban,
                        "locations": data.get("locations", [])
                    }, 200
                except json.JSONDecodeError:
                    return {
                        "status": "completed", 
                        "response": consult.ai_response, 
                        "locations": []
                    }, 200
            
            return {"status": "processing"}, 200
        finally:
            db.close()

@ns.route('/charities/list')
class CharityList(Resource):
    def get(self):
        db = SessionLocal()
        try:
            charities = db.query(Charity).all()
            return [{"id": c.id, "name": c.name} for c in charities], 200
        finally:
            db.close()

@ns.route('/donate/create')
class CreateDonation(Resource):
    @ns.expect(donation_input)
    def post(self):
        data = request.json
        email = data.get('email')
        amount = int(data.get('amount'))
        category = data.get('category')
        
        db = SessionLocal()
        try:
            one_minute_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
            existing_donation = db.query(Donation).filter(
                Donation.user_email == email,
                Donation.amount == amount,
                Donation.status == 'pending',
                Donation.created_at > one_minute_ago
            ).first()

            if existing_donation:
                logging.info(f"Duplicate request detected for {email}, returning existing link.")
                return {"payment_url": existing_donation.mayar_url}, 200
            payload = {
                "name": f"Donasi {category}",
                "amount": amount,
                "description": f"Pembayaran untuk donasi {category} dengan email {email}",
                "email": email,
                "mobile": "08123456789",
                "redirect_url": "https://zakatvibe.com/thanks"
            }
            
            url = f"{configs.MAYAR_BASE_URL.rstrip('/')}/payment/create"
            headers = {
                "Authorization": f"Bearer {configs.MAYAR_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            res_data = response.json()
            if response.status_code in [200, 201]:
                result_data = res_data.get('data', res_data)
                
                new_donation = Donation(
                    user_email=email,
                    amount=amount,
                    category=category,
                    status="pending",
                    mayar_url=result_data.get('link'),
                    mayar_link_id=str(result_data.get('id')) 
                )
                db.add(new_donation)
                db.commit()
                logging.info(f"Donation created successfully: {new_donation.mayar_link_id}")
                return {"payment_url": new_donation.mayar_url}, 201
            logging.error(f"Mayar API Error: {res_data}")
            return {"error": "Gagal membuat link pembayaran", "details": res_data}, response.status_code

        except Exception as e:
            db.rollback()
            logging.error(f"Error dalam CreateDonation: {str(e)}")
            return {"error": "Terjadi kesalahan internal"}, 500
        finally:
            db.close()

@ns.route('/donate/history')
class DonationHistory(Resource):
    @token_required
    def get(self, current_user_email):
        db = SessionLocal()
        try:
            logging.info(f"DEBUG: Mencari donasi untuk email: {current_user_email}")
            donations = db.query(Donation).all() 
            history_data = []
            for d in donations:
                history_data.append({
                    "id": d.id,
                    "date": d.created_at.strftime("%d %b %Y") if d.created_at else "-",
                    "category": d.category or "Zakat",
                    "amount": float(d.amount or 0),
                    "status": (d.status or "PENDING").upper()
                })
            return jsonify(history_data)
        
        except Exception as e:
            print(f"DEBUG: Error terjadi: {str(e)}")
            return {"error": str(e)}, 500
        finally:
            db.close()

@ns.route('/webhook/mayar')
class MayarWebhook(Resource):
    def post(self):
        data = request.json
        logging.info(f"Webhook received payload: {json.dumps(data)}")
        if data.get('event') == 'testing':
            return {"status": "success", "message": "Test connection successful"}, 200
        token = request.headers.get("X-Callback-Token")
        if token != configs.MAYAR_WEBHOOK_TOKEN:
            logging.warning(f"Unauthorized webhook attempt. Provided token: {token}")
            return {"status": "error", "message": "Unauthorized"}, 200
        payload = data.get('data', {})
        transaction_id = str(payload.get('transactionId') or payload.get('id') or "")
        product_id = str(payload.get('productId') or "")
        status = str(payload.get('status', '')).lower()
        
        logging.info(f"Processing transaction: {transaction_id}, product_id: {product_id}, status: {status}")
        if status in ['paid', 'success', 'settlement', 'captured']:
            db = SessionLocal()
            try:
                query = db.query(Donation).filter(
                    (Donation.mayar_link_id == transaction_id) | 
                    (Donation.mayar_link_id == product_id)
                )
                if transaction_id.isdigit():
                    query = query.union(db.query(Donation).filter(Donation.id == int(transaction_id)))
                
                donation = query.first()
                if donation:
                    if donation.status != 'SUCCESS':
                        donation.status = 'SUCCESS'
                        db.commit()
                        send_thank_you_email.delay(
                            donation.user_email, 
                            donation.amount, 
                            donation.category
                        )
                        logging.info(f"Donation ID {donation.id} marked as SUCCESS.")
                    else:
                        logging.info(f"Donation ID {donation.id} already SUCCESS.")
                else:
                    logging.warning(f"Donation not found for transaction: {transaction_id}")
                    return {"status": "error", "message": "Donation not found"}, 200
                
            except Exception as e:
                db.rollback()
                logging.error(f"Database error in webhook: {str(e)}")
                return {"status": "error", "message": "Internal server error"}, 500
            finally:
                db.close()
                
        return {"status": "success", "message": "Webhook processed"}, 200