"""
OSMnx road network downloader and converter for Colombo, Sri Lanka.

Downloads the drivable road network, converts to GeoDataFrame,
and exports as GeoJSON for further analysis.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional

import osmnx as ox
import geopandas as gpd
from shapely.geometry import LineString


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Constants
LOCATION_NAME = "Colombo, Sri Lanka"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
ROAD_NETWORK_FILE = "colombo_road_network.geojson"
GRAPH_FILE = "colombo_road_network_graph.graphml"


def setup_output_directory() -> Path:
    """
    Create output directory if it doesn't exist.

    Returns:
        Path: Path to the output directory.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {OUTPUT_DIR}")
    return OUTPUT_DIR


def download_road_network(
    location: str = LOCATION_NAME,
    network_type: str = "drive",
    timeout: int = 180,
) -> object:
    """
    Download drivable road network from OpenStreetMap using OSMnx.

    Args:
        location: Location name (e.g., "Colombo, Sri Lanka").
        network_type: Type of road network ('drive', 'walk', 'bike', 'all').
        timeout: Timeout for API request in seconds.

    Returns:
        networkx.MultiDiGraph: Road network graph.

    Raises:
        Exception: If download fails.
    """
    try:
        logger.info(f"Downloading road network for {location}...")
        logger.info(f"Network type: {network_type}")

        # Download graph from place. Some OSMnx versions don't accept a `timeout` kwarg,
        # so try with it first and fall back to calling without it if needed.
        try:
            graph = ox.graph_from_place(
                query=location,
                network_type=network_type,
                simplify=True,
                retain_all=False,
                truncate_by_edge=True,
                timeout=timeout,
            )
        except TypeError as e:
            msg = str(e)
            if "timeout" in msg and "unexpected" in msg:
                logger.warning("Installed OSMnx does not accept `timeout`; retrying without it.")
                graph = ox.graph_from_place(
                    query=location,
                    network_type=network_type,
                    simplify=True,
                    retain_all=False,
                    truncate_by_edge=True,
                )
            else:
                raise

        # Get statistics
        num_nodes = len(graph.nodes())
        num_edges = len(graph.edges())

        # basic_stats may not include 'area' depending on OSMnx version.
        stats = ox.stats.basic_stats(graph)
        if "area" in stats:
            area_m2 = stats["area"]
        else:
            # Fall back: compute approximate area (m^2) from node convex hull
            try:
                nodes_gdf, _ = ox.graph_to_gdfs(graph)
                # Project to metric CRS (Web Mercator) then compute convex hull area
                nodes_proj = nodes_gdf.to_crs(epsg=3857)
                hull = nodes_proj.unary_union.convex_hull
                area_m2 = hull.area
            except Exception:
                area_m2 = None

        area_km2 = (area_m2 / 1_000_000) if area_m2 is not None else None

        logger.info(f"Download successful!")
        logger.info(f"  - Nodes: {num_nodes}")
        logger.info(f"  - Edges (road segments): {num_edges}")
        logger.info(f"  - Area: {area_km2:.2f} km²")

        return graph

    except Exception as e:
        logger.error(f"Failed to download road network: {str(e)}")
        raise


