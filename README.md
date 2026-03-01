# autoLV

autoLV는 지번/도로명 기반으로 개별공시지가를 조회하는 웹 서비스입니다.  
현재는 단건 조회와 인증 기능을 구현했으며, `v1` 범위로 파일조회(엑셀 대량 처리) 기능을 진행 중입니다.

## 현재 구현 기능
- 지번 검색: 시/도 → 시/군/구 → 읍/면/동 + 지번(일반/산, 본번/부번) 입력
- 도로명 검색: 시/도 → 시/군/구 → 자음 → 도로명 + 건물번호 입력
- 개별공시지가 실데이터 조회: VWorld API 연동
- 회원가입/로그인/로그아웃/내 정보 조회 (`HttpOnly` 쿠키 기반)
- 조회기록 페이지: 로그인 사용자 기준 최근순 표시, 클릭 시 결과 재열람
- 비로그인/로그인 상태에 따른 네비게이션 및 화면 분기

## 현재 미구현(다음 단계)
- 엑셀 업로드 및 10,000행 비동기 일괄 처리(v1 진행 중)
- 서버 DB 기반 조회기록 영구 저장
- 회원정보 수정/비밀번호 변경/회원탈퇴 실제 처리
- 소셜 로그인

## v1 파일조회 목표
- 표준 엑셀 양식 다운로드 및 입력 가이드 제공
- 열 순서가 달라도 자동 매핑/전처리로 주소 정규화 후 조회
- 원본 파일 구조를 유지하고 뒤쪽 열에 연도별 공시지가(최신순) 추가
- 로그인 사용자 기준 파일 작업 이력/진행상태/결과 다운로드 제공

## 기술 스택 (AS-IS)
- Web: Next.js 15, React 19, TypeScript, Tailwind CSS
- API: FastAPI, SQLAlchemy, Pydantic Settings
- DB: SQLite (`apps/api/autolv.db`)
- 외부 연동: VWorld API (개별공시지가, 주소 변환)

## 빠른 시작
### 1) 저장소 클론
```bash
git clone https://github.com/heejoo0203/autoLV.git
cd autoLV
```

### 2) API 환경변수 설정
`apps/api/.env` 파일을 만들고 아래 값을 설정합니다.
```env
CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
DATABASE_URL=sqlite:///./autolv.db
JWT_SECRET_KEY=change-me-access-key
JWT_REFRESH_SECRET_KEY=change-me-refresh-key
ACCESS_TOKEN_EXP_MINUTES=60
REFRESH_TOKEN_EXP_DAYS=14
VWORLD_API_BASE_URL=https://api.vworld.kr
VWORLD_API_DOMAIN=localhost
VWORLD_TIMEOUT_SECONDS=15
VWORLD_API_KEY=발급받은_키
ROAD_NAME_FILE_PATH=
```

참고:
- `VWORLD_API_DOMAIN=localhost` 기준으로 동작하도록 맞춰져 있습니다.
- `ROAD_NAME_FILE_PATH`를 비워두면 기본 경로 `docs/TN_SPRD_RDNM.txt`를 자동 탐색합니다.

### 3) API 실행
```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Web 실행
```bash
cd apps/web
npm install
npm run dev:clean
```

접속:
- Web: `http://localhost:3000`
- API: `http://127.0.0.1:8000`

## 관리자 계정 초기화 스크립트
```bash
cd apps/api
python scripts/reset_db_and_seed_admin.py
```

기본 계정:
- 이메일: `admin@admin.com`
- 비밀번호: `admin1234`

## 문서
- 요구사항: `docs/01-requirements.md`
- 시스템 아키텍처: `docs/02-system-architecture.md`
- API 명세: `docs/03-api-spec.md`
- DB/저장 구조: `docs/04-db-schema.md`
- 폴더 구조: `docs/05-folder-structure.md`
- 기능 상세: `docs/feature-spec.md`

## 레포 구조(요약)
```text
autoLV/
  apps/
    api/
    web/
  docs/
  backend/   # 레거시
  frontend/  # 레거시
  crawler/   # 레거시
```

## 기여
1. 기능 단위로 작업하고 커밋합니다.
2. Conventional Commit 메시지 규칙을 사용합니다.
3. 기능 변경 시 관련 문서를 함께 갱신합니다.

## 기여자
- heejoo0203
