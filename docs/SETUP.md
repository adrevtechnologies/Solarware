# Solarware - Setup & Deployment Guide

## Local Development Setup

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.11+, Node.js 18+, PostgreSQL 15+

### Option 1: Quick Start with Docker (Recommended)

```bash
# Clone/navigate to repository
cd Solarware

# Copy and configure environment
cp .env.template .env
# Edit .env if needed (defaults work for local development)

# Start all services
docker-compose up

# Services available at:
# - Frontend: http://localhost:3000 or http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Database: localhost:5432 (solarware/solarware_dev_password)
```

### Option 2: Manual Setup (Local Development)

#### Backend

1. **Create Python environment:**

```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Set up environment:**

```bash
cp ../.env.template ../.env
# Edit ../.env if needed
```

4. **Initialize database:**

```bash
# Ensure PostgreSQL is running locally
# Update DATABASE_URL in .env if not using defaults

# Create PostGIS extension (if not automatic):
psql -U solarware -d solarware -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

5. **Run backend:**

```bash
uvicorn app.main:app --reload
# Runs on http://localhost:8000
```

#### Frontend

1. **Install dependencies:**

```bash
cd frontend
npm install
```

2. **Configure API URL:**

```bash
# .env in frontend/ (optional, defaults to localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env
```

3. **Run development server:**

```bash
npm run dev
# Runs on http://localhost:5173
```

## Production Deployment

### Option 1: Google Cloud Run (Recommended for MVP)

**Advantages:** Auto-scaling, pay-per-use, integrated monitoring, free tier available

#### Prerequisites

- GCP account
- gcloud CLI installed
- Cloud Build & Cloud Run enabled

#### Deploy Backend

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/solarware-backend backend/

# Create Cloud SQL PostgreSQL instance (if not existing)
gcloud sql instances create solarware-db \
  --database-version POSTGRES_15 \
  --region us-central1 \
  --tier db-f1-micro

# Create database and enable PostGIS
gcloud sql databases create solarware --instance solarware-db
gcloud sql databases create template_postgis --instance solarware-db

# Create service account and add Cloud SQL Client role
gcloud iam service-accounts create solarware-sa
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member serviceAccount:solarware-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role roles/cloudsql.client

# Deploy to Cloud Run
gcloud run deploy solarware-backend \
  --image gcr.io/YOUR_PROJECT_ID/solarware-backend \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --timeout 3600 \
  --set-env-vars DATABASE_URL=postgresql://USER:PASSWORD@CLOUD_SQL_IP/solarware \
  --service-account solarware-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated

# Get service URL
gcloud run services describe solarware-backend --platform managed --region us-central1
```

#### Deploy Frontend

```bash
# Build
cd frontend
npm run build

# Create Cloud Storage bucket
gsutil mb gs://solarware-frontend

