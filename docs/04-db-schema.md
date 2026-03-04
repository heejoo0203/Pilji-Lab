# 데이터 저장 구조 (v2.1.0 기준)

## 1. DB 런타임 구성
- 로컬 개발 기본 DB: SQLite (`apps/api/autolv.db`)
- 운영 배포 DB: PostgreSQL (Neon/Railway)
- 공간 확장: PostgreSQL에서 `postgis` 확장 사용
- 스키마 관리: Alembic (`apps/api/alembic/versions`)

마이그레이션 이력:
- `20260302_0001`: `users`, `bulk_jobs`
- `20260302_0002`: `query_logs`
- `20260304_0003`: `parcels` + PostGIS 컬럼/인덱스(`geog`, `geom`)
- `20260305_0004`: `email_verifications` + `users` 약관 컬럼
- `20260305_0005`: `users.phone_number`

## 2. 테이블 상세
### 2.1 users
- `id` (String(36), PK)
- `email` (String(255), UNIQUE, NOT NULL, INDEX)
- `password_hash` (String(255), NOT NULL)
- `full_name` (String(100), NULL)
- `phone_number` (String(20), NULL, INDEX)
- `profile_image_path` (String(500), NULL)
- `role` (String(20), NOT NULL, 기본값 `user`)
- `auth_provider` (String(20), NOT NULL, 기본값 `local`)
- `terms_version` (String(30), NOT NULL)
- `terms_snapshot` (Text, NOT NULL)
- `terms_accepted_at` (DateTime(timezone=True), NULL)
- `created_at` (DateTime(timezone=True), NOT NULL)
- `updated_at` (DateTime(timezone=True), NOT NULL)

### 2.2 bulk_jobs
- `id` (String(36), PK)
- `user_id` (String(36), FK -> `users.id`, NOT NULL, INDEX)
- `file_name` (String(255), NOT NULL)
- `upload_path` (String(500), NOT NULL)
- `result_path` (String(500), NULL)
- `status` (String(20), NOT NULL, INDEX)
- `total_rows` (Integer, NOT NULL)
- `processed_rows` (Integer, NOT NULL)
- `success_rows` (Integer, NOT NULL)
- `failed_rows` (Integer, NOT NULL)
- `error_message` (Text, NULL)
- `created_at` (DateTime(timezone=True), NOT NULL)
- `updated_at` (DateTime(timezone=True), NOT NULL)

상태 값:
- `queued`
- `processing`
- `completed`
- `failed`

### 2.3 query_logs
- `id` (String(36), PK)
- `user_id` (String(36), FK -> `users.id`, NOT NULL, INDEX)
- `search_type` (String(10), NOT NULL)  
  허용: `jibun | road | map`
- `pnu` (String(19), NOT NULL, INDEX)
- `address_summary` (String(300), NOT NULL)
- `rows_json` (Text, NOT NULL)  
  조회 결과 행(JSON 문자열)
- `result_count` (Integer, NOT NULL)
- `created_at` (DateTime(timezone=True), NOT NULL, INDEX)

### 2.4 parcels
- `id` (String(36), PK)
- `pnu` (String(19), UNIQUE, NOT NULL, INDEX)
- `lat` (Float, NOT NULL)
- `lng` (Float, NOT NULL)
- `area` (Float, NULL)
- `price_current` (BigInteger, NULL)
- `price_previous` (BigInteger, NULL)
- `updated_at` (DateTime(timezone=True), NOT NULL)
- `geog` (Geography POINT, 4326, PostgreSQL only)
- `geom` (Geometry POLYGON, 4326, PostgreSQL only)

공간 인덱스(PostgreSQL):
- `idx_parcels_geog_gist` (GIST on `geog`)
- `idx_parcels_geom_gist` (GIST on `geom`)

### 2.5 email_verifications
- `id` (String(36), PK)
- `purpose` (String(30), NOT NULL, INDEX)  
  허용: `signup | find_id | reset_password`
- `email` (String(255), NOT NULL, INDEX)
- `full_name` (String(100), NULL)
- `code_hash` (String(128), NOT NULL)
- `attempt_count` (Integer, NOT NULL)
- `max_attempts` (Integer, NOT NULL)
- `expires_at` (DateTime(timezone=True), NOT NULL, INDEX)
- `verified_at` (DateTime(timezone=True), NULL)
- `consumed_at` (DateTime(timezone=True), NULL)
- `meta_json` (Text, NOT NULL)
- `created_at` (DateTime(timezone=True), NOT NULL)
- `updated_at` (DateTime(timezone=True), NOT NULL)

## 3. 저장소(파일) 구조
- 대량조회 업로드/결과: `apps/api/storage/bulk`
- 프로필 이미지: `apps/api/storage/profile_images`

파일은 DB BLOB이 아닌 경로(`upload_path`, `result_path`, `profile_image_path`)로 관리한다.

## 4. 조회기록 저장 정책
- 로그인 사용자의 개별/지도 조회 기록은 `query_logs`에 서버 영구 저장된다.
- 로그아웃 후 재로그인해도 기록이 유지된다.
- 기록 UI 필터/정렬은 DB 조회 결과 기반으로 동작한다.

## 5. 운영 체크 포인트
1. `alembic_version` 테이블에서 `head` 적용 여부 확인
2. `users.phone_number`, `users.terms_*` 컬럼 존재 확인
3. `query_logs`, `email_verifications`, `parcels` 테이블 존재 확인
4. PostgreSQL 환경에서 PostGIS 확장/공간 인덱스 생성 여부 확인
