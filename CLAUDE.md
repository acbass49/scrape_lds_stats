# Project: LDS Church Statistics Dashboard

## Overview

This project scrapes and visualizes country-level membership statistics from the LDS Church's official statistics pages. It produces a GitHub Pages-deployable interactive dashboard at `index.html`.

## Data Files

Located in `data/`:
- 7 CSV files named by pull date (e.g., `2025-01-xx_country_data.csv`)
- File name = date data was pulled; **data inside reflects the prior year**
- Coverage: years 2018–2025 (7 data points per country)
- ~160 countries with 4 metrics: members, congregations, temples, stakes

## Key Files

| File | Purpose |
|------|---------|
| `index.html` | Main GitHub Pages dashboard (single-file, all data embedded) |
| `data/country_analysis.html` | Exploratory analysis — 8 KPI cards, 10 Chart.js charts |
| `data/congregation_losses.html` | Deep dive on 38 countries with net congregation losses 2018→2025 |
| `main.py` | Primary scraper |
| `followers_scrape.py` | **Out of scope — never fully working, ignore** |

## Dashboard Architecture (`index.html`)

Single HTML file with all data embedded as JSON. Deployed to GitHub Pages.

### CDN Dependencies
```html
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
```

### Data Structure
```js
const DATA = {
  "Albania": { m:[...], c:[...], t:[...], s:[...] },
  // 160 countries × 7 years × 4 metrics
  // m = members, c = congregations, t = temples, s = stakes
}
```

### Two-View Layout
- **World view**: D3 choropleth map (Natural Earth projection) + global trend charts
  - Color scale: red (−25%) → yellow (0%) → green (+100%) based on membership % change
  - Click a country → triggers `selectCountry(name)`
- **Country view**: Per-country drill-down with summary, KPIs, trend charts, density charts

### Key Functions

**`buildMap()`** — D3 choropleth with ISO 3166-1 numeric codes via `N2I` mapping object

**`mkDensity(canvasId, noteId, allVals, selVal, unit, nPoints)`** — KDE density chart
- Gaussian kernel with Silverman's bandwidth: `1.06 * std * n^(-0.2)`
- Display clipped to 1st–99th percentile + bandwidth padding
- Vertical dashed annotation line at selected country's value (chartjs-plugin-annotation)
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

**`selectCountry(name)`** — Orchestrates country view: hides world view, shows country view, builds KPIs/trends/distributions/summary

**`CHARTS`** object — Tracks all Chart.js instances; `mkChart()` helper destroys before recreating to prevent canvas reuse errors

## Known Data Quirks

- **"United States"**: 2025 file uses "United States of America" — normalized to "United States" during extraction
- **"Réunion"**: Unicode accent caused duplicate entries — normalized to "Reunion"
- **All-zero countries** (e.g., Andorra, China): Treated as no-data, stored as `[null]*7`
- Countries with `null` values are excluded from density chart calculations

## Regenerating Data

To re-extract embedded JSON from CSVs, use a Python heredoc (not `-c` flag — multi-line strings cause shell parse errors):
```bash
python3 << 'EOF'
import csv, json, glob
# ... extraction logic
EOF
```