def convert_graph_to_geodataframe(
    graph: object,
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Convert OSMnx graph to GeoDataFrames for nodes and edges.

    Args:
        graph: networkx.MultiDiGraph road network graph.

    Returns:
        Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]: (nodes_gdf, edges_gdf)

    Raises:
        Exception: If conversion fails.
    """
    try:
        logger.info("Converting graph to GeoDataFrames...")

        # Convert to GeoDataFrames
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(graph)

        logger.info(f"  - Nodes GeoDataFrame: {len(nodes_gdf)} features")
        logger.info(f"  - Edges GeoDataFrame: {len(edges_gdf)} features")
        logger.info(f"  - Nodes CRS: {nodes_gdf.crs}")
        logger.info(f"  - Edges CRS: {edges_gdf.crs}")

        return nodes_gdf, edges_gdf

    except Exception as e:
        logger.error(f"Failed to convert graph: {str(e)}")
        raise


def save_geojson(
    geodataframe: gpd.GeoDataFrame,
    output_path: Path,
    description: str = "GeoDataFrame",
) -> None:
    """
    Save GeoDataFrame as GeoJSON file.

    Args:
        geodataframe: GeoDataFrame to save.
        output_path: Path to save GeoJSON file.
        description: Description for logging.

    Raises:
        Exception: If save fails.
    """
    try:
        logger.info(f"Saving {description}...")
        geodataframe.to_file(output_path, driver="GeoJSON")
        logger.info(f"  - Saved to {output_path}")
        logger.info(f"  - File size: {output_path.stat().st_size / 1024:.2f} KB")

    except Exception as e:
        logger.error(f"Failed to save GeoJSON: {str(e)}")
        raise


def save_graphml(
    graph: object,
    output_path: Path,
) -> None:
    """
    Save graph as GraphML file for network analysis.

    Args:
        graph: networkx.MultiDiGraph road network graph.
        output_path: Path to save GraphML file.

    Raises:
        Exception: If save fails.
    """
    try:
        logger.info("Saving graph as GraphML...")
        ox.save_graphml(graph, filepath=output_path)
        logger.info(f"  - Saved to {output_path}")
        logger.info(f"  - File size: {output_path.stat().st_size / 1024:.2f} KB")

    except Exception as e:
        logger.error(f"Failed to save GraphML: {str(e)}")
        raise


def get_network_statistics(
    edges_gdf: gpd.GeoDataFrame,
) -> dict:
    """
    Calculate statistics for the road network.

    Args:
        edges_gdf: GeoDataFrame of road segments.

    Returns:
        dict: Network statistics.
    """
    try:
        # Project to a metric CRS for accurate length/area calculations (Web Mercator)
        try:
            edges_proj = edges_gdf.to_crs(epsg=3857)
            total_length_m = edges_proj.geometry.length.sum()
            avg_segment_length_m = edges_proj.geometry.length.mean()
        except Exception:
            # Fall back to geographic lengths (may be inaccurate)
            total_length_m = edges_gdf.geometry.length.sum()
            avg_segment_length_m = edges_gdf.geometry.length.mean()

        total_length_km = total_length_m / 1000

        # Road classification distribution: handle list-like entries by exploding
        highway_types = {}
        if "highway" in edges_gdf.columns:
            try:
                hw_series = edges_gdf["highway"].apply(lambda v: v if isinstance(v, (list, tuple)) else [v])
                exploded = hw_series.explode()
                highway_types = exploded.value_counts()
                highway_types = highway_types.to_dict()
            except Exception:
                highway_types = {}

        stats = {
            "total_segments": len(edges_gdf),
            "total_length_m": total_length_m,
            "total_length_km": total_length_km,
            "avg_segment_length_m": avg_segment_length_m,
            "highway_types": highway_types,
        }

        return stats

    except Exception as e:
        logger.error(f"Failed to calculate statistics: {str(e)}")
        return {}


def download_and_process_road_network(
    location: str = LOCATION_NAME,
    network_type: str = "drive",
    save_graph: bool = True,
) -> Tuple[Path, Path, Optional[Path]]:
    """
    Main function to download, process, and save road network.

    Args:
        location: Location name (e.g., "Colombo, Sri Lanka").
        network_type: Type of road network ('drive', 'walk', 'bike', 'all').
        save_graph: Whether to save graph as GraphML.

    Returns:
        Tuple[Path, Path, Optional[Path]]: Paths to (edges_geojson, nodes_geojson, graph_graphml)

    Raises:
        Exception: If download or processing fails.
    """
    logger.info("=" * 60)
    logger.info("OSMnx Road Network Downloader")
    logger.info("=" * 60)

    try:
        # Setup
        setup_output_directory()

        # Download
        graph = download_road_network(location, network_type)

        # Convert
        nodes_gdf, edges_gdf = convert_graph_to_geodataframe(graph)

        # Calculate statistics
        stats = get_network_statistics(edges_gdf)
        logger.info("Network Statistics:")
        logger.info(f"  - Total segments: {stats.get('total_segments', 'N/A')}")
        total_km = stats.get('total_length_km')
        if isinstance(total_km, (int, float)):
            logger.info(f"  - Total length: {total_km:.2f} km")
        else:
            logger.info(f"  - Total length: {total_km}")

        avg_seg = stats.get('avg_segment_length_m')
        if isinstance(avg_seg, (int, float)):
            logger.info(f"  - Avg segment length: {avg_seg:.2f} m")
        else:
            logger.info(f"  - Avg segment length: {avg_seg}")

        # Save GeoJSON files
        edges_path = OUTPUT_DIR / ROAD_NETWORK_FILE
        nodes_path = OUTPUT_DIR / "colombo_road_nodes.geojson"
        save_geojson(edges_gdf, edges_path, "edges (road segments)")
        save_geojson(nodes_gdf, nodes_path, "nodes (intersections)")

        # Save GraphML
        graph_path = None
        if save_graph:
            graph_path = OUTPUT_DIR / GRAPH_FILE
            save_graphml(graph, graph_path)

        logger.info("=" * 60)
        logger.info("SUCCESS: Road network downloaded and processed")
        logger.info("=" * 60)

        return edges_path, nodes_path, graph_path

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"FAILED: {str(e)}")
        logger.error("=" * 60)
        raise


if __name__ == "__main__":
    # Example usage
    edges_geojson, nodes_geojson, graph_graphml = download_and_process_road_network()
