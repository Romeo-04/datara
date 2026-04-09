# STAR Regional Intelligence System
### START a Ton Challenge — DOST-SEI STAR Program

---

## What the System Does

The STAR Regional Intelligence System is a decision-support platform that transforms fragmented teacher, school, and training records into actionable regional intelligence for STAR capacity-building planners.

It answers three questions that STAR managers need most:

1. **Where** — Which regions and divisions need support most urgently?
2. **Why** — What specific capacity gaps are driving that need?
3. **What** — What type of STAR intervention should be deployed there?

---

## Features and Functionality

### 1. National Dashboard
- Displays national-level statistics at a glance: total divisions, critical count, high priority count, average mismatch rate, and average NAT MPS
- Shows a **UAI bar chart** of the top 20 most underserved divisions, color-coded by priority tier
- Shows a **regional capacity heatmap table** — all 17 regions with heat-colored columns for mismatch rate, training gap, geographic disadvantage, and NAT MPS
- Shows a **division card grid** of the top 15 most underserved divisions with mini factor bars and intervention badge

### 2. Philippines Map (`/map`)
- Full interactive **Leaflet map** centered on the Philippines
- Each of the 17 regions is plotted as a **color-coded circle marker**:
  - Red = Critical Priority (UAI ≥ 0.65)
  - Amber = High Priority (UAI 0.40–0.65)
  - Green = Standard Priority (UAI < 0.40)
- Circle size scales with total teacher count in the region
- Clicking a region circle opens a **popup** showing avg UAI score, priority label, division count, critical count, teacher count, mismatch rate, and NAT MPS, with a link to the region detail page
- **Zooming in to level 8+** reveals individual division dots, each clickable with a popup linking to the division detail page
- **Right side panel** shows:
  - National tier count summary (Critical / High / Standard)
  - Top 10 critical divisions with UAI mini-bars
  - All 17 regions ranked by average UAI score

### 3. Division List (`/divisions`)
- Paginated list of all 86 divisions ranked by Underserved Area Index
- **Filters**: search by name, filter by region, filter by priority tier
- Each division card shows: region, priority tier badge, UAI score, mismatch/training gap/geo factor bars, intervention type badge, teacher and school counts

### 4. Division Detail (`/divisions/[name]`)
- Full breakdown for a single division
- **UAI Factor Breakdown** — weighted bar for each of the 5 factors showing its normalized score and contribution to the total UAI
- **Gap Profile Radar chart** — spider/radar visualization of the 5 normalized factor scores
- **System Explanation** — plain-language sentence explaining why the division ranked where it did and what the top contributing factors are
- **Recommended STAR Intervention** — the specific intervention type with description, delivery mode, and target group
- **Capacity Metrics grid** — mismatch rate, training gap, novice rate, avg experience, learner-teacher ratio, geographic disadvantage score, and NAT MPS, with red highlighting for values that exceed alert thresholds
- Privacy notice confirming all data is aggregated at division level

### 5. Region Overview (`/regions`)
- Table of all 17 regions with heat-colored columns for mismatch rate, training gap, novice rate, geographic disadvantage, and NAT MPS
- Color intensity is relative to the national distribution (not fixed thresholds), so the worst-performing regions stand out clearly

### 6. Region Detail (`/regions/[name]`)
- Region-level summary metrics: total teachers, total schools, average mismatch rate, average training gap, average NAT MPS
- Alert banner if any divisions within the region are flagged as Critical Priority
- **UAI bar chart** showing all divisions within the region by score
- Division card grid of all divisions in the region ranked by priority

### 7. Dataset Upload (`/upload`)
- STAR managers can upload their own CSV datasets through a **drag-and-drop or file browser interface**
- Supports four file types: `teachers.csv`, `schools.csv`, `training_logs.csv`, `nat_scores.csv`
- Each file slot shows required columns and all columns in collapsible panels
- Files not uploaded fall back to the existing dataset automatically
- On submit: files are validated, saved, the full 6-module pipeline re-runs, and the API data store reloads — **no server restart needed**
- Results panel shows row counts per uploaded file, new division/region counts, critical division count, and mismatch rate
- Direct links to the refreshed dashboard and map after upload

---

## Underserved Area Index (UAI)

The UAI is the core scoring mechanism. It is a **transparent, weighted composite score** computed per division from five factors:

