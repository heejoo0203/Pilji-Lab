# 필지랩

필지랩은 **정확도 중심 필지·구역 작업 시스템**입니다.  
단순 공공정보 조회를 넘어서, `개별 필지 확인 -> 지도 기반 검토 -> 구역 집계 -> 파일 일괄 처리 -> 저장/재열람`까지 한 흐름으로 연결하는 토지 분석 도구를 목표로 합니다.

## 제품 방향
- 핵심 포지션: `공공 토지정보 조회 서비스`와 `상위 사업성 분석 플랫폼` 사이의 정밀 작업 도구
- 핵심 가치: 더 많은 정보를 붙이는 것보다, **필지를 더 빠르게 검토하고 구역을 더 정확하게 정리하는 것**
- 현재 우선순위:
  - 지도/구역조회 작업 흐름 안정화
  - 파일분석을 품질 관리 도구처럼 개선
  - 저장/이력/비교 흐름 강화
  - 모든 새 기능을 desktop/tablet/mobile 기준으로 함께 설계

## 이번 주 개발 초점
- 새 대형 기능 추가보다 **현행 기능 안정화와 UI/UX 디벨롭**을 우선합니다.
- 특히 다음 5가지를 중심으로 다듬고 있습니다.
  1. 지도조회/구역조회 워크스페이스 완성도
  2. 전 페이지 UI 규격 통일
  3. 파일분석 오류 진단/재작업 가독성
  4. 조회기록을 작업 내역처럼 재사용하는 흐름 강화
  5. 상태/오류/신뢰도 표현과 모바일 usable 수준 정리

## 릴리즈 상태
- 현재 기준 버전: **v3.0 준비 중**
- 이전 안정 태그: `v1.0.0` (2026-03-02)
- v2 핵심 확장: **카카오 지도조회 + 지도조회 기록 연동 + 조회기록 고급 필터/정렬**
- v2.1 핵심 확장: **인증 UX 개선(이메일 중복확인, 약관 팝업, 아이디 저장, 이름/연락처 기반 아이디 찾기)**
- v2.2 핵심 확장: **지도조회 완성도 강화 + 정책 페이지 + Android Wrapper 배포 정리**
- 최신 확장: **구역조회 정확도 고도화 2차(AI 추천/이상치/피드백 저장)**

## 주요 기능
### 1) 개별 필지 검토
- 지번 조회: `시/도 -> 시/군/구 -> 읍/면/동 -> 본번/부번`
- 도로명 조회: `시/도 -> 시/군/구 -> 초성 -> 도로명 -> 건물번호`
- VWorld API 연동 실데이터 조회
- 연도별 공시지가 결과 표시
- 지도조회로 이어보기, 토지특성 확인, 조회기록 복원 지원

### 2) 지도 기반 작업 공간
- Kakao 지도 기반 기본조회(비로그인 가능)
- 주소 / 지번 / PNU 검색
- 지도 클릭 조회, 지적도 토글, CSV 내보내기
- 구역조회(로그인 필요)
  - 폴리곤 분석
  - 필지 포함/경계/제외 상태 구분
  - overlap / confidence / AI 추천 / 이상치 표시
  - 저장 구역 재열람, 비교, 수동 검토

### 3) 파일 분석 (최대 10,000행)
- 표준 양식/가이드 제공
- 업로드 파일 헤더 자동 매핑 및 전처리
- Redis 큐 + 워커 분리형 비동기 처리 + 진행률 표시
- 완료 시 결과 파일 다운로드
- 작업 이력 페이징/선택 삭제
- 실패 원인 분류와 품질 진단 UX 지속 고도화 중

### 4) 구역 분석 지표
- 구역조회 결과에 건축 지표 요약 제공:
  - 건축물 수 / 노후 건축물 수 / 노후도(%)
  - 평균 사용승인년도
  - 총대지면적 / 총연면적 / 평균 용적률
  - 과소필지 비율(기본 90㎡ 미만)
- 구역 정확도 요약 제공:
  - 확정 포함 / 경계 후보 / 제외
  - 포함 필지 기준 총가치
  - 구역 내부 기준 총가치
  - 필지별 `overlap_ratio`, `confidence_score`, `inclusion_mode`
  - 필지별 `ai_recommendation`, `ai_confidence_score`, `selection_origin`
  - 구역 요약 `AI 추천 포함 수`, `AI 검토 필요 수`, `AI 요약 리포트`
  - 규칙 기반 이상치 검토(`anomaly_level`)

### 5) 이용내역 / 저장 결과
- 로그인 사용자 기준 DB 영속 저장
- 단건/지도 조회 기록 통합 관리
- 기록 클릭 시 해당 페이지(`개별조회` 또는 `지도조회`)로 복원 이동
- 필터:
  - 유형
  - 시/도(선택형)
  - 시/군/구(선택형)
- 헤더 클릭 3단 정렬:
  - 내림차순 -> 오름차순 -> 기본
  - 적용 컬럼: 일시, 유형, 주소, 결과건수
- 저장 구역은 재열람/이름 수정/삭제/비교가 가능

### 6) 인증/계정
- 회원가입/로그인/로그아웃
- 회원가입 이메일 중복확인 + 이메일 인증코드 검증
- 회원가입 입력 확장: 이름 + 연락처 + 약관 팝업 동의
- 아이디 저장(localStorage) 지원
- 아이디 찾기(이름 + 연락처, 마스킹 이메일 응답)
- 비밀번호 표시 토글
- 프로필 수정(닉네임/이미지)
- 비밀번호 변경
- 회원 탈퇴
- HttpOnly 쿠키 기반 세션 처리

