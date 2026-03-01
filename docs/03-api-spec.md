# API 명세 (현재 구현 기준)

기본 경로: `/api/v1`  
인증: 쿠키 기반 JWT (`access_token`, `refresh_token`)

## 1. 공통
### GET `/`
응답 200:
```json
{ "service": "autoLV-api", "status": "ok" }
```

### GET `/health`
응답 200:
```json
{ "status": "healthy" }
```

## 2. 인증 API
### POST `/auth/register`
요청:
```json
{
  "email": "user@example.com",
  "password": "Abcd1234!",
  "confirm_password": "Abcd1234!",
  "full_name": "홍길동",
  "agreements": true
}
```

응답 201:
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "full_name": "홍길동"
}
```

검증 규칙:
- `email`: 형식 검증 + 중복 불가
- `password`: 8~16자, 영문/숫자/특수문자 포함, UTF-8 기준 72바이트 이하
- `confirm_password`: password와 동일
- `full_name`: 2~20자, 한글/영문/숫자만 허용
- `agreements`: `true` 필수

### POST `/auth/login`
요청:
```json
{
  "email": "user@example.com",
  "password": "Abcd1234!"
}
```

응답 200:
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "full_name": "홍길동"
}
```

비고:
- 성공 시 HttpOnly 쿠키(`access_token`, `refresh_token`)가 설정됩니다.

### POST `/auth/logout`
응답 204 (쿠키 삭제)

### GET `/auth/me`
응답 200:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "홍길동",
  "role": "user",
  "auth_provider": "local"
}
```

## 3. 개별공시지가 조회 API
### POST `/land/single`
지번 검색 요청:
```json
{
  "search_type": "jibun",
  "ld_code": "1168011800",
  "san_type": "일반",
  "main_no": "970",
  "sub_no": "0"
}
```

도로명 검색 요청:
```json
{
  "search_type": "road",
  "sido": "서울특별시",
  "sigungu": "강남구",
  "road_name": "도곡로",
  "building_main_no": "21",
  "building_sub_no": ""
}
```

응답 200:
```json
{
  "search_type": "road",
  "pnu": "1168011800109700000",
  "address_summary": "서울특별시 강남구 도곡동 970",
  "rows": [
    {
      "기준년도": "2025",
      "토지소재지": "서울특별시 강남구 도곡동",
      "지번": "970",
      "개별공시지가": "14,000,000 원/㎡",
      "기준일자": "01월 01일",
      "공시일자": "20250430",
      "비고": ""
    }
  ]
}
```

비고:
- 내부적으로 VWorld API를 호출합니다.
- 같은 연도 데이터가 여러 건이면 최신 `lastUpdtDt`를 사용합니다.

### GET `/land/road-initials`
쿼리:
- `sido`: 시/도
- `sigungu`: 시/군/구

응답 200:
```json
{
  "sido": "서울특별시",
  "sigungu": "강남구",
  "initials": ["ㄱ", "ㄴ", "ㄷ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅌ", "ㅎ"]
}
```

### GET `/land/road-names`
쿼리:
- `sido`: 시/도
- `sigungu`: 시/군/구
- `initial`: 초성

응답 200:
```json
{
  "sido": "서울특별시",
  "sigungu": "강남구",
  "initial": "ㄷ",
  "roads": ["도곡로", "도곡로11길", "도곡로13길"]
}
```

## 4. 오류 응답 형식
FastAPI 기본 `detail` 형식을 사용합니다.

예시:
```json
{
  "detail": {
    "code": "VWORLD_KEY_MISSING",
    "message": "VWORLD_API_KEY 설정이 필요합니다."
  }
}
```

주요 오류 코드:
- `VWORLD_KEY_MISSING`
- `VWORLD_INVALID_KEY` 계열 (VWorld 응답 코드 매핑)
- `ROAD_GEOCODE_FAILED`
- `PARCEL_NOT_FOUND`
- `UNAUTHORIZED`
