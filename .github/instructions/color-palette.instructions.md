---
description: 'Use when adding, changing, or applying a color anywhere in the web app — components, stylesheets, or map layer definitions. Defines the two places color may be declared, what to do when a value changes, and why geometry is deliberately not locked.'
name: 'Color Palette'
applyTo: 'webapp/**'
---

# Color Palette

Color is the one design value where deviation is a defect rather than a judgement. An off-palette color fragments the brand, is where a model most plausibly invents a near miss, and carries a contrast risk. So it is constrained, and the constraint is enforced rather than requested.

## Color is declared in exactly two places

**The stylesheet's theme block**, which defines the tokens the interface uses, and **the TypeScript palette module**, which exists because map layers need numeric values and cannot read CSS.

Every entry appears in both, with corresponding names — kebab-case in the stylesheet, camelCase in TypeScript — and identical values. A check compares them by name and value together, so they cannot drift apart.

They already had drifted before this rule existed: the same name meant one green in the stylesheet and a different one on the map, and nobody decided that. This is what the rule prevents.

## Nowhere else may write a color

A color literal — hex, `rgb()`, `hsl()` — is rejected in components, in any TypeScript module other than the palette, and in any stylesheet outside its theme block. So is an arbitrary color utility such as `bg-[#1f7a58]`.

The one exception is the stylesheet inherited from before this rule, which is inventoried instead; see below.

The framework's default palette is cleared, so a utility naming a color that is not in the palette does not exist at all. It fails at build time rather than rendering something slightly wrong.

Passing a palette color through data is fine — interpolating a value that came from the palette is not writing a color.

## Geometry is deliberately not locked

Radius, spacing, shadow size and similar values are **judgements, not defects**. Whether a card corner is 6px or 9px has no correctness dimension, and forcing every surface through a few named roles is how a product ends up looking uniform and lifeless.

Arbitrary values are legitimate there, and so are arbitrary variants — the state-selecting kind, which carry no design value and which overlay primitives require.

Do not extend the color rule to cover them. If a check starts rejecting a spacing value, that is a bug in the check.

## Changing a color's value

Change it in **both** declarations, in the same commit. Changing one produces a failure naming the token, its expected value and what it actually is.

A value change is a **visual change**: regenerate the screenshot baselines and put the images in the pull request so a person looks at them. Never regenerate baselines to turn a red build green.

## Adding a color

Add it to both declarations, with corresponding names. **This is a normal reviewed act, not something to route around.** The palette is a boundary, not a fixed size — the redesign will need more colors than exist today.

If adding an entry feels like fighting the system, the system is being read wrong. The failure to prevent is a component reaching _past_ the palette, not the palette growing.

Trying a color temporarily works the same way: add the entry, try it, remove it. Do not reach for an arbitrary value to avoid a two-line edit.

## Color inherited from before the rule

The stylesheet carries colors that were picked by eye before any of this existed. They are inventoried exactly rather than converted, because turning several dozen one-off tints into palette entries would make the palette a color dump instead of a design system, and they disappear when the applications are redesigned.

The inventory is asserted as an exact set, which cuts both ways: adding one fails, and **removing one without updating the inventory also fails**. Cleaning them up is welcome; doing so silently is not.

## When a color cannot satisfy a contrast requirement

Accessibility violations are recorded, so a color change that adds one will fail the recorded baseline rather than pass unnoticed. Fixing existing contrast failures is welcome and requires updating that record in the same change — the record is meant to track reality, not to be worked around.
