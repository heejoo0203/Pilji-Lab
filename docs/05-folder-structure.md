# 폴더 구조

기준일: `2026-03-11`

## 1. 현재 소스 트리
```text
Pilji-Lab/
  apps/
    api/
      alembic/
      app/
        api/
        core/
        db/
        models/
        repositories/
        schemas/
        services/
      scripts/
      .env.example
      README.md
      alembic.ini
      ld_codes.json
      requirements.txt
      TN_SPRD_RDNM.txt
    web/
      app/
      public/
      scripts/
      .env.example
      README.md
      package.json
      tsconfig.json
    mobile/
      android/
      assets/
      www/
      capacitor.config.json
      package.json
      README.md
  docs/
    assets/
      brand/
      diagrams/
    releases/
    01-requirements.md
    02-system-architecture.md
    03-api-spec.md
    04-db-schema.md
    05-folder-structure.md
    06-deployment.md
  infra/
    docker/
    vworld-proxy/
  README.md
```

## 2. 디렉터리 역할
- `apps/api`: 운영 API, DB 마이그레이션, bulk worker 스크립트
- `apps/web`: 운영 웹 애플리케이션
- `apps/mobile`: Android wrapper와 빌드 자산
- `docs`: 공개 문서와 릴리즈 노트
- `infra/docker`: 로컬 또는 보조 배포용 도커 자산
- `infra/vworld-proxy`: 고정 IP 기반 VWorld 우회 프록시

## 3. 주요 경로
- 도로명 원본 데이터: `apps/api/TN_SPRD_RDNM.txt`
- 법정동 코드: `apps/web/public/ld_codes.json`
- API 실행 진입점: `apps/api/app/main.py`
- 웹 지도 화면: `apps/web/app/(main)/map/page.tsx`
- bulk worker: `apps/api/scripts/run_bulk_worker.py`
- APK 다운로드 경로: `apps/web/public/downloads`

## 4. 운영 기준 정리
- 레거시 `backend`, `frontend`, `crawler` 디렉터리는 제거했다.
- 생성물과 로컬 산출물은 저장소 기준 구조에 포함하지 않는다.
- 문서 루트에는 운영 기준 문서만 남기고 이미지와 릴리즈 기록은 하위 디렉터리로 분리한다.
