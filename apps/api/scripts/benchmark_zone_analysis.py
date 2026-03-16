from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.map import MapAddressSearchRequest, MapCoordinate, MapZoneAnalyzeRequest
from app.services.map_service import lookup_map_by_address
from app.services.map_zone_service import analyze_zone

try:
    from app.services.map_zone.geometry import is_postgres
except ImportError:  # pragma: no cover - backward-compatible benchmark helper
    is_postgres = None


@dataclass(frozen=True)
class BenchmarkPreset:
    name: str
    address: str
    delta: float
    overlap_threshold: float = 0.9


@dataclass
class BenchmarkRun:
    run_index: int
    elapsed_ms: float
    parcel_count: int
    counted_parcel_count: int
    boundary_parcel_count: int
    building_data_ready: bool


PRESETS: dict[str, BenchmarkPreset] = {
    "mapo-small": BenchmarkPreset(
        name="mapo-small",
        address="서울특별시 마포구 마포대로 89",
        delta=0.00025,
    ),
    "pangyo-small": BenchmarkPreset(
        name="pangyo-small",
        address="경기도 성남시 분당구 판교역로 166",
        delta=0.00025,
    ),
    "mapo-medium": BenchmarkPreset(
        name="mapo-medium",
        address="서울특별시 마포구 마포대로 89",
        delta=0.0004,
    ),
}


def _square(lat: float, lng: float, delta: float) -> list[MapCoordinate]:
    return [
        MapCoordinate(lat=lat - delta, lng=lng - delta),
        MapCoordinate(lat=lat - delta, lng=lng + delta),
        MapCoordinate(lat=lat + delta, lng=lng + delta),
        MapCoordinate(lat=lat + delta, lng=lng - delta),
    ]


