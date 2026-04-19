"""
Overpass API Service - Real building detection from OpenStreetMap
FREE - NO API KEY REQUIRED
Fetches ONLY commercial buildings with tags
"""
import requests
import logging
from typing import List, Dict, Optional, Tuple
import math
import time
from pydantic import BaseModel
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]
DEFAULT_HEADERS = {"User-Agent": "Solarware/1.0"}


def _query_overpass_xml(query: str) -> Optional[str]:
    """Query Overpass with endpoint failover and retry/backoff for 429/5xx."""
    max_attempts_per_endpoint = 2

    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(1, max_attempts_per_endpoint + 1):
            try:
                response = requests.post(
                    endpoint,
                    data={"data": query},
                    timeout=45,
                    headers=DEFAULT_HEADERS,
                )

                # Retry on rate-limit and transient server errors.
                if response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(
                        "Overpass transient error %s on %s (attempt %s/%s)",
                        response.status_code,
                        endpoint,
                        attempt,
                        max_attempts_per_endpoint,
                    )
                    if attempt < max_attempts_per_endpoint:
                        time.sleep(1.5 * attempt)
                    continue

                response.raise_for_status()
                return response.text

            except requests.exceptions.RequestException as e:
                logger.warning(
                    "Overpass request failed on %s (attempt %s/%s): %s",
                    endpoint,
                    attempt,
                    max_attempts_per_endpoint,
                    e,
                )
                if attempt < max_attempts_per_endpoint:
                    time.sleep(1.5 * attempt)

    logger.error("All Overpass endpoints failed")
    return None


