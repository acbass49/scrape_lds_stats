# Project: LDS Church Statistics Dashboard

## Overview

This project scrapes and visualizes country- and state-level membership statistics from the LDS Church's official statistics pages. It produces a GitHub Pages-deployable interactive dashboard at `index.html`.

## Data Files

Located in `data/`:
- CSV files named by pull date (e.g., `country-2025-04-27.csv`, `state-2025-04-27.csv`)
- **File name = date scraped; data inside represents the previous calendar year** (e.g., `country-2019-11-21.csv` contains 2018 data, `country-2026-04-16.csv` contains 2025 data)
- Coverage: years 2011–2025 (14 data points per country/state; no 2020 data released)
- ~160 countries and all 50 U.S. states with 4 metrics: members, congregations, temples, stakes

### Current data files
| File | Coverage |
|------|---------|
| `country-2012-08-13.csv` | country data (2011) |
| `country-2013-07-25.csv` | country data (2012) |
| `country-2014-08-21.csv` | country data (2013) |
| `country-2015-08-13.csv` | country data (2014) |
| `country-2016-06-17.csv` | country data (2015) |
| `country-2017-06-22.csv` | country data (2016) |
| `country-2018-06-13.csv` | country data (2017) |
| `country-2019-11-21.csv` | country data (2018) |
| `country-2020-10-01.csv` | country data (2019) |
| `country-2022-04-28.csv` | country data (2021) |
| `country-2023-06-29.csv` | country data (2022) |
| `country-2024-07-23.csv` | country data (2023) |
| `country-2025-04-27.csv` | country data (2024) |
| `country-2026-04-16.csv` | country data (2025) |
| `state-2012-08-13.csv` | U.S. state data (2011) |
| `state-2013-07-25.csv` | U.S. state data (2012) |
| `state-2014-08-21.csv` | U.S. state data (2013) |
| `state-2015-08-13.csv` | U.S. state data (2014) |
| `state-2016-06-17.csv` | U.S. state data (2015) |
| `state-2017-06-22.csv` | U.S. state data (2016) |
| `state-2018-06-13.csv` | U.S. state data (2017) |
| `state-2019-11-21.csv` | U.S. state data (2018) |
| `state-2020-10-01.csv` | U.S. state data (2019) |
| `state-2022-04-28.csv` | U.S. state data (2021) |
| `state-2023-06-29.csv` | U.S. state data (2022) |
| `state-2024-07-23.csv` | U.S. state data (2023) |
| `state-2025-04-27.csv` | U.S. state data (2024) |
| `state-2026-04-16.csv` | U.S. state data (2025) |
| `temple-2024-07-23.csv` | temple data |
| `temple-2025-04-27.csv` | temple data |
| `social_count.csv` | social media follower counts |

## Key Files

| File | Purpose |
|------|---------|
| `index.html` | Main GitHub Pages dashboard (single-file, all data embedded) |
| `data/country_analysis.html` | Exploratory analysis — 8 KPI cards, 10 Chart.js charts |
| `data/congregation_losses.html` | Deep dive on 38 countries with net congregation losses 2018→2025 |
| `main.py` | Primary scraper (newsroom.churchofjesuschrist.org, 2019–present) |
| `wayback_scrape.py` | Wayback Machine scraper for newsroom.churchofjesuschrist.org snapshots |
| `mormonnewsroom_scrape.py` | Wayback Machine scraper for old mormonnewsroom.org domain (2011–2017 stats) |
| `followers_scrape.py` | **Out of scope — never fully working, ignore** |

## Python Environment

Use `.venv` for all Python work in this project:
```bash
source .venv/bin/activate
```
Do **not** create new venvs (e.g. `venv_test`) — use `.venv` exclusively.

## Scraper Overview

There are two historical scrapers covering different eras of the Church's statistics website:

### `wayback_scrape.py` — newsroom.churchofjesuschrist.org (2019–present domain)
Scrapes Wayback Machine snapshots of the current domain. Uses CSS selectors `.stat-line.one-fifth` and `.stat-line.w-graph` for both country and state pages.

### `mormonnewsroom_scrape.py` — mormonnewsroom.org (old domain, pre-2019)
Scrapes 7 snapshots covering **2011–2017 stats** (scrape dates 2012–2018). The old site had three different HTML structures across years, so the parser detects which to use:

| Years (data) | Scrape dates | HTML structure | Parser used |
|---|---|---|---|
| 2011–2017 states | all years | `.stat-line.one-fifth` + `.stat-line.w-graph` | Structure 0 |
| 2016–2017 countries | 2017–2018 snapshots | `div.stat-line` → `div.stat-block` (concatenated text) | Structure 1 |
| 2012–2015 countries | 2013–2016 snapshots | `div.FAS-country` → `h3.stat-num` / `p.stat-label` pairs | Structure 2 |
| 2011 countries | 2012 snapshot | `table.facts_stats_table` with label/value rows | Structure 3 |

**Important caveats for mormonnewsroom.org data:**
- **Stakes, Wards, Branches, Districts are all 0** — the old site did not publish these metrics at the country level
- State pages do include Stakes (via the `.stat-line.one-fifth` structure)
- State links are not linked from the US country page on the old site — they are constructed from a hardcoded slug list in `STATE_SLUGS`

### Rate limiting
Both scrapers use:
- `time.sleep(10)` between every page request
- `fetch_with_retry()` with 6 retries and exponential backoff starting at 60s (60, 120, 240, 480, 960s)
- 60s request timeout

Both scrapers resume automatically if interrupted (they check for existing CSVs and skip already-scraped rows).

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
