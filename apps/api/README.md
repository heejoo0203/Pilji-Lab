# apps/api

## 실행 방법
```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 환경변수
- `CORS_ORIGINS`: 허용할 웹 출처 목록(쉼표 구분)
  - 기본값: `http://127.0.0.1:3000,http://localhost:3000`
- `DATABASE_URL`: DB 연결 문자열 (기본값: `sqlite:///./autolv.db`)
- `JWT_SECRET_KEY`: Access 토큰 서명 키
- `JWT_REFRESH_SECRET_KEY`: Refresh 토큰 서명 키

## 엔드포인트
- `GET /` : 서비스 상태 확인
- `GET /health` : 헬스체크
- `POST /api/v1/auth/register` : 회원가입
- `POST /api/v1/auth/login` : 로그인(쿠키 발급)
- `POST /api/v1/auth/logout` : 로그아웃(쿠키 삭제)
- `GET /api/v1/auth/me` : 현재 로그인 사용자 조회

## DB 초기화 및 관리자 계정 생성
```bash
cd apps/api
python scripts/reset_db_and_seed_admin.py
```

생성 계정:
- 닉네임: `admin`
- 이메일: `admin@admin.com`
- 비밀번호: `admin1234`
