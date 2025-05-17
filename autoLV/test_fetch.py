# test_fetch.py (임시 파일)

from crawler.fetch_land_price_api import get_land_price

API_KEY = "EA1BD82E-E7AF-33DA-B9B6-E97EDFCA13C7"
pnu = "1168010600101320000"
year = "2024"

result = get_land_price(pnu, year, API_KEY)
print(result)
