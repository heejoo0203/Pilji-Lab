# API 명세 (1단계)

기본 경로: `/api/v1`
인증: 쿠키 기반 JWT (`access_token`, `refresh_token`)

## 1. 인증
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
{ "user_id": "uuid", "email": "user@example.com", "full_name": "홍길동" }
```

검증 규칙:
- `email`: 형식 검증 + 중복 불가
- `password`: 8~16자, 영문/숫자/특수문자 조합, UTF-8 72바이트 이하
- `confirm_password`: `password`와 완전 일치
- `full_name`: 2~20자, 한글/영문/숫자만 허용(공백/특수문자 불가)
- `agreements`: `true` 필수

### POST `/auth/login`
요청:
```json
{ "email": "user@example.com", "password": "string" }
```
응답 200:
```json
{ "user_id": "uuid", "email": "user@example.com", "full_name": "홍길동" }
```
(HttpOnly 쿠키 설정)

### POST `/auth/logout`
응답 204

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

## 2. 단건/다건 주소 조회
### POST `/land/query`
요청:
```json
{
  "addresses": [
    { "raw": "서울특별시 강남구 역삼동 123-45", "type": "jibun" },
    { "raw": "서울특별시 강남구 테헤란로 1", "type": "road" }
  ]
}
```
응답 200:
```json
{
  "results": [
    {
      "raw": "...",
      "normalized": {"ld_code":"...","is_san":false,"main_no":123,"sub_no":45},
      "status": "ok",
      "data": {
        "address": "...",
        "jimok": "대",
        "total_area": 120.5,
        "units": [{"dong":"101","ho":"1001","area":35.1}],
        "price_per_m2": 1234567,
        "year": "2025",
        "date": "2025-01-01"
      }
    }
  ]
}
```

## 3. 엑셀 작업 (인증 필요)
### POST `/excel/jobs`
Content-Type: `multipart/form-data`
- `file`: xlsx/csv
- `sheet_name` (선택)
- `address_column_hint` (선택)

응답 202:
```json
{ "job_id": "uuid", "status": "queued" }
```

### GET `/excel/jobs/{job_id}`
응답 200:
```json
{
  "job_id":"uuid",
  "status":"queued|running|completed|failed|partial_failed",
  "total_rows":10000,
  "processed_rows":4200,
  "success_rows":4100,
  "failed_rows":100,
  "address_column":"address",
  "confidence":0.93,
  "download_url":null
}
```

### GET `/excel/jobs/{job_id}/download`
응답 302 또는 서명 URL JSON.

## 4. 기록 (인증 필요)
### GET `/history/queries?limit=50&cursor=...`
응답 200:
```json
{
  "items":[
    {"id":"uuid","type":"manual","created_at":"2026-03-01T10:00:00Z","summary":"2 addresses"},
    {"id":"uuid","type":"excel","created_at":"2026-03-01T09:55:00Z","summary":"10000 rows, completed"}
  ],
  "next_cursor":"..."
}
```

## 5. 오류 모델
```json
{
  "error": {
    "code": "ADDRESS_PARSE_FAILED",
    "message": "Cannot parse road address",
    "detail": {"row": 19}
  }
}
```

공통 오류 코드:
- `UNAUTHORIZED`
- `FORBIDDEN`
- `VALIDATION_ERROR`
- `ADDRESS_PARSE_FAILED`
- `PUBLIC_API_TIMEOUT`
- `JOB_NOT_FOUND`
- `FILE_TOO_LARGE`
- `TOO_MANY_ROWS`
