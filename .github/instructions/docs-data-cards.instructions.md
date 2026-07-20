---
description: 'Use when adding, editing, or reviewing a dataset card under docs/data/. Defines the required sections of a Foundation Data Layer dataset card, including the description of the data itself: format, coverage, resolution, vintage, fields, units, and known gaps.'
name: 'Dataset Cards'
applyTo: 'docs/data/**'
---

# Dataset Cards

Every dataset integrated into the Foundation Data Layer gets one card at `docs/data/<dataset>/README.md`, with `README.ja.md` and `README.zh.md` partners maintained in the same change. `docs/data/README.*` is the catalog and the only Markdown allowed directly under `docs/data/`.

A dataset that has been evaluated but **not** integrated does not get a card. It belongs in an evaluation under `docs/summary/`.

## Required sections, in this order

1. `## Data description` (`## データの内容` / `## 数据内容`)
2. `## Source` (`## 出典` / `## 来源`)
3. `## Use in this project` (`## 本 project での利用` / `## 在本项目中的使用`)
4. `## License` (identical heading in all three languages)
5. `## Commercial-use cautions` (`## 商用利用時の注意` / `## 商业使用注意`)

The repository's documentation validation checks that all five headings exist in all three language files. It cannot check that the content is correct — that is on the author.

## `## Data description` — describe the data, not its paperwork

This section answers "what *is* this data?" before the card explains where it came from and how the project uses it. Source, licence, and usage belong in the later sections; do not answer them here.

State every point below that applies to the dataset. Omit a bullet only when it genuinely does not apply, not when it is merely inconvenient to look up:

- **Format and structure** — raster/vector/tabular/time series, file format, and how records are organised (e.g. "64-band Cloud Optimized GeoTIFF", "CSV with a six-row metadata preamble").
- **Spatial coverage and CRS** — the publisher's full extent, the subset this project caches, and the coordinate reference system with its EPSG code.
- **Resolution or granularity** — grid spacing, zoom levels, or the real-world entity one record represents.
- **Temporal coverage and vintage** — observation period, snapshot date, or climatology window, plus the publisher's update cadence.
- **Key fields or variables with units** — name the fields the project actually reads, with units. Do not write "various attributes".
- **Volume as cached here** — record or tile counts for the local snapshot, so a reader can tell a demo subset from a full extract.
- **Known gaps and quality caveats** — missingness, encodings that trip up naive readers, completeness that is not guaranteed, resolution that does not support a use the reader might assume.

Prefer concrete numbers over adjectives. "628 facility rows, Shift-JIS (CP932) encoded" is a description; "a moderately sized dataset" is not.

Keep the three language versions factually identical. Numbers, units, EPSG codes, field names, and file paths must match exactly across `README.md`, `README.ja.md`, and `README.zh.md`; only prose wording differs.

## Front matter

Immediately under the title and language navigation, keep a short bullet list carrying the card's at-a-glance facts — at minimum `FL status`, plus the one or two identifiers that distinguish this dataset (publisher, resolution, variable, product version). Details go in `## Data description`; the front matter is a summary, not a substitute.

## When the data changes

Re-read the card whenever a pipeline that consumes the dataset changes. Field lists, record counts, and vintages in `## Data description` are the parts most likely to go stale silently — validation checks that the section exists, never that its numbers are still true.
