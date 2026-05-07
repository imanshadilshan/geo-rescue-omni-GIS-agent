"""Run a near-real-time flood analysis cycle using live weather input."""

import logging
from pathlib import Path

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


if __name__ == "__main__":
    run_cycle()