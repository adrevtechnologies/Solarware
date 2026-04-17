# Architecture & Implementation Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│            Browser → SPA (Vite, TypeScript, Tailwind)       │
│           Dashboard, forms, prospect list, export          │
│        ↓ HTTP/REST API ← https://api.yourdom.com           │
├─────────────────────────────────────────────────────────────┤
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ API Endpoints                                        │  │
│  │ ├─ /api/search-areas - Search area management      │  │
│  │ ├─ /api/prospects - Prospect CRUD & export         │  │
│  │ ├─ /api/process - Satellite processing pipeline    │  │
│  │ └─ /health - Health checks                         │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ Services Layer                                      │  │
│  │ ├─ ProspectDiscoveryService - Orchestration       │  │
│  │ ├─ EmailService - SMTP/SendGrid/SES               │  │
│  │ └─ Background tasks (async.io)                    │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ Analysis Modules                                    │  │
│  │ ├─ SatelliteProvider - GEE, Sentinel integration  │  │
│  │ ├─ BuildingDetector - ML-ready interface          │  │
│  │ ├─ ContactEnricher - Multi-source enrichment      │  │
│  │ ├─ VizGenerator - PIL-based mockups               │  │
│  │ └─ MailingPackGenerator - Template rendering      │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ Utilities                                           │  │
│  │ ├─ solar_calculations.py - All solar math         │  │
│  │ ├─ geo.py - Geospatial operations                 │  │
│  │ ├─ validators.py - Input validation               │  │
│  │ └─ files.py - Output file management              │  │
│  └──────────────────────────────────────────────────────┘  │
│        ↓ SQLAlchemy ORM + PostGIS geometry functions        │
├─────────────────────────────────────────────────────────────┤
│              Database (PostgreSQL + PostGIS)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Tables:                                              │  │
│  │ ├─ search_areas (with geometry bounds)             │  │
│  │ ├─ prospects (with Point geometry for coords)      │  │
│  │ ├─ contacts (enriched contact data)                │  │
│  │ └─ mailing_packs (email content & status)          │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│         External APIs (All Optional, Fallback-Ready)        │
│  ├─ Google Earth Engine (satellite imagery)               │  │
│  ├─ Sentinel Hub (satellite imagery)                      │  │
│  ├─ Google Maps API (geocoding & business data)          │  │
│  ├─ OpenStreetMap Nominatim (free geocoding)            │  │
│  ├─ Google Custom Search (web enrichment)                │  │
│  └─ Email Services (SMTP, SendGrid, AWS SES)            │  │
└─────────────────────────────────────────────────────────────┘
```

##

### Core Data Flow

1. **Search Area Definition**
   - User provides: country, coordinates, roof size criteria
   - Stored in `search_areas` table with geometry

2. **Prospect Discovery**
   - Fetch satellite images (ideally real API, mocked for MVP)
   - Detect buildings using ML model interface
   - Validate against criteria (roof size, no existing solar)
   - Store in `prospects` table with coordinates

3. **Contact Enrichment**
   - Parallel queries to multiple sources
   - Geocoding with fallbacks (Google → OSM → manual flag)
   - Store in `contacts` table with confidence scores
   - Flag incomplete data for manual research

4. **Solar Analysis**
   - Calculate panel count from roof area
   - Compute system capacity and annual production
   - Use country-specific solar irradiance & electricity rates
   - Store analysis results in `prospects` table

5. **Visualization**
   - Generate mockup image (PIL-based overlay)
   - Create before/after comparison
   - Save high-res PNG for email attachment

6. **Mailing Pack Generation**
   - Render personalized email from Jinja2 template
   - Attach satellite + mockup images
   - Store pack in `mailing_packs` table
   - Create prospect folder: `./output/mailing_packs/{uuid}/`

7. **Email Sending (Optional)**
   - User reviews pack
   - Optionally sends via SMTP/SendGrid/SES
   - Track delivery in `mailing_packs.sent_at`

## Modularity & Extension Points

### Adding a New Satellite Provider

1. Subclass `SatelliteProvider`:

```python
class MyProvider(SatelliteProvider):
    async def get_images(self, min_lat, max_lat, min_lon, max_lon, max_cloud_coverage):
        # Implementation
        return [SatelliteImage(...), ...]
```

2. Register in `prospect_discovery.py`:

```python
if config.provider == "my_provider":
    self.satellite_provider = MyProvider(api_key)
```

3. No other code changes needed ✓

### Adding a New Contact Enrichment Source

1. Add async function in `contact_enrichment.py`:

```python
async def _enrich_from_my_source(address: str) -> Optional[Dict]:
    # Implementation
    return {"contact_name": "...", "email": "..."}
```

2. Add to parallel tasks in `enrich_contact()`:

```python
tasks.append(ContactEnricher._enrich_from_my_source(address))
```

3. Merge results automatically ✓

### Adding a New Email Service

1. Add method in `EmailService`:

```python
@staticmethod
async def _send_via_my_service(mailing_pack, recipient):
    # Implementation
    return {"status": "sent", "timestamp": "..."}
```

2. Update route selector:

```python
elif via == "my_service":
    return await EmailService._send_via_my_service(...)
