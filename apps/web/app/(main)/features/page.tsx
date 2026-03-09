"use client";

import Link from "next/link";

import { BrandLogo } from "@/app/components/brand-logo";
import { useAuth } from "@/app/components/auth-provider";

const coreFeatures = [
  {
    icon: "◎",
    kicker: "Single Lookup",
    title: "개별조회",
    body: "시·도부터 도로명까지 구조화된 입력 흐름으로 개별공시지가를 빠르게 확인합니다. 연도별 공시지가 이력, 토지특성, 조회기록 복원까지 한 번에 이어집니다.",
    bullets: ["지번·도로명 동시 지원", "연도별 공시지가 이력 확인", "로그인 시 조회기록 자동 누적"],
    href: "/search",
    cta: "개별조회 시작",
  },
  {
    icon: "▣",
    kicker: "Spatial Analysis",
    title: "지도·구역 분석",
    body: "필지를 직접 클릭하거나 다각형을 그려 구역 내부 필지의 공시지가, 노후도, 평균 용적률, 과소필지 비율까지 분석합니다.",
    bullets: ["필지 90% 포함 기준 집계", "지적도 오버레이 전환", "저장 구역 불러오기·CSV 내보내기"],
    href: "/map",
    cta: "지도 분석 열기",
  },
  {
    icon: "▤",
    kicker: "Bulk Processing",
    title: "파일조회",
    body: "대량 주소 파일을 업로드하면 행 구조를 자동 해석해 비동기 조회를 수행하고, 결과 파일과 작업 이력을 함께 관리합니다.",
    bullets: ["최대 10,000행 처리", "열 순서 자동 매핑", "작업별 진행률·다운로드 관리"],
    href: "/files",
    cta: "파일조회 이동",
  },
] as const;

const processSteps = [
  {
    title: "필지 단위 입력",
    body: "주소를 직접 선택하거나 지도를 클릭해 기준 필지를 좁힙니다.",
  },
  {
    title: "공식 데이터 결합",
    body: "VWorld, 건축HUB, PostGIS를 조합해 공시지가와 공간 정보를 정제합니다.",
  },
  {
    title: "실무형 의사결정",
    body: "구역 단위 집계, CSV 내보내기, 저장 구역 재호출로 검토 흐름을 이어갑니다.",
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
          <h1 className="hero-title">필지 경계부터 구역 사업성까지, 한 화면에서 정리합니다.</h1>
          <p className="hero-copy">
            필지랩은 단순 조회 화면이 아니라, 개별공시지가와 공간 데이터를 실무 흐름에 맞춰 읽고 판단할 수 있도록
            구성한 필지 분석 워크스페이스입니다.
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
        </div>

        <div className="hero-visual-stack">
          <div className="hero-brand-card">
            <BrandLogo size="lg" />
            <div className="hero-badge-row">
              <span className="hero-badge">공시지가</span>
              <span className="hero-badge">필지 경계</span>
              <span className="hero-badge">구역 분석</span>
              <span className="hero-badge">대량 파일 처리</span>
            </div>
          </div>
          <div className="hero-stat-grid">
            <div className="hero-stat-card">
              <div className="hero-stat-label">핵심 워크플로우</div>
              <div className="hero-stat-value small">개별조회 → 지도조회 → 구역 분석 → 파일조회</div>
            </div>
            <div className="hero-stat-card">
              <div className="hero-stat-label">분석 관점</div>
              <div className="hero-stat-value small">공시지가, 노후도, 용적률, 과소필지 비율</div>
            </div>
            <div className="hero-stat-card">
              <div className="hero-stat-label">처리 방식</div>
              <div className="hero-stat-value small">공식 API + PostGIS + 캐시 기반</div>
            </div>
            <div className="hero-stat-card">
              <div className="hero-stat-label">활용 목적</div>
              <div className="hero-stat-value small">재개발·재건축 검토, 토지 조사, 물건 스크리닝</div>
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="section-head">
          <span className="eyebrow">Core Workspace</span>
          <h2>주요 기능</h2>
          <p className="hint">필지랩의 모든 화면은 실제 검토 순서에 맞춰 연결됩니다.</p>
        </div>
        <div className="feature-card-grid">
          {coreFeatures.map((feature) => (
            <article key={feature.title} className="feature-card-pro">
              <div className="feature-visual-pro" aria-hidden>
                {feature.icon}
              </div>
              <div className="feature-kicker">{feature.kicker}</div>
              <h3>{feature.title}</h3>
              <p className="hint">{feature.body}</p>
              <ul className="feature-list">
                {feature.bullets.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              {feature.href === "/files" && !isLoggedIn ? (
                <button type="button" className="nav-item" onClick={() => openAuth("login")}>
                  로그인 후 열기
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

      <section className="panel">
        <div className="section-head">
          <span className="eyebrow">Workflow</span>
          <h2>필지랩 사용 흐름</h2>
        </div>
        <div className="feature-process">
          {processSteps.map((step, index) => (
            <article key={step.title} className="process-step">
              <div className="process-step-index">{index + 1}</div>
              <h3>{step.title}</h3>
              <p className="hint">{step.body}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
