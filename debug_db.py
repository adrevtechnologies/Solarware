#!/usr/bin/env python3
"""Debug database structure and content"""
import sys
sys.path.insert(0, 'd:/Solarware/Solarware/backend')

from app.core.database import get_engine
from sqlalchemy.orm import sessionmaker
from app.models import SearchArea, Prospect

engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

# Check SearchArea data
print("=== SEARCH AREAS ===")
areas = session.query(SearchArea).all()
for area in areas:
    print(f"\nName: {area.name}")
    print(f"Country: {area.country}")
    print(f"Region: {area.region}")
    print(f"Bounds: Lat({area.min_latitude}, {area.max_latitude}) Lon({area.min_longitude}, {area.max_longitude})")
    
    # Count prospects in this area
    pp_count = session.query(Prospect).filter(
        Prospect.search_area_id == area.id
    ).count()
    print(f"Prospects in this area: {pp_count}")

# Check some sample prospects
print("\n=== SAMPLE PROSPECTS ===")
samples = session.query(Prospect).limit(5).all()
for s in samples:
    print(f"\nID: {s.id}")
    print(f"  Address: {s.address}")
    print(f"  Location: ({s.latitude}, {s.longitude})")
    print(f"  Search Area ID: {s.search_area_id}")
    print(f"  Solar Confidence: {s.solar_confidence}")

session.close()
