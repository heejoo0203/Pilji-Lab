# 데이터 저장 구조 (현재 구현 기준)

## 1. 서버 DB (AS-IS)
현재 서버 DB는 SQLite 기반이며 사용자 인증 관련 데이터만 저장합니다.

### users
- `id` (String(36), PK)
- `email` (String(255), UNIQUE, NOT NULL)
- `password_hash` (String(255), NOT NULL)
- `full_name` (String(100), NULL)
- `role` (String(20), NOT NULL, 기본값 `user`)
- `auth_provider` (String(20), NOT NULL, 기본값 `local`)
- `created_at` (DateTime, NOT NULL)
- `updated_at` (DateTime, NOT NULL)

비고:
- 관리자 계정 생성 스크립트에서 `role=admin`을 사용합니다.
- SQLAlchemy `Base.metadata.create_all()`로 테이블을 생성합니다.

## 2. 클라이언트 저장소 (AS-IS)
조회기록은 현재 서버 DB가 아니라 브라우저 `localStorage`에 저장됩니다.

키:
- `autolv_search_history_v1`

구조:
```json
[
  {
    "id": "1700000000000-ab12cd",
    "ownerKey": "user@example.com",
    "시각": "2026-03-02T10:20:30.000Z",
    "유형": "지번",
    "주소요약": "서울특별시 강남구 도곡동 970",
    "결과": [
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
]
```

## 3. 초기화/시드
명령:
```bash
cd apps/api
python scripts/reset_db_and_seed_admin.py
```

효과:
- DB 초기화(drop/create)
- 관리자 계정 생성
  - 이메일: `admin@admin.com`
  - 비밀번호: `admin1234`

## 4. 다음 단계 (TO-BE)
다음 릴리스에서 아래 구조를 서버 DB에 추가할 예정입니다.
- 단건 조회 기록 테이블(`query_logs`)
- 파일 업로드 작업 테이블(`excel_jobs`)
- 파일 행 단위 처리 결과 테이블(`excel_job_rows`)
- refresh token 저장/철회 테이블(`refresh_tokens`, 선택)
