# DEPLOYMENT INSTRUCTIONS FOR SOLARWARE

## FIXED ISSUES

✅ Frontend now reads backend URL from environment variable (not hardcoded localhost)
✅ Added satellite imagery URLs to API response
✅ All tests passing (19/19)
✅ Frontend builds without errors

## WHAT YOU NEED TO DO NOW

### STEP 1: Push code to GitHub

```bash
cd d:\Solarware\Solarware
git add -A
git commit -m "Fix search API and add satellite imagery support"
git push origin main
```

### STEP 2: Configure RENDER Backend Deployment

1. Go to your Render project dashboard
2. Click on your backend service
3. Go to **Environment** settings
4. Add/Update these environment variables:

```
VITE_API_URL=https://YOUR-RENDER-BACKEND-URL.onrender.com
DATABASE_URL=sqlite:///./solarware.db
DEBUG=False
ENVIRONMENT=production
```

5. Redeploy from GitHub

### STEP 3: Configure VERCEL Frontend Deployment

1. Go to your Vercel project dashboard
2. Go to **Settings → Environment Variables**
3. Add/Update for ALL environments (Production, Preview, Development):

```
VITE_API_URL=https://YOUR-RENDER-BACKEND-URL.onrender.com
```

Example: If your Render backend is `https://solarware-api.onrender.com`, use that.

4. Redeploy from GitHub (or trigger manually)

### STEP 4: Test the Live Search

Once deployed:

1. Open your Vercel frontend URL
2. Fill search form:
   - Country: South Africa
   - Province: Western Cape
   - City: Cape Town
   - Area: Goodwood
   - Street: 98 Richmond Street
3. Click "Find Solar Leads"
4. Should see results with addresses and satellite imagery URLs

## WHAT CHANGED

### Frontend

- `Dashboard.tsx`: Now uses `import.meta.env.VITE_API_URL` instead of hardcoded localhost
- `.env.local`: Local development config
- `.env.example`: Template for your team

### Backend

- `search.py`: Now returns `satellite_image_url` and `mockup_image_url`
- API Response includes imagery URLs for every prospect

### Database

- No changes needed - uses existing 926 prospects

## GOOGLE MAPS API KEY (OPTIONAL)

If satellite imagery URLs don't load:

1. Get a Google Maps API key: https://console.cloud.google.com/
2. Add to Vercel env vars:
   ```
   VITE_GOOGLE_MAPS_API_KEY=YOUR_KEY_HERE
   ```
3. Replace "YOUR_API_KEY" in backend/app/api/search.py line with actual key
4. Redeploy

## TROUBLESHOOTING

**If search still fails after deploy:**

- Check Vercel logs: Deployment → Logs
- Check Render logs: Dashboard → Backend service → Logs
- Verify VITE_API_URL is correct (must include https://)

**If imagery URLs don't work:**

- Render backend is running: check Render logs
- Google Maps API key is valid or remove key URLs

## YOUR LIVE DOMAINS

Update these below once deployed:

- **Frontend**: [Your Vercel URL]
- **Backend**: [Your Render URL]
