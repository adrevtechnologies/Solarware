# Solarware Deployment Guide

## Prerequisites

- GitHub repository: https://github.com/morgan9hips-sketch/Solarware
- Render account: https://render.com/
- Vercel account: https://vercel.com/

## Backend Deployment (Render)

### Step 1: Create Service on Render

1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect to GitHub repository `Solarware`
4. Select branch: `main`

### Step 2: Configure Service

- **Name:** solarware-backend
- **Environment:** Python 3
- **Build Command:** `pip install -r backend/requirements.txt`
- **Start Command:** `python wsgi.py`
- **Instance Type:** Starter (free tier) or Standard

### Step 3: Add Environment Variables

No special environment variables needed - the app uses defaults.

### Step 4: Deploy

Click "Create Web Service" - Render will automatically build and deploy.

**Backend URL:** `https://solarware-backend.onrender.com` (example - your URL will be different)

---

## Frontend Deployment (Vercel)

### Step 1: Create Project on Vercel

1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import GitHub repository `Solarware`
4. Select `main` branch

### Step 2: Configure Build Settings

- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`

### Step 3: Add Environment Variables

Create a `.env.production` file in `frontend/`:

```
VITE_API_URL=https://solarware-backend.onrender.com
```

Or set in Vercel dashboard:

- **Name:** `VITE_API_URL`
- **Value:** `https://solarware-backend.onrender.com` (replace with your actual backend URL)

### Step 4: Deploy

Click "Deploy" - Vercel will build and deploy automatically.

**Frontend URL:** `https://solarware.adrevtechnologies.com` (production domain)

---

## Testing the Live System

### Test 1: Goodwood Search

1. Open your frontend URL in browser
2. Select mode: "Address"
3. Enter:
   - Street Number: 98
   - Street Name: Richmond Street
   - Suburb: Goodwood
   - City: Cape Town
   - Province: Western Cape
4. Click "Find Solar Leads"
5. **Expected:** Real building addresses appear with roof sizes, solar capacity, annual kWh, savings potential

### Test 2: Check API Directly

```bash
curl -X POST https://your-backend-url/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "address",
    "street_number": "98",
    "street_name": "Richmond Street",
    "suburb": "Goodwood",
    "city": "Cape Town",
    "province": "Western Cape",
    "radius_m": 500
  }'
```

**Expected Response:**

```json
{
  "results": [
    {
      "lead_id": "place/XXXXX",
      "address": "98 Richmond Street, Goodwood, Cape Town",
      "building_type": "warehouse",
      "roof_area_sqm": 2500,
      "capacity_low_kw": 357,
      "capacity_high_kw": 500,
      "annual_kwh": 617500,
      "savings_potential_display": "R 1.1m – R 2.0m / year",
      "solar_score": 82,
      "satellite_image_url": "https://maps.googleapis.com/maps/api/staticmap?...",
      "latitude": -33.9184,
      "longitude": 18.6726
    }
  ],
  "count": X,
  "search_area": "Goodwood, Cape Town, Western Cape, South Africa",
  "message": "Found X commercial buildings with solar potential"
}
```

### Test 3: Verify No Fake Data

- ✓ No placeholder.com URLs
- ✓ No "Building near -33.x, 18.x" fake addresses
- ✓ Real Google Places addresses
- ✓ NO coordinates shown in UI (only in API response back-end)

### Test 4: Check Google Imagery

- Click on any result to view satellite image
- **Expected:** Real satellite photo from Google Static Maps showing the building roof

---

## Key Features Deployed

1. **Real Building Detection** - Google Places API
2. **Real Geocoding** - Google Geocoding API
3. **Real Roof Area Calculation** - Google-based rooftop estimation
4. **Real Solar Calculations** - South African tariff scenarios
5. **Real Satellite Imagery** - Google Static Maps (25k/day free)
6. **No Fake Data** - 100% live API queries, zero placeholders

---

## Troubleshooting

### Backend won't start

- Check Procfile: `web: python wsgi.py`
- Check requirements.txt in backend/ directory
- Render logs: See deployment logs in Render dashboard

### Frontend API calls failing

- Check VITE_API_URL environment variable
- Ensure backend is running (check Render dashboard)
- Check browser console for CORS errors

### Slow responses

- First query may take 20-30 seconds (provider API query time)
- Subsequent searches are faster
- This is normal for live provider data

---

## Production Checklist

- [ ] Backend deployed on Render
- [ ] Frontend deployed on Vercel
- [ ] Environment variables configured
- [ ] Test search on Goodwood
- [ ] Verify real addresses appear
- [ ] Confirm no coordinates in UI
- [ ] Confirm Google imagery loads
- [ ] Check loading and no-results states

---

**Note:** Both services use the free tier. For production use, upgrade to paid plans for higher rate limits and reliability.
