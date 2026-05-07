"""Download satellite imagery utilities."""
import os
import sys
import traceback
from dotenv import load_dotenv

load_dotenv()

print("Starting satellite download...")

try:
    from sentinelhub import (
        SHConfig, SentinelHubRequest, DataCollection,
        MimeType, BBox, CRS, bbox_to_dimensions
    )
    print("✅ sentinelhub imported")
except Exception as e:
    print("❌ sentinelhub import failed:", e)
    sys.exit()

try:
    config = SHConfig()
    config.sh_client_id = os.getenv("SENTINEL_CLIENT_ID")
    config.sh_client_secret = os.getenv("SENTINEL_CLIENT_SECRET")
    config.sh_base_url = "https://services.sentinel-hub.com"
    print("✅ Config loaded")
    print("   Client ID:", config.sh_client_id)
except Exception as e:
    print("❌ Config failed:", e)
    sys.exit()

try:
    colombo_bbox = BBox(bbox=[79.8, 6.85, 79.92, 6.97], crs=CRS.WGS84)
    resolution = 60
    size = bbox_to_dimensions(colombo_bbox, resolution=resolution)
    print(f"✅ BBox created, image size: {size}")
except Exception as e:
    print("❌ BBox failed:", e)
    sys.exit()

try:
    evalscript = """
    //VERSION=3
    function setup() {
        return { input: ["B04","B03","B02"], output: { bands: 3 } };
    }
    function evaluatePixel(sample) {
        return [3.5*sample.B04, 3.5*sample.B03, 3.5*sample.B02];
    }
    """

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=("2024-01-01", "2024-12-31"),
                mosaicking_order="leastCC"
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=colombo_bbox,
        size=size,
        config=config
    )
    print("✅ Request created, fetching data...")
except Exception as e:
    print("❌ Request creation failed:", e)
    traceback.print_exc()
    sys.exit()

try:
    data = request.get_data()
    print(f"✅ Data received, {len(data)} image(s)")
    image = data[0]
    print(f"   Image shape: {image.shape}")
except Exception as e:
    print("❌ Data fetch failed:", e)
    traceback.print_exc()
    sys.exit()

try:
    import matplotlib.pyplot as plt
    os.makedirs("data/raw", exist_ok=True)
    plt.imsave("data/raw/colombo.png", image)
    print("✅ Saved to data/raw/colombo.png")
except Exception as e:
    print("❌ Save failed:", e)
    traceback.print_exc()
