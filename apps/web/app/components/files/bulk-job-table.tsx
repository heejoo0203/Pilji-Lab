"use client";

import type { BulkJob } from "@/app/lib/types";

type Props = {
  jobs: BulkJob[];
  loading: boolean;
  onRefresh: () => void;
  onDownload: (job: BulkJob) => void;
};

export function BulkJobTable(props: Props) {
  return (
    <section className="panel">
      <div className="bulk-table-head">
        <h2>파일 작업 이력</h2>
        <button type="button" className="nav-item" onClick={props.onRefresh} disabled={props.loading}>
          새로고침
        </button>
      </div>
      {props.jobs.length === 0 ? (
        <div className="empty-box">아직 파일 작업 이력이 없습니다.</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>파일명</th>
              <th>상태</th>
              <th>행 수</th>
              <th>진행률</th>
              <th>일시</th>
              <th>다운로드</th>
            </tr>
          </thead>
          <tbody>
            {props.jobs.map((job) => (
              <tr key={job.job_id}>
                <td>{job.file_name}</td>
                <td>
                  <span className={`status-badge ${job.status}`}>{toStatusLabel(job.status)}</span>
                </td>
                <td>
                  {job.processed_rows.toLocaleString()} / {job.total_rows.toLocaleString()}
                </td>
                <td>{job.progress_percent.toFixed(2)}%</td>
                <td>{formatDateTime(job.created_at)}</td>
                <td>
                  <button
                    type="button"
                    className="nav-item"
                    disabled={!job.can_download}
                    onClick={() => props.onDownload(job)}
                  >
                    다운로드
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
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
  return date.toLocaleString("ko-KR", { hour12: false });
}
