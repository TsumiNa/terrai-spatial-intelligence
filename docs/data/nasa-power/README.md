# NASA POWER Solar-Climatology Data

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated and cached
- Variable: `ALLSKY_SFC_SW_DWN`
- Climatology period: 2001–2020

## Data description

- **Format** — JSON returned by the NASA POWER climatology API, cached into `data/mobara/solar_summary.json`. It is a point query, not a raster download.
- **Variable** — `ALLSKY_SFC_SW_DWN`: all-sky surface shortwave downward irradiance, i.e. global horizontal irradiance (GHI).
- **Units and cached values** — the API returns kWh/m²/day. The cache stores `daily_ghi_kwh_m2` = 3.7747, `annual_ghi_kwh_m2` = 1,378, and a twelve-entry `monthly_ghi` breakdown.
- **Temporal coverage** — a 2001–2020 climatology, i.e. a twenty-year average, not any individual year.
- **Spatial granularity** — POWER serves a global reanalysis grid of roughly 0.5° latitude × 0.625° longitude. One grid cell covers the entire Mobara demo area, so the value does not vary across the site.
- **Volume** — one queried point, yielding twelve monthly values plus an annual mean.
- **Known gaps** — a single grid cell carries no intra-site variation, so it cannot distinguish one candidate cell from another. Climatological means are not P50/P90 production estimates, and the value excludes shading, terrain, orientation, temperature, soiling, and equipment losses.

## Source

NASA POWER Climatology API: https://power.larc.nasa.gov/docs/services/api/temporal/climatology/

## Use in this project

Provides long-term regional solar-resource context for Mobara; current annual mean GHI is about 1,378 kWh/m². It does not enter per-cell energy-yield modeling and cannot replace equipment, shading, orientation, temperature, or loss models.

## License

NASA data is generally not subject to US copyright, but check product-specific notices and provide appropriate credit. Do not use NASA marks or imply endorsement without permission.

## Commercial-use cautions

Commercial reports should state variable, climatology period, spatial scale, and retrieval date. Climate means are not project-level P50/P90 production estimates or finance-grade guarantees. Revalidate units, missingness, and bias before integrating finer time series.
