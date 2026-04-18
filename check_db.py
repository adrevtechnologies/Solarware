#!/usr/bin/env python3
"""
Check database state and trigger discovery if needed
"""
import sys
sys.path.insert(0, 'd:\\Solarware\\Solarware\\backend')

from app.core.database import get_engine
from sqlalchemy.orm import sessionmaker
from app.models import Prospect, SearchArea

# Get database connection
engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

# Count prospects
prospect_count = session.query(Prospect).count()
search_area_count = session.query(SearchArea).count()

print(f"Database state:")
print(f"  Prospects: {prospect_count}")
print(f"  Search Areas: {search_area_count}")

if prospect_count > 0:
    # Show sample prospects
    prospects = session.query(Prospect).limit(3).all()
    print(f"\nSample prospects:")
    for p in prospects:
        print(f"  - {p.address}: solar_confidence={p.solar_confidence}, business_type={p.business_type}")
else:
    print(f"\n⚠️ No prospects in database. Need to run discovery first.")
    
    # List search areas
    if search_area_count > 0:
        areas = session.query(SearchArea).limit(3).all()
        print(f"\nAvailable search areas:")
        for a in areas:
            print(f"  - {a.name} (ID: {a.id})")

session.close()
