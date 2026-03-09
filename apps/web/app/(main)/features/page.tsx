"use client";

import Link from "next/link";

import { BrandLogo } from "@/app/components/brand-logo";
import { useAuth } from "@/app/components/auth-provider";

const coreFeatures = [
  {
    icon: "개별",
    title: "개별조회",
    summary: "지번·도로명으로 단건 공시지가를 빠르게 확인",
    href: "/search",
    cta: "바로가기",
  },
  {
    icon: "지도",
    title: "지도조회",
    summary: "필지 클릭과 구역 분석으로 공간 단위 검토 수행",
    href: "/map",
    cta: "바로가기",
  },
  {
    icon: "파일",
    title: "파일조회",
    summary: "대량 주소 파일을 업로드해 비동기 조회 처리",
    href: "/files",
    cta: "바로가기",
  },
] as const;

export default function FeaturesPage() {
  const { user, openAuth } = useAuth();
  const isLoggedIn = Boolean(user);

  return (
    <div className="page-grid">
      <section className="page-hero hero-grid">
        <div>
          <span className="eyebrow">Parcel Intelligence</span>
          <h1 className="hero-title">필지 경계부터 구역 분석까지, 핵심만 빠르게 봅니다.</h1>
          <p className="hero-copy">
            필지랩은 개별공시지가 조회와 구역 분석을 한 흐름으로 연결해 재개발·재건축 검토에 필요한 기준 데이터를
            빠르게 읽을 수 있게 구성한 실무형 워크스페이스입니다.
          </p>
          <div className="hero-actions">
            <Link href="/search" className="btn-primary">
              개별조회 시작
            </Link>
            {isLoggedIn ? (
              <Link href="/map" className="nav-item active">
                지도·구역 분석 열기
              </Link>
            ) : (
              <button className="nav-item" type="button" onClick={() => openAuth("login")}>
                로그인 후 전체 기능 사용
              </button>
            )}
          </div>
          <div className="feature-summary-strip">
            <span className="feature-summary-chip">공시지가</span>
            <span className="feature-summary-chip">필지 경계</span>
            <span className="feature-summary-chip">노후도</span>
            <span className="feature-summary-chip">용적률</span>
            <span className="feature-summary-chip">구역 집계</span>
          </div>
        </div>

        <aside className="compact-hero-note">
          <BrandLogo size="lg" />
          <div className="hero-stat-grid">
            <div className="hero-stat-card">
              <div className="hero-stat-label">핵심 흐름</div>
              <div className="hero-stat-value small">개별조회 → 지도조회 → 구역 분석</div>
            </div>
            <div className="hero-stat-card">
              <div className="hero-stat-label">분석 관점</div>
              <div className="hero-stat-value small">공시지가, 노후도, 용적률, 과소필지</div>
            </div>
          </div>
        </aside>
      </section>

      <section className="panel">
        <div className="section-head">
          <span className="eyebrow">Core Features</span>
          <h2>주요 기능</h2>
        </div>
        <div className="compact-feature-grid">
          {coreFeatures.map((feature) => (
            <article key={feature.title} className="feature-card-pro">
              <div className="feature-kicker">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p className="hint">{feature.summary}</p>
              {feature.href === "/files" && !isLoggedIn ? (
                <button type="button" className="nav-item" onClick={() => openAuth("login")}>
                  로그인 필요
                </button>
              ) : (
                <Link href={feature.href} className="nav-item active">
                  {feature.cta}
                </Link>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
