# -*- coding: utf-8 -*-

import requests
import logging
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------------------------------------------------
# LOG AYARLARI
# -------------------------------------------------
logging.getLogger("urllib3").setLevel(logging.WARNING)

# -------------------------------------------------
# FLASK APP
# -------------------------------------------------
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 🔥 UTF-8 Türkçe karakter fix

# -------------------------------------------------
# API LISTESI (RENDER DOMAINLERI)
# -------------------------------------------------
APIS = [
    "https://okulnodata1.onrender.com/f3system/api/okulno",
    "https://okulnodata2.onrender.com/f3system/api/okulno",
    "https://okulnodata3.onrender.com/f3system/api/okulno",
    "https://okulnodata4.onrender.com/f3system/api/okulno",
    "https://okulnodata5.onrender.com/f3system/api/okulno",
    "https://okulnodata6.onrender.com/f3system/api/okulno",
]

# -------------------------------------------------
# API CAGIRAN FONKSIYON
# -------------------------------------------------
def fetch_api(api_url, params):
    try:
        response = requests.get(
            api_url,
            params=params,
            timeout=10,
            headers={
                "Accept": "application/json; charset=utf-8",
                "User-Agent": "Mozilla/5.0"
            }
        )

        if response.status_code == 200:
            response.encoding = "utf-8"
            return response.json()
        else:
            print(f"⚠️ {api_url} HTTP {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ {api_url} bağlantı hatası: {e}")
        return None

# -------------------------------------------------
# ANA ENDPOINT
# -------------------------------------------------
@app.route("/f3system/api/okulno", methods=["GET"])
def search_okulno():

    tc     = request.args.get("tc", "").strip()
    isim   = request.args.get("isim", "").strip()
    okul   = request.args.get("okul", "").strip()
    durum  = request.args.get("durum", "").strip()
    limit  = request.args.get("limit", "50").strip()

    try:
        limit_int = min(int(limit), 100)
    except:
        limit_int = 50

    params = {}
    if tc:    params["tc"] = tc
    if isim:  params["isim"] = isim
    if okul:  params["okul"] = okul
    if durum: params["durum"] = durum
    params["limit"] = str(limit_int)

    print(f"\n🔍 Sorgu başlatıldı: {params}")

    all_results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_api, api, params): api for api in APIS}

        for future in as_completed(futures):
            api_url = futures[future]
            try:
                data = future.result()

                if data and isinstance(data.get("sonuclar"), list):
                    results = data["sonuclar"]
                    all_results.extend(results)
                    print(f"✅ {api_url}: {len(results)} kayıt alındı")
                else:
                    print(f"❌ {api_url}: geçersiz yanıt")

            except Exception as e:
                print(f"❌ {api_url}: istisna - {e}")

    print(f"📊 Toplam {len(all_results)} kayıt birleştirildi")

    # LIMIT
    all_results = all_results[:limit_int]

    return jsonify({
        "aramalar": {
            "tc": tc,
            "isim": isim,
            "okul": okul,
            "durum": durum
        },
        "toplam_kayit": len(all_results),
        "bulunan": len(all_results),
        "sonuclar": all_results
    })

# -------------------------------------------------
# ANA SAYFA
# -------------------------------------------------
@app.route("/")
def home():
    return "🚀 6 API Birleştirici Çalışıyor | /f3system/api/okulno?isim=YILMAZ"

# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    print("🚀 Flask API başlatılıyor...")
    print(f"📡 {len(APIS)} API sorgulanacak")
    print("🌐 Endpoint: /f3system/api/okulno")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=False
  )
