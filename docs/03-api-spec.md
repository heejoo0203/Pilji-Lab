# API 명세 (v2.1.0)

기본 경로: `/api/v1`  
인증: 쿠키 기반 JWT(`access_token`, `refresh_token`)

## 0. VWorld 호출 정책
- `/land/single`는 VWorld 직접 호출을 먼저 시도한다.
- 직접 호출 실패 시 `VWORLD_PROXY_URL`이 설정되어 있으면 프록시 경로를 재시도한다.
- 두 경로가 모두 실패하면 `VWORLD_DIRECT_AND_PROXY_FAILED`로 직접/프록시 실패 원인을 함께 반환한다.

## 1. 공통 API
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
  "phone_number": "01012345678",
  "agreements": true,
  "verification_id": "c4f4aa8c-5f52-4df3-b3e7-7f16abdf3f2c",
  "verification_code": "123456"
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
- `confirm_password`: `password`와 동일
- `full_name`: 2~20자, 한글/영문/숫자만 허용(닉네임 규칙)
- `phone_number`: 숫자/하이픈 허용, 서버에서 숫자만 정규화, 9~11자리
- `agreements`: `true` 필수
- `verification_id`, `verification_code`: 이메일 인증 코드 검증

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
- 성공 시 HttpOnly 쿠키(`access_token`, `refresh_token`)가 설정된다.

### POST `/auth/logout`
응답 204 (쿠키 삭제)

### GET `/auth/me`
응답 200:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "홍길동",
  "phone_number": "01012345678",
  "role": "user",
  "auth_provider": "local",
  "profile_image_url": "/media/profile/ab12cd34ef56.png"
}
```

### GET `/auth/email-availability?email=user@example.com`
설명:
- 회원가입용 이메일 중복 확인 API

응답 200:
```json
{
  "email": "user@example.com",
  "available": true
}
```

### PATCH `/auth/profile`
설명:
- 닉네임과 프로필 사진을 수정한다.

요청:
- `multipart/form-data`
  - `full_name` (옵션): 닉네임
  - `profile_image` (옵션): png/jpg/jpeg/webp, 최대 5MB

응답 200:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "새닉네임",
  "role": "user",
  "auth_provider": "local",
  "profile_image_url": "/media/profile/f0e1d2c3b4a5.webp"
}
```

