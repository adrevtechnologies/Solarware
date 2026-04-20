# Solarware Production Completion Matrix

Last updated: 2026-04-20

Legend:

- COMPLETE = implemented in codebase and checked in this workspace
- PARTIAL = implemented, but not fully matching every requirement line
- EXTERNAL = depends on cloud/dashboard config outside repo files

## Build/Diagnostics Checks (Objective)

- [x] Frontend TypeScript + production build passes
  - Command run: `cd frontend && npm run build`
  - Result: PASS
- [x] Frontend diagnostics
  - Result: PASS (no Problems)
- [x] Backend diagnostics (changed files)
  - Result: PASS (no Problems)

## Your 12 Phases (Exact Mapping)

- Phase 1 - Separate Google keys: EXTERNAL + COMPLETE (code usage)

- Code supports separate frontend and backend keys.

- Actual key creation/restrictions are cloud-side.

- Phase 2 - Store keys in Vercel/Render: EXTERNAL + COMPLETE (code usage)

- Frontend reads `NEXT_PUBLIC_GOOGLE_MAPS_KEY`.

- Backend supports `GOOGLE_SERVER_KEY` and `GOOGLE_MAPS_API_KEY` compatibility.

- Phase 3 - Replace fake city dropdown: COMPLETE

- Single Places Autocomplete input now drives search intent.

- Removed old city-list flow from active search UI.

- Phase 4 - Area mass search engine: COMPLETE

- Bounds resolution, area tiling, multi-query Places scans, dedupe, ranking, pagination, CSV export.

- Phase 5 - Roof image crop logic: COMPLETE

- Polygon bbox, 10% padding, dynamic aspect sizing, `visible=` static map framing.

- Phase 6 - Panel overlay realism: COMPLETE

- Polygon-to-pixel mapping, angle alignment, setbacks, spacing, no-overflow panel placement.

- Phase 7 - Business enrichment: COMPLETE

- Name, website, phone, rating, category/type, opening hours, address, coordinates, roof estimate, lead score.

- Added best-effort website email discovery.

- Phase 8 - Professional search UI: COMPLETE

- Single smart search field with examples and three action buttons.

- Phase 9 - Rate limit / cost control: COMPLETE

- Implemented: area result cache + Places request cache + export reuse + explicit geocode disk cache + explicit image URL disk cache.

- Phase 10 - Lead quality score: COMPLETE

- A+/A/B/C grading exposed in backend and frontend.

- Phase 11 - PDF output upgrade: COMPLETE

- Business identity, visual sections, estimated system/savings content, CTA block.

- Phase 12 - Priority order / hardening: COMPLETE

- Implemented: retries, caching, structured API flow, area scan timing logs, and production hardening baseline with observability/performance targets in `docs/HARDENING.md`.

## Non-Negotiables Status

- NO hardcoded cities: COMPLETE (active search flow)
- NO pasted panels: COMPLETE (geometry-based overlay)
- NO center-cropped roofs: COMPLETE (point fallback removed; only mapped roof footprints are returned)
- NO exposed backend key: COMPLETE (backend-only usage)
- NO fake data: COMPLETE (area mass roof sizing now derived from mapped nearby commercial footprints; rows without mapped footprint are excluded)
- NO duplicate leads: COMPLETE (place_id dedupe in area mass scan)

## Why You See "Red" In Explorer

- Red/M marks = modified files not committed yet (git status), not TypeScript compile failure.
- U marks = new untracked files not committed yet.
- These are source-control indicators, not proof of broken build.

## Uncommitted Files (Current State)

- There are modified and new files intentionally implementing the production upgrades.
- If you want clean explorer state, commit is required.

## Manual Actions Required

- None required for compile/build.
- External deployment validation remains outside this repository:
  - confirm production env vars in Vercel/Render
  - confirm API key restrictions in Google Cloud Console
