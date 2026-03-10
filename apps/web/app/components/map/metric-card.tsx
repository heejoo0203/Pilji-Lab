"use client";

export function MetricCard({ label, value }: { label: string; value: string }) {
  const digitCount = value.replace(/[^0-9]/g, "").length;
  const sizeClass = digitCount >= 14 ? "compact-xl" : digitCount >= 11 ? "compact-lg" : "";

  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${sizeClass}`.trim()} title={value}>
        {value}
      </div>
    </div>
  );
}
