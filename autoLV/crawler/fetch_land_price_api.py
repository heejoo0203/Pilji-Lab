# crawler/fetch_land_price_api.py

import requests

def get_land_price(pnu: str, year: str, api_key: str) -> dict:
    url = "https://api.vworld.kr/ned/data/getIndvdLandPriceAttr"
    params = {
        "pnu": pnu,
        "stdrYear": year,
        "format": "json",
        "key": api_key
    }
    res = requests.get(url, params=params)
    data = res.json()

    if "field" not in data:
        return {"error": "조회 실패", "response": data}

    return {
        "address": f"{data['field'].get('ldCodeNm', '')} {data['field'].get('mnnmSlno', '')}",
        "price_per_m2": data['field'].get("pblntfPclnd", None),
        "year": data['field'].get("stdrYear", year)
    }
