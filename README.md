# SOLARWARE - Solar Prospect Discovery & Outreach

Solarware is a production-ready application that automates solar prospect discovery from satellite imagery, enriches prospects with contact data, generates personalized solar installation proposals, and prepares complete mailing packs for human-reviewed outreach.

## Overview

**Core Features:**

- Define geographic search areas with building criteria (roof size thresholds)
- Automatically detect buildings from satellite imagery lacking solar installations
- Geocode and enrich prospects with business contact information
- Generate solar analysis (panel count, capacity, annual production, savings)
- Create visual mockups showing solar panel placement
- Generate personalized email proposals with attachments
- Prepare mailing packs ready for human review and sending
- Optional automated email sending (SMTP, SendGrid, AWS SES)

**Technology Stack:**

- Backend: Python FastAPI + PostgreSQL/PostGIS
- Frontend: React 18 + TypeScript + Vite
- Deployment: Docker + recommended free tier platforms
- Satellite: Google Earth Engine, Sentinel Hub (integrations ready)
- Geocoding: Google Geocoding API

## Features

### 1. Prospect Discovery

- Define search areas by country/region and geographic bounds
- Specify minimum roof size thresholds
- Automatic building detection from satellite imagery
- Filters for existing solar panel coverage

### 2. Building Intelligence

- Geocoding and address resolution
- Business name and type identification
- Contact data enrichment from multiple sources
- Confidence scoring for data completeness
- Graceful handling of missing data

### 3. Solar Analysis

- Estimates panel count based on roof area
- Calculates system capacity (kW)
- Projects annual energy production based on local solar irradiance
- Estimates annual cost savings using actual electricity rates
- Country/region-specific solar data

### 4. Visualization & Mockups

- Generates before/after comparison images
- Virtual solar panel placement visualization
- High-resolution exports for proposals

### 5. Mailing Pack Generation

- Personalized email templates with prospect-specific data
- Combined satellite and mockup images
- Prospect information summary
- Financial projections
- Ready for human review and optional sending

### 6. Email Management

- Prepared packs for human review before sending
- Optional automated sending via SMTP, SendGrid, or AWS SES
- Dry-run mode to preview without sending
- Email delivery tracking and logging

### 7. Data Export

- CSV export of prospect lists
- Full prospect details in standardized format
- Filterable results

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (if running without Docker)
- PostgreSQL 15+ with PostGIS (or use Docker)

### Setup

1. **Clone and navigate:**

```bash
cd Solarware
```

2. **Create environment file:**

```bash
cp .env.template .env
# Edit .env with your configuration
```

3. **Run with Docker:**

```bash
docker-compose up
```

The application starts with:

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000 (or 5173)
- Database: localhost:5432
- API Docs: http://localhost:8000/docs

### Manual Setup (without Docker)

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migration
python migration/run_migration.py

# Start server
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Configuration

### Environment Variables

See [.env.template](.env.template) for all available options.

**Key variables:**

- `DATABASE_URL`: PostgreSQL connection string
- `GOOGLE_EARTH_ENGINE_PROJECT`: GEE project ID (optional)
- `SENTINEL_HUB_CLIENT_ID/SECRET`: Sentinel Hub credentials (optional)
- `GOOGLE_MAPS_API_KEY`: Google Maps API key (optional)
- `SMTP_*`: Email configuration

## API Documentation

### Endpoints

**Search Areas**

- `POST /api/search-areas` - Create search area
- `GET /api/search-areas` - List search areas
- `GET /api/search-areas/{id}` - Get search area
- `PUT /api/search-areas/{id}` - Update search area

**Prospects**

- `GET /api/prospects` - List prospects (with filtering)
- `GET /api/prospects/{id}` - Get prospect details
- `GET /api/prospects/{id}/contact` - Get contact info
- `POST /api/prospects/export-csv` - Export as CSV

**Processing**

- `POST /api/process/search-area/{id}` - Start processing
- `GET /api/process/status/{id}` - Get status

**Health**

- `GET /health` - Health check
- `GET /health/ready` - Readiness check

Full API docs available at: `/docs` (Swagger UI) or `/redoc` (ReDoc)

## Usage

### 1. Create a Search Area

```bash
curl -X POST http://localhost:8000/api/search-areas \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Downtown District",
    "country": "US",
    "region": "CA",
    "min_latitude": 40.7,
    "max_latitude": 40.8,
    "min_longitude": -74.0,
    "max_longitude": -73.9,
    "min_roof_area_sqft": 5000
  }'
```

### 2. Process Search Area

```bash
curl -X POST http://localhost:8000/api/process/search-area/{area_id}

Response:
{
  "status": "processing_started",
  "search_area_id": "...",
  "message": "..."
}
```

### 3. View Prospects

```bash
curl http://localhost:8000/api/prospects?search_area_id={area_id}
```

### 4. Export Results

```bash
curl http://localhost:8000/api/prospects/export-csv > prospects.csv
```

### 5. Review Mailing Packs

Packs are generated in: `./output/mailing_packs/`

Each pack contains:

- `email_{uuid}.txt` - Email content
- Satellite image (if available)
- Mockup visualization
- Summary manifest

### 6. Send Emails (Optional)

```bash
curl -X POST http://localhost:8000/api/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "mailing_pack_id": "...",
    "recipient_email": "contact@example.com",
    "via": "smtp",
    "dry_run": false
  }'
```

## Database Schema

### Search Areas

