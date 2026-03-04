from __future__ import annotations

from datetime import datetime


CURRENT_TERMS_VERSION = "2026-03-05-v1"

CURRENT_TERMS_CONTENT = """[autoLV 서비스 이용약관]
제1조 (목적)
본 약관은 autoLV 서비스(이하 "서비스")의 이용과 관련하여 운영자와 회원 간 권리·의무 및 책임사항을 규정함을 목적으로 합니다.

제2조 (제공 기능)
서비스는 개별공시지가 단건 조회, 파일 대량조회, 지도조회 및 조회기록 관리 기능을 제공합니다.

제3조 (회원정보)
회원은 정확한 정보를 입력해야 하며, 계정 보안 책임은 회원 본인에게 있습니다.

제4조 (외부 API)
서비스는 공공/외부 API(VWorld 등) 결과를 기반으로 동작하며, 외부 장애·정책 변경으로 일부 기능이 제한될 수 있습니다.

제5조 (서비스 제한)
비정상적 자동화 요청, 과도한 트래픽 유발, 타인 권리 침해 행위가 확인될 경우 서비스 이용이 제한될 수 있습니다.

제6조 (면책)
서비스에서 제공하는 정보는 의사결정을 위한 참고자료이며, 최종 판단과 책임은 사용자에게 있습니다.

제7조 (약관 변경)
운영자는 관련 법령 범위 내에서 약관을 변경할 수 있으며, 변경 시 서비스 내 공지합니다.
"""


def get_current_terms() -> tuple[str, str]:
    return CURRENT_TERMS_VERSION, CURRENT_TERMS_CONTENT


def format_terms_response(version: str, content: str, accepted_at: datetime | None) -> dict:
    return {
        "version": version,
        "content": content,
        "accepted_at": accepted_at,
    }
