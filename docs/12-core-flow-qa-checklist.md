# 핵심 플로우 QA 체크리스트 (2026-03-11)

## 0. 목적
- 이번 주 마감 전 필수 플로우를 `깨지지 않는 사용 흐름 + 설명 가능한 결과 + 모바일 usable` 기준으로 검증한다.
- 새 기능 추가보다 현재 구현의 회귀 방지와 정확도 설명 가능성을 우선한다.
- 자동 스모크와 수동 QA를 분리해 반복 가능하게 관리한다.

## 1. 자동 스모크
### 1.1 실행 명령
```bash
cd apps/web
npm run qa:smoke
```

### 1.2 포함 범위
- `qa:ui-regression`
  - 지도조회 드로어 핸들 문구 회귀
  - 지도조회/개별조회 연도별 공시지가 기준일자 포맷 회귀
  - 파일조회 필터 상태에서 숨은 행 선택 회귀
  - 조회기록 총량/현재 결과 분리 표시 회귀
  - 마이페이지 액션별 로딩 상태 회귀
- `npm run lint`
  - 치명적 JSX/Hooks 오류 탐지
- `npm run build`
  - 타입/빌드 회귀 탐지

### 1.3 합격 기준
- 세 명령이 모두 종료 코드 0으로 끝나야 한다.
- lint warning은 남아 있을 수 있으나, 이번 주 수정 범위의 회귀나 hooks rule error는 없어야 한다.

## 2. 수동 QA 범위
### 2.1 인증
- 회원가입
- 로그인
- 로그아웃
- 아이디 찾기
- 비밀번호 재설정

### 2.2 개별조회 `/search`
- 지번 조회
- 도로명 조회
- 결과 카드 수치 가독성
- 토지특성 열기/닫기
- 연도별 공시지가 기준일자 `1/1` 표기 확인
- 지도에서 이어서 보기 동작

### 2.3 지도조회 `/map`
- 기본조회
  - 주소 검색
  - 지도 클릭 조회
  - 결과 보기 핸들 열기/닫기
  - 토지특성 열기/닫기
  - 연도별 상세 조회
  - CSV 다운로드
- 구역조회
  - 폴리곤 작성
  - 분석 실행
  - 리뷰 큐 필터
  - 포함/제외/보류 액션
  - 구역 저장
  - 저장 구역 열람/이름 수정/삭제
  - 비교 카드 확인

### 2.4 파일조회 `/files`
- 샘플 파일 업로드
  - [`docs/samples/bulk_test_input_verified_100.csv`](/d:/Users/Desktop/HJ/04_코딩/Pilji-Lab/docs/samples/bulk_test_input_verified_100.csv)
  - [`docs/samples/bulk_test_input_verified_100_result.xlsx`](/d:/Users/Desktop/HJ/04_코딩/Pilji-Lab/docs/samples/bulk_test_input_verified_100_result.xlsx)
- 작업 상태 필터
- 진행률 확인
- 결과 다운로드
- 선택 삭제

### 2.5 조회기록 `/history`
- 지도/개별조회 후 기록 저장
- 유형/시도/시군구 필터
- 정렬 토글
- 복원 이동
- 선택 삭제
- 누적 기록 vs 현재 결과 표시 확인

### 2.6 마이페이지 `/mypage`
- 회원정보 수정
- 비밀번호 변경
- 약관 로드
- APK 다운로드 링크
- 회원 탈퇴 문구 검증
- 액션별 버튼 로딩 문구 확인

## 3. 모바일 usable 체크
### 3.1 최소 해상도
- 360px
- 390px
- 430px
- tablet 폭

### 3.2 필수 확인 항목
- `/map` 결과 보기 핸들 접근 가능
- `/map` 연도별 공시지가 표 겹침 없음
- `/search` 결과 카드 숫자 줄바꿈이 읽기 가능
- `/files` 상태/다운로드/선택 삭제가 터치 가능
- `/history` 필터와 표 카드형 전환이 usable
- `/mypage` 핵심 액션 버튼 오작동 없음

## 4. 정확도 QA
### 4.1 기본조회 정확도
- 같은 필지를 지번/도로명/지도 클릭으로 조회했을 때 최신 연도 가격이 일치해야 한다.
- 연도별 공시지가 행은 기준년도 내림차순이어야 한다.
- 전년 대비 수치가 최신값과 이전값 기준으로 계산되는지 확인한다.
- 자동 기본조회 smoke 실행:
```powershell
cd apps/api
$env:DATABASE_URL='sqlite:///./autolv.db'
$env:FORCE_DISABLE_REDIS='1'
$env:BULK_EXECUTION_MODE='background'
python scripts/run_accuracy_golden_set.py
```

### 4.2 구역조회 정확도
- `boundary_candidate` 필지가 리뷰 큐와 테이블에 노출되는지 확인한다.
- `ai_recommendation`, `confidence_score`, `selection_origin`, `anomaly_level` 이 사용자 판단에 충분한지 확인한다.
- 수동 포함/제외 후 요약 수치와 선택 출처가 즉시 갱신되는지 확인한다.
- 저장 후 재열람/비교 시 동일 구역 상태가 재현되는지 확인한다.

### 4.3 오포함/누락 기록 양식
- 케이스 ID
- 입력 방식: 지번 / 도로명 / 지도 / 구역
- 기대 결과
- 실제 결과
- 유형: 오포함 / 누락 / 경계 / 이상치 / 문구 혼동
- 재현 가능 여부
- 스크린샷/기록 링크
- 상세 케이스 매트릭스: [docs/13-accuracy-golden-set.md](/d:/Users/Desktop/HJ/04_코딩/Pilji-Lab/docs/13-accuracy-golden-set.md)

## 5. 이번 주 릴리즈 게이트
- 자동 스모크 통과
- 핵심 수동 QA P0 플로우 전부 통과
- 모바일 최소 해상도 4종에서 치명적 레이아웃 붕괴 없음
- 정확도 샘플에서 치명적 오포함/누락 케이스 미해결 항목 없음
- 남은 warning/tech debt는 다음 주 처리 항목으로 분리 기록
