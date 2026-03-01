# autoLV v2 (애자일 개발 계획)

기준일: 2026-03-01

## 프로젝트 목표
지번 주소 또는 도로명 주소를 입력해 개별공시지가를 조회하고, 로그인 사용자는 엑셀(최대 10,000행) 업로드를 통해 대량 조회, 결과 다운로드, 조회 이력 확인까지 할 수 있는 웹 서비스를 구축해야 한다.

핵심 요구사항:
- 지번/도로명 주소를 모두 지원해야 한다.
- 다건 조회를 지원해야 한다.
- 엑셀 업로드 대량 처리(최대 10,000행)를 지원해야 한다.
- 로그인 사용자만 엑셀 기능을 사용할 수 있어야 한다.
- 조회 이력을 최근순으로 제공해야 한다.

## 확정 기술 스택 (선택안 A)
- 프론트엔드: Next.js 15 + TypeScript + Tailwind + shadcn/ui
- 백엔드 API: FastAPI
- 비동기 워커: Celery
- 큐/캐시: Redis
- 데이터베이스: PostgreSQL
- 파일 스토리지: S3 호환 스토리지
- 배포: Vercel(Web), Railway(API/Worker/Redis), Neon(Postgres)

## 지금까지 완료된 작업

### 1) 기존 코드베이스 분석
기존 `backend/frontend/crawler` 구조와 코드 흐름을 전체 점검했다.

확인된 기존 동작:
- 프론트(HTML+JS)에서 법정동 선택/지번 입력 후 FastAPI를 호출한다.
- 백엔드에서 PNU를 생성한 뒤 VWorld API(공시지가/지목/면적)를 조회한다.
- CSV 다운로드 기능이 포함되어 있다.

### 2) v2 설계 문서 작성 완료 (`docs/`)
다음 문서를 신규 작성했다.
- `docs/01-requirements.md`: 요구사항(SRS)
- `docs/02-system-architecture.md`: 시스템 아키텍처 설명
- `docs/03-api-spec.md`: API 명세 초안
- `docs/04-db-schema.md`: DB 스키마 초안
- `docs/05-folder-structure.md`: 목표 폴더 구조
- `docs/architecture.svg`: 시스템/데이터 흐름 아키텍처 다이어그램

### 3) v2 폴더 골격 생성 완료
아래 구조를 생성했다.
- `apps/web`
- `apps/api/app/{api,core,models,schemas,services,repositories}`
- `apps/worker/{jobs,tasks}`
- `packages/shared/{contracts,utils}`
- `infra/{docker,scripts,sql}`

### 4) 개발 방식 전환 확정
초기 계획(순차형)에서 애자일 방식으로 전환했다.
- 기능 단위로 UI+API+DB를 함께 완성해야 한다.
- 단계별로 배포 가능한 상태를 유지해야 한다.
- 불확실성(인프라/데이터 구조)을 초기에 제거해야 한다.

## 현재 디렉토리 구조 (요약)
```text
autoLV/
  backend/                # legacy
  frontend/               # legacy
  crawler/                # legacy
  apps/
    web/
    api/
      app/
        api/
        core/
        models/
        schemas/
        services/
        repositories/
    worker/
      jobs/
      tasks/
  packages/
    shared/
      contracts/
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
```

## 앞으로 할 작업 (애자일 로드맵)

### 0단계. 배포 가능한 최소 골격
목표: 첫날에 Hello World를 배포해야 한다.
- [ ] `apps/web` Next.js를 부트스트랩해야 한다.
- [ ] `apps/api` FastAPI를 부트스트랩하고 `/health`를 제공해야 한다.
- [ ] Vercel/Railway/Neon 연결 환경변수를 정의해야 한다.
- [ ] 환경변수 템플릿(`.env.example`)을 작성해야 한다.

완료 기준:
- Web/API 각각 배포 URL에서 정상 응답을 확인해야 한다.

