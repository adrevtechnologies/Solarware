# Solarware - Complete Deployment Guide

This guide covers deploying Solarware to production environments.

## Table of Contents

1. [Platform Selection](#platform-selection)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Google Cloud Run (Recommended)]
4. [AWS Deployment](#aws-deployment)
5. [Azure Deployment](#azure-deployment)
6. [Railway.app](#railwayapp)
7. [Monitoring & Updates](#monitoring--updates)

---

## Platform Selection

| Platform              | Cost         | Ease   | Scalability | Free Tier  |
| --------------------- | ------------ | ------ | ----------- | ---------- |
| **Google Cloud Run**  | $0.40/M reqs | Medium | Excellent   | 2M req/mo  |
| **Railway.app**       | $5-50/mo     | Easy   | Good        | Free trial |
| **AWS Fargate**       | $0.05/hour   | Hard   | Excellent   | Yes (12mo) |
| **Azure App Service** | $7-50/mo     | Medium | Good        | Free tier  |
| **Heroku**            | Discontinued | N/A    | N/A         | N/A        |

**Recommendation for MVP:** Google Cloud Run or Railway.app

---

## Pre-Deployment Checklist

**Code:**

- [ ] All tests passing (`pytest`)
- [ ] Environment variables documented
- [ ] API keys configured (or marked as optional)
- [ ] Debug mode disabled in production
- [ ] Logging configured for production

**Infrastructure:**

- [ ] Database backups automated
- [ ] HTTPS/SSL configured
- [ ] CORS origins set correctly
- [ ] Database migrations applied
- [ ] Secrets manager configured

**Documentation:**

- [ ] API documentation deployed
- [ ] Deployment procedure documented
- [ ] Rollback procedure defined
- [ ] On-call emergency contacts listed
- [ ] Database schema backed up

**Testing:**

- [ ] Load testing completed
- [ ] End-to-end testing in staging
- [ ] Security scanning completed
- [ ] Database connections verified

---

# Google Cloud Run Deployment (Recommended)

## 1. Prerequisites

```bash
# Install gcloud CLI: https://cloud.google.com/sdk/docs/install

gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## 2. Create Cloud SQL PostgreSQL

```bash
# Create instance
gcloud sql instances create solarware-db \
  --database-version POSTGRES_15 \
  --region us-central1 \
  --tier db-f1-micro \
  --availability-type REGIONAL

# Create database
gcloud sql databases create solarware --instance solarware-db

# Create app user
gcloud sql users create solarware \
  --instance solarware-db \
  --password

# Note the password shown - you'll need it
```

## 3. Build and Push Backend

```bash
# From project root

# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/solarware-backend backend/

# Verify image pushed
gcloud container images list --repository gcr.io/YOUR_PROJECT_ID
```

## 4. Deploy Backend Service

```bash
# Get Cloud SQL connection name
gcloud sql instances describe solarware-db --format='value(connectionName)'
# Output: YOUR_PROJECT_ID:us-central1:solarware-db

# Deploy to Cloud Run
gcloud run deploy solarware-backend \
  --image gcr.io/YOUR_PROJECT_ID/solarware-backend \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --timeout 3600 \
  --set-env-vars "DATABASE_URL=postgresql://solarware:PASSWORD@CLOUD_SQL_IP:5432/solarware" \
  --allow-unauthenticated \
  --set-cloudsql-instances YOUR_PROJECT_ID:us-central1:solarware-db

# Get service URL
gcloud run services describe solarware-backend --platform managed --region us-central1 --format='value(status.url)'
```

## 5. Deploy Frontend

```bash
# Build frontend
cd frontend
npm install
npm run build
# Output: dist/ folder

# Create Cloud Storage bucket
gsutil mb gs://solarware-frontend-prod

# Upload built files
gsutil -m cp -r dist/* gs://solarware-frontend-prod/

# Configure Cloud CDN (optional but recommended)
gcloud compute backend-buckets create solarware-frontend \
  --gcs-url-mask='gs://solarware-frontend-prod/*' \
  --enable-cdn

# Create firewall rule
gcloud compute firewalls create allow-frontend \
  --allow tcp:443 --source-ranges '0.0.0.0/0'
```

## 6. Configure Domain (Optional)

```bash
# Point your domain's nameservers to Google Cloud DNS
# Or create DNS records:

# For Cloud Run backend
gcloud dns record-sets create api.yourdomain.com \
  --type CNAME \
  --ttl 300 \
  --rrdatas [YOUR_CLOUD_RUN_URL]

# For frontend (if using Cloud Storage)
gcloud dns record-sets create yourdomain.com \
  --type A \
  --ttl 300 \
  --rrdatas [CLOUD_LB_IP]
```

## 7. Monitoring

```bash
# View logs
gcloud run logs read solarware-backend --limit 100

# Stream logs (real-time)
gcloud run logs read solarware-backend --limit 100 --follow

# View metrics
gcloud monitoring dashboards create --config-from-file -<<EOF
{
  "displayName": "Solarware Backend",
  "dashboardFilters": [],
  "gridLayout": {
    "widgets": [
      {
        "title": "Request Count",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"solarware-backend\""
              }
            }
          }]
        }
      }
    ]
  }
}
EOF
```

---

# AWS Deployment

## 1. Prerequisites

```bash
# Install AWS CLI v2
# https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html

aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)
```

## 2. Create RDS PostgreSQL

```bash
# Via AWS Management Console:
# 1. RDS → Databases → Create Database
# 2. Select PostgreSQL 15
# 3. Use 'db.t3.micro' (free tier eligible)
# 4. Enable "Public accessibility" for development
# 5. Security group: Allow inbound 5432 from anywhere (or your IP only)
# 6. Subnet group: default-vpc
# 7. Create

# Or via CLI:
aws rds create-db-instance \
  --db-instance-identifier solarware-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15 \
  --master-username solarware \
  --master-user-password 'YourSecurePassword123!' \
  --allocated-storage 20 \
  --publicly-accessible \
  --region us-east-1
```

## 3. Create ECS Cluster and Task

```bash
# Create cluster
aws ecs create-cluster --cluster-name solarware

# Create task definition
cat > task-definition.json <<'EOF'
{
  "family": "solarware-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "solarware-backend",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/solarware-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://solarware:PASSWORD@RDS_ENDPOINT:5432/solarware"
        },
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/solarware",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster solarware \
  --service-name solarware-backend \
  --task-definition solarware-backend:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## 4. Setup S3 for Frontend

```bash
# Create bucket
aws s3 mb s3://solarware-frontend-prod --region us-east-1

# Build and deploy
cd frontend
npm run build
aws s3 sync dist/ s3://solarware-frontend-prod/ --delete

# Enable website hosting
aws s3 website s3://solarware-frontend-prod/ \
  --index-document index.html \
  --error-document index.html

# Create CloudFront distribution for HTTPS
# Via AWS Console: CloudFront → Create Distribution → Select S3 bucket
```

---

# Azure Deployment

## 1. Prerequisites

```bash
# Install Azure CLI
# https://learn.microsoft.com/en-us/cli/azure/install-azure-cli

az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

## 2. Create Resource Group

```bash
az group create --name solarware-rg --location eastus
```

## 3. Create Database

```bash
# Create PostgreSQL server
az postgres server create \
  --resource-group solarware-rg \
  --name solarware-db \
  --admin-user solarware \
  --admin-password 'YourSecurePassword123!' \
  --sku-name B_Gen5_1 \
  --storage-size 51200

# Create database
az postgres db create \
  --resource-group solarware-rg \
  --server-name solarware-db \
  --name solarware

# Enable PostGIS
az postgres server configuration set \
  --resource-group solarware-rg \
  --server-name solarware-db \
  --name azure.extensions \
  --value POSTGIS
```

## 4. Deploy Backend

```bash
# Create App Service plan
az appservice plan create \
  --name solarware-plan \
  --resource-group solarware-rg \
  --sku B1 --is-linux

# Create web app
az webapp create \
  --resource-group solarware-rg \
  --plan solarware-plan \
  --name solarware-backend \
  --runtime "PYTHON|3.11"

# Configure app settings
az webapp config appsettings set \
  --resource-group solarware-rg \
  --name solarware-backend \
  --settings \
    DATABASE_URL="postgresql://solarware:PASSWORD@solarware-db.postgres.database.azure.com/solarware" \
    ENVIRONMENT=production

# Deploy code
cd backend
az webapp deployment source config-zip \
  --resource-group solarware-rg \
  --name solarware-backend \
  --src deployment.zip
```

## 5. Deploy Frontend

```bash
# Create static web app
az staticwebapp create \
  --name solarware-frontend \
  --resource-group solarware-rg \
  --source "https://github.com/YOUR_USERNAME/Solarware" \
  --location westus2 \
  --branch main \
  --app-location "frontend" \
  --output-location "dist"
```

---

# Railway.app

**Simplest option for solo developers**

## 1. Create Railway Account

Go to: https://railway.app/

## 2. Connect GitHub

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Authorize GitHub and select Solarware repo

## 3. Add Services

1. Click "Add Service"
2. Select PostgreSQL
3. Add another service, select "GitHub repo"

## 4. Configure Environment

In Railway dashboard:

```
DATABASE_URL=postgres://...  (auto-set by PostgreSQL)
ENVIRONMENT=production
DEBUG=false
```

## 5. Deploy

Push to GitHub - Railway auto-deploys:

```bash
git push origin main
```

## 6. View Logs & URLs

- Click service to view logs
- Railway shows auto-generated URLs
- Add custom domain in settings

---

## Monitoring & Updates

### Health Checks

```bash
# Google Cloud Run
curl https://YOUR_SERVICE_URL/health

# AWS
curl https://YOUR_ALB_DNS/health

# Azure
curl https://solarware-backend.azurewebsites.net/health
```

### Database Maintenance

```bash
# Backup (Cloud SQL)
gcloud sql backups create --instance solarware-db

# Monitor connections
gcloud sql instances describe solarware-db

# Vacuum & analyze (periodic maintenance)
gcloud sql import sql solarware-db gs://backup-bucket/vacuum.sql
```

### Log Aggregation

**Stackdriver (Google Cloud):**

```bash
gcloud logging sink create sql-logs \
  logging.googleapis.com/logs \
  --log-filter 'resource.type="cloud_sql_database"'
```

**CloudWatch (AWS):**

```bash
# Logs auto-collected in /ecs/solarware
# View: CloudWatch → Logs → /ecs/solarware
```

### Alerts

**Google Cloud:**

```bash
gcloud alpha monitoring policies create \
  --notification-channels CHANNEL_ID \
  --display-name "Solarware Backend Down" \
  --condition-display-name "Service unavailable"
```

### Zero-Downtime Deployment

For critical updates:

1. **Create new version** of container
2. **Deploy to staging environment**
3. **Run integration tests**
4. **Gradual traffic shift:**
   - Cloud Run: Deploy new revision, check metrics
   - AWS: Update task definition, use CodeDeploy
   - Railway: Push to separate branch, validate
5. **Rollback plan:** Keep previous version available

---

## Cost Optimization

| Service                 | Monthly Cost | Notes                        |
| ----------------------- | ------------ | ---------------------------- |
| Cloud Run (2M reqs)     | $0           | Covered by free tier         |
| Cloud SQL (db-f1-micro) | ~$20         | Free tier for first 365 days |
| Cloud Storage           | ~$2          | Mailing packs/visualizations |
| **Total (Year 1)**      | ~$100        | With free tier               |
| **Total (Year 2+)**     | ~$300        | After free tier ends         |

**Cost reduction tips:**

1. Use free tier for first year
2. Use Cloud CDN for frontend caching
3. Archive old mailing packs to cheaper storage
4. Use spot instances (EC2) for batch processing
5. Monitor and set billing alerts

---

## Security Hardening

```bash
# Cloud Run: Restrict CORS
gcloud run update solarware-backend \
  --set-env-vars "CORS_ORIGINS=https://yourdomain.com"

# Cloud Run: Require authentication (if needed)
gcloud run update solarware-backend \
  --no-allow-unauthenticated

# Database: Restrict IP access
gcloud sql instances patch solarware-db \
  --require-ssl

# Secrets: Use Secret Manager
gcloud secrets create db-password --data-file=-
gcloud run update solarware-backend \
  --set-secrets DB_PASSWORD=db-password:latest
```

---

## Scaling

**Horizontal (more instances):**

- Cloud Run: Auto-scales automatically (0-100s of instances)
- AWS ECS: Set desired count to 2+
- Railway: Configure auto-scale in settings

**Vertical (bigger instances):**

- Cloud Run: Increase memory from 512MB → 2GB, 4GB
- AWS: Change db.t3.micro → db.t3.small
- Railway: Upgrade plan tier

**Database:**

- Create read replicas for queries
- Implement connection pooling
- Archive old prospect data to cold storage

---

## Disaster Recovery

**Backup Strategy:**

- Database: Daily backups, retained 30 days
- Mailing packs: Weekly backups to separate bucket
- Code: GitHub repo with tags for releases

**Restore Procedure:**

1. Provision new database from backup
2. Update DATABASE_URL in env vars
3. Restart application
4. Verify health checks pass
5. Point DNS to new instance

**RTO (Recovery Time):** ~15 minutes
**RPO (Recovery Point):** 24 hours (for DB), 7 days (for files)

---

**Last Updated:** 2024  
**Status:** Production-Ready