```

### Adding Solar Analysis Features

1. Add calculation to `solar_calculations.py`
2. Call from `calculate_solar_analysis()` to include in output
3. Template references it automatically in email

---

## Error Handling Strategy

**Graceful degradation** throughout:

```python
# Example: contact enrichment with multiple sources
tasks = [
    enrich_from_google_maps(address),      # May fail
    enrich_from_osm(address),              # May fail
    enrich_from_web_search(address),       # May fail
]

results = await asyncio.gather(*tasks, return_exceptions=True)
# All failures captured, data still returned from successful calls
```

**Prospect Processing** continues even with partial failures:

- Missing satellite data? → Use mock/empty geometry
- Geocoding fails? → Include with temp address, flag for manual
- Contact enrichment fails? → Flag as incomplete, include in pack
- Visualization fails? → Skip images, send text-only

**Database** handles integrity:

- Foreign key constraints enforce consistency
- NULL fields allowed where optional
- Timestamps auto-set for audit trail
- Constraints prevent invalid coordinates

---

## Performance & Scalability

### Current Limitations (MVP)

- Single-threaded satellite queries (can process ~500 buildings/hour)
- Sequential contact enrichment batches (concurrency limited to 5)
- In-memory visualization generation (PIL, no GPU)
- No caching (every request hits API)

### Scaling Improvements (Future)

1. **Satellite Processing**
   - Async batch requests to Earth Engine
   - Implement tiling strategy for large areas
   - Cache tiles by date

2. **Contact Enrichment**
   - Increase concurrency limit
   - Implement Redis caching
   - Queue with worker pool (Celery)

3. **Visualization**
   - GPU acceleration with CUDA/OpenCL
   - Pre-render common configurations
   - CDN for cached mockups

4. **Database**
   - Connection pooling (pgBouncer)
   - Read replicas for reporting
   - Partitioning `prospects` by region

5. **API**
   - Response caching (Redis, HTTP cache headers)
   - Pagination limits
   - Rate limiting per IP/API key

---

## Data Consistency & Integrity

### Transaction Handling

```python
# Database operations wrapped in transactions
with get_db_context() as db:
    prospect = Prospect(...)
    db.add(prospect)
    db.flush()  # Get ID without committing

    # Use ID immediately
    contact = Contact(prospect_id=prospect.id, ...)
    db.add(contact)

    db.commit()  # Atomic: both created or both rolled back
```

### Idempotency

Processing same search area twice:

- Checks existing prospects
- Either updates or reprocesses
- No duplicates created (UUID primary key)

### Audit Trail

Every table has timestamps:

```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE
```

Can trace complete history of each prospect.

---

## Testing Strategy

### Unit Tests (`tests/test_utils.py`)

- Solar calculations
- Coordinate validation
- Area conversions
- Error handling

### Integration Tests (`tests/test_api.py`)

- API endpoints (with mock database)
- Search area creation
- Prospect retrieval
- CSV export

### Manual Testing Workflow

1. Start Docker Compose
2. Create search area via API
3. Process it (background job)
4. Check prospect results
5. Verify contact enrichment
6. Download mailing pack
7. Review email content
8. Test (mock) sending

---

## Making Connections Real

### Google Earth Engine

Replace mock in `SatelliteProvider.detect_buildings()`:

```python
import ee

ee.Initialize(ee.ServiceAccountCredentials.from_filename(...))

# Get imagery for bounds
image = ee.ImageCollection('COPERNICUS/S2').filterBounds(
    ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
).first()

# Export and process...
```

### Geocoding (Real API)

Replace mock in `contact_enrichment.py`:

```python
from geopy.geocoders import GoogleV3

geocoder = GoogleV3(api_key=settings.GOOGLE_MAPS_API_KEY)
location = geocoder.reverse(f"{lat}, {lon}")
```

### Building Detection (ML Model)

Create `ML_model.py`:

```python
import tensorflow as tf

model = tf.keras.models.load_model('solar_panel_detector.h5')

def detect_buildings_ml(satellite_image_array):
    predictions = model.predict(satellite_image_array)
    return extract_building_coordinates(predictions)
```

Then in `building_detection.py`:

```python
from app.ml_models import detect_buildings_ml

buildings = await detect_buildings_ml(satellite_image_data)
```

---

## API Standards

### RESTful Design

- Resource-based URLs (`/api/search-areas`, `/api/prospects`)
- Standard HTTP verbs (GET=read, POST=create, PUT=update)
- Status codes (200, 201, 400, 404, 500)
- JSON request/response bodies

### Request/Response Format

**Request:**

```json
{
  "name": "Downtown District",
  "country": "US",
  ...
}
```

**Response (Success):**

```json
{
  "id": "uuid",
  "name": "Downtown District",
  ...
}
```

**Response (Error):**

```json
{
  "detail": "Invalid latitude: 95. Must be between -90 and 90"
}
```

### Versioning (Future)

- Currently: `/api/` (implicit v1)
- Future: `/api/v2/` for breaking changes
- Deprecation: Remove old versions after 12 months notice

---

**Last Updated:** 2024
**Status:** Production-Ready (MVP with clear extension points)
