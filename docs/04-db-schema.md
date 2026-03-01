# 데이터베이스 스키마 (PostgreSQL)

## ERD 요약
- users 1:N query_logs
- users 1:N excel_jobs
- excel_jobs 1:N excel_job_rows
- query_logs N:1 address_norm_cache (선택 캐시)

## 테이블

### users
- id UUID PK
- email VARCHAR(255) UNIQUE NOT NULL
- password_hash TEXT NOT NULL
- full_name VARCHAR(100) NULL
- role VARCHAR(20) NOT NULL DEFAULT 'user'
- auth_provider VARCHAR(20) NOT NULL DEFAULT 'local'
- created_at TIMESTAMPTZ NOT NULL DEFAULT now()
- updated_at TIMESTAMPTZ NOT NULL DEFAULT now()

### query_logs
- id UUID PK
- user_id UUID NULL FK users(id)
- query_type VARCHAR(20) NOT NULL  -- manual|excel
- raw_address TEXT NOT NULL
- normalized_ld_code CHAR(10) NULL
- normalized_is_san BOOLEAN NULL
- normalized_main_no INT NULL
- normalized_sub_no INT NULL
- result_status VARCHAR(20) NOT NULL -- ok|failed
- result_payload JSONB NULL
- created_at TIMESTAMPTZ NOT NULL DEFAULT now()

인덱스:
- (user_id, created_at desc)
- (normalized_ld_code, normalized_main_no, normalized_sub_no)

### excel_jobs
- id UUID PK
- user_id UUID NOT NULL FK users(id)
- original_filename TEXT NOT NULL
- stored_input_key TEXT NOT NULL
- stored_output_key TEXT NULL
- status VARCHAR(20) NOT NULL -- queued|running|completed|failed|partial_failed
- address_column TEXT NULL
- confidence NUMERIC(4,3) NULL
- total_rows INT NOT NULL DEFAULT 0
- processed_rows INT NOT NULL DEFAULT 0
- success_rows INT NOT NULL DEFAULT 0
- failed_rows INT NOT NULL DEFAULT 0
- error_message TEXT NULL
- created_at TIMESTAMPTZ NOT NULL DEFAULT now()
- started_at TIMESTAMPTZ NULL
- completed_at TIMESTAMPTZ NULL

인덱스:
- (user_id, created_at desc)
- (status, created_at desc)

### excel_job_rows
- id BIGSERIAL PK
- job_id UUID NOT NULL FK excel_jobs(id) ON DELETE CASCADE
- row_number INT NOT NULL
- raw_address TEXT NOT NULL
- normalized JSONB NULL
- status VARCHAR(20) NOT NULL -- ok|failed
- error_code VARCHAR(100) NULL
- error_message TEXT NULL
- result_payload JSONB NULL
- created_at TIMESTAMPTZ NOT NULL DEFAULT now()

인덱스:
- (job_id, row_number)
- (job_id, status)

### refresh_tokens (선택, 강제 로그아웃용)
- id UUID PK
- user_id UUID NOT NULL FK users(id)
- token_hash TEXT NOT NULL
- expires_at TIMESTAMPTZ NOT NULL
- revoked_at TIMESTAMPTZ NULL
- created_at TIMESTAMPTZ NOT NULL DEFAULT now()

## 보존 정책
- excel_job_rows: 90일 보관 (설정 가능)
- query_logs: 180일 보관 (설정 가능)
