"use client";

import Link from "next/link";

import { useAuth } from "@/app/components/auth-provider";

export default function FeaturesPage() {
  const { user, openAuth } = useAuth();
  const isLoggedIn = Boolean(user);

  return (
    <>
      <section className="panel">
        <h2>기능설명</h2>
        <p className="hint">autoLV의 조회 기능별 사용 방법을 한눈에 볼 수 있도록 정리했습니다.</p>
      </section>

      <section className="panel feature-grid">
        <article className="feature-card">
          <div className="feature-visual single">개별조회</div>
          <h3>1. 개별조회 (지번/도로명)</h3>
          <p>
            시/도, 시/군/구, 읍/면/동 또는 도로명 정보를 입력해 단건 공시지가를 확인합니다.
            조회 결과는 연도별 내역과 함께 표 형태로 확인할 수 있습니다.
          </p>
          <ol className="feature-steps">
            <li>조회 메뉴에서 `개별조회` 선택</li>
            <li>지번 또는 도로명 탭 선택 후 주소 입력</li>
            <li>검색 버튼 클릭 후 결과 확인</li>
          </ol>
          <Link href="/search" className="nav-item active">
            개별조회 바로가기
          </Link>
        </article>

        <article className="feature-card">
          <div className="feature-visual map">지도조회</div>
          <h3>2. 지도조회</h3>
          <p>
            지도를 클릭하거나 주소를 입력하면 좌표를 기반으로 필지 정보를 조회합니다.
            면적, 현재/전년도 공시지가, 증감률, 인근 평균을 확인할 수 있습니다.
          </p>
          <ol className="feature-steps">
            <li>조회 메뉴에서 `지도조회` 선택</li>
            <li>지도 클릭 또는 주소 입력으로 조회</li>
            <li>필요 시 CSV 다운로드/연도별 상세 조회</li>
          </ol>
          {isLoggedIn ? (
            <Link href="/map" className="nav-item active">
              지도조회 바로가기
            </Link>
          ) : (
            <button className="nav-item" type="button" onClick={() => openAuth("login")}>
              로그인 후 지도조회 사용
            </button>
          )}
        </article>

        <article className="feature-card">
          <div className="feature-visual file">파일조회</div>
          <h3>3. 파일조회 (대량)</h3>
          <p>
            엑셀/CSV 파일을 업로드하면 최대 10,000행까지 비동기 조회를 처리합니다.
            완료 후 결과 파일을 다운로드하고 작업 이력을 관리할 수 있습니다.
          </p>
          <ol className="feature-steps">
            <li>조회 메뉴에서 `파일조회` 선택</li>
            <li>양식 확인 후 파일 업로드</li>
            <li>진행률 확인 후 결과 다운로드</li>
          </ol>
          {isLoggedIn ? (
            <Link href="/files" className="nav-item active">
              파일조회 바로가기
            </Link>
          ) : (
            <button className="nav-item" type="button" onClick={() => openAuth("login")}>
              로그인 후 파일조회 사용
            </button>
          )}
        </article>
      </section>
    </>
  );
}