### 1단계. 인증 MVP (기능 단위 E2E)
목표: 로그인 기능을 end-to-end로 완성해야 한다.
- [ ] DB `users`/`refresh_tokens`를 적용해야 한다.
- [ ] 회원가입/로그인/로그아웃 API를 구현해야 한다.
- [ ] JWT + HttpOnly Cookie를 적용해야 한다.
- [ ] 로그인/로그아웃 UI를 구현해야 한다.
- [ ] 보호 라우트(엑셀 업로드 페이지 접근 제한)를 구현해야 한다.

완료 기준:
- 로그인 상태에서만 보호 페이지 접근이 가능해야 한다.

### 2단계. 수동 주소 조회 MVP
목표: 지번/도로명 입력 조회를 제공해야 한다.
- [ ] 주소 정규화 로직(도로명 -> 표준 키)을 구현해야 한다.
- [ ] 단건/다건 조회 API를 구현해야 한다.
- [ ] 결과 테이블 UI를 구현해야 한다.
- [ ] 실패 케이스 에러 표시를 구현해야 한다.
- [ ] 조회 로그(`query_logs`)를 저장해야 한다.

완료 기준:
- 지번/도로명 혼합 입력 조회가 성공해야 한다.

### 3단계. 기록 페이지
목표: 최근 조회 이력을 제공해야 한다.
- [ ] `GET /history/queries`를 구현해야 한다.
- [ ] 최근순 목록 UI를 구현해야 한다.
- [ ] 필터(기간/상태/키워드)를 구현해야 한다.

완료 기준:
- 로그인 사용자가 과거 조회 내역을 재확인할 수 있어야 한다.

### 4단계. 엑셀 대량 처리
목표: 최대 10,000행 비동기 처리를 제공해야 한다.
- [ ] 파일 업로드 API(`POST /excel/jobs`)를 구현해야 한다.
- [ ] 주소 열 자동 감지(헤더/샘플 스코어)를 구현해야 한다.
- [ ] Celery worker 비동기 처리를 구현해야 한다.
- [ ] 진행률/상태 조회 API를 구현해야 한다.
- [ ] 결과 파일 생성 및 다운로드를 구현해야 한다.
- [ ] 엑셀 작업 이력 화면을 연동해야 한다.

완료 기준:
- 10,000행 입력 파일 처리 후 결과 다운로드가 가능해야 한다.

### 5단계. 운영 안정화
- [ ] 레이트리밋/재시도/타임아웃을 적용해야 한다.
- [ ] 로깅/모니터링을 구축해야 한다.
- [ ] 에러코드 표준화를 최종 확정해야 한다.
- [ ] 기본 테스트(핵심 API/주소 정규화/작업 큐)를 추가해야 한다.

## API/DB/문서 동기화 규칙
변경 시 아래 3가지를 반드시 동시 반영해야 한다.
1. `docs/03-api-spec.md`
2. `docs/04-db-schema.md`
3. 구현 코드 (`apps/api`, `apps/web`, `apps/worker`)

## VSCode에서 이어서 작업하는 방법

### 1) 열기
- VSCode에서 폴더를 연다: `D:\Users\Desktop\HJ\04_코딩\autoLV\autoLV`

### 2) 우선 확인 파일
- `README.md` (현재 파일)
- `docs/01-requirements.md`
- `docs/02-system-architecture.md`
- `docs/03-api-spec.md`
- `docs/04-db-schema.md`

### 3) 바로 시작할 구현 우선순위
1. `apps/web` Next.js 초기화
2. `apps/api` FastAPI + `/health`
3. 인프라 환경변수/배포 설정
4. 로그인 기능 E2E

## 메모 (기존 레거시 코드 관련)
- 기존 `backend/frontend/crawler`는 참고용 레거시로 유지한다.
- 신규 구현은 `apps/*` 기준으로 진행한다.
- 기능 이관 완료 후 레거시 경로를 단계적으로 정리한다.
