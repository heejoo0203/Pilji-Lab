# Pilji-Lab

필지랩은 개별 필지 조회와 지도 기반 구역 분석을 한 흐름으로 묶은 토지 작업 도구다.
단건 조회, 지도 워크스페이스, 구역 저장/비교, 파일 일괄 처리, 이용내역 재열람까지 현재 운영 경로 기준으로 정리돼 있다.

## Applications
- `apps/web`: Next.js 웹 애플리케이션
- `apps/api`: FastAPI API와 bulk worker 스크립트
- `apps/mobile`: Capacitor Android wrapper
- `infra/vworld-proxy`: VWorld 고정 IP 우회 프록시

## Core Features
- 개별 조회: 지번/도로명 기반 공시지가 조회, 연도별 이력, 토지특성 조회
- 지도 조회: Kakao Maps 기반 클릭 조회, 주소 검색, 지적도 토글, CSV 내보내기
- 구역 분석: 폴리곤 분석, 포함/경계/제외 판정, 저장, 비교, 리뷰
- 파일 처리: 최대 10,000행 비동기 처리, 진행률 확인, 결과 다운로드
- 이용내역: 조회 기록 복원, 필터링, 정렬, 선택 삭제
- 계정 관리: 회원가입, 로그인, 프로필 수정, 비밀번호 변경, 탈퇴

## Stack
- Web: `Next.js 15`, `React 19`, `TypeScript`, `Tailwind CSS`
- API: `FastAPI`, `SQLAlchemy`, `Alembic`
- Data: `PostgreSQL`, `PostGIS`, `Redis`, local `SQLite`
- External: `VWorld`, `Kakao Maps`, 건축물대장 API
- Deploy: `Vercel`, `Railway`, `Neon`, `AWS EC2`(VWorld proxy)

## Repository Layout
```text
Pilji-Lab/
  apps/
    api/
    web/
    mobile/
  docs/
    assets/
    releases/
  infra/
    docker/
    vworld-proxy/
  README.md
```

## Local Setup
```bash
git clone https://github.com/heejoo0203/Pilji-Lab.git
cd Pilji-Lab
```

API:
```bash
cp apps/api/.env.example apps/api/.env
cd apps/api
pip install -r requirements.txt
python scripts/run_migrations.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Web:
```bash
cp apps/web/.env.example apps/web/.env.local
cd apps/web
npm install
npm run dev:clean
```

Bulk worker:
```bash
cd apps/api
python scripts/run_bulk_worker.py
```

Android wrapper:
```bash
cd apps/mobile
npm install
npx cap sync android
```

## Deployment
- Web: Vercel
- API: Railway
- Database: Neon PostgreSQL + PostGIS
- Cache/Queue: Redis
- Proxy: `infra/vworld-proxy`

## Documentation
- [Requirements](docs/01-requirements.md)
- [Architecture](docs/02-system-architecture.md)
- [API Spec](docs/03-api-spec.md)
- [DB Schema](docs/04-db-schema.md)
- [Folder Structure](docs/05-folder-structure.md)
- [Deployment](docs/06-deployment.md)
- [Latest Release](docs/releases/v2.2.1.md)