## 기술 스택
- Frontend: `Next.js 15`, `React 19`, `TypeScript`, `Tailwind CSS`
- Backend: `FastAPI`, `SQLAlchemy`, `Pydantic Settings`, `Alembic`
- Database: `PostgreSQL`(운영), `SQLite`(로컬), `PostGIS`(지도 확장 대비)
- Cache/Queue: `Redis`(캐시/비동기 처리)
- External API: `VWorld`, `Kakao Maps JS SDK`
- Deploy: `Vercel`(Web), `Railway`(API/Redis), `Neon(Postgres/PostGIS)`
- Network Fallback: `AWS EC2 고정 IP VWorld Proxy` (필요 시)

## 로컬 실행
## 1. 저장소
```bash
git clone https://github.com/heejoo0203/autoLV.git
cd autoLV
```

## 2. 환경변수
### API
```bash
copy apps\\api\\.env.example apps\\api\\.env
```

### Web
```bash
copy apps\\web\\.env.example apps\\web\\.env.local
```

필수 주요 키:
- API(`apps/api/.env`)
  - `DATABASE_URL`
  - `VWORLD_API_KEY`
  - `VWORLD_API_DOMAIN`
  - `CORS_ORIGINS`
  - `ROAD_NAME_FILE_PATH`
  - `REDIS_URL`
  - `BULK_EXECUTION_MODE`, `BULK_QUEUE_NAME`, `BULK_QUEUE_PROCESSING_NAME`, `BULK_WORKER_POLL_SECONDS`
  - `MAIL_DELIVERY_MODE`, `MAIL_FROM`
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
  - (선택) `VWORLD_PROXY_URL`, `VWORLD_PROXY_TOKEN`
  - `MAP_ZONE_AI_ENABLED`, `MAP_ZONE_AI_INCLUDE_THRESHOLD`, `MAP_ZONE_AI_UNCERTAIN_THRESHOLD`
- Web(`apps/web/.env.local`)
  - `NEXT_PUBLIC_API_BASE_URL`
  - `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`
  - `NEXT_PUBLIC_MAP_CENTER_LAT`
  - `NEXT_PUBLIC_MAP_CENTER_LNG`

## 3. API 실행
```bash
cd apps/api
pip install -r requirements.txt
python scripts/run_migrations.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3-1. Bulk Worker 실행
```bash
cd apps/api
python scripts/run_bulk_worker.py
```

- 운영 환경에서는 API 프로세스와 별도 서비스로 실행하는 것을 권장합니다.
- `REDIS_URL`이 없거나 `BULK_EXECUTION_MODE=background`이면 기존 `BackgroundTasks` fallback으로 동작합니다.

## 4. Web 실행
```bash
cd apps/web
npm install
npm run dev:clean
```

접속:
- Web: `http://localhost:3000`
- API: `http://127.0.0.1:8000`

## Android APK (Capacitor)
```bash
cd apps/mobile
npm install
npx cap sync android
npm run android:build:debug
```

필지랩 APK 다운로드:
- 운영 URL: [`https://auto-lv.vercel.app/downloads/autoLV-android-release-v2.2.0.apk`](https://auto-lv.vercel.app/downloads/autoLV-android-release-v2.2.0.apk)
- 저장소 파일: [`apps/web/public/downloads/autoLV-android-release-v2.2.0.apk`](apps/web/public/downloads/autoLV-android-release-v2.2.0.apk)
- Play Console 업로드용 AAB: `apps/mobile/android/app/build/outputs/bundle/release/app-release.aab`

상세 가이드:
- `apps/mobile/README.md`

## 관리자 시드
```bash
cd apps/api
set ADMIN_SEED_EMAIL=your-admin-email@example.com
set ADMIN_SEED_PASSWORD=your-strong-password
set ADMIN_SEED_NAME=관리자
python scripts/reset_db_and_seed_admin.py
```

또는 마이그레이션 실행 전에 동일한 환경변수를 설정하면 초기 관리자 계정을 함께 생성할 수 있습니다.

## 배포 요약
- Web: Vercel (`apps/web`)
- API: Railway (`apps/api`)
- DB: Neon Postgres/PostGIS (또는 Railway Postgres)
- 상세 가이드: `docs/06-deployment.md`

## 문서
- 요구사항: `docs/01-requirements.md`
- 아키텍처: `docs/02-system-architecture.md`
- API 명세: `docs/03-api-spec.md`
- DB 스키마: `docs/04-db-schema.md`
- 폴더 구조: `docs/05-folder-structure.md`
- 배포 가이드: `docs/06-deployment.md`
- 구역 정확도 향상 설계안(v3): `docs/11-ai-zone-accuracy-plan.md`
- 릴리즈 노트(v1, 아카이브): `docs/07-release-notes-v1.0.0.md`
- 릴리즈 노트(최신): `docs/09-release-notes-v2.2.0.md`
- 포트폴리오/운영 개선: `docs/08-portfolio-enhancement.md`
- 기능 상세: `docs/feature-spec.md`
- 개인정보처리방침: `https://auto-lv.vercel.app/privacy`
- 계정삭제 안내(Play Console 제출용): `https://auto-lv.vercel.app/account-deletion`

## 레포 구조
```text
autoLV/
  apps/
    api/      # 현재 운영 API
    web/      # 현재 운영 웹
    mobile/   # Android wrapper
  docs/
  infra/
  backend/   # legacy (보관용)
  frontend/  # legacy (보관용)
  crawler/   # legacy (보관용)
```

## 기여 규칙
1. 기능 단위 커밋
2. Conventional Commits 사용
3. 코드 변경 시 문서 동기화

## 기여자
- heejoo0203
