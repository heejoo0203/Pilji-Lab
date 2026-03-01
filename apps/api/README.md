# apps/api

## 실행 방법
```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 환경변수
기본 템플릿: `apps/api/.env.example`  
실행 환경에서는 `apps/api/.env` 사용을 권장합니다.

주요 변수:
- `CORS_ORIGINS`: 허용할 웹 출처 목록(쉼표 구분)
- `DATABASE_URL`: DB 연결 문자열 (기본값 `sqlite:///./autolv.db`)
- `JWT_SECRET_KEY`: Access 토큰 서명 키
- `JWT_REFRESH_SECRET_KEY`: Refresh 토큰 서명 키
- `VWORLD_API_BASE_URL`: VWorld API 기본 URL
- `VWORLD_API_KEY`: VWorld 인증키
- `VWORLD_API_DOMAIN`: 발급받은 키의 허용 도메인(예: `localhost`)
- `ROAD_NAME_FILE_PATH`: 도로명 파일 경로(미입력 시 `docs/TN_SPRD_RDNM.txt` 자동 탐색)

## 엔드포인트
- `GET /` : 서비스 상태
- `GET /health` : 헬스체크
- `POST /api/v1/auth/register` : 회원가입
- `POST /api/v1/auth/login` : 로그인(쿠키 발급)
- `POST /api/v1/auth/logout` : 로그아웃(쿠키 삭제)
- `GET /api/v1/auth/me` : 현재 로그인 사용자 조회
- `POST /api/v1/land/single` : 지번/도로명 단건 공시지가 조회
- `GET /api/v1/land/road-initials` : 지역별 사용 가능한 도로명 자음 목록
- `GET /api/v1/land/road-names` : 지역+자음 기반 도로명 목록

## DB 초기화 및 관리자 계정 생성
```bash
cd apps/api
python scripts/reset_db_and_seed_admin.py
```

생성 계정:
- 닉네임: `admin`
- 이메일: `admin@admin.com`
- 비밀번호: `admin1234`
