"""
Overpass API Service - Real building detection from OpenStreetMap
FREE - NO API KEY REQUIRED
Fetches ONLY commercial buildings with tags
"""
import requests
import logging
from typing import List, Dict, Optional, Tuple
import math
from pydantic import BaseModel
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


class BuildingPolygon(BaseModel):
    """Real building from OpenStreetMap"""
    osm_id: str
    name: Optional[str] = None
    building_type: str  # warehouse, retail, office, school, etc.
    latitude: float
    longitude: float
    address: Optional[str] = None
    suburb: Optional[str] = None
    nodes: List[Tuple[float, float]]  # Polygon coordinates


def calculate_polygon_area(nodes: List[Tuple[float, float]]) -> float:
    """
    Calculate polygon area using Shoelace formula
    RETURNS: Area in square meters
    """
    if len(nodes) < 3:
        return 0
    
    # Close polygon if needed
    coords = nodes + [nodes[0]]
    
    # Shoelace formula (returns approximate area in degrees squared)
    area_deg = 0
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        area_deg += (lon1 * lat2 - lon2 * lat1)
    
    area_deg = abs(area_deg) / 2

    # Convert to meters at building location (rough approximation)
    avg_lat = sum(n[0] for n in nodes) / len(nodes)
    meters_per_degree_lat = 111000  # ≈ 111 km
    meters_per_degree_lon = 111000 * math.cos(math.radians(avg_lat))
    
    area_sqm = area_deg * meters_per_degree_lat * meters_per_degree_lon
    return area_sqm


def query_commercial_buildings(
    min_lat: float, max_lat: float, min_lon: float, max_lon: float
) -> List[BuildingPolygon]:
    """
    Query Overpass API for commercial buildings ONLY
    
    Fetches buildings tagged as:
    - warehouse, retail, factory, office, school, church, hospital, farm
    
    IGNORES: residential, house, shed, garage, hut
    
    RETURNS: List of real buildings with coordinates and footprints
    """
    bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    
    # Overpass QL query for commercial buildings
    query = f"""
    [bbox:{bbox_str}];
    (
        way["building"~"warehouse|retail|factory|office|school|church|hospital|farm_auxiliary|supermarket|industrial"];
        way["building:use"~"commercial|industrial|retail|office|warehouse"];
        relation["building"~"warehouse|retail|factory|office|school|church|hospital|farm_auxiliary|supermarket|industrial"];
    );
    out geom;
    """

    try:
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=30,
            headers={"User-Agent": "Solarware/1.0"}
        )
        response.raise_for_status()
        
        buildings = []
        
        # Parse XML response
        try:
            root = ET.fromstring(response.text)
        except:
            logger.warning(f"Failed to parse Overpass response for bbox {bbox_str}")
            return []

        # Extract ways (building polygons)
        for way in root.findall(".//way"):
            osm_id = way.get("id")
            
            # Get tags
            tags = {}
            for tag in way.findall("tag"):
                tags[tag.get("k")] = tag.get("v")

            building_type = tags.get("building", "unknown")
            shop_type = tags.get("shop")
            use_type = tags.get("building:use")

            # Determine commercial category
            if building_type in ["warehouse", "factory", "industrial"]:
                category = building_type
            elif building_type == "retail" or shop_type:
                category = "retail"
            elif building_type in ["office"]:
                category = "office"
            elif building_type == "school":
                category = "school"
            elif building_type == "church":
                category = "church"
            elif building_type == "hospital":
                category = "hospital"
            elif shop_type:
                category = "retail"
            else:
                category = building_type

            # REJECT residential, house, shed, garage, hut
            if category in ["residential", "house", "hut", "garage", "shed", ""]:
                continue

            # Extract polygon nodes
            nodes = []
            for nd in way.findall("nd"):
                ref = nd.get("ref")
                # Find coordinate in ways
                for node in root.findall(f".//node[@id='{ref}']"):
                    lat = float(node.get("lat"))
                    lon = float(node.get("lon"))
                    nodes.append((lat, lon))

            # Only include if we have polygon
            if len(nodes) < 3:
                logger.debug(f"Skipping building {osm_id} - insufficient nodes")
                continue

            # Calculate roof area
            roof_area_sqm = calculate_polygon_area(nodes)

            # Reject if roof too small
            if roof_area_sqm < 100:
                continue

            # Get center coordinates
            avg_lat = sum(n[0] for n in nodes) / len(nodes)
            avg_lon = sum(n[1] for n in nodes) / len(nodes)

            building = BuildingPolygon(
                osm_id=osm_id,
                name=tags.get("name"),
                building_type=category,
                latitude=avg_lat,
                longitude=avg_lon,
                address=tags.get("addr:street"),
                suburb=tags.get("addr:suburb"),
                nodes=nodes
            )

            buildings.append(building)
            logger.debug(f"Found building: {building.name or category} ({roof_area_sqm:.0f} sqm)")

        logger.info(f"Overpass query found {len(buildings)} commercial buildings")
        return buildings

    except requests.exceptions.ConnectTimeout:
        logger.error("Overpass API timeout - server may be rate limiting")
        return []
    except Exception as e:
        logger.error(f"Overpass API error: {e}")
        return []


def filter_nearby_buildings(
    buildings: List[BuildingPolygon],
    center_lat: float,
    center_lon: float,
    radius_km: float = 1.0
) -> List[BuildingPolygon]:
    """
    Filter buildings to only those within radius of center point
    """
    filtered = []
    
    for building in buildings:
        # Haversine distance
        lat_diff = (building.latitude - center_lat) * 111000  # meters
        lon_diff = (building.longitude - center_lon) * 111000 * math.cos(math.radians(center_lat))
        distance = math.sqrt(lat_diff**2 + lon_diff**2)
        
        if distance <= radius_km * 1000:
            filtered.append(building)
    
    return filtered
