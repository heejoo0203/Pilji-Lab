"use client";

import { useEffect, useRef, useState } from "react";

import { downloadMapLookupCsv, fetchMapLookup } from "@/app/lib/map-api";
import type { LandResultRow, MapLookupResponse } from "@/app/lib/types";

declare global {
  interface Window {
    kakao?: {
      maps: {
        load: (callback: () => void) => void;
        Map: new (container: HTMLElement, options: Record<string, unknown>) => any;
        LatLng: new (lat: number, lng: number) => any;
        Marker: new (options: Record<string, unknown>) => any;
        event: {
          addListener: (target: any, type: string, handler: (event: any) => void) => void;
        };
      };
    };
  }
}

const CLICK_DEBOUNCE_MS = 300;
const KAKAO_SDK_ID = "autolv-kakao-map-sdk";
const DEFAULT_CENTER_LAT = Number(process.env.NEXT_PUBLIC_MAP_CENTER_LAT ?? "37.5662952");
const DEFAULT_CENTER_LNG = Number(process.env.NEXT_PUBLIC_MAP_CENTER_LNG ?? "126.9779451");

export default function MapPage() {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const debounceTimerRef = useRef<number | null>(null);
  const inFlightKeyRef = useRef<string>("");
  const lastResolvedKeyRef = useRef<string>("");

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("지도를 클릭하면 해당 필지의 공시지가를 조회합니다.");
  const [result, setResult] = useState<MapLookupResponse | null>(null);

  useEffect(() => {
    const appKey = process.env.NEXT_PUBLIC_KAKAO_MAP_APP_KEY?.trim();
    if (!appKey) {
      setMessage("NEXT_PUBLIC_KAKAO_MAP_APP_KEY 설정이 필요합니다.");
      return;
    }

    let mounted = true;
    void loadKakaoMapSdk(appKey)
      .then(() => {
        if (!mounted || !window.kakao?.maps || !mapContainerRef.current) return;
        window.kakao.maps.load(() => {
          if (!mounted || !mapContainerRef.current || !window.kakao?.maps) return;
          const center = new window.kakao.maps.LatLng(DEFAULT_CENTER_LAT, DEFAULT_CENTER_LNG);
          const map = new window.kakao.maps.Map(mapContainerRef.current, {
            center,
            level: 4,
          });
          mapRef.current = map;

          window.kakao.maps.event.addListener(map, "click", (mouseEvent: any) => {
            const lat = Number(mouseEvent?.latLng?.getLat?.());
            const lng = Number(mouseEvent?.latLng?.getLng?.());
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
            scheduleLookup(lat, lng);
          });
        });
      })
      .catch(() => {
        if (!mounted) return;
        setMessage("카카오 지도를 불러오지 못했습니다. 앱 키/도메인 설정을 확인해 주세요.");
      });

    return () => {
      mounted = false;
      if (debounceTimerRef.current) {
        window.clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = null;
      }
    };
  }, []);

  const scheduleLookup = (lat: number, lng: number) => {
    if (debounceTimerRef.current) {
      window.clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = window.setTimeout(() => {
      void runLookup(lat, lng);
    }, CLICK_DEBOUNCE_MS);
  };

  const runLookup = async (lat: number, lng: number) => {
    const pointKey = toPointKey(lat, lng);
    if (inFlightKeyRef.current === pointKey) return;
    if (lastResolvedKeyRef.current === pointKey && result) {
      setMessage("이미 조회한 위치입니다. 다른 위치를 클릭해 주세요.");
      return;
    }

    inFlightKeyRef.current = pointKey;
    setLoading(true);
    setMessage("지도 위치를 조회 중입니다...");
    setMarker(lat, lng);

    try {
      const payload = await fetchMapLookup(lat, lng);
      setResult(payload);
      lastResolvedKeyRef.current = pointKey;
      setMessage(payload.cache_hit ? "캐시된 데이터로 조회되었습니다." : "최신 데이터로 조회되었습니다.");
    } catch (error) {
      setResult(null);
      setMessage(error instanceof Error ? error.message : "지도 조회 중 오류가 발생했습니다.");
    } finally {
      inFlightKeyRef.current = "";
      setLoading(false);
    }
  };

  const setMarker = (lat: number, lng: number) => {
    if (!window.kakao?.maps || !mapRef.current) return;
    const position = new window.kakao.maps.LatLng(lat, lng);
    if (!markerRef.current) {
      markerRef.current = new window.kakao.maps.Marker({
        position,
        map: mapRef.current,
      });
    } else {
      markerRef.current.setPosition(position);
    }
  };

  const downloadCsv = async () => {
    if (!result?.pnu) return;
    try {
      await downloadMapLookupCsv(result.pnu);
      setMessage("CSV 다운로드를 시작했습니다.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "CSV 다운로드에 실패했습니다.");
    }
  };

  return (
    <section className="map-page">
      <div className="map-stage panel">
        <h2>지도조회</h2>
        <p className="hint">지도를 클릭하면 좌표를 PNU로 변환하고 개별공시지가를 조회합니다.</p>
        <div ref={mapContainerRef} className="map-canvas" />
      </div>

      <section className="map-result panel">
        <div className="map-result-head">
          <h2>조회 결과</h2>
          <button className="btn-primary" onClick={() => void downloadCsv()} disabled={!result?.pnu}>
            CSV 내보내기
          </button>
        </div>
        <p className="hint">{loading ? "조회 중입니다..." : message}</p>

        {!result ? (
          <div className="map-empty">지도를 클릭해 필지 정보를 조회해 주세요.</div>
        ) : (
          <>
            <div className="map-metrics">
              <MetricCard label="주소" value={result.address_summary || "-"} />
              <MetricCard label="PNU" value={result.pnu} />
              <MetricCard label="현재 공시지가(원/㎡)" value={formatNumber(result.price_current)} />
              <MetricCard label="전년도 공시지가(원/㎡)" value={formatNumber(result.price_previous)} />
              <MetricCard label="증감률(%)" value={formatRate(result.growth_rate)} />
              <MetricCard label="면적(㎡)" value={formatArea(result.area)} />
              <MetricCard label="면적×단가(원)" value={formatNumber(result.estimated_total_price)} />
              <MetricCard
                label={`인근 평균(${result.nearby_radius_m}m, 원/㎡)`}
                value={formatNumber(result.nearby_avg_price)}
              />
            </div>

            <div className="hint">
              좌표: {result.lat.toFixed(6)}, {result.lng.toFixed(6)} / 데이터 소스: {result.cache_hit ? "DB 캐시" : "실시간"}
            </div>

            <MapRowsTable rows={result.rows} />
          </>
        )}
      </section>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
    </div>
  );
}

function MapRowsTable({ rows }: { rows: LandResultRow[] }) {
  if (!rows.length) {
    return <div className="map-empty">연도별 상세 데이터는 실시간 조회 시 표시됩니다.</div>;
  }
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>가격기준년도</th>
          <th>토지소재지</th>
          <th>지번</th>
          <th>개별공시지가</th>
          <th>기준일자</th>
          <th>공시일자</th>
          <th>비고</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, idx) => (
          <tr key={`${row.토지소재지}-${row.기준년도}-${idx}`}>
            <td>{row.기준년도}</td>
            <td>{row.토지소재지}</td>
            <td>{row.지번}</td>
            <td>{row.개별공시지가}</td>
            <td>{row.기준일자}</td>
            <td>{row.공시일자}</td>
            <td>{row.비고}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function toPointKey(lat: number, lng: number): string {
  return `${lat.toFixed(6)}:${lng.toFixed(6)}`;
}

function formatNumber(value: number | null): string {
  if (value === null || value === undefined) return "-";
  return value.toLocaleString("ko-KR");
}

function formatArea(value: number | null): string {
  if (value === null || value === undefined) return "-";
  return Number(value).toLocaleString("ko-KR", { maximumFractionDigits: 2 });
}

function formatRate(value: number | null): string {
  if (value === null || value === undefined) return "-";
  return `${value.toFixed(2)}%`;
}

async function loadKakaoMapSdk(appKey: string): Promise<void> {
  if (window.kakao?.maps) return;
  const existing = document.getElementById(KAKAO_SDK_ID) as HTMLScriptElement | null;
  if (existing) {
    await waitScript(existing);
    return;
  }

  const script = document.createElement("script");
  script.id = KAKAO_SDK_ID;
  script.async = true;
  script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(appKey)}&autoload=false&libraries=services,drawing`;
  document.head.appendChild(script);
  await waitScript(script);
}

function waitScript(script: HTMLScriptElement): Promise<void> {
  return new Promise((resolve, reject) => {
    if (script.getAttribute("data-loaded") === "true" && window.kakao?.maps) {
      resolve();
      return;
    }

    script.addEventListener("load", () => {
      script.setAttribute("data-loaded", "true");
      resolve();
    });
    script.addEventListener("error", () => reject(new Error("script load failed")));
  });
}
