# Projected CRS Measurement

- Status: In progress

## Context

Every distance and area behind the current AL scores is computed on a local planar
approximation of geographic coordinates. Two build scripts carry the same constant block:

- `scripts/build_joint_analysis.py:18-20` — `LAT0 = radians(35.4465)`, `M_PER_DEG_LAT = 111_320.0`,
  `M_PER_DEG_LON = M_PER_DEG_LAT * cos(LAT0)`
- `scripts/build_multiscale_evidence.py:17-19` — the same three constants with `LAT0 = radians(35.446)`

`111_320.0` is the length of a degree of longitude at the equator. It is being used as the
length of a degree of latitude, where the GRS80 meridian arc at 35.4°N is approximately
110,941 m. North–south distance is therefore overstated by about 0.34% systematically, before
any error from the flat-plane assumption or from applying one latitude's scale factor across
both demo regions.

This is not a cosmetic inaccuracy. The scores are threshold classifiers, and the thresholds are
metric: 55 m corridor membership, 150 m road proximity and served-hub radius, 250 m served-hub
radius in the evidence build, 90 m roof matching. A feature whose true separation sits near a
threshold can be placed in the wrong band by an error the pipeline neither corrects nor records,
and the band is what the customer sees.

The limitation is already disclosed to users. `webapp/src/lib/audit.ts:687-691` tells every
reader that "the PoC uses a local planar approximation; production should use a suitable
projection and record error." Disclosure was the right interim move; it is not a fix, and the
disclosure text itself becomes wrong once the pipeline is corrected.

The original justification no longer holds. The module docstring at
`scripts/build_joint_analysis.py:5-6` says the script uses only the standard library "so that
the demo can be regenerated without a GIS stack". `pyproj>=3.6` has since become a default
dependency (`pyproject.toml:16`), installed unconditionally, and `scripts/fetch_mlit_foundation.py`
already reprojects with `fiona.transform`. The constraint that produced the approximation was
removed by a later change without the approximation being revisited.

## Decision

Compute all metric quantities in a projected CRS. Adopt **EPSG:6677** (JGD2011 / Japan Plane
Rectangular CS IX) as the single measurement CRS for the demo, transform once at load, measure in
metres, and keep EPSG:4326 as the only storage and delivery format.

Zone IX covers Kanagawa and Chiba, so both Yokohama and Mobara measure in the same zone. No
per-region zone selection is needed, and no cross-zone comparison problem is introduced.

The measurement CRS becomes a named, tested constant shared by both scripts rather than a
constant block copied into each. Regenerated outputs will differ from the committed ones; that
difference is the point, and it must be quantified in the PR rather than absorbed silently.

## Alternatives considered

### Keep the planar approximation and only correct `M_PER_DEG_LAT`

Rejected. Replacing 111,320 with 110,941 removes the largest single error term but leaves the
flat-plane assumption, the single-latitude scale factor applied across both regions, and the
absence of any recorded error bound. It would also produce a second set of magic constants that
a reader cannot verify against any authority.

### Implement a transverse Mercator projection in the standard library

Rejected. It preserves a property — regeneration without a GIS stack — that the project already
gave up when `pyproj` became a default dependency. Hand-rolling a projection to satisfy a
constraint nothing enforces adds roughly forty lines of unreviewable numerical code and a second
source of truth for a transformation `pyproj` already performs correctly.

### Measure with a geodesic solver instead of a projected CRS

Rejected for this refactor. `pyproj.Geod` gives exact ellipsoidal distances between point pairs,
but the pipeline also needs point-to-segment distance, polygon area, and buffer-like radius tests.
Those are natural in a projected plane and awkward geodesically. Zone IX scale distortion over the
demo extents is far below the classification thresholds at stake.

### Reproject the stored GeoJSON to EPSG:6677

Rejected. RFC 7946 mandates CRS84 for GeoJSON, the frontend and deck.gl consume WGS84, and the
tile scheme is Web Mercator. Projection belongs inside the computation, not in the storage format.

## Scope

- One shared measurement module exposing the target CRS, a forward transform, and metric
  distance/area helpers.
- `scripts/build_joint_analysis.py` and `scripts/build_multiscale_evidence.py` migrated onto it.
- An inventory of every committed value whose magnitude changes, with the change quantified.
- Regenerated `joint` and `evidence` task outputs.
- Audit provenance text updated to describe what the pipeline now does.

## Non-goals

- No change to any threshold, weight, or scoring formula. This refactor changes how a distance is
  measured, not what is done with it.
- No vertical datum, elevation, or 3D work. Depth and height belong to the underground refactor.
- No reprojection of stored or delivered GeoJSON.
- No new analysis, module, or view.
- No change to the MLIT ingest path, which already transforms correctly.

## Consequences

- Published distances, areas, and any band derived from them become defensible against an
  independent GIS check. Today they are not.
- Some features will change band. The count is the headline result of the PR and must appear in
  its description.
- The audit drawer stops telling users the numbers are approximate, because they no longer are.
  Removing that sentence is only honest after the outputs are regenerated, so the copy change and
  the data change ship together.
- The two build scripts gain a real dependency on `pyproj`. That dependency is already installed
  by default; the stale stdlib-only claim in the docstrings is removed rather than worked around.

## Delivery plan

- [01-projected-measurement-pr1.md](01-projected-measurement-pr1.md): move both build scripts onto
  a projected measurement module, regenerate outputs, and quantify what moved.
