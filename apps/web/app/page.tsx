"use client";

import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type AuthMode = "login" | "register";
type SearchTab = "지번" | "도로명";
type UserMenu = "개별조회" | "파일조회" | "조회기록";
type LdMap = Record<string, Record<string, Record<string, string>>>;

type AuthUser = {
  id?: string;
  user_id?: string;
  email: string;
  full_name?: string | null;
};

type ResultRow = {
  기준년도: string;
  토지소재지: string;
  지번: string;
  개별공시지가: string;
  기준일자: string;
  공시일자: string;
  비고: string;
};

const SAN_OPTIONS = ["일반", "산"] as const;
const ROAD_POOL = ["중앙로", "시청로", "문화로", "강남대로", "테헤란로", "한강대로", "올림픽로", "세종대로"] as const;

export default function Home() {
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authLoading, setAuthLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState("로그인 후 파일 조회 기능을 사용할 수 있습니다.");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [userMenu, setUserMenu] = useState<UserMenu>("개별조회");

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerPasswordConfirm, setRegisterPasswordConfirm] = useState("");
  const [registerAgreements, setRegisterAgreements] = useState(false);

  const [ldMap, setLdMap] = useState<LdMap>({});
  const [searchTab, setSearchTab] = useState<SearchTab>("지번");
  const [sido, setSido] = useState("");
  const [sigungu, setSigungu] = useState("");
  const [dong, setDong] = useState("");
  const [road, setRoad] = useState("");
  const [sanType, setSanType] = useState<(typeof SAN_OPTIONS)[number]>("일반");
  const [mainNo, setMainNo] = useState("");
  const [subNo, setSubNo] = useState("");
  const [buildingNo1, setBuildingNo1] = useState("");
  const [buildingNo2, setBuildingNo2] = useState("");

  const [resultRows, setResultRows] = useState<ResultRow[]>([]);
  const [searchMessage, setSearchMessage] = useState("시/도, 시/군/구, 읍/면/동(또는 도로명)을 선택해 주세요.");
  const [healthMessage, setHealthMessage] = useState("API 상태 미확인");
  const [excelMessage, setExcelMessage] = useState("로그인하면 엑셀 업로드 기능이 활성화됩니다.");

  const isLoggedIn = Boolean(currentUser);
  const userLabel = useMemo(() => currentUser?.full_name?.trim() || currentUser?.email || "사용자", [currentUser]);
  const sidoList = useMemo(() => Object.keys(ldMap), [ldMap]);
  const sigunguList = useMemo(() => (sido ? Object.keys(ldMap[sido] ?? {}) : []), [ldMap, sido]);
  const dongList = useMemo(() => (sido && sigungu ? Object.keys(ldMap[sido]?.[sigungu] ?? {}) : []), [ldMap, sido, sigungu]);
  const roadList = useMemo(() => {
    if (!sigungu) return [];
    const count = 4 + (sigungu.length % 4);
    return ROAD_POOL.slice(0, count).map((name) => `${sigungu} ${name}`);
  }, [sigungu]);

  useEffect(() => {
    void loadCodes();
    void checkApiHealth();
    void fetchMe();
  }, []);

  const loadCodes = async () => {
    try {
      const res = await fetch("/ld_codes.json", { cache: "force-cache" });
      if (!res.ok) throw new Error("주소 코드 로드 실패");
      setLdMap((await res.json()) as LdMap);
    } catch {
      setSearchMessage("주소 선택 데이터를 불러오지 못했습니다.");
    }
  };

  const checkApiHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
      const data = (await res.json()) as { status?: string };
      setHealthMessage(res.ok ? `API ${data.status ?? "정상"}` : "API 오류");
    } catch {
      setHealthMessage("API 연결 실패");
    }
  };

  const fetchMe = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, { credentials: "include" });
      if (!res.ok) return;
      setCurrentUser((await res.json()) as AuthUser);
      setExcelMessage("파일 조회 기능이 활성화되었습니다.");
    } catch {}
  };

  const onSido = (v: string) => {
    setSido(v);
    setSigungu("");
    setDong("");
    setRoad("");
  };
  const onSigungu = (v: string) => {
    setSigungu(v);
    setDong("");
    setRoad("");
  };

  const login = async () => {
    if (!loginEmail || !loginPassword) return setAuthMessage("이메일과 비밀번호를 입력해 주세요.");
    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const payload = (await res.json()) as AuthUser | Record<string, unknown>;
      if (!res.ok) throw new Error(extractError(payload, "로그인에 실패했습니다."));
      setCurrentUser(payload as AuthUser);
      setAuthOpen(false);
      setAuthMessage("로그인되었습니다.");
      setExcelMessage("파일 조회 기능이 활성화되었습니다.");
    } catch (e) {
      setAuthMessage(e instanceof Error ? e.message : "로그인 실패");
    } finally {
      setAuthLoading(false);
    }
  };

  const register = async () => {
    if (!registerName || !registerEmail || !registerPassword || !registerPasswordConfirm) return setAuthMessage("회원가입 필수 항목을 입력해 주세요.");
    if (!registerAgreements) return setAuthMessage("필수 약관 동의가 필요합니다.");
    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email: registerEmail,
          password: registerPassword,
          confirm_password: registerPasswordConfirm,
          full_name: registerName,
          agreements: registerAgreements,
        }),
      });
      const payload = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(extractError(payload, "회원가입에 실패했습니다."));
      setAuthMessage("회원가입이 완료되었습니다. 로그인해 주세요.");
      setAuthMode("login");
      setLoginEmail(registerEmail);
    } catch (e) {
      setAuthMessage(e instanceof Error ? e.message : "회원가입 실패");
    } finally {
      setAuthLoading(false);
    }
  };

  const logout = async () => {
    await fetch(`${API_BASE}/api/v1/auth/logout`, { method: "POST", credentials: "include" });
    setCurrentUser(null);
    setUserMenu("개별조회");
    setExcelMessage("로그인하면 엑셀 업로드 기능이 활성화됩니다.");
  };

  const runSearch = () => {
    if (!sido || !sigungu) return setSearchMessage("시/도와 시/군/구를 선택해 주세요.");
    if (searchTab === "지번") {
      if (!dong || !mainNo) return setSearchMessage("지번 검색에는 읍/면/동과 본번이 필요합니다.");
      const jibun = `${sanType === "산" ? "산 " : ""}${mainNo}${subNo ? `-${subNo}` : ""}`;
      setResultRows([
        { 기준년도: "2025", 토지소재지: `${sido} ${sigungu} ${dong}`, 지번: jibun, 개별공시지가: "1,396,000 원/㎡", 기준일자: "01월 01일", 공시일자: "20250430", 비고: "정상" },
        { 기준년도: "2024", 토지소재지: `${sido} ${sigungu} ${dong}`, 지번: jibun, 개별공시지가: "1,356,000 원/㎡", 기준일자: "01월 01일", 공시일자: "20240430", 비고: "정상" },
      ]);
      return setSearchMessage(`지번 조회 완료: ${sido} ${sigungu} ${dong} ${jibun}`);
    }
    if (!road || !buildingNo1) return setSearchMessage("도로명 검색에는 도로명과 건물번호가 필요합니다.");
    const roadAddr = `${road} ${buildingNo1}${buildingNo2 ? `-${buildingNo2}` : ""}`;
    setResultRows([
      { 기준년도: "2025", 토지소재지: `${sido} ${sigungu} ${roadAddr}`, 지번: "변환지번 12-1", 개별공시지가: "1,280,000 원/㎡", 기준일자: "01월 01일", 공시일자: "20250430", 비고: "정상" },
      { 기준년도: "2024", 토지소재지: `${sido} ${sigungu} ${roadAddr}`, 지번: "변환지번 12-1", 개별공시지가: "1,240,000 원/㎡", 기준일자: "01월 01일", 공시일자: "20240430", 비고: "정상" },
    ]);
    setSearchMessage(`도로명 조회 완료: ${sido} ${sigungu} ${roadAddr}`);
  };

  const openExcelFeature = () => {
    if (!isLoggedIn) {
      setAuthMode("login");
      setAuthOpen(true);
      return setExcelMessage("파일 조회는 로그인 후 사용할 수 있습니다.");
    }
    setExcelMessage("엑셀 업로드 API 연동 단계에서 실제 처리됩니다.");
  };

  return (
    <div style={wrap}>
      <header style={header}>
        <div style={logo}><span style={{ fontWeight: 900 }}>auto</span><span style={{ fontWeight: 900, color: "#6b90d9" }}>LV</span></div>
        {!isLoggedIn ? (
          <nav style={nav}>
            <button style={{ ...navBtn, ...activeBtn }}>개별조회</button>
            <button style={navBtn} onClick={() => { setAuthMode("login"); setAuthOpen(true); }}>로그인</button>
            <button style={{ ...navBtn, ...blueBtn }} onClick={() => { setAuthMode("register"); setAuthOpen(true); }}>회원가입</button>
          </nav>
        ) : (
          <nav style={nav}>
            {(["개별조회", "파일조회", "조회기록"] as UserMenu[]).map((m) => (
              <button key={m} style={{ ...navBtn, ...(userMenu === m ? activeBtn : {}) }} onClick={() => setUserMenu(m)}>{m}</button>
            ))}
            <div style={profile}><span style={avatar}>{userLabel.charAt(0).toUpperCase()}</span><span>{userLabel}</span></div>
          </nav>
        )}
      </header>

      <main style={main}>
        {!isLoggedIn && (
          <section style={hero}>
            <h1 style={{ margin: 0, fontSize: 48 }}>정확한 토지 가치 데이터, 더 쉽게</h1>
            <p style={{ margin: "8px 0 0", color: "#475569" }}>비로그인 상태에서도 개별 주소 조회를 바로 사용할 수 있습니다.</p>
          </section>
        )}

        <section style={card}>
          <h2 style={h2}>스크롤 방식 주소 선택기</h2>
          <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
            <button style={{ ...chip, ...(searchTab === "지번" ? chipOn : {}) }} onClick={() => setSearchTab("지번")}>지번 검색</button>
            <button style={{ ...chip, ...(searchTab === "도로명" ? chipOn : {}) }} onClick={() => setSearchTab("도로명")}>도로명 검색</button>
          </div>
          <div style={grid3}>
            <Box title="시/도 선택"><select size={8} style={sel} value={sido} onChange={(e) => onSido(e.target.value)}>{sidoList.map((v) => <option key={v}>{v}</option>)}</select></Box>
            <Box title="시/군/구 선택"><select size={8} style={sel} value={sigungu} onChange={(e) => onSigungu(e.target.value)}>{sigunguList.map((v) => <option key={v}>{v}</option>)}</select></Box>
            <Box title={searchTab === "지번" ? "읍/면/동 선택" : "도로명 선택"}>
              <select size={8} style={sel} value={searchTab === "지번" ? dong : road} onChange={(e) => searchTab === "지번" ? setDong(e.target.value) : setRoad(e.target.value)}>
                {(searchTab === "지번" ? dongList : roadList).map((v) => <option key={v}>{v}</option>)}
              </select>
            </Box>
          </div>
          {searchTab === "지번" ? (
            <div style={inline}>
              <b>지번 입력</b>
              <select style={miniSel} value={sanType} onChange={(e) => setSanType(e.target.value as (typeof SAN_OPTIONS)[number])}>{SAN_OPTIONS.map((v) => <option key={v}>{v}</option>)}</select>
              <input style={miniIn} placeholder="본번" value={mainNo} onChange={(e) => setMainNo(e.target.value)} />
              <span>-</span>
              <input style={miniIn} placeholder="부번" value={subNo} onChange={(e) => setSubNo(e.target.value)} />
            </div>
          ) : (
            <div style={inline}>
              <b>건물번호</b>
              <input style={miniIn} placeholder="본번" value={buildingNo1} onChange={(e) => setBuildingNo1(e.target.value)} />
              <span>-</span>
              <input style={miniIn} placeholder="부번" value={buildingNo2} onChange={(e) => setBuildingNo2(e.target.value)} />
            </div>
          )}
          <button style={searchBtn} onClick={runSearch}>검색</button>
          <p style={msg}>{searchMessage}</p>
        </section>

        <section style={card}>
          <h2 style={h2}>검색 결과 테이블</h2>
          {resultRows.length === 0 ? <p style={msg}>검색 결과가 없습니다.</p> : <Result rows={resultRows} />}
        </section>

        {!isLoggedIn ? (
          <section style={card}>
            <h2 style={h2}>엑셀 대량 조회 (로그인 필요)</h2>
            <p style={msg}>회원가입 후 최대 10,000행 파일 조회, 비동기 처리, 결과 다운로드를 사용할 수 있습니다.</p>
            <button style={searchBtn} onClick={() => { setAuthMode("register"); setAuthOpen(true); }}>회원가입하고 파일 조회 사용하기</button>
          </section>
        ) : (
          <>
            {userMenu === "파일조회" && (
              <section style={card}>
                <h2 style={h2}>파일 조회</h2>
                <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12 }}>
                  <div style={drop}>엑셀 파일 Drag & Drop 또는 클릭 업로드</div>
                  <div style={status}>
                    <b>작업 상태</b>
                    <p style={msg}>엑셀 처리 중: 6,500 / 10,000 행, 65%</p>
                    <div style={track}><div style={{ ...fill, width: "65%" }} /></div>
                  </div>
                </div>
                <button style={searchBtn} onClick={openExcelFeature}>업로드 및 비동기 처리</button>
                <p style={msg}>{excelMessage}</p>
              </section>
            )}
            {(userMenu === "파일조회" || userMenu === "조회기록") && (
              <section style={card}>
                <h2 style={h2}>조회 이력</h2>
                <table style={tbl}><thead><tr style={trh}><th style={th}>순번</th><th style={th}>일시</th><th style={th}>행 수</th><th style={th}>작업진행도</th><th style={th}>다운로드</th></tr></thead>
                  <tbody>{[
                    [1, "2024-05-15 14:30:22", "6,500", "진행중"],
                    [2, "2024-05-15 14:30:22", "1,200", "완료"],
                    [3, "2024-05-15 14:30:22", "10,000", "오류"],
                  ].map((r) => <tr key={String(r[0])}><td style={td}>{r[0]}</td><td style={td}>{r[1]}</td><td style={td}>{r[2]}</td><td style={td}><span style={{ ...badge, ...(r[3] === "완료" ? ok : r[3] === "진행중" ? ing : err) }}>{r[3]}</span></td><td style={td}><button style={down}>엑셀 다운로드</button></td></tr>)}</tbody>
                </table>
              </section>
            )}
          </>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, alignItems: "center" }}>
          <button style={smallBtn} onClick={checkApiHealth}>API 상태 확인</button>
          <span style={chip}>{healthMessage}</span>
          {isLoggedIn && <button style={link} onClick={logout}>로그아웃</button>}
        </div>
      </main>

      {authOpen && (
        <div style={overlay} onClick={() => setAuthOpen(false)}>
          <div style={modal} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ margin: 0 }}>{authMode === "login" ? "로그인" : "회원가입"}</h3>
              <button style={x} onClick={() => setAuthOpen(false)}>✕</button>
            </div>
            <div style={{ display: "flex", gap: 8, margin: "10px 0" }}>
              <button style={{ ...chip, ...(authMode === "login" ? chipOn : {}) }} onClick={() => setAuthMode("login")}>로그인</button>
              <button style={{ ...chip, ...(authMode === "register" ? chipOn : {}) }} onClick={() => setAuthMode("register")}>회원가입</button>
            </div>
            {authMode === "login" ? (
              <div style={fgrid}>
                <input style={input} placeholder="이메일" value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)} />
                <input style={input} placeholder="비밀번호" type="password" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} />
                <button style={searchBtn} onClick={login} disabled={authLoading}>{authLoading ? "처리 중..." : "로그인"}</button>
                <div style={{ display: "flex", gap: 10 }}>
                  <button style={link} onClick={() => setAuthMessage("아이디 찾기 기능은 준비 중입니다.")}>아이디 찾기</button>
                  <button style={link} onClick={() => setAuthMessage("비밀번호 찾기 기능은 준비 중입니다.")}>비밀번호 찾기</button>
                </div>
              </div>
            ) : (
              <div style={fgrid}>
                <input style={input} placeholder="닉네임 (2~20자, 한글/영문/숫자)" value={registerName} onChange={(e) => setRegisterName(e.target.value)} />
                <input style={input} placeholder="이메일" value={registerEmail} onChange={(e) => setRegisterEmail(e.target.value)} />
                <input style={input} placeholder="비밀번호 (8~16자, 영문/숫자/특수문자)" type="password" value={registerPassword} onChange={(e) => setRegisterPassword(e.target.value)} />
                <input style={input} placeholder="비밀번호 확인" type="password" value={registerPasswordConfirm} onChange={(e) => setRegisterPasswordConfirm(e.target.value)} />
                <label style={{ fontSize: 13, color: "#475569" }}><input type="checkbox" checked={registerAgreements} onChange={(e) => setRegisterAgreements(e.target.checked)} /> [필수] 서비스 이용약관 및 개인정보 처리방침 동의</label>
                <button style={searchBtn} onClick={register} disabled={authLoading}>{authLoading ? "처리 중..." : "회원가입"}</button>
              </div>
            )}
            <p style={msg}>{authMessage}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function Result({ rows }: { rows: ResultRow[] }) {
  return (
    <table style={tbl}>
      <thead><tr style={trh}><th style={th}>가격기준년도</th><th style={th}>토지소재지</th><th style={th}>지번</th><th style={th}>개별공시지가</th><th style={th}>기준일자</th><th style={th}>공시일자</th><th style={th}>비고</th></tr></thead>
      <tbody>{rows.map((r, i) => <tr key={`${r.토지소재지}-${i}`}><td style={td}>{r.기준년도}</td><td style={td}>{r.토지소재지}</td><td style={td}>{r.지번}</td><td style={td}>{r.개별공시지가}</td><td style={td}>{r.기준일자}</td><td style={td}>{r.공시일자}</td><td style={td}>{r.비고}</td></tr>)}</tbody>
    </table>
  );
}

