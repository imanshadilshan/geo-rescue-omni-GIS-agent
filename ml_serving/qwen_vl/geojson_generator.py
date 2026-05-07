"""Convert AI vision output into valid GeoJSON FeatureCollections."""

import json
import geojson


def parse_zones_to_geojson(ai_output: str, metadata: dict = None) -> dict:
    """Convert AI text output into a valid GeoJSON FeatureCollection.
    
    Handles both well-formed JSON from the model and graceful fallbacks
    when the model returns malformed output.
    
    Args:
        ai_output: Raw text from Qwen-VL (expected to be JSON).
        metadata: Optional extra properties to attach to each feature.
        
    Returns:
        A GeoJSON FeatureCollection dict.
    """
    try:
        # Try to extract JSON from the AI output (model may wrap it in markdown)
        cleaned = ai_output.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        parsed = json.loads(cleaned)
        zones = parsed.get("affected_zones", [])
        severity = parsed.get("severity", "unknown")
    except (json.JSONDecodeError, AttributeError, IndexError):
        # Fallback: return empty collection if AI output isn't valid JSON
        return geojson.FeatureCollection([])

    features = []
    for i, zone_coords in enumerate(zones):
        if not zone_coords:
            continue

        # Ensure polygon is closed (GeoJSON requirement)
        if zone_coords[0] != zone_coords[-1]:
            zone_coords.append(zone_coords[0])

        polygon = geojson.Polygon([zone_coords])
        feature = geojson.Feature(
            geometry=polygon,
            properties={
                "zone_id": i + 1,
                "severity": severity,
                "source": "qwen-vl-analysis",
                **(metadata or {}),
            },
        )
        features.append(feature)

    return geojson.FeatureCollection(features)
