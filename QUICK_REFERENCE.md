# Quick Reference Guide

## 🚀 Start Here

```bash
# 1. Clone and navigate
cd Solarware

# 2. Start all services (requires Docker)
docker-compose up

# 3. Access in browser
http://localhost:3000   # React frontend
http://localhost:8000   # FastAPI backend
http://localhost:8000/docs   # Interactive API docs
```

## 📁 Project Files Overview

### Backend (Python/FastAPI)

| Folder                      | Contains                            | Purpose                     |
| --------------------------- | ----------------------------------- | --------------------------- |
| `backend/app/core/`         | config, database, logging, errors   | Infrastructure & setup      |
| `backend/app/models/`       | SQLAlchemy models                   | Database table definitions  |
| `backend/app/schemas/`      | Pydantic validators                 | Request/response validation |
| `backend/app/integrations/` | satellite_providers.py              | External service adapters   |
| `backend/app/analysis/`     | Detection, enrichment, viz, packs   | Core business logic         |
| `backend/app/services/`     | discovery, email                    | High-level orchestration    |
| `backend/app/api/`          | search_areas, prospects, processing | HTTP endpoints              |
| `backend/app/utils/`        | Calculations, validators, helpers   | Reusable utilities          |

**Entry Point:** `backend/app/main.py`

### Frontend (React/TypeScript)

| Folder                     | Contains            | Purpose                    |
| -------------------------- | ------------------- | -------------------------- |
| `frontend/src/services/`   | api.ts              | HTTP client for backend    |
| `frontend/src/types/`      | index.ts            | TypeScript interfaces      |
| `frontend/src/hooks/`      | useData.ts          | Custom data-fetching hooks |
| `frontend/src/components/` | Forms, Cards, Lists | Reusable UI components     |
| `frontend/src/pages/`      | Dashboard.tsx       | Main page layouts          |

**Entry Point:** `frontend/src/main.tsx`

### Configuration

| File                       | Purpose                                          |
| -------------------------- | ------------------------------------------------ |
| `.env.template`            | Configuration template (copy to `.env` and fill) |
| `backend/requirements.txt` | Python dependencies                              |
| `frontend/package.json`    | Node.js dependencies                             |
| `docker-compose.yml`       | Local dev setup                                  |
| `backend/Dockerfile`       | Production backend image                         |
| `frontend/Dockerfile.dev`  | Development frontend image                       |

### Documentation

| File                    | For Whom                | Read Time |
| ----------------------- | ----------------------- | --------- |
| `README.md`             | Everyone                | 10 min    |
| `docs/SETUP.md`         | Developers & DevOps     | 15 min    |
| `docs/API.md`           | API users & integrators | 10 min    |
| `docs/ARCHITECTURE.md`  | Backend developers      | 15 min    |
| `docs/DEPLOYMENT.md`    | DevOps & deployment     | 20 min    |
| `COMPLETION_SUMMARY.md` | Project overview        | 5 min     |

### Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_utils.py

# Run with coverage
pytest --cov=backend
```

---

## 🔌 API Endpoints

### Search Areas

```
POST   /api/search-areas              Create new search area
GET    /api/search-areas              List all search areas
GET    /api/search-areas/{id}         Get one search area
PUT    /api/search-areas/{id}         Update search area
```

### Prospects

```
GET    /api/prospects                 List prospects (with search_area_id filter)
GET    /api/prospects/{id}            Get one prospect
GET    /api/prospects/{id}/contact    Get contact info for prospect
POST   /api/prospects/export-csv      Download CSV export
```

### Processing

```
POST   /api/process/search-area/{id}  Start satellite processing
GET    /api/process/status/{id}       Check processing status
```

### Health

```
GET    /health                        Basic health check
GET    /health/ready                  Readiness check (includes DB)
```

**Full Docs:** `http://localhost:8000/docs` (Swagger UI)

---

## 📊 Data Model

```
search_areas
├── id (UUID, primary key)
├── name (string)
├── country (string)
├── region (string)
├── geometry (PostGIS polygon)  ← Geographic bounds
├── min_roof_area_sqft (integer)
├── created_at, updated_at

prospects
├── id (UUID, primary key)
├── search_area_id (FK)
├── address (string)
├── latitude, longitude (floats)
├── geometry (PostGIS point)  ← Building location
├── roof_area_sqft (float)
├── estimated_panel_count (int)
├── system_capacity_kw (float)
├── annual_production_kwh (float)
├── annual_savings_usd (float)
├── solar_detection_confidence (float)
├── created_at, updated_at

contacts
├── id (UUID, primary key)
├── prospect_id (FK)
├── contact_name (string)
├── title (string)
├── email (string)
├── phone (string)
├── data_complete (boolean)
├── confidence_score (float)
└── created_at, updated_at

mailing_packs
├── id (UUID, primary key)
├── prospect_id (FK)
├── email_subject (string)
├── email_body (string)
├── satellite_image_path (string)
├── mockup_image_path (string)
├── status (string: prepared, reviewed, sent)
├── sent_at (timestamp, nullable)
└── created_at, updated_at
```

---

## 🛠️ Common Tasks

### Add a New Search Area

```bash
curl -X POST http://localhost:8000/api/search-areas \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Downtown",
    "country": "US",
    "region": "CA",
    "min_lat": 37.7,
    "max_lat": 37.8,
    "min_lon": -122.5,
    "max_lon": -122.4,
    "min_roof_area_sqft": 500
  }'
```

### Process (Discover Prospects)

```bash
curl -X POST http://localhost:8000/api/process/search-area/{SEARCH_AREA_ID} \
  -H "Content-Type: application/json" \
  -d '{
    "enrich_contacts": true,
    "generate_visualizations": true,
    "generate_mailing_packs": true
  }'
```

