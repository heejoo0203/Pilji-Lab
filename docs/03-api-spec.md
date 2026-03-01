# API 명세 (현재 + v1 파일조회 목표)

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

## 4. 파일조회 API (v1 목표)
인증: 로그인 필수 (`credentials: include`)

### GET `/bulk/template`
설명:
- 표준 엑셀 양식(.xlsx) 파일을 내려준다.
- 양식에는 최소 안내 시트(필수/권장 컬럼, 입력 예시)를 포함한다.

응답 200:
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### GET `/bulk/guide`
설명:
- 프론트에서 파일조회 안내 문구/양식 규칙을 렌더링할 때 사용하는 메타정보를 반환한다.

응답 200:
```json
{
  "max_rows": 10000,
  "required_common": ["주소유형"],
  "recommended_jibun": ["시도", "시군구", "읍면동", "산구분", "본번", "부번"],
  "recommended_road": ["시도", "시군구", "도로명", "건물본번", "건물부번"],
  "alias_examples": {
    "시도": ["시/도", "시도명"],
    "본번": ["주번", "본번(주번)"]
  }
}
```

### POST `/bulk/jobs`
설명:
- 엑셀 파일을 업로드하고 비동기 작업을 생성한다.
- 열 순서가 달라도 헤더 기반 자동 매핑/전처리를 수행한다.

요청:
- `multipart/form-data`
  - `file`: 업로드 파일 (`.xlsx`, `.xls`, `.csv`)
  - `address_mode`(옵션): `auto | jibun | road` (기본 `auto`)

응답 202:
```json
{
  "job_id": "8f31f6b1-5d7a-4b87-b4f6-75fb0d0d9a49",
  "status": "queued",
  "total_rows": 6500,
  "created_at": "2026-03-02T02:10:30Z"
}
```

### GET `/bulk/jobs`
설명:
- 로그인 사용자의 파일조회 작업 이력을 최신순으로 반환한다.

응답 200:
```json
{
  "items": [
    {
      "job_id": "8f31f6b1-5d7a-4b87-b4f6-75fb0d0d9a49",
      "file_name": "sample.xlsx",
      "status": "processing",
      "total_rows": 6500,
      "processed_rows": 2150,
      "success_rows": 2000,
      "failed_rows": 150,
      "created_at": "2026-03-02T02:10:30Z",
      "updated_at": "2026-03-02T02:11:10Z"
    }
  ]
}
```

### GET `/bulk/jobs/{job_id}`
설명:
- 단일 작업의 진행 상태를 조회한다.

응답 200:
```json
{
  "job_id": "8f31f6b1-5d7a-4b87-b4f6-75fb0d0d9a49",
  "status": "processing",
  "total_rows": 6500,
  "processed_rows": 2150,
  "success_rows": 2000,
  "failed_rows": 150,
  "progress_percent": 33.08
}
```

### GET `/bulk/jobs/{job_id}/download`
설명:
- 작업이 완료되면 결과 파일을 다운로드한다.
- 결과 파일은 원본 행/컬럼을 유지하고, 뒤쪽에 연도별 공시지가 컬럼(최신순)을 추가한다.

응답 200:
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

결과 파일 컬럼 예시(추가 컬럼):
- `공시지가_2025`
- `공시지가_2024`
- `공시지가_2023`
- `조회상태`
- `오류사유`

## 5. 오류 응답 형식
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
- `BULK_FILE_INVALID`
- `BULK_ROW_LIMIT_EXCEEDED`
- `BULK_COLUMN_MAPPING_FAILED`
- `BULK_JOB_NOT_FOUND`
- `BULK_JOB_NOT_READY`
