"""
GeoJSON export utilities for GeoPandas GeoDataFrames.

Provides reusable functions to export GeoDataFrames to GeoJSON format
with CRS validation, automatic folder creation, and error handling.
"""

import logging
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
from pyproj import CRS


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Constants
DEFAULT_CRS = "EPSG:4326"  # WGS84 - standard for GeoJSON
VALID_MIME_TYPES = {
    "geojson": "application/geo+json",
    "json": "application/json",
}


class CRSValidationError(Exception):
    """Raised when CRS validation fails."""
    pass


class GeoJSONExportError(Exception):
    """Raised when GeoJSON export fails."""
    pass


def ensure_directory_exists(
    directory: Union[str, Path],
    create_if_missing: bool = True,
) -> Path:
    """
    Ensure output directory exists, creating if necessary.

    Args:
        directory: Path to directory.
        create_if_missing: Whether to create directory if it doesn't exist.

    Returns:
        Path: Directory path (as Path object).

    Raises:
        OSError: If directory cannot be created.
    """
    try:
        dir_path = Path(directory)
        
        if not dir_path.exists():
            if create_if_missing:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            else:
                raise OSError(f"Directory does not exist: {dir_path}")
        
        return dir_path

    except Exception as e:
        logger.error(f"Failed to ensure directory: {str(e)}")
        raise


def validate_crs(
    geodataframe: gpd.GeoDataFrame,
    target_crs: Optional[str] = DEFAULT_CRS,
    auto_convert: bool = False,
) -> gpd.GeoDataFrame:
    """
    Validate CRS of GeoDataFrame and optionally convert.

    Args:
        geodataframe: GeoDataFrame to validate.
        target_crs: Target CRS (default: EPSG:4326 for GeoJSON).
        auto_convert: Whether to auto-convert if CRS doesn't match.

    Returns:
        gpd.GeoDataFrame: GeoDataFrame with valid CRS.

    Raises:
        CRSValidationError: If CRS is invalid or conversion fails.
    """
    try:
        if geodataframe.crs is None:
            logger.warning(f"GeoDataFrame has no CRS, assuming {target_crs}")
            geodataframe = geodataframe.set_crs(target_crs)
            return geodataframe

        current_crs = str(geodataframe.crs)
        logger.info(f"Current CRS: {current_crs}")

        # Check if CRS matches target
        if str(geodataframe.crs) == str(CRS.from_string(target_crs)):
            logger.info(f"CRS validation passed: {current_crs}")
            return geodataframe

        # Handle CRS mismatch
        if auto_convert:
            logger.info(f"Converting CRS from {current_crs} to {target_crs}...")
            geodataframe = geodataframe.to_crs(target_crs)
            logger.info(f"CRS conversion successful: {target_crs}")
            return geodataframe
        else:
            logger.warning(
                f"CRS mismatch: {current_crs} != {target_crs}. "
                f"Consider setting auto_convert=True"
            )
            return geodataframe

    except Exception as e:
        raise CRSValidationError(f"CRS validation failed: {str(e)}")


def validate_geometry(
    geodataframe: gpd.GeoDataFrame,
) -> bool:
    """
    Validate that all geometries are valid.

    Args:
        geodataframe: GeoDataFrame to validate.

    Returns:
        bool: True if all geometries are valid.

    Raises:
        ValueError: If invalid geometries found.
    """
    try:
        # Check for empty geometries
        empty_count = geodataframe.geometry.is_empty.sum()
        if empty_count > 0:
            logger.warning(f"Found {empty_count} empty geometries")

        # Check for invalid geometries
        invalid_count = (~geodataframe.geometry.is_valid).sum()
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} invalid geometries")
            # Optionally fix them
            geodataframe["geometry"] = geodataframe.geometry.buffer(0)
            logger.info("Applied buffer(0) to fix invalid geometries")

        logger.info(f"Geometry validation complete: {len(geodataframe)} features")
        return True

    except Exception as e:
        raise ValueError(f"Geometry validation failed: {str(e)}")


def get_geojson_metadata(
    geodataframe: gpd.GeoDataFrame,
) -> dict:
    """
    Extract metadata about GeoDataFrame for export.

    Args:
        geodataframe: GeoDataFrame to analyze.

    Returns:
        dict: Metadata dictionary.
    """
    try:
        bounds = geodataframe.total_bounds
        
        metadata = {
            "feature_count": len(geodataframe),
            "crs": str(geodataframe.crs) if geodataframe.crs else "None",
            "geometry_types": geodataframe.geometry.geom_type.unique().tolist(),
            "bounds": {
                "minx": float(bounds[0]),
                "miny": float(bounds[1]),
                "maxx": float(bounds[2]),
                "maxy": float(bounds[3]),
            },
            "columns": geodataframe.columns.tolist(),
        }
        
        return metadata

    except Exception as e:
        logger.error(f"Failed to extract metadata: {str(e)}")
        return {}