function Box({ title, children }: { title: string; children: React.ReactNode }) {
  return <div><label style={{ fontSize: 14, fontWeight: 700, color: "#334155" }}>{title}</label>{children}</div>;
}

function extractError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0] && typeof (detail[0] as { msg?: unknown }).msg === "string") return String((detail[0] as { msg: string }).msg);
  if (detail && typeof detail === "object" && typeof (detail as { message?: unknown }).message === "string") return String((detail as { message: string }).message);
  return fallback;
}

const wrap: CSSProperties = { minHeight: "100vh", background: "linear-gradient(180deg,#fafaf9 0%,#f3f4f6 100%)" };
const header: CSSProperties = { height: 80, borderBottom: "1px solid #e5e7eb", background: "rgba(255,255,255,.95)", display: "grid", gridTemplateColumns: "220px 1fr", alignItems: "center", padding: "0 22px", position: "sticky", top: 0, zIndex: 10 };
const logo: CSSProperties = { fontSize: 38, letterSpacing: "-1px" };
const nav: CSSProperties = { display: "flex", justifyContent: "flex-end", gap: 8, alignItems: "center" };
const navBtn: CSSProperties = { border: "none", borderRadius: 10, padding: "9px 12px", background: "transparent", fontWeight: 700, cursor: "pointer", color: "#334155" };
const activeBtn: CSSProperties = { background: "#e2e8f0", color: "#0f172a" };
const blueBtn: CSSProperties = { background: "#4f82db", color: "white" };
const profile: CSSProperties = { display: "flex", alignItems: "center", gap: 8, marginLeft: 8, color: "#0f172a", fontWeight: 700 };
const avatar: CSSProperties = { width: 32, height: 32, borderRadius: "50%", background: "#dbeafe", display: "grid", placeItems: "center", fontWeight: 800 };
const main: CSSProperties = { maxWidth: 1500, margin: "0 auto", padding: "18px 20px 34px", display: "grid", gap: 14 };
const hero: CSSProperties = { border: "1px solid #e5e7eb", borderRadius: 16, background: "linear-gradient(120deg,#f8fafc 0%,#e5e7eb 100%)", padding: "30px 20px", textAlign: "center" };
const card: CSSProperties = { border: "1px solid #e5e7eb", borderRadius: 16, background: "#fffefb", padding: 16 };
const h2: CSSProperties = { margin: "0 0 10px", fontSize: 32, fontWeight: 900, color: "#111827" };
const chip: CSSProperties = { border: "none", borderRadius: 8, padding: "8px 12px", background: "#e2e8f0", color: "#334155", fontWeight: 700, cursor: "pointer" };
const chipOn: CSSProperties = { background: "#4f82db", color: "white" };
const grid3: CSSProperties = { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 };
const sel: CSSProperties = { width: "100%", minHeight: 210, border: "1px solid #d1d5db", borderRadius: 8, padding: 6, background: "white", marginTop: 4 };
const inline: CSSProperties = { marginTop: 10, display: "flex", alignItems: "center", gap: 8 };
const miniSel: CSSProperties = { border: "1px solid #d1d5db", borderRadius: 6, height: 34, paddingInline: 8 };
const miniIn: CSSProperties = { border: "1px solid #d1d5db", borderRadius: 6, height: 34, width: 90, paddingInline: 8 };
const searchBtn: CSSProperties = { marginTop: 10, width: "100%", border: "none", borderRadius: 10, padding: "12px 14px", background: "linear-gradient(90deg,#4f82db 0%,#6c8ef0 100%)", color: "white", fontWeight: 800, cursor: "pointer" };
const msg: CSSProperties = { margin: "10px 0 0", fontSize: 14, color: "#475569" };
const tbl: CSSProperties = { width: "100%", borderCollapse: "separate", borderSpacing: 0 };
const trh: CSSProperties = { background: "#f1f5f9" };
const th: CSSProperties = { textAlign: "left", padding: "10px 12px", borderBottom: "1px solid #e2e8f0", color: "#334155", fontSize: 14 };
const td: CSSProperties = { padding: "10px 12px", borderBottom: "1px solid #f1f5f9", color: "#1f2937", fontSize: 14 };
const drop: CSSProperties = { border: "1px dashed #94a3b8", borderRadius: 12, minHeight: 126, display: "grid", placeItems: "center", background: "white", textAlign: "center", padding: 12, fontWeight: 700, color: "#334155" };
const status: CSSProperties = { border: "1px solid #dbe3ed", borderRadius: 12, background: "white", padding: 12 };
const track: CSSProperties = { width: "100%", height: 9, background: "#e2e8f0", borderRadius: 999, overflow: "hidden" };
const fill: CSSProperties = { height: "100%", background: "linear-gradient(90deg,#4f82db 0%,#6c8ef0 100%)" };
const badge: CSSProperties = { display: "inline-block", padding: "4px 10px", borderRadius: 999, fontSize: 12, fontWeight: 700 };
const ok: CSSProperties = { background: "#dcfce7", color: "#166534" };
const ing: CSSProperties = { background: "#dbeafe", color: "#1d4ed8" };
const err: CSSProperties = { background: "#fee2e2", color: "#991b1b" };
const down: CSSProperties = { border: "1px solid #d1d5db", borderRadius: 8, background: "white", padding: "6px 10px", cursor: "pointer", fontWeight: 700 };
const smallBtn: CSSProperties = { border: "1px solid #cbd5e1", borderRadius: 8, padding: "7px 10px", background: "white", cursor: "pointer" };
const link: CSSProperties = { border: "none", background: "transparent", color: "#2563eb", textDecoration: "underline", textUnderlineOffset: "2px", cursor: "pointer", fontWeight: 700, padding: 0 };
const overlay: CSSProperties = { position: "fixed", inset: 0, background: "rgba(15,23,42,.3)", display: "grid", placeItems: "center", zIndex: 20 };
const modal: CSSProperties = { width: "min(520px,calc(100vw - 24px))", background: "#fffefc", border: "1px solid #e5e7eb", borderRadius: 16, padding: 16, boxShadow: "0 16px 40px rgba(15,23,42,.25)" };
const x: CSSProperties = { border: "none", width: 30, height: 30, borderRadius: 8, background: "#f1f5f9", cursor: "pointer" };
const fgrid: CSSProperties = { display: "grid", gap: 10 };
const input: CSSProperties = { border: "1px solid #d1d5db", borderRadius: 8, padding: "11px 12px", fontSize: 14 };
