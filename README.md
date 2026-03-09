# 🌙 ZakatVibe AI: Smart Ramadhan Charity & Zakat Hub

ZakatVibe AI adalah platform digital yang dirancang untuk mengoptimalkan pengelolaan Zakat, Infaq, dan Sedekah (ZIS) di bulan Ramadhan. Memanfaatkan kekuatan **Vibecoding**, platform ini dibangun untuk memberikan efisiensi transaksi, akurasi perhitungan zakat berbasis AI, dan transparansi donasi yang terintegrasi secara *real-time* dengan sistem pembayaran **Mayar**.

## 🚀 Key Features (The Vibecoding Edge)
* **AI Zakat Assistant:** Konsultasi zakat yang presisi menggunakan integrasi API **Google Gemini 1.5 Flash**, memberikan panduan perhitungan zakat yang akurat sesuai kaidah fiqih.
* **Seamless Payment Integration:** Integrasi *end-to-end* dengan **Mayar Payment Gateway** untuk memproses donasi secara instan dengan Webhook callback otomatis.
* **High-Concurrency Engine:** Dibangun dengan **Flask + Gevent** untuk memastikan performa responsif, serta **Celery** untuk pemrosesan *background task* (seperti pengiriman kuitansi dan notifikasi) yang efisien.
* **Professional API Documentation:** Dokumentasi API lengkap melalui **Swagger UI (Flask-RESTX)**, memudahkan transparansi dan integrasi sistem.

## 🛠 Tech Stack
* **Backend:** Python 3.10+, Flask, Flask-RESTX
* **Concurrency:** Gevent, Celery (with Redis/RabbitMQ)
* **AI Engine:** Google Gemini API
* **Database:** PostgreSQL with SQLAlchemy ORM
* **Payment:** Mayar API
* **Deployment:** Cloud-Native Architecture

## 📋 API Documentation (Swagger)
Akses dokumentasi API interaktif kami di endpoint `/swagger` pada URL aplikasi yang ter-deploy.

## ⚙️ How It Works
1.  **Consultation:** User menanyakan perhitungan zakat via chat -> AI memproses -> Respons disimpan di DB.
2.  **Donation Flow:** User memilih kategori donasi -> API men-generate `Payment Link` via **Mayar** -> User menyelesaikan pembayaran.
3.  **Webhook Callback:** **Mayar** mengirim sinyal ke webhook kami -> **Celery** memicu update status transaksi di database -> Notifikasi donasi dikirim otomatis.

## 🚀 Quick Setup (Development)
1. Clone repositori ini.
2. Setup environment variables (`.env`):
   ```bash
   MAYAR_API_KEY=your_key
   POSTGRES_URI=your_db_url