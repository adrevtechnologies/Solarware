# API Reference

## Authentication (Future Enhancement)

Currently no authentication. For production deployment, implement JWT token validation.

## Base URL

- Development: `http://localhost:8000`
- Production: Your deployment URL

## Response Format

All responses follow this format:

```json
{
  "data": { ... },
  "status": "success|error",
  "timestamp": "2024-01-15T10:30:45Z"
}
```

Errors return HTTP status codes with error details.

## Endpoints

### Search Areas

#### Create Search Area

```http
POST /api/search-areas
Content-Type: application/json

{
  "name": "Downtown District",
  "country": "US",
  "region": "CA",
  "min_latitude": 40.7,
  "max_latitude": 40.8,
  "min_longitude": -74.0,
  "max_longitude": -73.9,
  "min_roof_area_sqft": 5000
}
```

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Downtown District",
  "country": "US",
  "region": "CA",
  "min_latitude": 40.7,
  "max_latitude": 40.8,
  "min_longitude": -74.0,
  "max_longitude": -73.9,
  "min_roof_area_sqft": 5000,
  "created_at": "2024-01-15T10:30:45Z",
  "updated_at": "2024-01-15T10:30:45Z"
}
```

#### List Search Areas

```http
GET /api/search-areas?country=US&skip=0&limit=50
```

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Downtown District",
    ...
  }
]
```

#### Get Search Area

```http
GET /api/search-areas/{id}
```

#### Update Search Area

```http
PUT /api/search-areas/{id}
Content-Type: application/json

{
  "name": "Updated Name",
  ...
}
```

---

### Prospects

#### List Prospects

```http
GET /api/prospects?search_area_id={id}&skip=0&limit=50
```

**Query Parameters:**

- `search_area_id` (optional): Filter by search area
- `skip` (default: 0): Pagination offset
- `limit` (default: 50, max: 500): Results per page

**Response:** `200 OK`

```json
[
  {
    "id": "650e8400-e29b-41d4-a716-446655440001",
    "search_area_id": "550e8400-e29b-41d4-a716-446655440000",
    "address": "123 Main St, New York, NY",
    "latitude": 40.7128,
    "longitude": -74.006,
    "roof_area_sqft": 10000,
    "roof_area_sqm": 929,
    "estimated_panel_count": 25,
    "estimated_system_capacity_kw": 10.0,
    "estimated_annual_production_kwh": 12500,
    "estimated_annual_savings_usd": 1875,
    "has_existing_solar": false,
    "created_at": "2024-01-15T10:35:20Z"
  }
]
```

#### Get Prospect

```http
GET /api/prospects/{id}
```

#### Get Prospect Contact

```http
GET /api/prospects/{id}/contact
```

**Response:**

```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "prospect_id": "650e8400-e29b-41d4-a716-446655440001",
  "contact_name": "John Smith",
  "title": "Facilities Manager",
  "email": "john.smith@company.com",
  "phone": "(555) 123-4567",
  "data_complete": true,
  "confidence_score": 0.95,
  "created_at": "2024-01-15T10:35:20Z"
}
```

#### Export Prospects as CSV

```http
GET /api/prospects/export-csv
```

**Response:** CSV file download

```
address,business_name,roof_area_sqft,system_capacity_kw,annual_savings,created_at
"123 Main St, New York, NY",,10000,10.0,1875,"2024-01-15T10:35:20Z"
```

---

### Processing

#### Process Search Area

```http
POST /api/process/search-area/{area_id}?generate_visualizations=true&enrich_contacts=true&generate_packs=true
```

**Query Parameters:**

- `generate_visualizations` (default: true): Generate mockup images
- `enrich_contacts` (default: true): Enrich contact information
- `generate_packs` (default: true): Generate mailing packs

**Response:** `202 Accepted` (processing starts in background)

```json
{
  "status": "processing_started",
  "search_area_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Processing has been queued. Check status for updates."
}
```

#### Get Processing Status

```http
GET /api/process/status/{area_id}
```

**Response:**

```json
{
  "search_area_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed|processing|failed",
  "prospects_discovered": 45,
  "prospects_analyzed": 45,
  "contacts_enriched": 42,
  "visualizations_generated": 45,
  "mailing_packs_generated": 45,
  "errors": [],
  "started_at": "2024-01-15T10:30:45Z",
  "completed_at": "2024-01-15T11:15:30Z"
}
```

---

### Health

#### Health Check

```http
GET /health
```

**Response:** `200 OK`

```json
{
  "status": "ok",
  "environment": "development"
}
```

#### Readiness Check

```http
GET /health/ready
```

**Response:** `200 OK` (ready) or `503 Service Unavailable` (not ready)

```json
{
  "status": "ready|not_ready",
  "database": "connected|error"
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error description"
}
```

### HTTP Status Codes

- `200 OK` - Successful GET/PUT
- `201 Created` - Successful POST
- `202 Accepted` - Processing started (async)
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - External API error
- `503 Service Unavailable` - Service down

### Error Examples

**Invalid coordinates:**

```json
{
  "detail": "Invalid latitude: 95. Must be between -90 and 90"
}
```

**Satellite provider error:**

```json
{
  "detail": "Failed to retrieve satellite images: API rate limit exceeded"
}
```

**Not found:**

```json
{
  "detail": "Prospect 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

---

## Rate Limiting

Current implementation: No rate limiting (add via nginx, Cloud Run, or API Gateway)

Recommended limits:

- `/api/process/*` : 1 request per minute per IP (processing is heavy)
- `/api/prospects` : 10 requests per minute per IP
- Other endpoints: 100 requests per minute per IP

---

## Pagination

List endpoints support pagination via `skip` and `limit`:

```http
GET /api/prospects?skip=50&limit=50
```

Gets items 50-100 (second "page" of 50 items)

---

## Filtering

**Search Areas:**

- `country`: Filter by country code (case-insensitive, auto-upper cased)

**Prospects:**

- `search_area_id`: Filter by search area UUID

---

## Data Types

| Type         | Format   | Example                                |
| ------------ | -------- | -------------------------------------- |
| UUID         | String   | `550e8400-e29b-41d4-a716-446655440000` |
| Timestamp    | ISO 8601 | `2024-01-15T10:30:45Z`                 |
| Latitude     | Float    | `-90.0 to 90.0`                        |
| Longitude    | Float    | `-180.0 to 180.0`                      |
| Currency     | Float    | `1234.56` (USD)                        |
| Area (sq ft) | Float    | `5000.0`                               |
| Area (sq m)  | Float    | `464.5`                                |
| Capacity     | Float    | `10.5` (kW)                            |
| Production   | Float    | `12500.0` (kWh/year)                   |

---

## Batch Operations (Future)

Planned endpoints for bulk operations:

- `POST /api/prospects/batch` - Create multiple
- `POST /api/email/batch-send` - Send multiple packs
- `POST /api/process/batch` - Process multiple areas

---

## WebSocket (Future)

Real-time progress updates during processing:

```
WS /ws/process/status/{area_id}
```

Would emit events like:

```json
{
  "event": "progress",
  "step": "detecting_buildings",
  "progress": 45,
  "message": "Detected 123 buildings..."
}
```

---

**Last Updated:** 2024
**API Version:** 0.1.0
