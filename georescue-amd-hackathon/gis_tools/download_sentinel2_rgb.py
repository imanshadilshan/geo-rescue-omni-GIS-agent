"""
Sentinel-2 RGB imagery downloader using Sentinel Hub API.

Downloads Sentinel-2 satellite imagery for a specified location,
extracts RGB bands (B04, B03, B02), and saves as PNG.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from PIL import Image
import logging

from sentinelhub import (
    SentinelHubRequest,
    DataCollection,
    DownloadRequest,
    MimeType,
    CRS,
    BBox,
)

from config import CLIENT_ID, CLIENT_SECRET


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Constants
COLOMBO_BBOX = BBox(
    bbox=[80.65, 6.80, 81.05, 7.10],  # [min_lon, min_lat, max_lon, max_lat]
    crs=CRS.WGS84
)
RESOLUTION_M = 10  # 10 meters per pixel
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"
IMAGE_NAME_TEMPLATE = "sentinel2_rgb_colombo_{}.png"


def setup_output_directory() -> Path:
    """
    Create output directory if it doesn't exist.

    Returns:
        Path: Path to the output directory.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {OUTPUT_DIR}")
    return OUTPUT_DIR


def create_sentinel_request(
    start_date: str = None,
    end_date: str = None,
) -> SentinelHubRequest:
    """
    Create a SentinelHubRequest for RGB imagery download.

    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 30 days ago.
        end_date: End date in YYYY-MM-DD format. Defaults to today.

    Returns:
        SentinelHubRequest: Configured request object.
    """
    # Default date range (last 30 days)
    if end_date is None:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    if start_date is None:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    logger.info(f"Date range: {start_date} to {end_date}")

    # Calculate image size (roughly 40km x 30km area at 10m resolution)
    image_size_pixels = 4096

    # Define evalscript for RGB bands (B04=Red, B03=Green, B02=Blue)
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B04", "B03", "B02"],
                units: "DN"
            }],
            output: {
                bands: 3,
                sampleType: "UINT8"
            }
        };
    }

    function evaluatePixel(sample) {
        // Scale bands from 0-4095 DN to 0-255
        let factor = 255.0 / 4095.0;
        return [
            sample.B04 * factor,
            sample.B03 * factor,
            sample.B02 * factor
        ];
    }
    """

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            DataCollection.SENTINEL2_L2A.define_latest(
                name="s2l2a"
            )
        ],
        responses=[
            DownloadRequest(type=MimeType.PNG)
        ],
        bbox=COLOMBO_BBOX,
        size=[image_size_pixels, image_size_pixels],
        data_folder=None,
        config={"sh_client_id": CLIENT_ID, "sh_client_secret": CLIENT_SECRET},
        time_interval=(start_date, end_date),
    )

    logger.info(f"SentinelHubRequest created for {COLOMBO_BBOX}")
    return request


def download_imagery(request: SentinelHubRequest) -> np.ndarray:
    """
    Download satellite imagery from Sentinel Hub.

    Args:
        request: SentinelHubRequest object.

    Returns:
        np.ndarray: Downloaded imagery as numpy array.

    Raises:
        RuntimeError: If download fails.
    """
    try:
        logger.info("Downloading Sentinel-2 imagery...")
        data = request.get_data()[0]
        logger.info(f"Download successful. Shape: {data.shape}")
        return data
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise RuntimeError(f"Failed to download imagery: {str(e)}")


def save_image_as_png(
    image_array: np.ndarray,
    output_path: Path
) -> None:
    """
    Save image array as PNG file.

    Args:
        image_array: Image data as numpy array (uint8).
        output_path: Path to save PNG file.

    Raises:
        ValueError: If image array format is invalid.
    """
    if image_array.dtype != np.uint8:
        raise ValueError(
            f"Image array must be uint8, got {image_array.dtype}"
        )

    if len(image_array.shape) != 3 or image_array.shape[2] != 3:
        raise ValueError(
            f"Image array must have shape (height, width, 3), "
            f"got {image_array.shape}"
        )

    # Create PIL Image and save
    image = Image.fromarray(image_array, mode="RGB")
    image.save(output_path, format="PNG")
    logger.info(f"Image saved to {output_path}")


def generate_output_filename() -> str:
    """
    Generate timestamped output filename.

    Returns:
        str: Filename with timestamp.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return IMAGE_NAME_TEMPLATE.format(timestamp)


def download_sentinel2_rgb(
    start_date: str = None,
    end_date: str = None,
) -> Path:
    """
    Main function to download Sentinel-2 RGB imagery for Colombo, Sri Lanka.

    Args:
        start_date: Start date in YYYY-MM-DD format (optional).
        end_date: End date in YYYY-MM-DD format (optional).

    Returns:
        Path: Path to saved PNG file.

    Raises:
        RuntimeError: If download or save fails.
    """
    logger.info("=" * 60)
    logger.info("Sentinel-2 RGB Imagery Downloader")
    logger.info("=" * 60)

    try:
        # Setup
        setup_output_directory()

        # Create request
        request = create_sentinel_request(start_date, end_date)

        # Download
        imagery = download_imagery(request)

        # Save
        output_filename = generate_output_filename()
        output_path = OUTPUT_DIR / output_filename
        save_image_as_png(imagery, output_path)

        logger.info("=" * 60)
        logger.info(f"SUCCESS: Image saved to {output_path}")
        logger.info("=" * 60)

        return output_path

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"FAILED: {str(e)}")
        logger.error("=" * 60)
        raise


if __name__ == "__main__":
    # Example usage
    download_sentinel2_rgb()