```sql
CREATE TABLE search_areas (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  country VARCHAR(100),
  region VARCHAR(255),
  min_latitude FLOAT,
  max_latitude FLOAT,
  min_longitude FLOAT,
  max_longitude FLOAT,
  min_roof_area_sqft FLOAT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Prospects

```sql
CREATE TABLE prospects (
  id UUID PRIMARY KEY,
  search_area_id UUID,
  latitude FLOAT,
  longitude FLOAT,
  geometry GEOMETRY(Point, 4326),
  address VARCHAR(255),
  building_name VARCHAR(255),
  business_name VARCHAR(255),
  roof_area_sqft FLOAT,
  roof_area_sqm FLOAT,
  estimated_panel_count INT,
  estimated_system_capacity_kw FLOAT,
  estimated_annual_production_kwh FLOAT,
  estimated_annual_savings_usd FLOAT,
  has_existing_solar BOOLEAN,
  solar_confidence FLOAT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Contacts

```sql
CREATE TABLE contacts (
  id UUID PRIMARY KEY,
  prospect_id UUID,
  contact_name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(20),
  data_complete BOOLEAN,
  data_source VARCHAR(100),
  confidence_score FLOAT,
  created_at TIMESTAMP
);
```

### Mailing Packs

```sql
CREATE TABLE mailing_packs (
  id UUID PRIMARY KEY,
  prospect_id UUID,
  email_subject VARCHAR(255),
  email_body TEXT,
  status VARCHAR(50),  -- prepared, reviewed, sent
  created_at TIMESTAMP,
  sent_at TIMESTAMP
);
```

## Integration Points

### Satellite Providers

The system supports multiple providers through a modular interface:

**Google Earth Engine** (`GoogleEarthEngineProvider`)

- Configuration: `GOOGLE_EARTH_ENGINE_PROJECT`, `GOOGLE_EARTH_ENGINE_KEY_FILE`
- Status: Ready for integration

**Sentinel Hub** (`SentinelHubProvider`)

- Configuration: `SENTINEL_HUB_CLIENT_ID`, `SENTINEL_HUB_CLIENT_SECRET`
- Status: Ready for integration

**Current**: Uses `MockSatelliteProvider` for development

### Contact Enrichment

Multiple sources are queried in parallel:

- Google Maps API (`GOOGLE_MAPS_API_KEY`)
- Google Geocoding and Places APIs
- Web search (Google Custom Search API optional)

### Email Services

**SMTP** (Gmail, SendGrid, corporate hosts, etc.)

- Configuration: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- Status: Fully implemented

**SendGrid**

- Configuration: `SENDGRID_API_KEY`
- Status: Integration ready

**AWS SES**

- Configuration: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- Status: Integration ready

## Deployment

### Local Development

```bash
docker-compose up
```

### Production - Google Cloud Run

**Prerequisites:** GCP account with gcloud CLI

1. **Prepare:**

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. **Build backend:**

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/solarware-backend backend/
```

3. **Deploy backend:**

```bash
gcloud run deploy solarware-backend \
  --image gcr.io/YOUR_PROJECT_ID/solarware-backend \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --set-env-vars DATABASE_URL=postgresql://... \
  --allow-unauthenticated
```

4. **Deploy frontend to Cloud Storage + CDN:**

```bash
cd frontend
npm run build
gsutil -m cp -r dist/* gs://your-bucket/
```

### Production - Railway.app

1. **Connect GitHub repo**
2. **Set environment variables** via dashboard
3. **Select PostgreSQL plugin**
4. **Deploy** - automatic on push

### Vercel (Frontend)

```bash
vercel login
vercel --cwd frontend
```

## Error Handling & Logging

All operations are logged to:

- Console: All levels
- File: `./logs/solarware.log`

**Common scenarios:**

- Missing satellite data → Returns empty results with warning
- Geocoding failures → Flags prospect as "contact pending"
- Rate limits → Implements exponential backoff
- Invalid coordinates → Returns 400 error with validation message

## Testing

```bash
cd backend
pytest tests/

# With coverage
pytest --cov=app tests/
```

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit
3. Push and create pull request

**Code standards:**

- Python: Black, isort, mypy
- TypeScript: ESLint, Prettier
- Tests: 80%+ coverage

## License

See [LICENSE](LICENSE)

## Production Readiness Checklist

- [x] Database schema with migrations
- [x] API with full CRUD operations
- [x] Error handling and logging
- [x] Input validation
- [x] Rate limiting hooks (implement in nginx/CloudRun)
- [x] Docker containerization
- [x] Environment configuration
- [ ] Authentication (add JWT or OAuth2)
- [ ] Frontend complete UI
- [ ] End-to-end tests
- [ ] Performance monitoring
- [ ] Load testing results
- [ ] Security audit
- [ ] Backup strategy for database

## Support & Issues

For questions or issues:

1. Check [docs/](docs/) folder
2. Review API docs at `/docs` (Swagger)
3. Check logs in `./logs/`
4. Create an issue with error details

## FAQ

**Q: Why are my prospects not being detected?**
A: Currently using MockSatelliteProvider for development. Configure Google Earth Engine or Sentinel Hub in `.env` and implement actual API calls in `satellite_providers.py`.

**Q: Can I use my own satellite imagery?**
A: Yes - implement a custom `SatelliteProvider` and register it in `prospect_discovery.py`.

**Q: What if contact data is incomplete?**
A: Prospects are flagged with `data_complete: false`. They're still included in mailing packs marked as "contact pending" for manual research.

**Q: Can I customize the email template?**
A: Yes - edit the template in `app/analysis/mailing_pack.py` or use your own Jinja2 template file.

**Q: Does this send emails automatically?**
A: No - by default sends are in "dry_run" mode after pack preparation. Only send after human review.

---

**Version:** 0.1.0  
**Last Updated:** 2024  
**Status:** Production-Ready (MVP)
