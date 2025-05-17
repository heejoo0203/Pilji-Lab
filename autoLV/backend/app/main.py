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

@app.get("/landprice/api")
def fetch_land_price_latest(
    ld_code: str = Query(...),
    main_no: int = Query(...),
    sub_no: int = Query(0),
    is_san: bool = Query(False)
):
    pnu = make_pnu(ld_code, main_no, sub_no, is_san)
    base_url = "https://api.vworld.kr/ned/data/getIndvdLandPriceAttr"

    for year in range(2025, 2009, -1):  # 2025년부터 2010년까지
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

            # 데이터가 있을 경우 반환
            fields = data.get("indvdLandPrices", {}).get("field", [])
            if fields:
                field = fields[0]
                return {
                    "address": field.get("ldCodeNm", ""),
                    "price_per_m2": int(field.get("pblntfPclnd", 0)),
                    "year": field.get("stdrYear", ""),
                    "date": field.get("pblntfDe", "")
                }

        except Exception as e:
            continue  # 오류 발생 시 다음 연도로 진행

    return {"error": "요청한 지번에 대한 공시지가 정보를 찾을 수 없습니다."}
