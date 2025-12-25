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
    """Tek API'den veri çek"""
    try:
        url = f"{domain}/f3system/api/okulno?{urlencode(params)}"
        response = requests.get(url, timeout=5)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            return {
                "domain": domain.replace('https://', ''),
                "success": True,
                "data": response.json() if response.text.strip() else []
            }
        return {
            "domain": domain.replace('https://', ''),
            "success": False,
            "error": f"Status: {response.status_code}"
        }
    except:
        return {
            "domain": domain.replace('https://', ''),
            "success": False,
            "error": "Connection failed"
        }

@app.route('/f3system/api/okulno', methods=['GET'])
def okulno():
    """Ana endpoint - tüm API'leri sorgula"""
    # Parametreleri al
    tc = request.args.get('tc')
    isim = request.args.get('isim')
    limit = request.args.get('limit')
    
    # Parametre kontrol
    if not tc and not isim:
        return jsonify({
            "error": "tc veya isim parametresi gerekli"
        }), 400
    
    # Sorgu parametreleri
    params = {}
    if tc:
        params['tc'] = tc
    if isim:
        params['isim'] = isim
    if limit:
        params['limit'] = limit
    
    # Tüm API'leri paralel sorgula
    all_results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_from_api, domain, params) for domain in DOMAINS]
        for future in as_completed(futures):
            result = future.result()
            if result["success"] and result["data"]:
                if isinstance(result["data"], list):
                    all_results.extend(result["data"])
                else:
                    all_results.append(result["data"])
    
    # Limit uygula
    if limit and limit.isdigit():
        all_results = all_results[:int(limit)]
    
    # JSON döndür
    return jsonify({
        "query": params,
        "results": all_results,
        "count": len(all_results)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
