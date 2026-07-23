# Basemap View Modes and 2.5D

- Status: Planned

## Context

Today the map has four basemaps (`standard`, `photo`, `hillshade`, `slope`) and
the 2.5D surface (`setTerrain` over the GSI DEM) is **hard-tied to the hillshade
basemap** — selecting hillshade both drapes the shaded-relief raster and tilts
into 3D, and no other basemap can be viewed in 3D. `setTerrain` is in fact
**orthogonal** to which raster is shown (it displaces the mesh; any layer drapes
over it), so the coupling is a UX choice, not a constraint.

The owner has settled a cleaner model: a smaller basemap set, an explicit **2.5D
toggle** decoupled from the basemap, per-mode 2.5D behaviour, and an automatic
colour-by-height tint in the hillshade mode that is meaningful at wide zoom and
fades away as the view goes local.

## Decision

**Basemap set — drop `slope`.** Keep `standard`, `photo` (imagery), and
`hillshade` (起伏). The slope raster (傾斜量図) view mode is removed. Note this is
the slope **basemap** only; the building **slope-risk analysis**
(`interactive-al-compute`, computed from DEM materials and carried on the
buildings) is a different thing and is unaffected.

**2.5D is a toggle on the map, decoupled from the basemap.** A switch button
placed on the map turns 2.5D on/off for whichever basemap is active. Its effect
is per-mode:

| Basemap | 2.5D off | 2.5D on |
| --- | --- | --- |
| `standard` | flat, top-down | **perspective only** (pitch), **no 3D terrain** |
| `photo` | flat, top-down | perspective **+ 3D terrain** (`setTerrain`) |
| `hillshade` | flat, top-down | perspective **+ 3D terrain** (`setTerrain`) |

Standard stays a clean flat cartographic map even tilted — a 3D-terrain-warped
vector standard map reads as noise, so it gets the viewing angle without the
geometry. Photo and hillshade are the modes where real relief adds meaning
(imagery on terrain = the Google-Earth read; hillshade on terrain = doubled,
legible relief), so they get the DEM surface automatically when 2.5D is on.

**Hillshade gains an automatic colour-by-height tint, zoom-faded.** In hillshade
mode a hypsometric colour-elevation layer (GSI's 色別標高図 `relief` tiles, or an
equivalent elevation tint) is drawn over the shaded relief, with **zoom-driven
opacity**: strong at low zoom, fading toward transparent as the user zooms in,
and the layer hidden entirely past a threshold. Colour-by-height reads the
region's elevation structure at a wide view; once the view is local it says
nothing useful and would only muddy the hillshade, so it removes itself. This is
tied to the hillshade mode and to zoom, independent of the 2.5D toggle (so wide
hillshade is coloured relief whether flat or tilted; when 2.5D is on and the
terrain is up, wide zoom shows coloured 3D relief).

## Rationale

- **Decoupling 2.5D from the basemap** is the generalisation already noted while
  designing the tiles: `setTerrain` displaces geometry and every layer drapes over
  it, so binding 3D to one basemap was arbitrary. A toggle lets the user read any
  mode flat or tilted.
- **Per-mode terrain** matches where relief helps: photo/hillshade yes, standard
  no (warping vector cartography is noise, not information).
- **Removing slope** trims a mode whose job (steepness) is better served, in this
  product, by the building slope-risk analysis on the buildings themselves.
- **Zoom-faded height tint** puts colour-by-height only where it means something
  (regional overview) and takes it away where it does not (local), the same
  "wide-view-only" logic the owner set.

## Non-goals

- No self-hosting of any raster — imagery/hillshade/relief/DEM stay live GSI
  production endpoints (the `dem_selfhost` option is separate and unrelated here).
- No change to the building layer, the tiles, or the analysis layers. The slope
  **analysis** stays; only the slope **basemap** view is removed.
- No new camera/animation system — the toggle applies pitch and terrain through
  the existing MapLibre calls.
- Depends on nothing in the tile work; but see the sequencing note — it should
  land before `osm-basemap-tiles` PR4 so the 2.5D building extrusion builds on the
  final toggle/terrain model, and after the MapLibre v6 upgrade so it targets v6.

## Planned PRs

1. `01-view-modes-and-25d-toggle-pr1.md` — retire the `slope` basemap, add the
   on-map 2.5D switch button decoupled from the basemap, and wire the per-mode
   behaviour (standard = pitch only; photo/hillshade = pitch + `setTerrain`).
2. `02-hillshade-height-tint-pr2.md` — add the colour-by-height tint in hillshade
   mode (GSI `relief`/色別標高図 or equivalent) with zoom-driven opacity that
   fades on zoom-in and hides past a threshold.
