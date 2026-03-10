"use client";

import type { BulkJob } from "@/app/lib/types";

type Props = {
  jobs: BulkJob[];
  page: number;
  totalPages: number;
  loading: boolean;
  deleting: boolean;
  selectedIds: Set<string>;
  onRefresh: () => void;
  onDeleteSelected: () => void;
  onDownload: (job: BulkJob) => void;
  onToggleSelect: (jobId: string) => void;
  onToggleSelectAll: (checked: boolean) => void;
  onPageChange: (page: number) => void;
};

export function BulkJobTable(props: Props) {
  const allSelected = props.jobs.length > 0 && props.jobs.every((job) => props.selectedIds.has(job.job_id));
  const anySelected = props.selectedIds.size > 0;

  return (
    <section className="panel">
      <div className="bulk-table-head">
        <h2>파일 작업 이력</h2>
        <div className="bulk-head-actions">
          <button type="button" className="nav-item" onClick={props.onRefresh} disabled={props.loading || props.deleting}>
            새로고침
          </button>
          <button
            type="button"
            className="nav-item danger"
            onClick={props.onDeleteSelected}
            disabled={!anySelected || props.deleting || props.loading}
          >
            {props.deleting ? "삭제 중..." : "선택 삭제"}
          </button>
        </div>
      </div>
      {props.jobs.length === 0 ? (
        <div className="empty-box">아직 파일 작업 이력이 없습니다.</div>
      ) : (
        <>
          <table className="data-table bulk-center-table mobile-card-table">
            <thead>
              <tr>
                <th>파일명</th>
                <th>상태</th>
                <th>행 수</th>
                <th>진행률</th>
                <th>조회시작 일시</th>
                <th>다운로드</th>
                <th className="checkbox-col">
                  <input
                    type="checkbox"
                    aria-label="현재 페이지 전체 선택"
                    checked={allSelected}
                    onChange={(e) => props.onToggleSelectAll(e.target.checked)}
                  />
                </th>
              </tr>
            </thead>
            <tbody>
              {props.jobs.map((job) => (
                <tr key={job.job_id}>
                  <td data-label="파일명">{job.file_name}</td>
                  <td data-label="상태">
                    <span className={`status-badge ${job.status}`}>{toStatusLabel(job.status)}</span>
                    {job.error_message ? (
                      <p className="bulk-job-diagnosis">{diagnoseBulkError(job.error_message)}</p>
                    ) : null}
                  </td>
                  <td data-label="행 수">
                    {job.processed_rows.toLocaleString()} / {job.total_rows.toLocaleString()}
                  </td>
                  <td data-label="진행률">{job.progress_percent.toFixed(2)}%</td>
                  <td data-label="조회시작 일시">{formatDateTime(job.created_at)}</td>
                  <td data-label="다운로드">
                    {job.can_download ? (
                      <button type="button" className="nav-item" disabled={props.deleting} onClick={() => props.onDownload(job)}>
                        다운로드
                      </button>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="checkbox-col" data-label="선택">
                    <input
                      type="checkbox"
                      aria-label={`${job.file_name} 선택`}
                      checked={props.selectedIds.has(job.job_id)}
                      onChange={() => props.onToggleSelect(job.job_id)}
                      disabled={props.deleting || job.status === "processing"}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={props.page} totalPages={props.totalPages} onChange={props.onPageChange} />
        </>
      )}
    </section>
  );
}

function Pagination(props: { page: number; totalPages: number; onChange: (page: number) => void }) {
  if (props.totalPages <= 1) return null;
  const pages = Array.from({ length: props.totalPages }, (_, idx) => idx + 1);
  return (
    <div className="pagination">
      <button type="button" className="nav-item" disabled={props.page <= 1} onClick={() => props.onChange(props.page - 1)}>
        이전
      </button>
      {pages.map((page) => (
        <button
          type="button"
          key={page}
          className={`nav-item ${page === props.page ? "active" : ""}`}
          onClick={() => props.onChange(page)}
        >
          {page}
        </button>
      ))}
      <button
        type="button"
        className="nav-item"
        disabled={props.page >= props.totalPages}
        onClick={() => props.onChange(props.page + 1)}
      >
        다음
      </button>
    </div>
  );
}

function toStatusLabel(status: BulkJob["status"]): string {
  if (status === "queued") return "대기";
  if (status === "processing") return "처리중";
  if (status === "completed") return "완료";
  return "실패";
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const weekdays = ["일", "월", "화", "수", "목", "금", "토"] as const;
  const weekday = weekdays[date.getDay()];

  const hour = date.getHours();
  const minute = String(date.getMinutes()).padStart(2, "0");
  const ampm = hour < 12 ? "am" : "pm";
  const hour12 = hour % 12 || 12;

  return `${year}.${month}.${day}(${weekday}) ${hour12}:${minute} ${ampm}`;
}

function diagnoseBulkError(message: string): string {
  const normalized = message.toLowerCase();
  if (normalized.includes("duplicate") || normalized.includes("중복")) {
    return "중복 주소 또는 중복 행이 포함된 작업입니다.";
  }
  if (normalized.includes("address") || normalized.includes("주소")) {
    return "주소 형식 또는 필수 주소 요소 누락을 확인해 주세요.";
  }
  if (normalized.includes("pnu")) {
    return "PNU 변환 단계에서 해석되지 않은 행이 많습니다.";
  }
  if (normalized.includes("timeout") || normalized.includes("timed out")) {
    return "외부 API 응답 지연으로 작업이 중단됐습니다.";
  }
  if (normalized.includes("vworld") || normalized.includes("api")) {
    return "외부 연동 응답 오류입니다. 잠시 후 다시 시도해 주세요.";
  }
  if (normalized.includes("xlsx") || normalized.includes("csv") || normalized.includes("excel")) {
    return "파일 형식 또는 읽기 가능한 시트 구조를 확인해 주세요.";
  }
  return "실패 원인을 재검토해야 하는 작업입니다.";
}
