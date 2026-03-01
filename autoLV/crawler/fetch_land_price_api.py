import requests

def get_land_price(pnu: str, year: str, api_key: str) -> dict:
    # 개별공시지가 API
    price_url = "https://api.vworld.kr/ned/data/getIndvdLandPriceAttr"
    price_params = {
        "pnu": pnu,
        "stdrYear": year,
        "format": "json",
        "key": api_key
    }
    price_res = requests.get(price_url, params=price_params)
    price_data = price_res.json()

    if "indvdLandPrices" not in price_data or "field" not in price_data["indvdLandPrices"]:
        return {"error": "조회 실패", "response": price_data}

    field = price_data["indvdLandPrices"]["field"][0]  # 첫 번째 항목 사용

    # 공부상면적 API
    try:
        study_res = requests.get("https://api.vworld.kr/ned/data/getLandCharacteristics", params={
            "pnu": pnu,
            "format": "json",
            "numOfRows": "1",
            "pageNo": "1",
            "key": "670B8923-83DE-3713-8C6C-9F7C5DBC7E99",
            "domain": "http://127.0.0.1:3000"
        })
        study_data = study_res.json()
        study_field = study_data.get("landCharacteristics", {}).get("field", [])
        total_area = float(study_field[0].get("lndpclAr", 0)) if study_field else 0.0
    except Exception:
        total_area = 0.0

    # 지목/세대 면적 조회 (getPossessionAttr)
    try:
        possession_res = requests.get("https://api.vworld.kr/ned/data/getPossessionAttr", params={
            "pnu": pnu,
            "format": "json",
            "numOfRows": "100",
            "pageNo": "1",
            "key": "AD72DC75-4329-3047-A5FF-ECB440BBBC5C",
            "domain": "http://127.0.0.1:3000"
        })
        possession_data = possession_res.json()
        fields = possession_data.get("possessions", {}).get("field", [])
        
        # 중복 제거 로직 추가
        seen_units = set()
        units = []
        for f in fields:
            floor = f.get("buldFloorNm", "")
            ho = f.get("buldHoNm", "")
            dong = f.get("buldDongNm", "")
            unit_key = f"{floor}-{ho}"
            if unit_key and unit_key not in seen_units:
                seen_units.add(unit_key)
                units.append({
                    "dong": dong,
                    "ho": ho,
                    "area": float(f.get("lndpclAr", 0))
                })
    except Exception:
        units = []

    return {
        "address": f"{field.get('ldCodeNm', '')} {field.get('mnnmSlno', '')}",
        "jimok": field.get("lndcgrCodeNm", ""),
        "units": units,  # ✅ 프론트에서 반복 출력할 배열
        "total_area": round(total_area, 2),
        "price_per_m2": field.get("pblntfPclnd", None),
        "year": field.get("stdrYear", year),
        "date": field.get("pblntfDe", "")
    }
