# apps/api

## Run
```bash
cd apps/api
pip install -r requirements.txt
python scripts/run_migrations.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Worker
```bash
cd apps/api
python scripts/run_bulk_worker.py
```

## Environment
- template: `apps/api/.env.example`
- local file: `apps/api/.env`

주요 항목:
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `JWT_REFRESH_SECRET_KEY`
- `ADMIN_SEED_EMAIL`
- `ADMIN_SEED_PASSWORD`
- `ADMIN_SEED_NAME`
- `VWORLD_API_KEY`
- `VWORLD_API_DOMAIN`
- `VWORLD_PROXY_URL`
- `VWORLD_PROXY_TOKEN`
- `ROAD_NAME_FILE_PATH`
- `LD_CODE_FILE_PATH`
- `BULK_STORAGE_DIR`
- `PROFILE_IMAGE_DIR`

기본 탐색 경로:
- 도로명 원본: `apps/api/TN_SPRD_RDNM.txt`
- 법정동 코드: `apps/web/public/ld_codes.json`

## Migrations
```bash
cd apps/api
alembic upgrade head
```

## Utilities
- `scripts/run_migrations.py`
- `scripts/run_bulk_worker.py`
- `scripts/reset_db_and_seed_admin.py`
- `scripts/run_accuracy_golden_set.py`
- `scripts/run_zone_flow_smoke.py`