def _percentile(sorted_values: list[float], ratio: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = ratio * (len(sorted_values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * weight


def _db_kind() -> str:
    return settings.database_url.split(":", maxsplit=1)[0] or "unknown"


def _resolve_coordinates(preset: BenchmarkPreset) -> tuple[float, float]:
    db = SessionLocal()
    try:
        lookup = lookup_map_by_address(db, MapAddressSearchRequest(address=preset.address))
        return lookup.lat, lookup.lng
    finally:
        db.close()


def _run_once(preset: BenchmarkPreset, run_index: int) -> BenchmarkRun:
    lat, lng = _resolve_coordinates(preset)
    payload = MapZoneAnalyzeRequest(
        zone_name=f"benchmark-{preset.name}",
        coordinates=_square(lat, lng, preset.delta),
        overlap_threshold=preset.overlap_threshold,
    )
    db = SessionLocal()
    try:
        started_at = time.perf_counter()
        result = analyze_zone(db, payload=payload)
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        summary = result.summary
        return BenchmarkRun(
            run_index=run_index,
            elapsed_ms=elapsed_ms,
            parcel_count=int(getattr(summary, "parcel_count", 0) or 0),
            counted_parcel_count=int(getattr(summary, "counted_parcel_count", 0) or 0),
            boundary_parcel_count=int(getattr(summary, "boundary_parcel_count", 0) or 0),
            building_data_ready=bool(getattr(summary, "building_data_ready", False)),
        )
    finally:
        db.close()


def _assert_prerequisites() -> None:
    if is_postgres is None:
        return
    db = SessionLocal()
    try:
        if not is_postgres(db):
            raise RuntimeError("zone benchmark requires PostgreSQL/PostGIS")
    finally:
        db.close()


def _summarize_runs(runs: list[BenchmarkRun]) -> dict[str, float | int | bool]:
    elapsed_values = sorted(run.elapsed_ms for run in runs)
    parcel_count_set = {run.parcel_count for run in runs}
    counted_count_set = {run.counted_parcel_count for run in runs}
    boundary_count_set = {run.boundary_parcel_count for run in runs}
    building_ready_set = {run.building_data_ready for run in runs}
    return {
        "runs": len(runs),
        "avg_ms": round(statistics.fmean(elapsed_values), 2),
        "median_ms": round(statistics.median(elapsed_values), 2),
        "p95_ms": round(_percentile(elapsed_values, 0.95), 2),
        "min_ms": round(elapsed_values[0], 2),
        "max_ms": round(elapsed_values[-1], 2),
        "parcel_count": next(iter(parcel_count_set)) if len(parcel_count_set) == 1 else -1,
        "counted_parcel_count": next(iter(counted_count_set)) if len(counted_count_set) == 1 else -1,
        "boundary_parcel_count": next(iter(boundary_count_set)) if len(boundary_count_set) == 1 else -1,
        "building_data_ready": next(iter(building_ready_set)) if len(building_ready_set) == 1 else False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark zone analysis latency with repeatable presets.")
    parser.add_argument(
        "--preset",
        action="append",
        choices=sorted(PRESETS.keys()),
        help="Preset to benchmark. Can be repeated. Defaults to mapo-small.",
    )
    parser.add_argument("--runs", type=int, default=5, help="Measured run count per preset. Default: 5")
    parser.add_argument("--warmup", type=int, default=1, help="Warm-up run count per preset. Default: 1")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected_presets = [PRESETS[name] for name in (args.preset or ["mapo-small"])]

    if os.environ.get("FORCE_DISABLE_REDIS") == "1" or os.environ.get("REDIS_URL", None) == "":
        settings.redis_url = ""

    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")
    if args.warmup < 0:
        raise SystemExit("--warmup must be >= 0")

    _assert_prerequisites()

    reports: list[dict[str, object]] = []
    for preset in selected_presets:
        for index in range(args.warmup):
            _run_once(preset, run_index=-(index + 1))

        measured_runs = [_run_once(preset, run_index=index + 1) for index in range(args.runs)]
        summary = _summarize_runs(measured_runs)
        reports.append(
            {
                "preset": asdict(preset),
                "environment": {
                    "database": _db_kind(),
                    "redis_enabled": bool(settings.redis_url),
                    "building_cache_ttl_hours": getattr(settings, "map_zone_building_cache_ttl_hours", None),
                    "bbox_split_max_depth": getattr(settings, "map_zone_bbox_split_max_depth", None),
                    "land_metadata_workers": getattr(settings, "map_zone_land_metadata_workers", None),
                    "building_workers": getattr(settings, "map_zone_building_workers", None),
                    "ai_enabled": getattr(settings, "map_zone_ai_enabled", None),
                },
                "summary": summary,
                "runs": [asdict(run) for run in measured_runs],
            }
        )

    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        return 0

    for report in reports:
        preset = report["preset"]
        summary = report["summary"]
        env = report["environment"]
        print(
            f"[{preset['name']}] address={preset['address']} delta={preset['delta']} "
            f"runs={summary['runs']} avg={summary['avg_ms']:.2f}ms median={summary['median_ms']:.2f}ms "
            f"p95={summary['p95_ms']:.2f}ms min={summary['min_ms']:.2f}ms max={summary['max_ms']:.2f}ms"
        )
        print(
            f"  parcels={summary['parcel_count']} counted={summary['counted_parcel_count']} "
            f"boundary={summary['boundary_parcel_count']} building_ready={summary['building_data_ready']}"
        )
        print(
            f"  env=db:{env['database']} redis:{env['redis_enabled']} bbox_split:{env['bbox_split_max_depth']} "
            f"land_workers:{env['land_metadata_workers']} building_workers:{env['building_workers']} ai:{env['ai_enabled']}"
        )
        for run in report["runs"]:
            print(
                f"    run#{run['run_index']}: {run['elapsed_ms']:.2f}ms "
                f"(parcels={run['parcel_count']}, boundary={run['boundary_parcel_count']}, building_ready={run['building_data_ready']})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