# Upload built files
gsutil -m cp -r dist/* gs://solarware-frontend/

# Configure Cloud CDN and CORS (optional but recommended)
gcloud compute backend-buckets create solarware-frontend-bucket \
  --gcs-url-mask='gs://solarware-frontend/*'
```

### Option 2: Railway.app (Easiest)

**Advantages:** GitHub integration, automatic deploys, simple dashboard

```bash
# Prerequisites
# - GitHub account
# - GitHub repo connected to Railway

# 1. Create Railway account at railway.app
# 2. Create new project
# 3. Connect GitHub repository
# 4. Add PostgreSQL plugin from dashboard
# 5. Set environment variables:
#    DATABASE_URL (auto-set by PostgreSQL plugin)
#    GOOGLE_EARTH_ENGINE_PROJECT (optional)
#    SENTINEL_HUB_CLIENT_ID (optional)
#    etc...
# 6. Deploy backend service
# 7. Attach PostgreSQL
# 8. Deploy frontend service
# 9. Railway auto-assigns URLs and manages HTTPS
```

### Option 3: AWS (Advanced)

**Alternatives:**

- **Backend:** AWS ECS Fargate + RDS PostgreSQL
- **Frontend:** Amazon S3 + CloudFront
- **Emails:** AWS SES (included configuration)

See AWS deployment guide in `/docs/aws-deployment.md`

### Option 4: Azure (Alternative)

See comprehensive Azure setup in `/docs/azure-deployment.md`

## Database Setup

### Local PostgreSQL (Development)

```bash
# Using Docker:
docker run --name solarware-db \
  -e POSTGRES_USER=solarware \
  -e POSTGRES_PASSWORD=solarware_dev_password \
  -e POSTGRES_DB=solarware \
  -p 5432:5432 \
  postgis/postgis:15-3.3

# Or using existing PostgreSQL:
createdb -U postgres solarware
psql -U postgres -d solarware -c "CREATE EXTENSION postgis;"
```

### Production PostgreSQL (Cloud)

**Google Cloud SQL** (recommended):

```bash
# See deployment section above for full setup
# Automatically includes PostGIS support
```

**AWS RDS:**

```bash
# Enable PostGIS extension during RDS creation
# Connect via RDS endpoint in DATABASE_URL
```

## Environment Configuration

### Development

Copy `.env.template` to `.env` - defaults work for local Docker setup:

```env
DATABASE_URL=postgresql://solarware:solarware_dev_password@postgres:5432/solarware
ENVIRONMENT=development
DEBUG=true
```

### Production

**Never commit real API keys.** Use platform secrets management:

```env
# Database
DATABASE_URL=postgresql://user:password@cloud-db-host/solarware

# Satellite (optional - configure which providers you'll use)
GOOGLE_EARTH_ENGINE_PROJECT=your-project-id
SENTINEL_HUB_CLIENT_ID=your-client-id
SENTINEL_HUB_CLIENT_SECRET=your-secret

# Contact enrichment (optional)
GOOGLE_MAPS_API_KEY=your-key
GOOGLE_SEARCH_API_KEY=your-key
GOOGLE_SEARCH_ENGINE_ID=your-id

# Email (at least one should be configured)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourcompany.com

# Or use SendGrid/AWS SES
SENDGRID_API_KEY=your-key
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1

# App configuration
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://yourdomain.com
```

## API Keys & Third-Party Setup

### Google Earth Engine (Satellite Imagery)

1. Go to: https://developers.google.com/earth-engine
2. Create project and request access
3. Generate service account key JSON
4. Set `GOOGLE_EARTH_ENGINE_PROJECT` and `GOOGLE_EARTH_ENGINE_KEY_FILE`

### Sentinel Hub (Satellite Imagery)

1. Go to: https://www.sentinel-hub.com/
2. Create account and get free tier
3. Generate client credentials
4. Set `SENTINEL_HUB_CLIENT_ID` and `SENTINEL_HUB_CLIENT_SECRET`

### Google Maps API (Geocoding)

1. Go to: https://console.cloud.google.com/
2. Create project
3. Enable Maps Platform and Places API
4. Create API key with appropriate restrictions
5. Set `GOOGLE_MAPS_API_KEY`

### SendGrid (Email Sending)

1. Go to: https://sendgrid.com/
2. Create free account (12,000 emails/month)
3. Generate API key
4. Set `SENDGRID_API_KEY`

### AWS SES (Email Sending)

1. Go to: https://aws.amazon.com/ses/
2. Verify your domain (SES console)
3. Create access keys in IAM
4. Set AWS credentials

### Gmail SMTP (Email Sending)

1. Enable 2-factor authentication
2. Generate app password: https://myaccount.google.com/apppasswords
3. Set `SMTP_USERNAME` = your@gmail.com
4. Set `SMTP_PASSWORD` = generated app password

## Monitoring & Logging

### Local Development

Logs available at:

- Console output (real-time)
- `./logs/solarware.log` (file)

### Production

**Google Cloud Run:**

```bash
# View logs
gcloud run logs read solarware-backend --limit 100

# Stream logs
gcloud run logs read solarware-backend --limit 100 --follow
```

**Railway:**

- View in Railway dashboard
- Logs tab shows real-time output

**AWS CloudWatch:**

```bash
# View logs
aws logs tail /aws/ecs/solarware-backend --follow
```

## Testing

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage report
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v
```

## Troubleshooting

### "Connection refused" when starting backend

**Solution:** Database not running or DATABASE_URL incorrect

```bash
# Check database is running
docker-compose ps  # Should show postgres container

# Or check local PostgreSQL
psql -U solarware -d solarware -c "SELECT 1"

# Update DATABASE_URL in .env if needed
```

### "PostGIS extension not found"

**Solution:** Extension not loaded in database

```bash
# Connect to database and enable
psql -U solarware -d solarware -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Frontend can't reach backend

**Solution:** CORS or API URL misconfiguration

```bash
# In frontend/.env:
VITE_API_URL=http://localhost:8000

# Check backend CORS_ORIGINS in .env:
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### API rate limits

**Solution:** Implement backoff or use API keys

- Satellite providers: Request higher quota
- Google Maps: Enable billing and set quotas
- Email services: Check sending limits in dashboard

### Out of memory errors

**Solution:** Increase container/VM memory

```bash
# Docker Compose
docker-compose exec backend free -h

# Google Cloud Run
gcloud run update solarware-backend --memory 4Gi

# Railway/AWS: Check dashboard settings
```

## Performance Optimization

### Database

```sql
-- Index commonly queried columns
CREATE INDEX idx_search_area_country ON search_areas(country);
CREATE INDEX idx_prospect_search_area ON prospects(search_area_id);
CREATE INDEX idx_prospect_geometry ON prospects USING GIST(geometry);
```

### API

- Response caching for satellite images (24+ hours)
- Batch processing for contact enrichment (rate limiting)
- Async email sending (don't block on SMTP)

### Frontend

- Production build (`npm run build`) uses minification/optimization
- CSS-in-JS removed, uses Tailwind
- Image lazy loading for prospect list

## Backup & Recovery

### Database Backup

**Local:**

```bash
# Backup
pg_dump -U solarware solarware > backup.sql

# Restore
psql -U solarware solarware < backup.sql
```

**Google Cloud SQL:**

```bash
# Create backup
gcloud sql backups create --instance=solarware-db

# List backups
gcloud sql backups list --instance=solarware-db

# Restore
gcloud sql backups restore BACKUP_ID --backup-instance=solarware-db
```

### Output Files

```bash
# Backup mailing packs and visualizations
cd Solarware
tar -czf output_backup_$(date +%Y%m%d).tar.gz ./output/
```

## Security Checklist

- [ ] Never commit `.env` or secrets to repository
- [ ] Use HTTPS in production (automatic with Cloud Run, Railway, etc.)
- [ ] Set strong database passwords
- [ ] Rotate API keys regularly
- [ ] Enable CORS only for trusted origins
- [ ] Use authentication for admin endpoints (future enhancement)
- [ ] Log all operations for audit trail
- [ ] Regular database backups enabled
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints

## Support

See main README.md for FAQ and feature documentation.

---

**Last Updated:** 2024
**Status:** Production-Ready (MVP)
