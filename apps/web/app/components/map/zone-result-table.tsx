"use client";

import { MetricCard } from "@/app/components/map/metric-card";
import { formatArea, formatNumber } from "@/app/lib/map-view-utils";
import type { MapZoneResponse } from "@/app/lib/types";

export function ZoneResultTable({
  zoneResult,
  selectedPnuSet,
  onSelect,
  onLocate,
  onOpenBasic,
}: {
  zoneResult: MapZoneResponse | null;
  selectedPnuSet: Set<string>;
  onSelect: (pnu: string, checked: boolean) => void;
  onLocate: (lat: number | null, lng: number | null) => void;
  onOpenBasic: (parcel: MapZoneResponse["parcels"][number]) => void;
}) {
  if (!zoneResult) {
    return <div className="map-empty">구역 좌표를 선택하고 `구역 분석`을 실행해 주세요.</div>;
  }

  const { summary, parcels } = zoneResult;
  const overlapPercent = Math.round((summary.overlap_threshold || 0.9) * 100);
  return (
    <>
      <div className="map-metrics">
        <MetricCard label="구역명" value={summary.zone_name} />
        <MetricCard label="기준연도(최신)" value={summary.base_year || "-"} />
        <MetricCard label="구역 면적(㎡)" value={formatArea(summary.zone_area_sqm)} />
        <MetricCard label="구역 내 필지 수" value={formatNumber(summary.parcel_count)} />
        <MetricCard label="평균 공시지가(원/㎡)" value={formatNumber(summary.average_unit_price)} />
        <MetricCard label="총 공시지가 합계(원)" value={formatNumber(summary.assessed_total_price)} />
        <MetricCard label="건축물 수" value={formatNumber(summary.total_building_count)} />
        <MetricCard label="노후 건축물 수" value={formatNumber(summary.aged_building_count)} />
        <MetricCard label="노후도(%)" value={formatNumber(summary.aged_building_ratio)} />
        <MetricCard label="사용승인년도" value={summary.average_approval_year ? String(summary.average_approval_year) : "-"} />
        <MetricCard label="총 대지면적(㎡)" value={formatArea(summary.total_site_area_sqm)} />
        <MetricCard label="총 연면적(㎡)" value={formatArea(summary.total_floor_area_sqm)} />
        <MetricCard label="용적률(%)" value={formatNumber(summary.average_floor_area_ratio)} />
        <MetricCard label="과소필지 비율(%)" value={formatNumber(summary.undersized_parcel_ratio)} />
      </div>
      <p className="hint">필지 포함 기준: 구역 내부 {overlapPercent}% 이상 포함된 경우만 집계하며, 계산 반영 필지는 지도에서 진하게 표시합니다.</p>
      <p className="hint">건축 지표 기준: 노후도는 사용승인 30년 이상, 과소필지는 90㎡ 미만 필지를 기준으로 계산합니다.</p>
      {summary.building_data_message ? <p className="hint">{summary.building_data_message}</p> : null}
      <div className="map-zone-table-wrap">
        <table className="data-table map-zone-table">
          <thead>
            <tr>
              <th className="center narrow">선택</th>
              <th className="address-col">지번 주소</th>
              <th className="center">지목</th>
              <th className="center">용도지역명</th>
              <th className="center">주용도</th>
              <th className="center narrow">건축물 수</th>
              <th className="center narrow">노후 건물 수</th>
              <th className="center">사용승인년도</th>
              <th className="right">용적률(%)</th>
              <th className="right">면적(㎡)</th>
              <th className="right">공시지가(원/㎡)</th>
              <th className="right">면적×공시지가</th>
              <th className="center narrow">연도</th>
            </tr>
          </thead>
          <tbody>
            {parcels.map((row) => {
              const selected = selectedPnuSet.has(row.pnu);
              return (
                <tr key={row.pnu} className={!row.included ? "excluded" : ""} onClick={() => onLocate(row.lat, row.lng)}>
                  <td className="center" data-label="선택" onClick={(event) => event.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selected}
                      disabled={!row.included}
                      onChange={(event) => onSelect(row.pnu, event.target.checked)}
                      aria-label={`필지 선택 ${row.pnu}`}
                    />
                  </td>
                  <td className="address-col" data-label="지번 주소" onClick={(event) => event.stopPropagation()}>
                    <button type="button" className="map-address-link" onClick={() => onOpenBasic(row)}>
                      {row.jibun_address || "-"}
                    </button>
                  </td>
                  <td className="center" data-label="지목">{row.land_category_name || "-"}</td>
                  <td className="center" data-label="용도지역명">{row.purpose_area_name || "-"}</td>
                  <td className="center" data-label="주용도">{row.primary_purpose_name || "-"}</td>
                  <td className="center" data-label="건축물 수">{formatNumber(row.building_count)}</td>
                  <td className="center" data-label="노후 건물 수">{formatNumber(row.aged_building_count)}</td>
                  <td className="center" data-label="사용승인년도">{row.average_approval_year || "-"}</td>
                  <td className="right" data-label="용적률(%)">{formatNumber(row.floor_area_ratio)}</td>
                  <td className="right" data-label="면적(㎡)">{formatArea(row.area_sqm)}</td>
                  <td className="right" data-label="공시지가(원/㎡)">{formatNumber(row.price_current)}</td>
                  <td className="right" data-label="면적×공시지가">{formatNumber(row.estimated_total_price)}</td>
                  <td className="center" data-label="연도">{row.price_year || "-"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