| Factor | Weight | What it measures |
|---|---|---|
| Specialization Mismatch Rate | 30% | % of teachers teaching outside their major/specialization |
| Training Coverage Gap | 25% | % of teachers with fewer than 2 STAR trainings |
| Geographic Disadvantage | 20% | Isolation score based on remoteness, island location, or conflict-affected status |
| Staffing Pressure (LTR) | 15% | Average learner-to-teacher ratio |
| Learning Outcome Gap (NAT) | 10% | Inverse of NAT Mean Percentage Score in Science and Math |

Each factor is normalized to [0, 1] before weighting. The UAI score ranges from 0 to 1, where 1 is the most underserved. Divisions are then ranked nationally and grouped into three tiers: **Critical Priority**, **High Priority**, and **Standard Priority**.

---

## Intervention Recommendation Logic

The system maps each division's dominant gap factors to one of five STAR intervention types using rule-based logic:

| Intervention | Triggered when |
|---|---|
| Comprehensive STAR Support Package | UAI ≥ 0.65 with 3 or more dominant factors |
| Blended / Asynchronous Learning Program | Geographic disadvantage is the dominant factor |
| Specialization Upskilling Program | Mismatch rate is the dominant factor |
| Mobile Training Deployment | Training coverage gap is the dominant factor |
| In-School Coaching and Mentoring | Staffing pressure or high novice rate is dominant |

---

## Privacy Design

The system processes teacher-level records internally but **never exposes individual teacher data in any output**. The privacy boundary is enforced at the pipeline level:

```
Module 2 (Teacher Profiler)       Module 3 (Regional Aggregator)
Per-teacher flags computed    →   Division-level percentages only
  is_mismatched: true               mismatch_rate: 0.43
  has_training_gap: true            training_gap_rate: 0.61
  _support_need_score: 2        ← this column is never written to disk
```

By the time data reaches the API or the frontend, the smallest visible unit is a **division**.

---

## System Architecture

### Overview

```
RAW DATA (CSVs)
    │
    ▼
PIPELINE (Python)          — runs once, or on each upload
    │
    ▼
PROCESSED DATA (JSON)      — division_intelligence.json, region_summary.json
    │
    ▼
API (FastAPI)              — serves, filters, paginates; no computation at request time
    │
    ▼
FRONTEND (Nuxt 3 / Vue 3) — SSR pages, interactive charts, Leaflet map
    │
    ▼
BROWSER
```

### Data Flow Through the Pipeline

```
[1] ingest.py
    Load CSVs → validate columns → normalize text → flag bad data

[2] teacher_profiler.py        ← backend only
    Per-record: subject vs. specialization match, training gap, experience band

[3] regional_aggregator.py
    Group by division → compute rates, averages, geo scores
    Group by region   → include avg UAI score after step [4]

[4] uai_engine.py
    Normalize each factor → weighted composite UAI score → rank → tier

[5] intervention_recommender.py
    Match dominant factor profile → assign STAR intervention type

[6] explainer.py
    Generate plain-language explanation per division

Output → division_intelligence.json + region_summary.json
```

---

## Technology Stack

### Backend

| Technology | Role |
|---|---|
| **Python 3.12** | Core language for all pipeline and API code |
| **pandas** | Data loading, cleaning, transformation, aggregation |
| **numpy** | Normalization and numerical operations |
| **scikit-learn** | (Available) for future ML-based scoring extensions |
| **FastAPI** | REST API framework — lightweight, async, auto-generates Swagger docs |
| **Pydantic v2** | Request/response schema validation |
| **python-multipart** | Multipart form parsing for CSV file uploads |
| **uvicorn** | ASGI server for running FastAPI |

### Frontend

| Technology | Role |
|---|---|
| **Nuxt 3** | Full-stack Vue framework — SSR, file-based routing, Nitro server |
| **Vue 3** | Component framework with Composition API |
| **TypeScript** | Type safety across all components, composables, and API calls |
| **Tailwind CSS** | Utility-first styling via `@nuxtjs/tailwindcss` |
| **Chart.js + vue-chartjs** | Bar charts (UAI rankings) and Radar charts (factor profiles) |
| **Leaflet + @types/leaflet** | Interactive Philippines map with region and division markers |
| **Nitro proxy** | Routes `/api/**` → `http://localhost:8000` for both SSR and client fetches |

### Data

| Format | Purpose |
|---|---|
| **CSV** | Raw input — teachers, schools, training logs, NAT scores |
| **JSON** | Processed output served by the API — division and region intelligence |
| **In-memory store** | FastAPI loads JSON at startup; reloads without restart after upload |

