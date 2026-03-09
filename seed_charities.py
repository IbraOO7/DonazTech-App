from databases.config import SessionLocal
from databases.models.charity import Charity

def seed_data():
    db = SessionLocal()
    
    # Koordinat pusat (approximate) untuk 8 wilayah Jabodetabek
    # Format: "Nama Wilayah": (lat, lng)
    regions = {
        "Jakarta Pusat": (-6.1754, 106.8272),
        "Jakarta Selatan": (-6.2615, 106.8106),
        "Jakarta Barat": (-6.1683, 106.7588),
        "Bogor": (-6.5950, 106.8166),
        "Depok": (-6.4025, 106.7942),
        "Tangerang": (-6.1783, 106.6319),
        "Bekasi": (-6.2383, 106.9756),
        "Tangerang Selatan": (-6.2924, 106.7167)
    }

    charities = []
    
    for region, (base_lat, base_lng) in regions.items():
        for i in range(1, 4):  # Membuat 3 data per wilayah
            # Variasi koordinat kecil agar tersebar (0.005 derajat)
            offset = i * 0.002
            charities.append({
                "name": f"Yayasan Zakat {region} {i}",
                "desc": f"Lembaga amil zakat terpercaya yang melayani masyarakat di wilayah {region} dan sekitarnya.",
                "lat": base_lat + (offset if i % 2 == 0 else -offset),
                "lng": base_lng + (offset if i % 3 == 0 else -offset)
            })

    try:
        # Menghapus data lama agar tidak duplikat saat dijalankan berkali-kali (opsional)
        db.query(Charity).delete()
        
        for c in charities:
            new_charity = Charity(
                name=c["name"], 
                description=c["desc"], 
                lat=c["lat"], 
                lng=c["lng"]
            )
            db.add(new_charity)
            
        db.commit()
        print(f"Berhasil menambahkan {len(charities)} yayasan ke database (Jabodetabek)!")
    except Exception as e:
        print(f"Gagal seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()