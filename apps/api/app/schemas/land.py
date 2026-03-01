from typing import Literal

from pydantic import BaseModel, Field, model_validator


class LandLookupRequest(BaseModel):
    search_type: Literal["jibun", "road"] = Field(description="검색 유형")

    # 지번 검색 입력값
    ld_code: str | None = Field(default=None, description="법정동코드 10자리")
    san_type: Literal["일반", "산"] = Field(default="일반", description="특수지 구분")
    main_no: str | None = Field(default=None, description="지번 본번")
    sub_no: str | None = Field(default="", description="지번 부번")

    # 도로명 검색 입력값
    sido: str | None = Field(default=None, description="시/도")
    sigungu: str | None = Field(default=None, description="시/군/구")
    road_name: str | None = Field(default=None, description="도로명")
    building_main_no: str | None = Field(default=None, description="건물번호 본번")
    building_sub_no: str | None = Field(default="", description="건물번호 부번")

    @model_validator(mode="after")
    def validate_by_type(self) -> "LandLookupRequest":
        if self.search_type == "jibun":
            if not self.ld_code:
                raise ValueError("지번 검색에는 ld_code가 필요합니다.")
            if not self.main_no:
                raise ValueError("지번 검색에는 main_no가 필요합니다.")
        else:
            required = {
                "sido": self.sido,
                "sigungu": self.sigungu,
                "road_name": self.road_name,
                "building_main_no": self.building_main_no,
            }
            missing = [k for k, v in required.items() if not v]
            if missing:
                raise ValueError(f"도로명 검색 필수값 누락: {', '.join(missing)}")
        return self


class LandResultRow(BaseModel):
    기준년도: str
    토지소재지: str
    지번: str
    개별공시지가: str
    기준일자: str
    공시일자: str
    비고: str


class LandLookupResponse(BaseModel):
    search_type: Literal["jibun", "road"]
    pnu: str
    address_summary: str
    rows: list[LandResultRow]


class RoadNameListResponse(BaseModel):
    sido: str
    sigungu: str
    initial: str
    roads: list[str]
