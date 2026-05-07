"""Run a near-real-time flood analysis cycle using live weather input."""

import logging
from pathlib import Path
import json
from datetime import datetime, timezone

from live_flood_feed import generate_live_flood_polygon
from flood_overlay import analyze_flood_impact
from routing import plan_safe_route, save_route_geojson


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_cycle() -> None:
    flood_polygon_path, snapshot = generate_live_flood_polygon()
    blocked_roads_path, saved_polygon_path, stats = analyze_flood_impact(
        flood_polygon_path=flood_polygon_path
    )

    route_path, route_gdf = plan_safe_route(
        remove_blocked=True,
        blocked_roads_path=blocked_roads_path,
    )

    latest_route_path = Path(__file__).parent.parent / "data" / "processed" / "latest_route.geojson"
    save_route_geojson(route_gdf, latest_route_path)

    logger.info("Live flood cycle complete")
    logger.info("  - Input severity: %s", snapshot.get("derived_severity"))
    logger.info("  - Blocked roads output: %s", blocked_roads_path)
    logger.info("  - Flood polygon output: %s", saved_polygon_path)
    logger.info("  - Route output: %s", route_path)
    logger.info("  - Latest route output: %s", latest_route_path)
    logger.info("  - Affected roads: %s", stats.get("total_affected_roads"))

    # Emit a compact status JSON for UI polling
    try:
        processed_dir = Path(__file__).parent.parent / "data" / "processed"
        status = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "severity": snapshot.get("derived_severity"),
            "affected_roads": stats.get("total_affected_roads"),
            "total_affected_length_m": stats.get("total_affected_length_m"),
            "route_length_m": float(route_gdf["length_m"].sum()) if not route_gdf.empty else None,
            "route_path": str(route_path),
            "latest_route_path": str(latest_route_path),
        }

        status_path = processed_dir / "latest_status.json"
        processed_dir.mkdir(parents=True, exist_ok=True)
        with status_path.open("w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)

        logger.info("  - Latest status written: %s", status_path)
    except Exception as exc:
        logger.error("Failed to write latest status: %s", exc)


if __name__ == "__main__":
    run_cycle()