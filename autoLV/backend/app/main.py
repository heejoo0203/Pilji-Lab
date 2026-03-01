from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from crawler.pnu_util import make_pnu
import requests

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# getPossessionAttr로 지목 및 개별 세대 면적 계산
def fetch_possession_attr(pnu: str) -> dict:
    url = "https://api.vworld.kr/ned/data/getPossessionAttr"
    params = {
        "pnu": pnu,
        "format": "json",
        "numOfRows": "100",
        "pageNo": "1",
        "key": "AD72DC75-4329-3047-A5FF-ECB440BBBC5C",
        "domain": "http://127.0.0.1:3000"
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()
        print("지목/세대면적 응답:", data)

        fields = data.get("possessions", {}).get("field", [])
        seen_units = set()
        units = []

        for f in fields:
            dong = f.get("buldDongNm", "") or "미상"
            ho = f.get("buldHoNm", "") or "미상"
            floor = f.get("buldFloorNm", "") or "미상"
            area = float(f.get("lndpclAr", 0))
            unit_key = f"{dong}-{floor}-{ho}"

            if unit_key not in seen_units:
                seen_units.add(unit_key)
                units.append({
                    "dong": dong,
                    "ho": ho,
                    "area": area
                })

        result = {
            "jimok": fields[0].get("lndcgrCodeNm", "") if fields else "",
            "units": units
        }

        return result

    except Exception as e:
        print("지목/세대면적 오류:", e)

    return {"jimok": "", "units": []}

@app.get("/landprice/house-units")
def fetch_house_units(
    ld_code: str = Query(...),
    main_no: int = Query(...),
    sub_no: int = Query(0),
    is_san: bool = Query(False)
):
    pnu = make_pnu(ld_code, main_no, sub_no, is_san)
    return fetch_possession_attr(pnu)

# getLandCharacteristics로 공부상 면적 조회
def fetch_study_area(pnu: str) -> float:
    url = "https://api.vworld.kr/ned/data/getLandCharacteristics"
    params = {
        "pnu": pnu,
        "format": "json",
        "numOfRows": "1",
        "pageNo": "1",
        "key": "670B8923-83DE-3713-8C6C-9F7C5DBC7E99",
        "domain": "http://127.0.0.1:3000"
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()
        print("공부상면적 응답:", data)

        # ✅ 오타 수정: 'landCharacteristics' → 'landCharacteristicss'
        field = data.get("landCharacteristicss", {}).get("field", [])
        if field:
            return float(field[0].get("lndpclAr", 0.0))
    except Exception as e:
        print("공부상면적 오류:", e)

    return 0.0

@app.get("/landprice/api")
def fetch_land_price_latest(
    ld_code: str = Query(...),
    main_no: int = Query(...),
    sub_no: int = Query(0),
    is_san: bool = Query(False)
):
    pnu = make_pnu(ld_code, main_no, sub_no, is_san)
    base_url = "https://api.vworld.kr/ned/data/getIndvdLandPriceAttr"

    for year in range(2025, 2009, -1):
        params = {
            "pnu": pnu,
            "stdrYear": str(year),
            "format": "json",
            "numOfRows": "10",
            "pageNo": "1",
            "key": "EA1BD82E-E7AF-33DA-B9B6-E97EDFCA13C7",
            "domain": "http://127.0.0.1:3000"
        }

        try:
            res = requests.get(base_url, params=params)
            data = res.json()
            print("공시지가 응답:", data)

            fields = data.get("indvdLandPrices", {}).get("field", [])
            if fields:
                field = fields[0]
                possession_data = fetch_possession_attr(pnu)
                study_area = fetch_study_area(pnu)
                return {
                    "address": field.get("ldCodeNm", ""),
                    "jimok": possession_data["jimok"],
                    "area": possession_data["units"][0]["area"] if possession_data["units"] else 0,
                    "units": possession_data["units"],
                    "total_area": round(study_area, 2),
                    "price_per_m2": int(field.get("pblntfPclnd", 0)),
                    "year": field.get("stdrYear", ""),
                    "date": field.get("pblntfDe", "")
                }

        except Exception as e:
            print("공시지가 오류:", e)
            continue

    return {"error": "요청한 지번에 대한 공시지가 정보를 찾을 수 없습니다."}
