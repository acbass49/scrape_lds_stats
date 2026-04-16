# Project: LDS Church Statistics Dashboard

## Overview

This project scrapes and visualizes country- and state-level membership statistics from the LDS Church's official statistics pages. It produces a GitHub Pages-deployable interactive dashboard at `index.html`.

## Data Files

Located in `data/`:
- CSV files named by pull date (e.g., `country-2025-04-27.csv`, `state-2025-04-27.csv`)
- File name = date data was pulled; **data inside reflects the prior year**
- Coverage: years 2018–2025 (7 data points per country/state)
- ~160 countries and all 50 U.S. states with 4 metrics: members, congregations, temples, stakes

### Current data files
| File | Coverage |
|------|---------|
| `country-2019-11-21.csv` | country data |
| `country-2020-10-01.csv` | country data |
| `country-2022-04-28.csv` | country data |
| `country-2023-06-29.csv` | country data |
| `country-2024-07-23.csv` | country data |
| `country-2025-04-27.csv` | country data |
| `country-2026-04-16.csv` | country data |
| `state-2019-11-21.csv` | U.S. state data |
| `state-2020-10-01.csv` | U.S. state data |
| `state-2022-04-28.csv` | U.S. state data |
| `state-2023-06-29.csv` | U.S. state data |
| `state-2024-07-23.csv` | U.S. state data |
| `state-2025-04-27.csv` | U.S. state data |
| `state-2026-04-16.csv` | U.S. state data |
| `temple-2024-07-23.csv` | temple data |
| `temple-2025-04-27.csv` | temple data |
| `social_count.csv` | social media follower counts |

## Key Files

| File | Purpose |
|------|---------|
| `index.html` | Main GitHub Pages dashboard (single-file, all data embedded) |
| `data/country_analysis.html` | Exploratory analysis — 8 KPI cards, 10 Chart.js charts |
| `data/congregation_losses.html` | Deep dive on 38 countries with net congregation losses 2018→2025 |
| `main.py` | Primary scraper |
| `followers_scrape.py` | **Out of scope — never fully working, ignore** |

## Dashboard Architecture (`index.html`)

Single HTML file with all data embedded as JSON. Deployed to GitHub Pages. Dark theme (`--bg:#0f1117`).

### CDN Dependencies
```html
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
```
Analytics via GoatCounter (`acbass49.goatcounter.com`).

### Data Structures
```js
const DATA = {
  "Albania": { m:[...], c:[...], t:[...], s:[...] },
  // ~160 countries × 7 years × 4 metrics
  // m = members, c = congregations, t = temples, s = stakes
}

const STATE_DATA = {
  "Utah": { m:[...], c:[...], t:[...], s:[...] },
  // 50 U.S. states × 7 years × 4 metrics
}
```

### Three-View Layout

**World view** (`#world-view`) — the default landing view. Has four sub-tabs:
- **Countries** — D3 choropleth world map + global KPIs and trend charts. Click country → `selectCountry(name)`
- **U.S. States** — D3 choropleth U.S. map + U.S. aggregate KPIs and trend charts. Click state → `selectState(name)`
- **World Regions** — bar charts comparing absolute/% change by geographic region
- **U.S. State Regions** — bar charts comparing absolute/% change by U.S. census region

**Country view** (`#country-view`) — per-country drill-down. "← World" button → `showWorld()`

**State view** (`#state-view`) — per-U.S.-state drill-down. "← U.S. States" button → `showStates()`

**Nav title** is clickable (cursor:pointer) and always returns to the world view via `showWorld()`.

Both world maps use the same color scale: red (−20%) → yellow (0%) → green (+20%/+100%) based on membership % change over the selected year range. A year-range selector in the nav controls start/end years.

### Key Functions

**`buildMap()`** — D3 choropleth world map with ISO 3166-1 numeric codes via `N2I` mapping object

**`buildUSMap()`** — D3 choropleth U.S. state map

**`setWorldView(view)`** — switches between the four world-view sub-tabs (`'country'`, `'states'`, `'region'`, `'us-region'`)

**`selectCountry(name)`** — hides world view, shows country view; builds KPIs, trend charts, spaghetti charts, density charts, and rule-based summary

**`selectState(name)`** — hides world view, shows state view; same structure as country view but for U.S. states

**`showWorld()`** — returns to world view from any drill-down

**`showStates()`** — returns to world view (U.S. States tab) from state drill-down

**`mkDensity(canvasId, noteId, allVals, selVal, unit, nPoints)`** — KDE density chart
- Gaussian kernel with Silverman's bandwidth: `1.06 * std * n^(-0.2)`
- Display clipped to 1st–99th percentile + bandwidth padding
- Vertical dashed annotation line at selected country/state value (chartjs-plugin-annotation)
- Label shows value + percentile (e.g., "7.5% · 62nd %ile")

**`buildCountrySummary(name, d)`** — Generates 3–4 sentence rule-based summary:
- s1: membership size + growth trend
- s2: congregation analysis (diverging from members / both declining / fast growth / stable / growing)
- s3: temple milestone (only when noteworthy: first temple, count increase, multiple temples)
- s4: **Always present** — activity level from members-per-congregation ratio
  - `>900`: quite low activity, nominally on rolls
  - `650–900`: below average activity
  - `450–650`: broadly typical (~global avg of ~555)
  - `250–450`: above average activity
  - `<250`: notably small, highly active units

**`buildStateSummary(name, d)`** — same structure as country summary but adapted for U.S. states

**`CHARTS`** object — tracks all Chart.js instances; `mkChart()` helper destroys before recreating to prevent canvas reuse errors

**`toggleSpaghettiFilter(prefix)`** — checkbox toggle to show only the selected country/state in spaghetti charts (hides all gray background lines)

### Search
The nav search bar (`#search`) covers both countries and U.S. states. Results show a `(US state)` badge for states. Selecting a result calls `selectCountry()` or `selectState()` accordingly.

### Stale Data Warning
Country view shows a callout (`#c-stale-warning`) when the two most recent data points are identical, indicating the Church website hasn't updated yet.

## Known Data Quirks

- **"United States"**: 2025 file uses "United States of America" — normalized to "United States" during extraction
- **"Réunion"**: Unicode accent caused duplicate entries — normalized to "Reunion"
- **All-zero countries** (e.g., Andorra, China): Treated as no-data, stored as `[null]*7`
- Countries/states with `null` values are excluded from density chart calculations

## Regenerating Data

To re-extract embedded JSON from CSVs, use a Python heredoc (not `-c` flag — multi-line strings cause shell parse errors):
```bash
python3 << 'EOF'
import csv, json, glob
# ... extraction logic
EOF
```
