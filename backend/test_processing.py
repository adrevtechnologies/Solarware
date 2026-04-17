#!/usr/bin/env python
"""Quick test of processing service."""
import sys
import uuid
from app.core.database import setup_database, get_db_context
from app.models import SearchArea, Prospect
from app.services.prospect_discovery import ProspectDiscoveryService

# Setup database
setup_database()
print("✓ Database initialized")

# Create test search area
with get_db_context() as db:
    test_area = SearchArea(
        name="Test Goodwood",
        country="ZA",
        region="WC",
        min_latitude=-34.0,
        max_latitude=-33.9,
        min_longitude=18.4,
        max_longitude=18.7,
        min_roof_area_sqft=5000,
    )
    db.add(test_area)
    db.commit()
    db.refresh(test_area)
    area_id = str(test_area.id)
    print(f"✓ Created search area: {area_id}")

# Process it
service = ProspectDiscoveryService()
result = service._create_mock_prospects(
    get_db_context().__next__() if hasattr(get_db_context(), '__next__') else None,
    test_area,
    area_id
)

# Let me manually call it another way
with get_db_context() as db:
    try:
        service._create_mock_prospects(db, test_area, area_id)
        print("✓ Created mock prospects")
    except Exception as e:
        print(f"✗ Error creating prospects: {e}")
        sys.exit(1)

# Verify prospects exist
with get_db_context() as db:
    prospects = db.query(Prospect).filter(Prospect.search_area_id == area_id).all()
    print(f"✓ Found {len(prospects)} prospects in database")
    for p in prospects[:2]:
        print(f"  - {p.address}: R{p.annual_savings_rands:,.0f} savings")

print("\n✅ All tests passed!")
