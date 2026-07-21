# KuniJiban Boreholes

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated as an on-demand, user-supplied regional extract
- Publisher/source system: MLIT, PWRI, PARI / KuniJiban
- Dataset/API key: `kunijiban_borehole` / `kunijibanBoreholes`

## Data description

- **Format and structure:** three Apache Parquet files: one nested row per borehole, one flat row per stratigraphic layer, and one flat row per SPT test. `data/external/kunijiban_borehole/manifest.json` records assets, byte sizes, SHA-256 hashes, timestamps, counts, and provenance classes.
- **Coverage and CRS:** a user-supplied regional selection from KuniJiban, not complete national coverage. Horizontal coordinates are WGS 84 longitude/latitude (`EPSG:4326`). Elevations are metres but their vertical datum is source-dependent and has not been normalized; harbour or river records may use a local datum. The supplied package does not define an authoritative bounding box.
- **Granularity and volume:** 12,067 boreholes, 122,693 stratigraphic intervals, and 239,137 SPT observations. The three Parquet assets total 12,010,681 bytes.
- **Vintage:** the integration run completed on 2026-06-27 and is recorded as `retrieved_at=2026-06-27T13:04:00+09:00`. There is no single publisher snapshot date; boreholes originate from investigations conducted at different times. KuniJiban may correct records without notice.
- **Key fields and units:** borehole ID, location, source class, latitude/longitude in decimal degrees, ground elevation in metres, total drilled depth and groundwater depth in metres, stratigraphic base depth in metres, raw Japanese layer name/symbol, normalized layer category, SPT depth in metres, and SPT N-value as a blow count. The nested table also retains source or synthetic XML for audit.
- **Provenance:** 6,462 boreholes are parsed from source JGS XML, 5,241 are reconstructed from column-diagram PDFs by a VLM, and 364 PDF records contain no usable stratigraphy. `data_source` must remain attached to every record; VLM-extracted fields are not source observations.
- **Known gaps:** elevation is absent for 86 boreholes, groundwater is populated for 6,030, and 364 records have zero layers. Survey purpose, precision, units in legacy tests, elevation datum, and freshness vary. SPT values above 100 require review; the reported maximum of 794 is an apparent source outlier.

## Source

- [KuniJiban](https://www.kunijiban.pwri.go.jp/)
- [Official terms](https://www.kunijiban.pwri.go.jp/jp/terms.html)
- [Official use cautions](https://www.kunijiban.pwri.go.jp/jp/attention.html)

The package was supplied by the project owner after targeted retrieval from the interactive KuniJiban service. KuniJiban removed bulk-download functionality in 2019. `Full_Pipeline_Run_Report.md` documents the integration run, field mappings, missingness, and VLM-derived subset. The extraction scripts and upstream PDFs/XML are not part of this repository, so the current snapshot is not automatically reproducible from source.

## Use in this project

This dataset is subsurface Foundation Data Layer evidence. `GET /api/v1/catalog` exposes its readiness and borehole count; `GET /api/v1/datasets/kunijibanBoreholes` returns the audit manifest. The three Parquet files are available on demand below `/api/v1/assets/external/kunijiban_borehole/` and are not loaded into the exhibition bootstrap.

The current FastAPI service catalogs and serves the assets but does not query Parquet rows. Future SL models may use source-qualified layers and SPT records to estimate missing geotechnical parameters. AL modules must preserve `data_source`, survey-time limitations, and unresolved vertical datum rather than treating the extract as a current site investigation.

## License

KuniJiban's terms permit searching, downloading, viewing, copying, modifying, distributing, lending, and selling the ground information under their stated conditions. When information is provided to third parties, it must be identified as KuniJiban ground information, and users must not assert copyright over the source ground information.

## Commercial-use cautions

Retain visible KuniJiban attribution and link to the terms. Clearly distinguish source-XML records from VLM-extracted PDF reconstructions and validate model-extracted values against the source before consequential use. KuniJiban warns that groundwater and test values describe survey-time conditions, precision varies by investigation, records are not necessarily checked against originals, older values may not use SI units, and records may change without notice. Do not use this regional extract alone for design, construction, excavation, safety, or regulatory decisions. Review any separate terms that applied to the VLM used during extraction. This card is a data-governance summary, not legal advice.
