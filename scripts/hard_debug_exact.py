import json
import math
from pathlib import Path

from backend.app.api.search_real import (
    _distance_point_polygon_m,
    _meters_per_degree,
    _nearest_building_with_distance,
    _select_exact_target_building,
)
from backend.app.analysis.visualization import VizGenerator
from backend.app.services.nominatim_service import geocode_address, geocode_address_polygon, get_bounding_box
from backend.app.services.overpass_service import BuildingPolygon, calculate_polygon_area, query_commercial_buildings
from backend.app.services.satellite_service import get_satellite_image_url_for_polygon
from backend.app.services.solar_calculations import get_solar_stats


def geo_polygon_to_pixel(polygon, image_bbox, width, height):
    min_lat, max_lat, min_lon, max_lon = image_bbox
    lat_span = (max_lat - min_lat) or 1e-9
    lon_span = (max_lon - min_lon) or 1e-9
    px = []
    for lat, lon in polygon:
        x = (lon - min_lon) / lon_span * width
        y = (max_lat - lat) / lat_span * height
        px.append((x, y))
    return px


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def compute_overlay_rects(polygon_px, panel_count):
    xs = [p[0] for p in polygon_px]
    ys = [p[1] for p in polygon_px]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    panel_w = 22
    panel_h = 12
    spacing = 3

    rects = []
    y = min_y
    while y + panel_h <= max_y and len(rects) < panel_count:
        x = min_x
        while x + panel_w <= max_x and len(rects) < panel_count:
            corners = [
                (x, y),
                (x + panel_w, y),
                (x + panel_w, y + panel_h),
                (x, y + panel_h),
            ]
            if all(point_in_polygon(c, polygon_px) for c in corners):
                rects.append((x, y, x + panel_w, y + panel_h))
            x += panel_w + spacing
        y += panel_h + spacing
    return rects


def run_one(address, city, province, suburb, postcode, country):
    out = {
        "address_query": address,
        "status": "FAIL",
    }

    geo = geocode_address(address, city=city, province=province, suburb=suburb, postcode=postcode, country=country)
    if not geo:
        out["reason"] = "geocode_failed"
        return out

    center_lat, center_lon = geo.latitude, geo.longitude
    out["geocode_result"] = geo.address
    out["lat_lng"] = [center_lat, center_lon]

    radius_km = 0.3
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(center_lat, center_lon, radius_km)

    buildings = query_commercial_buildings(
        min_lat,
        max_lat,
        min_lon,
        max_lon,
        include_residential=True,
        include_all_buildings=True,
        min_polygon_area_sqm=20.0,
    )
    if not buildings:
        wider = max(0.8, radius_km * 2)
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(center_lat, center_lon, wider)
        buildings = query_commercial_buildings(
            min_lat,
            max_lat,
            min_lon,
            max_lon,
            include_residential=True,
            include_all_buildings=True,
            min_polygon_area_sqm=20.0,
        )

    parcel_polygon = geocode_address_polygon(
        address,
        city=city,
        province=province,
        suburb=suburb,
        postcode=postcode,
        country=country,
    )
    out["parcel_polygon_source"] = "nominatim" if parcel_polygon else "none"
    out["building_polygon_source"] = "overpass" if buildings else "none"

    selected = _select_exact_target_building(buildings, center_lat, center_lon, max_distance_m=80.0)
    selected_source = "overpass_exact"

    if not selected and parcel_polygon:
        roof_area_sqm = max(20.0, calculate_polygon_area(parcel_polygon))
        selected = BuildingPolygon(
            osm_id=f"nominatim-debug-{abs(hash(address)) % 1000000}",
            name=None,
            building_type="residential",
            latitude=sum(p[0] for p in parcel_polygon) / len(parcel_polygon),
            longitude=sum(p[1] for p in parcel_polygon) / len(parcel_polygon),
            roof_area_sqm=roof_area_sqm,
            nodes=parcel_polygon,
        )
        selected_source = "nominatim_polygon"

    if not selected:
        nearest, nearest_m = _nearest_building_with_distance(buildings, center_lat, center_lon)
        if nearest and nearest_m <= 250.0:
            selected = nearest
            selected_source = f"overpass_nearest_{nearest_m:.0f}m"

    if not selected:
        out["reason"] = "no_target_polygon"
        return out

    out["selected_polygon_source"] = selected_source
    out["selected_roof_polygon_points"] = len(selected.nodes)
    out["centroid_used"] = [selected.latitude, selected.longitude]

    lats = [n[0] for n in selected.nodes]
    lons = [n[1] for n in selected.nodes]
    pad_lat = (max(lats) - min(lats)) * 0.35 or 0.00012
    pad_lon = (max(lons) - min(lons)) * 0.35 or 0.00012
    image_bbox = (min(lats) - pad_lat, max(lats) + pad_lat, min(lons) - pad_lon, max(lons) + pad_lon)
    out["image_bbox_used"] = image_bbox

    solar = get_solar_stats(selected.roof_area_sqm, selected.building_type, province=province)
    panel_count = int(solar["estimated_panel_count"])

    before_url = get_satellite_image_url_for_polygon(selected.nodes)
    out["before_image"] = before_url

    mockup_path = VizGenerator._create_panel_overlay(
        satellite_image_path=before_url,
        panel_count=panel_count,
        roof_area_sqm=selected.roof_area_sqm,
        system_capacity_kw=float(solar["capacity_high_kw"]),
        roof_polygon=selected.nodes,
        image_bbox=image_bbox,
    )

    # Save deterministic debug artifact
    out_dir = Path("backend/output/debug")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"{address.replace(' ', '_').replace(',', '')}.png"
    out_path = out_dir / out_name
    mockup_path.save(out_path)
    out["after_image"] = str(out_path).replace("\\", "/")

    # Recompute overlay coordinates exactly as generator logic for log output
    width, height = mockup_path.size
    polygon_px = geo_polygon_to_pixel(selected.nodes, image_bbox, width, height)
    rects = compute_overlay_rects(polygon_px, panel_count)
    out["overlay_coordinates"] = rects[:20]

    # Validate no neighboring roofs touched: every panel rectangle corner must be in polygon
    no_spill = True
    for x0, y0, x1, y1 in rects:
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        if not all(point_in_polygon(c, polygon_px) for c in corners):
            no_spill = False
            break

    # Validate selected house proximity
    d = _distance_point_polygon_m(center_lat, center_lon, selected.nodes)
    out["distance_geocode_to_selected_m"] = round(d, 2)
    out["status"] = "PASS" if no_spill and d <= 250.0 and len(rects) > 0 else "FAIL"
    if out["status"] == "FAIL":
        out["reason"] = "overlay_spill_or_target_distance"
    return out


def main():
    addresses = [
        "98 Richmond Street",
        "97 Voortrekker Road",
        "40 McDonald Street",
        "12 Townsend Street",
        "20 Milton Road",
        "65 Vasco Boulevard",
    ]

    results = []
    for a in addresses:
        try:
            r = run_one(
                address=a,
                city="Cape Town",
                province="Western Cape",
                suburb="Goodwood",
                postcode="7460",
                country="South Africa",
            )
        except Exception as e:
            r = {"address_query": a, "status": "FAIL", "reason": str(e)}
        results.append(r)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
