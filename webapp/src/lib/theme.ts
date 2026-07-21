/** The only place a color literal may be written in TypeScript.
 *
 *  Most of this product's color is not in CSS: the map layers need numeric
 *  values, so they were scattered as hex literals across `modules.ts` and
 *  `style-rules.ts`. That is how `lime` came to mean `#a9d96e` in the stylesheet
 *  and `#8fc85a` on the map without anyone deciding it should.
 *
 *  Every entry here also exists as a `--color-*` token in `app.css`, so the two
 *  cannot drift again. The enforcement check rejects color literals anywhere
 *  else; adding a color means adding it in both places, deliberately.
 *
 *  The two limes are kept apart rather than reconciled. They serve different
 *  roles and merging them would change what the map renders, which is a design
 *  decision for the redesign rather than a side effect of writing a lint rule.
 */
export const palette = {
  // Interface
  ink: "#10231e",
  muted: "#667770",
  line: "#dfe7e2",
  paper: "#f4f7f3",
  white: "#ffffff",
  forest: "#164d3b",
  green: "#1f7a58",
  lime: "#a9d96e",
  amber: "#e2a43c",
  red: "#d75b4c",
  blue: "#397ca3",

  // Map fills and strokes
  hub: "#8fc85a",
  gray: "#a9b5af",
  transmission: "#8e5eaa",
  // Underground utility networks follow the APWA one-call convention where the
  // existing palette already matches (water blue, sewer green, gas amber/yellow,
  // power red); communications orange is the one colour the palette lacked.
  comms: "#d97a35",
  exposureOutline: "#7b342b",
  buildingOutline: "#687b74",
  buildingOutlineSoft: "#6e7e78",
  buildingFill: "#8b9994",
  corridorOutline: "#0c4e34",
  zoneOutline: "#104b35",
} as const;

export type PaletteName = keyof typeof palette;