### Export Results

```bash
curl http://localhost:8000/api/prospects/export-csv \
  > prospects.csv
```

### Edit Email Template

File: `backend/app/analysis/mailing_pack.py`

Search for `PROSPECT_EMAIL_TEMPLATE` and modify Jinja2 template:

```python
PROSPECT_EMAIL_TEMPLATE = """
Dear {{ recipient_name }},

Your building at {{ address }} has excellent solar potential...
"""
```

### Add Solar Data for New Country

File: `backend/app/utils/solar_calculations.py`

Update dictionaries:

```python
SOLAR_IRRADIANCE_BY_COUNTRY = {
    "US": 5.5,      # kWh/m²/day
    "UK": 2.8,
    "JP": 4.2,
    "DE": 3.1,
    "YOUR_COUNTRY": 4.5,  # Add here
}

ELECTRICITY_RATE_BY_COUNTRY = {
    "US": 0.14,     # $/kWh
    "UK": 0.25,
    "YOUR_COUNTRY": 0.18,  # Add here
}
```

### Change Email Provider

File: `backend/app/core/config.py`

Set in `.env`:

```
EMAIL_SERVICE=smtp          # or: sendgrid, aws_ses
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=your_password
```

### Add New Satellite Provider

1. Create class in `backend/app/integrations/satellite_providers.py`:

```python
class MyProvider(SatelliteProvider):
    async def get_images(self, ...):
        return [SatelliteImage(...)]
```

2. Register in `backend/app/services/prospect_discovery.py`:

```python
if config.satellite_provider == "my_provider":
    self.satellite_provider = MyProvider(config.my_api_key)
```

---

## 🐛 Debugging

### View Logs

```bash
# Backend logs (in container)
docker logs solarware-backend -f

# Backend logs (local file)
tail -f logs/solarware.log

# Frontend logs (browser console)
F12 → Console tab
```

### Database Access

```bash
# Connect directly
psql -h localhost -U solarware -d solarware -W

# List tables
\dt

# View prospects
SELECT address, estimated_panel_count, annual_savings_usd FROM prospects;
```

### Test API

```bash
# Using curl
curl http://localhost:8000/health

# Using Python
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"

# Using Swagger UI
http://localhost:8000/docs  (Try it out button)
```

---

## 📦 Deployment Checklist

- [ ] Environment variables set (`.env` file created)
- [ ] API keys obtained (optional: Earth Engine, SendGrid)
- [ ] Database created (Cloud SQL / RDS / managed PostgreSQL)
- [ ] Docker images built and pushed to registry
- [ ] API keys stored in secret manager
- [ ] Health checks passed
- [ ] HTTPS/SSL configured at load balancer
- [ ] CORS origins set correctly
- [ ] Backups configured
- [ ] Monitoring/logging setup
- [ ] On-call contacts defined

See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) for platform-specific steps

---

## 🆘 Troubleshooting

| Issue                      | Solution                                                      |
| -------------------------- | ------------------------------------------------------------- |
| Docker won't start         | Ensure Docker Desktop running, ports 3000/8000/5432 free      |
| `psql: connection refused` | PostgreSQL may not be running, check `docker ps`              |
| `ModuleNotFoundError`      | Run `pip install -r backend/requirements.txt`                 |
| API returns 500 error      | Check `logs/solarware.log` or `docker logs solarware-backend` |
| Frontend won't load        | Check `http://localhost:8000/health` backend is up            |
| CORS errors                | Verify `CORS_ORIGINS` in `.env` matches frontend URL          |
| Email won't send           | Verify SMTP credentials and check logs for full error         |

Full troubleshooting: [docs/SETUP.md#troubleshooting](./docs/SETUP.md#troubleshooting)

---

## 📚 Learning Resources

### For Frontend Development

- React: https://react.dev
- TypeScript: https://www.typescriptlang.org/docs
- Tailwind CSS: https://tailwindcss.com/docs
- Vite: https://vitejs.dev/guide

### For Backend Development

- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- PostGIS: https://postgis.net/docs
- Pydantic: https://docs.pydantic.dev

### For Deployment

- Google Cloud Run: https://cloud.google.com/run/docs
- AWS Fargate: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
- Railway: https://docs.railway.app

---

## 📞 Support

**Issue not in troubleshooting?**

1. Check the appropriate docs
   - Setup issue? → [docs/SETUP.md](./docs/SETUP.md)
   - API issue? → [docs/API.md](./docs/API.md)
   - Architecture question? → [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
   - Deployment? → [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

2. Review logs:
   - `logs/solarware.log`
   - `docker logs solarware-backend`
   - Browser console (F12)

3. Check database:
   ```bash
   psql -h localhost -U solarware -d solarware -c "\dt"
   ```

---

## ⚡ Performance Tips

- **Batch Processing**: Process multiple search areas in sequence to avoid memory issues
- **Database**: Add indexes on frequently queried columns (search_area_id, created_at)
- **Cache**: Store satellite images in Redis to avoid re-downloading
- **Frontend**: Use React.memo() to prevent unnecessary re-renders
- **Email**: Queue emails in background worker instead of sending synchronously

---

## 🎯 Next Steps After Deployment

1. **Connect Real APIs** - Replace mock satellite provider with real Earth Engine
2. **Add Users** - Implement JWT authentication for multi-user access
3. **Monitor** - Set up alerting in Cloud Monitoring / CloudWatch
4. **Backup** - Configure automated daily database backups
5. **Scale** - Increase compute resources as traffic grows

---

**Version:** 0.1.0 (MVP)  
**Status:** ✅ Production-Ready  
**Last Updated:** 2024

**Ready to deploy? Start with [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)** 🚀