### Key Architectural Decisions

| Decision | Rationale |
|---|---|
| Pipeline outputs to JSON files | Decouples computation from API — pipeline can re-run without touching the server |
| Nuxt Nitro proxy | Eliminates the SSR URL problem — both server and browser use the same `/api/**` path |
| `.client.vue` suffix for charts | Chart.js and Leaflet require browser APIs — Nuxt skips these on the server automatically |
| `useAsyncData` for data fetching | Fetches on the server during SSR, deduplicates on client hydration — no loading flicker |
| Rule-based recommender | Transparent, explainable, auditable — no black-box model for a planning tool |
| UAI weights are documented | Planners can audit and adjust weights; system is not opaque |

---

## Running the System

### Prerequisites
- Python 3.12+
- Node.js 18+

### Step 1 — Generate data and run pipeline
```
start_pipeline.bat
```
Or manually:
```bash
python data/synthetic/generate_data.py
python -m backend.pipeline.run_pipeline
```

### Step 2 — Start the backend (Terminal 1)
```
start_backend.bat
```
API available at: `http://localhost:8000`
Swagger docs at: `http://localhost:8000/docs`

### Step 3 — Start the frontend (Terminal 2)
```
start_frontend.bat
```
Dashboard available at: `http://localhost:3000`

---

## Project Structure

```
StartATon/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py          # 7 REST endpoints
│   │   │   └── upload.py          # CSV upload + pipeline trigger
│   │   ├── core/
│   │   │   └── data_store.py      # In-memory JSON loader
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic response schemas
│   │   └── main.py                # FastAPI app entrypoint
│   └── pipeline/
│       ├── ingestion/ingest.py         # Module 1
│       ├── profiler/teacher_profiler.py # Module 2
│       ├── aggregator/regional_aggregator.py # Module 3
│       ├── uai/uai_engine.py           # Module 4
│       ├── recommender/intervention_recommender.py # Module 5
│       ├── explainer/explainer.py      # Module 6
│       └── run_pipeline.py             # Pipeline runner
├── frontend/
│   ├── components/
│   │   ├── charts/
│   │   │   ├── UAIBar.client.vue       # Bar chart
│   │   │   ├── FactorRadar.client.vue  # Radar chart
│   │   │   └── RegionHeatmap.vue       # Heat table
│   │   ├── dashboard/
│   │   │   └── DivisionCard.vue        # Division summary card
│   │   ├── map/
│   │   │   └── PhilippinesMap.client.vue # Leaflet map
│   │   └── ui/
│   │       ├── StatCard.vue
│   │       ├── TierBadge.vue
│   │       └── InterventionBadge.vue
│   ├── composables/
│   │   ├── useApi.ts               # API call wrappers
│   │   └── useUtils.ts             # Formatting and color helpers
│   ├── pages/
│   │   ├── index.vue               # Dashboard
│   │   ├── map/index.vue           # Philippines map
│   │   ├── divisions/index.vue     # Division list
│   │   ├── divisions/[name].vue    # Division detail
│   │   ├── regions/index.vue       # Region list
│   │   ├── regions/[name].vue      # Region detail
│   │   └── upload/index.vue        # Dataset upload
│   ├── types/index.ts              # TypeScript interfaces
│   ├── app.vue                     # Root layout + navigation
│   └── nuxt.config.ts              # Nuxt + Nitro proxy config
├── data/
│   ├── synthetic/                  # Generated or uploaded raw CSVs
│   └── processed/                  # Pipeline output JSON (served by API)
├── start_backend.bat
├── start_frontend.bat
└── start_pipeline.bat
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/stats` | National summary statistics |
| GET | `/api/v1/divisions` | Paginated, filterable division list |
| GET | `/api/v1/divisions/top?n=N` | Top N most underserved divisions |
| GET | `/api/v1/divisions/{name}` | Full detail for one division |
| GET | `/api/v1/regions` | All regions with aggregated metrics |
| GET | `/api/v1/regions/{name}/divisions` | All divisions within a region |
| GET | `/api/v1/interventions/{key}/divisions` | Divisions by intervention type |
| GET | `/api/v1/upload/schema` | Column requirements for upload form |
| POST | `/api/v1/upload` | Upload CSVs, re-run pipeline, reload data |

---

*STAR Regional Intelligence System — START a Ton Challenge — DOST-SEI STAR Program*