### POST `/auth/password/change`
요청:
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!",
  "confirm_new_password": "NewPass456!"
}
```

응답 200:
```json
{
  "message": "비밀번호가 변경되었습니다."
}
```

### DELETE `/auth/account`
설명:
- 확인 문구를 정확히 입력해야 탈퇴할 수 있다.

요청:
```json
{
  "confirmation_text": "홍길동 탈퇴를 동의합니다"
}
```

응답 204:
- 본문 없음

### GET `/auth/terms`
설명:
- 로그인 사용자가 동의한 약관 버전/본문/동의시각을 조회한다.

응답 200:
```json
{
  "version": "2026-03-05-v1",
  "content": "[autoLV 서비스 이용약관] ...",
  "accepted_at": "2026-03-05T06:31:15.000000+00:00"
}
```

### GET `/auth/terms/current`
설명:
- 비로그인(회원가입 화면 포함)에서 현재 약관 본문을 조회한다.

응답 200:
```json
{
  "version": "2026-03-05-v1",
  "content": "[autoLV 서비스 이용약관] ...",
  "accepted_at": null
}
```

### POST `/auth/recovery/send-code`
요청:
```json
{
  "purpose": "signup",
  "email": "user@example.com"
}
```

응답 200:
```json
{
  "verification_id": "c4f4aa8c-5f52-4df3-b3e7-7f16abdf3f2c",
  "expires_in_seconds": 600,
  "message": "인증 코드가 발송되었습니다.",
  "debug_code": null
}
```

비고:
- `purpose`: `signup | find_id | reset_password`
- 운영에서는 `debug_code`가 `null`이어야 한다(`EMAIL_DEBUG_RETURN_CODE=false` 권장).

### POST `/auth/recovery/find-id/profile`
설명:
- 이름 + 연락처로 가입 이메일을 찾고 마스킹된 이메일만 반환한다.

요청:
```json
{
  "full_name": "홍길동",
  "phone_number": "010-1234-5678"
}
```

응답 200:
```json
{
  "masked_email": "he***03@naver.com"
}
```

### POST `/auth/recovery/reset-password`
요청:
```json
{
  "email": "user@example.com",
  "verification_id": "c4f4aa8c-5f52-4df3-b3e7-7f16abdf3f2c",
  "code": "123456",
  "new_password": "NewPass456!",
  "confirm_new_password": "NewPass456!"
}
```

응답 200:
```json
{
  "message": "비밀번호가 재설정되었습니다. 새 비밀번호로 로그인해 주세요."
}
```

## 3. 개별공시지가 API
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

## 4. 파일조회 API (v1)
인증: 로그인 필수(`credentials: include`)

### GET `/bulk/guide`
설명:
- 파일조회 안내/권장 컬럼 메타 정보를 반환한다.

응답 200:
```json
{
  "max_rows": 10000,
  "required_common": ["주소유형"],
  "recommended_jibun": ["시도", "시군구", "읍면동", "산구분", "본번", "부번"],
  "recommended_road": ["시도", "시군구", "도로명", "건물본번", "건물부번"],
  "alias_examples": {
    "시도": ["시도", "시/도"],
    "본번": ["본번", "지번본번"],
    "주소": ["주소", "소재지"]
  }
}
```

### GET `/bulk/template`
설명:
- 표준 양식 엑셀 파일(`autolv_bulk_template.xlsx`)을 다운로드한다.

응답 200:
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### POST `/bulk/jobs`
설명:
- 업로드 파일로 비동기 작업을 생성한다.

요청:
- `multipart/form-data`
  - `file`: `.xlsx`, `.xls`, `.csv`
  - `address_mode`: `auto | jibun | road` (기본값 `auto`)

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
- 사용자 작업 이력을 최신순으로 페이지 조회한다.

쿼리:
- `page`: 기본 1, 최소 1
- `page_size`: 기본 10, 최소 1, 최대 10

응답 200:
```json
{
  "page": 1,
  "page_size": 10,
  "total_count": 24,
  "total_pages": 3,
  "items": [
    {
      "job_id": "8f31f6b1-5d7a-4b87-b4f6-75fb0d0d9a49",
      "file_name": "sample.xlsx",
      "status": "processing",
      "total_rows": 6500,
      "processed_rows": 2150,
      "success_rows": 2000,
      "failed_rows": 150,
      "progress_percent": 33.08,
      "created_at": "2026-03-02T02:10:30Z",
      "updated_at": "2026-03-02T02:11:10Z",
      "error_message": null,
      "can_download": false
    }
  ]
}
```

### GET `/bulk/jobs/{job_id}`
설명:
- 단일 작업 상태를 조회한다.

응답 200:
```json
{
  "job_id": "8f31f6b1-5d7a-4b87-b4f6-75fb0d0d9a49",
  "file_name": "sample.xlsx",
  "status": "completed",
  "total_rows": 6500,
  "processed_rows": 6500,
  "success_rows": 6300,
  "failed_rows": 200,
  "progress_percent": 100,
  "created_at": "2026-03-02T02:10:30Z",
  "updated_at": "2026-03-02T02:12:40Z",
  "error_message": null,
  "can_download": true
}
```

### GET `/bulk/jobs/{job_id}/download`
설명:
- 완료된 작업 결과 파일을 다운로드한다.

응답 200:
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### POST `/bulk/jobs/delete`
설명:
- 선택한 작업을 일괄 삭제한다.
- `processing` 상태 작업은 삭제 대상에서 제외된다.

요청:
```json
{
  "job_ids": ["job-id-1", "job-id-2"]
}
```

응답 200:
```json
{
  "deleted_count": 1,
  "skipped_count": 1,
  "deleted_job_ids": ["job-id-1"],
  "skipped_job_ids": ["job-id-2"]
}
```

## 5. 지도조회 API
### POST `/map/click`
요청:
```json
{
  "lat": 37.5662952,
  "lng": 126.9779451
}
```

응답 200:
```json
{
  "lat": 37.5662952,
  "lng": 126.9779451,
  "pnu": "1111010100100010000",
  "address_summary": "서울특별시 종로구 청운동 1",
  "jibun_address": "서울특별시 종로구 청운동 1",
  "road_address": "서울특별시 종로구 자하문로 1",
  "area": 1234.5,
  "price_current": 12000000,
  "price_previous": 11200000,
  "growth_rate": 7.14,
  "estimated_total_price": 14814000000,
  "nearby_avg_price": 10650000,
  "nearby_radius_m": 200,
  "cache_hit": false,
  "rows": []
}
```

### POST `/map/search`
요청:
```json
{
  "address": "서울특별시 종로구 세종대로 175"
}
```

응답:
- `/map/click`과 동일 스키마

### GET `/map/by-pnu?pnu=1111010100100010000`
응답:
- `/map/click`과 동일 스키마

### GET `/map/price-rows?pnu=1111010100100010000`
응답 200:
```json
{
  "pnu": "1111010100100010000",
  "rows": [
    {
      "기준년도": "2025",
      "토지소재지": "서울특별시 종로구 청운동",
      "지번": "1",
      "개별공시지가": "12,000,000 원/㎡",
      "기준일자": "01월 01일",
      "공시일자": "20250430",
      "비고": ""
    }
  ]
}
```

### GET `/map/land-details?pnu=1111010100100010000`
응답 200:
```json
{
  "pnu": "1111010100100010000",
  "stdr_year": "2025",
  "area": 1234.5,
  "land_category_name": "대",
  "purpose_area_name": "제2종일반주거지역",
  "purpose_district_name": "기타경관지구"
}
```

### GET `/map/export?pnu=1111010100100010000`
설명:
- CSV 다운로드 (`pnu, area, current_price, previous_price, growth_rate`)

응답 200:
- `Content-Type: text/csv; charset=utf-8`

## 6. 조회기록 API
인증: 로그인 필수

### POST `/history/query-logs`
설명:
- 개별조회/지도조회 결과를 저장하거나(3분 윈도우 내 중복 시) 최신 내용으로 병합한다.

요청:
```json
{
  "search_type": "map",
  "pnu": "1111010100100010000",
  "address_summary": "서울특별시 종로구 청운동 1",
  "rows": []
}
```

응답 201:
```json
{
  "id": "log-uuid",
  "search_type": "map",
  "pnu": "1111010100100010000",
  "address_summary": "서울특별시 종로구 청운동 1",
  "result_count": 0,
  "created_at": "2026-03-05T05:20:31.120000+00:00"
}
```

### GET `/history/query-logs`
쿼리:
- `page` (기본 1)
- `page_size` (기본 20, 최대 100)
- `search_type` (`jibun|road|map`)
- `sido` (주소 필터)
- `sigungu` (주소 필터)
- `sort_by` (`created_at|address_summary|search_type|result_count`)
- `sort_order` (`asc|desc`)

응답 200:
```json
{
  "page": 1,
  "page_size": 20,
  "total_count": 132,
  "total_pages": 7,
  "items": [
    {
      "id": "log-uuid",
      "search_type": "jibun",
      "pnu": "1168011800109700000",
      "address_summary": "서울특별시 강남구 도곡동 970",
      "result_count": 12,
      "created_at": "2026-03-05T05:19:10.230000+00:00"
    }
  ]
}
```

### GET `/history/query-logs/{log_id}`
응답 200:
```json
{
  "id": "log-uuid",
  "search_type": "jibun",
  "pnu": "1168011800109700000",
  "address_summary": "서울특별시 강남구 도곡동 970",
  "result_count": 12,
  "created_at": "2026-03-05T05:19:10.230000+00:00",
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

## 7. 오류 응답 형식
FastAPI 기본 `detail` 형식을 사용한다.

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
- `VWORLD_INVALID_KEY` 계열 (`VWORLD_<resultCode>`)
- `VWORLD_UNREACHABLE`
- `VWORLD_HTTP_ERROR`
- `VWORLD_INVALID_JSON`
- `VWORLD_PROXY_MISSING`
- `VWORLD_PROXY_UNREACHABLE`
- `VWORLD_PROXY_HTTP_ERROR`
- `VWORLD_PROXY_INVALID_JSON`
- `VWORLD_DIRECT_AND_PROXY_FAILED`
- `ROAD_FILE_NOT_FOUND`
- `ROAD_GEOCODE_FAILED`
- `PARCEL_NOT_FOUND`
- `PARCEL_COORDINATE_MISSING`
- `INVALID_COORDINATE`
- `INVALID_ADDRESS_QUERY`
- `MAP_ADDRESS_NOT_FOUND`
- `MAP_PNU_DATA_INVALID`
- `INVALID_PNU`
- `UNAUTHORIZED`
- `INVALID_CREDENTIALS`
- `EMAIL_ALREADY_EXISTS`
- `EMAIL_REQUIRED`
- `ACCOUNT_NOT_FOUND`
- `VERIFICATION_NOT_FOUND`
- `VERIFICATION_PURPOSE_MISMATCH`
- `VERIFICATION_EMAIL_MISMATCH`
- `VERIFICATION_USED`
- `VERIFICATION_EXPIRED`
- `VERIFICATION_ATTEMPTS_EXCEEDED`
- `VERIFICATION_CODE_INVALID`
- `BULK_FILE_INVALID`
- `BULK_ROW_LIMIT_EXCEEDED`
- `BULK_JOB_NOT_FOUND`
- `BULK_JOB_NOT_READY`
- `PROFILE_IMAGE_INVALID`
- `PROFILE_IMAGE_TOO_LARGE`
- `PROFILE_UPDATE_EMPTY`
- `PASSWORD_MISMATCH`
- `PASSWORD_SAME`
- `WITHDRAW_CONFIRM_INVALID`
- `QUERY_LOG_NOT_FOUND`