class BuildingPolygon(BaseModel):
    """Real building from OpenStreetMap"""
    osm_id: str
    name: Optional[str] = None
    building_type: str  # warehouse, retail, office, school, etc.
    latitude: float
    longitude: float
    address: Optional[str] = None
    suburb: Optional[str] = None
    house_number: Optional[str] = None
    street: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    roof_area_sqm: float
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
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    include_residential: bool = False,
    include_all_buildings: bool = False,
    min_polygon_area_sqm: float = 100.0,
) -> List[BuildingPolygon]:
    """
    Query Overpass API for buildings, defaulting to commercial-only.
    
    Fetches buildings tagged as:
    - warehouse, retail, factory, office, school, church, hospital, farm
    
    By default ignores: residential, house, shed, garage, hut
    
    RETURNS: List of real buildings with coordinates and footprints
    """
    bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    
    if include_all_buildings:
        query = f"""
        [bbox:{bbox_str}];
        (
            way["building"];
            relation["building"];
        );
        out geom;
        """
    else:
        residential_clause = ""
        if include_residential:
            residential_clause = """
            way[\"building\"~\"house|residential|detached|semidetached_house|terrace|apartments\"];
            relation[\"building\"~\"house|residential|detached|semidetached_house|terrace|apartments\"];
            way[\"addr:housenumber\"][\"addr:street\"];
            relation[\"addr:housenumber\"][\"addr:street\"];
            """

        # Overpass QL query for commercial buildings (and optional residential)
        query = f"""
        [bbox:{bbox_str}];
        (
            way["building"~"warehouse|retail|factory|office|school|church|hospital|farm|farm_auxiliary|barn|supermarket|industrial|commercial|mall"];
            way["building:use"~"commercial|industrial|retail|office|warehouse|mall|business_park"];
            way["office"];
            relation["building"~"warehouse|retail|factory|office|school|church|hospital|farm|farm_auxiliary|barn|supermarket|industrial|commercial|mall"];
            {residential_clause}
        );
        out geom;
        """

    try:
        xml_text = _query_overpass_xml(query)
        if not xml_text:
            return []

        buildings = []
        seen_ids = set()
        
        # Parse XML response
        try:
            root = ET.fromstring(xml_text)
        except Exception:
            logger.warning(f"Failed to parse Overpass response for bbox {bbox_str}")
            return []

        # Extract ways (building polygons)
        for way in root.findall(".//way"):
            osm_id = way.get("id")
            if not osm_id or osm_id in seen_ids:
                continue
            seen_ids.add(osm_id)
            
            # Get tags
            tags = {}
            for tag in way.findall("tag"):
                tags[tag.get("k")] = tag.get("v")

            building_type = tags.get("building", "unknown")
            shop_type = tags.get("shop")
            use_type = tags.get("building:use")
            office_tag = tags.get("office")

            # Determine commercial category
            if building_type in ["warehouse", "factory", "industrial"]:
                category = building_type
            elif building_type == "retail" or shop_type:
                category = "retail"
            elif building_type in ["office"] or office_tag:
                category = "office"
            elif building_type in ["commercial", "mall"]:
                category = "business_park"
            elif use_type == "business_park":
                category = "business_park"
            elif building_type == "school":
                category = "school"
            elif building_type == "church":
                category = "church"
            elif building_type == "hospital":
                category = "hospital"
            elif building_type in ["farm", "farm_auxiliary", "barn"]:
                category = "farm_building"
            elif shop_type:
                category = "retail"
            else:
                category = building_type

            if building_type in ["house", "residential", "detached", "semidetached_house", "terrace", "apartments"]:
                category = "residential"

            # Address-tagged `building=yes` is commonly used for mapped homes in OSM.
            if (
                include_residential
                and building_type == "yes"
                and (tags.get("addr:housenumber") or tags.get("addr:street"))
            ):
                category = "residential"

            excluded_categories = {
                "hut",
                "cabin",
                "shack",
                "garage",
                "garages",
                "shed",
                "service",
                "toilets",
                "yes",
                "no",
                "",
            }

            # For commercial mode, reject residential and utility structures.
            if not include_residential and not include_all_buildings:
                if category in {"residential", "house", "detached", "semidetached_house", "terrace", "apartments"}:
                    continue
                if category in excluded_categories:
                    continue

            # Residential mode still skips utility/non-target structures.
            if include_residential and category in excluded_categories:
                continue

            # Extract polygon nodes
            nodes = []
            for nd in way.findall("nd"):
                # Prefer geom attributes returned directly on nd by `out geom`
                nd_lat = nd.get("lat")
                nd_lon = nd.get("lon")
                if nd_lat is not None and nd_lon is not None:
                    nodes.append((float(nd_lat), float(nd_lon)))
                    continue

                # Fallback to referenced node lookup when geometry attrs are absent.
                ref = nd.get("ref")
                if not ref:
                    continue
                node = root.find(f".//node[@id='{ref}']")
                if node is None:
                    continue
                lat = node.get("lat")
                lon = node.get("lon")
                if lat is not None and lon is not None:
                    nodes.append((float(lat), float(lon)))

            # Only include if we have polygon
            if len(nodes) < 3:
                logger.debug(f"Skipping building {osm_id} - insufficient nodes")
                continue

            # Calculate roof area
            roof_area_sqm = calculate_polygon_area(nodes)

            # Reject tiny utility footprints unless caller explicitly lowers threshold.
            if roof_area_sqm < min_polygon_area_sqm:
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
                house_number=tags.get("addr:housenumber"),
                street=tags.get("addr:street"),
                website=tags.get("website") or tags.get("contact:website"),
                phone=tags.get("phone") or tags.get("contact:phone"),
                email=tags.get("email") or tags.get("contact:email"),
                contact_person=tags.get("contact:name"),
                roof_area_sqm=roof_area_sqm,
                nodes=nodes
            )

            buildings.append(building)
            logger.debug(f"Found building: {building.name or category} ({roof_area_sqm:.0f} sqm)")

        if include_all_buildings:
            mode_label = "all mapped buildings"
        else:
            mode_label = "commercial + residential" if include_residential else "commercial"
        logger.info(f"Overpass query found {len(buildings)} {mode_label} buildings")
        return buildings

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
