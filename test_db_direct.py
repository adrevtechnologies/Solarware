#!/usr/bin/env python3
"""Direct database test"""
import sys
sys.path.insert(0, 'd:/Solarware/Solarware/backend')

from app.core.database import get_engine
from sqlalchemy.orm import sessionmaker
from app.models import Prospect

engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

# Direct query
query = session.query(Prospect)
results = query.order_by(Prospect.solar_confidence.desc()).limit(500).all()

print(f"Total prospects returned: {len(results)}")
print(f"First prospect: {results[0].address if results else 'None'}")

session.close()
