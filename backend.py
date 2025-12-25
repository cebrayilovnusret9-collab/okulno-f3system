# -*- coding: utf-8 -*-
import requests
import json
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode

app = Flask(__name__)

# Domain listesi
DOMAINS = [
    "https://okulnodata1",
    "https://okulnodata2", 
    "https://okulnodata3",
    "https://okulnodata4",
    "https://okulnodata5",
    "https://okulnodata6"
]

def fetch_from_api(domain, params):
    """Tek API'den veri çek - SESSİZ"""
    try:
        url = f"{domain}/f3system/api/okulno?{urlencode(params)}"
        
        response = requests.get(
            url, 
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "data": data.get('sonuclar', []) if data else []
            }
        return {
            "success": False,
            "data": []
        }
            
    except:
        return {
            "success": False,
            "data": []
        }

@app.route('/f3system/api/okulno', methods=['GET'])
def okulno():
    """Ana endpoint - sessiz versiyon"""
    
    # Parametreleri al
    tc = request.args.get('tc', '')
    isim = request.args.get('isim', '')
    okul = request.args.get('okul', '')
    durum = request.args.get('durum', '')
    limit = request.args.get('limit', '50')
    
    # Limit kontrolü
    try:
        limit_int = min(int(limit), 100)
    except:
        limit_int = 50
    
    # Parametreleri hazırla
    params = {}
    if tc:
        params['tc'] = tc
    if isim:
        params['isim'] = isim
    if okul:
        params['okul'] = okul
    if durum:
        params['durum'] = durum
    if limit:
        params['limit'] = str(limit_int)
    
    # Tüm API'leri paralel sorgula
    all_results = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_from_api, domain, params) for domain in DOMAINS]
        
        for future in as_completed(futures):
            result = future.result()
            if result["success"] and result["data"]:
                all_results.extend(result["data"])
    
    # Limit uygula
    if len(all_results) > limit_int:
        all_results = all_results[:limit_int]
    
    # SADECE SONUÇLARI DÖN - AYNI FORMAT
    return jsonify({
        'aramalar': {
            'tc': tc,
            'isim': isim,
            'okul': okul,
            'durum': durum
        },
        'toplam_kayit': len(all_results),
        'bulunan': len(all_results),
        'sonuclar': all_results
    })

@app.route('/f3system/api/okulno/<tc_no>', methods=['GET'])
def get_by_tc(tc_no):
    """TC'ye göre arama"""
    
    all_results = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_from_api, domain, {'tc': tc_no}) for domain in DOMAINS]
        
        for future in as_completed(futures):
            result = future.result()
            if result["success"] and result["data"]:
                all_results.extend(result["data"])
    
    if all_results:
        return jsonify(all_results[0])
    
    return jsonify({'error': 'Kayıt bulunamadı'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
