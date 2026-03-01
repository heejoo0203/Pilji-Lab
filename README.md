# autoLV

지번 주소/도로명 주소를 기반으로 개별공시지가를 조회하고, 로그인 사용자는 엑셀 대량 조회(최대 10,000행)와 결과 다운로드, 조회 이력 관리를 할 수 있는 웹 서비스입니다.

## 주요 기능
- 지번 주소 조회
- 도로명 주소 조회
- 다건 주소 일괄 조회
- 엑셀 업로드 기반 비동기 대량 조회 (최대 10,000행)
- 조회 결과 엑셀 다운로드
- 로그인 사용자 전용 조회 이력 페이지

## 기술 스택
- Frontend: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui
- Backend: FastAPI, Celery, Redis
- Database: PostgreSQL
- Infra: Vercel, Railway, Neon, S3 호환 스토리지

## 빠른 시작
### 1) 저장소 클론
```bash
git clone https://github.com/heejoo0203/autoLV.git
cd autoLV
```

### 2) 프로젝트 문서 확인
- 요구사항: `docs/01-requirements.md`
- 시스템 아키텍처: `docs/02-system-architecture.md`
- API 명세: `docs/03-api-spec.md`
- DB 스키마: `docs/04-db-schema.md`
- 폴더 구조: `docs/05-folder-structure.md`

### 3) 개발 환경 준비(예정)
아래 구성은 단계적으로 추가됩니다.
- `apps/web`: Next.js 앱
- `apps/api`: FastAPI 앱
- `apps/worker`: Celery 워커

## 프로젝트 구조
```text
autoLV/
  apps/
    web/
    api/
    worker/
  backend/      # 레거시 코드(참고용)
  crawler/      # 레거시 코드(참고용)
  frontend/     # 레거시 코드(참고용)
  docs/
  infra/
  packages/
  README.md
```

## 문서 정책
- README는 제품 소개와 사용 안내 중심으로 유지합니다.
- 설계/명세/세부 계획은 `docs/*`에서 관리합니다.
- 기능/스키마/API 변경 시 관련 문서를 함께 갱신합니다.

## 기여 방법
1. 이슈를 생성하거나 기존 이슈를 확인합니다.
2. 기능 단위로 브랜치를 분리합니다.
3. 변경 후 테스트/검증을 수행합니다.
4. Conventional Commit 메시지로 커밋합니다.
5. PR에 변경 목적, 범위, 검증 내용을 작성합니다.

## 기여자
- heejoo0203

## 라이선스
별도 라이선스 파일이 아직 없으므로 기본적으로 모든 권리를 보유합니다.
오픈소스 공개를 원할 경우 `LICENSE` 파일을 추가해 명시해야 합니다.
