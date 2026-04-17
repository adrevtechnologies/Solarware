# 📑 Documentation Index

**Everything you need to get started with Solarware**

---

## 🎯 Start Here (Choose Your Role)

### I'm a **User** - Just want to run it

**Read in order (10 min total):**

1. Top of [README.md](./README.md) - Features overview
2. [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#-start-here) - Quick start (3 steps)
3. [docs/SETUP.md](./docs/SETUP.md#local-development) - Local dev setup

**Result:** Running locally with `docker-compose up`

---

### I'm a **Backend Developer** - Want to extend the code

**Read in order (25 min total):**

1. [README.md](./README.md#features) - Features overview
2. [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) - System design
3. [FILE_MANIFEST.md](./FILE_MANIFEST.md#-backend-files) - File structure
4. Relevant source file comments
5. [docs/ARCHITECTURE.md#making-connections-real](./docs/ARCHITECTURE.md#making-connections-real) - Real API integration

**Typical Tasks:**

- Add satellite imagery → See [docs/ARCHITECTURE.md#adding-a-new-satellite-provider](./docs/ARCHITECTURE.md#adding-a-new-satellite-provider)
- Add contact enrichment source → See nested instructions in same file
- Add solar calculation → See `backend/app/utils/solar_calculations.py`

---

### I'm a **Frontend Developer** - Want to modify the UI

**Read in order (20 min total):**

1. [README.md](./README.md#tech-stack) - Tech stack overview
2. [FILE_MANIFEST.md](./FILE_MANIFEST.md#-frontend-files) - Frontend file structure
3. Component files in `frontend/src/components/`
4. [docs/API.md](./docs/API.md) - Available API endpoints

**Typical Tasks:**

- Add new page → Copy pattern from `Dashboard.tsx`
- Change styling → Edit in `frontend/src/components/*.tsx` or `src/index.css`
- Add API call → Add method to `frontend/src/services/api.ts`

---

### I'm a **DevOps Engineer** - Need to deploy

**Read in order (30 min total):**

1. [README.md](./README.md#quick-start) - Overview
2. [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) - Full deployment guide
   - Choose your platform (Google Cloud, AWS, Azure, Railway)
   - Follow step-by-step instructions
3. [docs/SETUP.md](./docs/SETUP.md#production-deployment) - Multi-platform guide
4. [COMPLETION_SUMMARY.md](./COMPLETION_SUMMARY.md#production-readiness) - Pre-deploy checklist

**Platform-Specific (pick one):**

- [Google Cloud Run](./docs/DEPLOYMENT.md#google-cloud-run-deployment) - Recommended for MVP
- [AWS](./docs/DEPLOYMENT.md#aws-deployment) - Most control
- [Azure](./docs/DEPLOYMENT.md#azure-deployment) - Enterprise
- [Railway.app](./docs/DEPLOYMENT.md#railwayapp) - Simplest

---

### I'm a **Data Analyst** - Want to understand the data

**Read in order (10 min total):**

1. [README.md](./README.md#database-schema) - Schema overview
2. [docs/API.md](./docs/API.md#data-types-reference) - Data types
3. [FILE_MANIFEST.md](./FILE_MANIFEST.md#-backend-files) - Models location

**Query Prospect Data:**

```bash
docker exec solarware-backend psql -U solarware -d solarware -c "
SELECT address, estimated_panel_count, annual_savings_usd, data_complete
FROM prospects
LIMIT 10;
"
```

---

### I'm an **API Consumer** - Building integrations

**Read in order (15 min total):**

1. [docs/API.md](./docs/API.md#api-reference) - Full API documentation
   - All 26 endpoints with examples
   - Error codes & handling
2. [docs/API.md](./docs/API.md#example-workflow) - End-to-end example
3. [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#-api-endpoints) - Quick endpoint lookup

**Make Your First Request:**

```bash
# Create search area
curl -X POST http://localhost:8000/api/search-areas \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","country":"US","region":"CA","min_lat":37.7,"max_lat":37.8,"min_lon":-122.5,"max_lon":-122.4,"min_roof_area_sqft":500}'

# List prospects
curl http://localhost:8000/api/prospects
```

---

## 📚 Documentation Map

### Quick References

| File                                             | Purpose            | Read Time | Best For         |
| ------------------------------------------------ | ------------------ | --------- | ---------------- |
| [README.md](./README.md)                         | Project overview   | 5 min     | Everyone         |
| [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)       | Common tasks       | 5 min     | Developers       |
| [FILE_MANIFEST.md](./FILE_MANIFEST.md)           | All files created  | 10 min    | Code explorers   |
| [COMPLETION_SUMMARY.md](./COMPLETION_SUMMARY.md) | What was delivered | 5 min     | Project managers |

### Technical Guides

| File                                           | Purpose                  | Read Time | Best For     |
| ---------------------------------------------- | ------------------------ | --------- | ------------ |
| [docs/SETUP.md](./docs/SETUP.md)               | Installation & local dev | 15 min    | Developers   |
| [docs/API.md](./docs/API.md)                   | API reference            | 10 min    | API users    |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design            | 15 min    | Backend devs |
| [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)     | Production deployment    | 20 min    | DevOps       |

---

## 🗺️ How to Navigate Docs

### "How do I...?" Questions

| Question                      | Answer                                                                                                                                  |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Install locally?              | [docs/SETUP.md - Local Development](./docs/SETUP.md#local-development)                                                                  |
| Deploy to production?         | [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) or [Platform Guides](./docs/DEPLOYMENT.md#platform-selection)                                |
| Call an API endpoint?         | [docs/API.md](./docs/API.md) or [QUICK_REFERENCE.md - API Endpoints](./QUICK_REFERENCE.md#-api-endpoints)                               |
| Find a specific file?         | [FILE_MANIFEST.md](./FILE_MANIFEST.md)                                                                                                  |
| Add a new satellite provider? | [docs/ARCHITECTURE.md - Modularity](./docs/ARCHITECTURE.md#modularity--extension-points)                                                |
| Change the email provider?    | [QUICK_REFERENCE.md - Common Tasks](./QUICK_REFERENCE.md#-common-tasks)                                                                 |
| See all created files?        | [FILE_MANIFEST.md - Project Files](./FILE_MANIFEST.md#-project-root-files)                                                              |
| Understand the architecture?  | [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)                                                                                          |
| Debug an issue?               | [QUICK_REFERENCE.md - Debugging](./QUICK_REFERENCE.md#-debugging) or [docs/SETUP.md - Troubleshooting](./docs/SETUP.md#troubleshooting) |

---

## 🔗 Cross-Reference Guide

### From Frontend to Backend

**Frontend Component** → **Backend Endpoint** → **Backend Service**

```
SearchAreaForm.tsx (frontend)
    ↓ POST /api/search-areas
    ↓ backend/app/api/search_areas.py
    ↓ backend/app/models.py (SearchArea model)
```

**Example:** Want to add a field to search area?

1. Update Pydantic schema: `backend/app/schemas/__init__.py`
2. Update database model: `backend/app/models/__init__.py`
3. Update React form: `frontend/src/components/SearchAreaForm.tsx`

### Integration Dependencies

**Satellite** → Building Detection → Solar Analysis → Mailing Pack → Email

```
satellite_providers.py (get images)
    ↓ building_detection.py (find buildings)
    ↓ solar_calculations.py (estimate system)
    ↓ mailing_pack.py (create email)
    ↓ email_service.py (send)
```

---

## 🎓 Learning Paths

### Path 1: Understanding the System (30 min)

1. [README.md - Features](./README.md#features)
2. [docs/ARCHITECTURE.md - System Architecture](./docs/ARCHITECTURE.md#system-architecture)
3. [COMPLETION_SUMMARY.md - What's Delivered](./COMPLETION_SUMMARY.md#whats-been-delivered)

### Path 2: Getting Running Locally (15 min)

1. [QUICK_REFERENCE.md - Start Here](./QUICK_REFERENCE.md#-start-here)
2. [docs/SETUP.md - Local Development](./docs/SETUP.md#local-development)
3. Run: `docker-compose up`

### Path 3: API Integration (20 min)

1. [docs/API.md - Authentication](./docs/API.md#authentication) (currently none)
2. [docs/API.md - API Reference](./docs/API.md#api-reference)
3. [QUICK_REFERENCE.md - API Endpoints](./QUICK_REFERENCE.md#-api-endpoints)

### Path 4: Backend Development (45 min)

1. [docs/ARCHITECTURE.md - System Architecture](./docs/ARCHITECTURE.md)
2. [FILE_MANIFEST.md - Backend Files](./FILE_MANIFEST.md#-backend-files)
3. [docs/ARCHITECTURE.md - Modularity](./docs/ARCHITECTURE.md#modularity--extension-points)
4. Choose extension point and implement

### Path 5: Deployment to Production (60 min)

1. [COMPLETION_SUMMARY.md - Pre-Deploy Checklist](./COMPLETION_SUMMARY.md#production-readiness)
2. [docs/DEPLOYMENT.md - Platform Selection](./docs/DEPLOYMENT.md#platform-selection)
3. Choose platform and follow step-by-step
4. [docs/DEPLOYMENT.md - Monitoring & Updates](./docs/DEPLOYMENT.md#monitoring--updates)

---

## 📞 "Where is...?" Quick Lookup

| Looking for             | Location                                  |
| ----------------------- | ----------------------------------------- |
| Solar calculations code | `backend/app/utils/solar_calculations.py` |
| Database models         | `backend/app/models/__init__.py`          |
| API endpoints           | `backend/app/api/*.py`                    |
| Frontend components     | `frontend/src/components/*.tsx`           |
| API documentation       | `docs/API.md`                             |
| Setup instructions      | `docs/SETUP.md`                           |
| Deployment guide        | `docs/DEPLOYMENT.md`                      |
| Architecture docs       | `docs/ARCHITECTURE.md`                    |
| All files listed        | `FILE_MANIFEST.md`                        |

---

## ✅ Recommended Reading Order by Scenario

### Scenario 1: I have 5 minutes

→ [README.md](./README.md)

### Scenario 2: I want to evaluate if this fits my needs

→ [README.md](./README.md) + [COMPLETION_SUMMARY.md](./COMPLETION_SUMMARY.md)

### Scenario 3: I want to run it locally ASAP

→ [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#-start-here) + [docs/SETUP.md - Local](./docs/SETUP.md#local-development)

### Scenario 4: I want to deploy to production

→ [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) + your platform choice

### Scenario 5: I want to understand the full system

→ [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) + [FILE_MANIFEST.md](./FILE_MANIFEST.md)

### Scenario 6: I want to add new functionality

→ [docs/ARCHITECTURE.md - Modularity](./docs/ARCHITECTURE.md#modularity--extension-points) + relevant source files

### Scenario 7: I want to integrate with an external system

→ [docs/API.md](./docs/API.md) + relevant provider integration

---

## 🚀 Next Action

**Choose one:**

- [ ] **Just want to see it running?** → [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#-start-here)
- [ ] **Want to understand everything?** → [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [ ] **Ready for production?** → [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)
- [ ] **Need to extend something?** → [docs/ARCHITECTURE.md - Extension Points](./docs/ARCHITECTURE.md#modularity--extension-points)
- [ ] **Looking for a specific file?** → [FILE_MANIFEST.md](./FILE_MANIFEST.md)
- [ ] **Want all common tasks in one place?** → [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

---

## 📧 Still Have Questions?

Check:

1. **Troubleshooting** → [docs/SETUP.md - Troubleshooting](./docs/SETUP.md#troubleshooting)
2. **API Issues** → [docs/API.md](./docs/API.md)
3. **Architecture Questions** → [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
4. **File Structure** → [FILE_MANIFEST.md](./FILE_MANIFEST.md)

---

**Start with** [README.md](./README.md) **or** [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) **→ Then choose your next step above!**

**Version:** 0.1.0  
**Status:** ✅ Production-Ready  
**Last Updated:** 2024
