# crawler/pnu_util.py

def make_pnu(ld_code: str, main_no: int, sub_no: int = 0, is_san: bool = False) -> str:
    """
    법정동 코드와 지번 정보를 기반으로 PNU 코드 생성
    :param ld_code: 법정동코드 (10자리)
    :param main_no: 본번 (숫자)
    :param sub_no: 부번 (숫자, 기본값 0)
    :param is_san: 산 여부 (True면 산, False면 대지)
    :return: 19자리 PNU 코드
    """
    main_str = str(main_no).zfill(4)
    sub_str = str(sub_no).zfill(4)
    san_code = "1" if is_san else "2"

    return f"{ld_code}{main_str}{sub_str}{san_code}"
