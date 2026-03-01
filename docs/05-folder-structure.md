# 폴더 구조 (목표)

```text
autoLV/
  apps/
    web/                  # Next.js frontend
    api/                  # FastAPI backend
      app/
        api/
        core/
        models/
        schemas/
        services/
        repositories/
    worker/               # Celery worker
      jobs/
      tasks/
  packages/
    shared/
      contracts/          # shared API contracts
      utils/
  infra/
    docker/
    scripts/
    sql/
  docs/
    01-requirements.md
    02-system-architecture.md
    03-api-spec.md
    04-db-schema.md
    05-folder-structure.md
    architecture.svg
  backend/                # legacy (to be migrated)
  frontend/               # legacy (to be migrated)
  crawler/                # legacy (to be migrated)
```

## 마이그레이션 노트
- 기존 `backend/frontend/crawler`는 참고용으로 유지한다.
- 신규 구현은 `apps/*`에서 시작한다.
