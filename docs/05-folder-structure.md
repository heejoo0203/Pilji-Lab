# 폴더 구조

## 1. 현재 구조 (AS-IS)
```text
autoLV/
  apps/
    api/
      app/
        api/
          auth.py
          health.py
          land.py
        core/
          config.py
          security.py
        db/
          base.py
          session.py
        models/
          user.py
        repositories/
          user_repository.py
        schemas/
          auth.py
          land.py
        services/
          auth_service.py
          road_name_service.py
          vworld_service.py
      scripts/
        reset_db_and_seed_admin.py
      .env.example
      requirements.txt
      README.md
    web/
      app/
        (main)/
          layout.tsx
          search/page.tsx
          files/page.tsx
          history/page.tsx
        components/
          auth-provider.tsx
          auth-modal.tsx
        lib/
          types.ts
          address.ts
          history-storage.ts
        globals.css
        layout.tsx
        page.tsx
      public/
        ld_codes.json
      package.json
  docs/
    01-requirements.md
    02-system-architecture.md
    03-api-spec.md
    04-db-schema.md
    05-folder-structure.md
    feature-spec.md
    architecture.svg
    TN_SPRD_RDNM.txt
  backend/   # 레거시 코드
  crawler/   # 레거시 코드
  frontend/  # 레거시 코드
  infra/
  packages/
  README.md
```

## 2. 참고 사항
- `docs/TN_SPRD_RDNM.txt`는 도로명 자음/목록 필터링의 기준 데이터입니다.
- 조회기록은 현재 `apps/web`의 localStorage로 관리됩니다.
- `.env`, `.env.*`는 `.gitignore`로 제외되고 `.env.example`만 버전관리합니다.

## 3. 다음 단계 정리 계획
- `apps/worker` 추가(Celery/비동기 작업)
- `apps/api`에 엑셀 업로드/작업상태/다운로드 API 추가
- 서버 DB에 조회기록/작업기록 테이블 추가