def save_geojson(
    geodataframe: gpd.GeoDataFrame,
    output_path: Union[str, Path],
    validate_crs: bool = True,
    auto_convert_crs: bool = True,
    target_crs: str = DEFAULT_CRS,
    create_dir: bool = True,
    validate_geom: bool = True,
    verbose: bool = True,
) -> Path:
    """
    Save GeoDataFrame as GeoJSON with comprehensive validation and error handling.

    Args:
        geodataframe: GeoDataFrame to export.
        output_path: Path to save GeoJSON file.
        validate_crs: Whether to validate CRS before export.
        auto_convert_crs: Whether to auto-convert CRS if needed.
        target_crs: Target CRS for export (default: EPSG:4326).
        create_dir: Whether to create output directory if missing.
        validate_geom: Whether to validate geometries before export.
        verbose: Whether to log detailed information.

    Returns:
        Path: Path to saved file.

    Raises:
        GeoJSONExportError: If export fails.
        CRSValidationError: If CRS validation fails.
    """
    try:
        output_path = Path(output_path)
        
        if verbose:
            logger.info(f"Starting GeoJSON export to {output_path}...")

        # Create directory if needed
        if create_dir:
            ensure_directory_exists(output_path.parent, create_if_missing=True)

        # Copy to avoid modifying original
        gdf = geodataframe.copy()

        # Validate and convert CRS
        if validate_crs:
            gdf = validate_crs(gdf, target_crs, auto_convert_crs)

        # Validate geometries
        if validate_geom:
            validate_geometry(gdf)

        # Extract and log metadata
        metadata = get_geojson_metadata(gdf)
        if verbose:
            logger.info(f"Export metadata:")
            logger.info(f"  - Features: {metadata.get('feature_count', 'N/A')}")
            logger.info(f"  - CRS: {metadata.get('crs', 'N/A')}")
            logger.info(f"  - Geometry types: {metadata.get('geometry_types', 'N/A')}")
            logger.info(f"  - Bounds: {metadata.get('bounds', 'N/A')}")

        # Export to GeoJSON
        gdf.to_file(output_path, driver="GeoJSON")

        # Get file info
        file_size_kb = output_path.stat().st_size / 1024

        if verbose:
            logger.info(f"SUCCESS: GeoJSON exported")
            logger.info(f"  - Path: {output_path}")
            logger.info(f"  - Size: {file_size_kb:.2f} KB")

        return output_path

    except Exception as e:
        logger.error(f"FAILED to export GeoJSON: {str(e)}")
        raise GeoJSONExportError(f"Export failed: {str(e)}")


def save_geojson_batch(
    geodataframes: dict,
    output_dir: Union[str, Path],
    create_dir: bool = True,
    validate_crs: bool = True,
    auto_convert_crs: bool = True,
) -> dict:
    """
    Save multiple GeoDataFrames as GeoJSON files in batch.

    Args:
        geodataframes: Dictionary of {filename: GeoDataFrame}.
        output_dir: Output directory for all files.
        create_dir: Whether to create directory if missing.
        validate_crs: Whether to validate CRS.
        auto_convert_crs: Whether to auto-convert CRS.

    Returns:
        dict: Dictionary of {filename: output_path}.

    Raises:
        GeoJSONExportError: If any export fails.
    """
    try:
        output_dir = Path(output_dir)
        ensure_directory_exists(output_dir, create_if_missing=create_dir)

        results = {}
        logger.info(f"Starting batch export to {output_dir}...")

        for filename, gdf in geodataframes.items():
            if not filename.endswith('.geojson'):
                filename = f"{filename}.geojson"

            output_path = output_dir / filename

            try:
                path = save_geojson(
                    gdf,
                    output_path,
                    validate_crs=validate_crs,
                    auto_convert_crs=auto_convert_crs,
                    verbose=False,
                )
                results[filename] = path
                logger.info(f"  ✓ {filename}")

            except Exception as e:
                logger.error(f"  ✗ {filename}: {str(e)}")
                results[filename] = None

        success_count = sum(1 for v in results.values() if v is not None)
        total_count = len(results)
        logger.info(f"Batch export complete: {success_count}/{total_count} successful")

        return results

    except Exception as e:
        logger.error(f"Batch export failed: {str(e)}")
        raise GeoJSONExportError(f"Batch export failed: {str(e)}")


def load_geojson(
    geojson_path: Union[str, Path],
) -> gpd.GeoDataFrame:
    """
    Load GeoJSON file as GeoDataFrame with error handling.

    Args:
        geojson_path: Path to GeoJSON file.

    Returns:
        gpd.GeoDataFrame: Loaded GeoDataFrame.

    Raises:
        FileNotFoundError: If file not found.
    """
    try:
        geojson_path = Path(geojson_path)

        if not geojson_path.exists():
            raise FileNotFoundError(f"File not found: {geojson_path}")

        logger.info(f"Loading GeoJSON from {geojson_path}...")
        gdf = gpd.read_file(geojson_path)

        logger.info(f"  - Features: {len(gdf)}")
        logger.info(f"  - CRS: {gdf.crs}")
        logger.info(f"  - Geometry types: {gdf.geometry.geom_type.unique()}")

        return gdf

    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to load GeoJSON: {str(e)}")
        raise


if __name__ == "__main__":
    # Example usage
    pass
