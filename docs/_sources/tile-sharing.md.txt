# Tile Sharing

Tile sharing is an optimization that reduces the number of unique 8x8 tiles in your compiled tileset. When two metatile subtiles have the same pixel shape but different colors — for example, a red roof and a blue roof with identical geometry — Porytiles can store a single tile image and render it with different palettes. This frees up tile slots in the GBA's limited tile memory (primary tilesets have a hard cap of ~512 tiles).

## How It Works

### GBA Tiles Are Indexed

On the GBA, each 8x8 tile in `tiles.png` is a **4-bit indexed image**. Each pixel is not a color — it's a slot number (0–15) that points into one of the hardware palettes. When the GBA renders a tile, it looks up each pixel's slot number in the assigned palette to get the actual color.

This means the same tile image can produce completely different colors depending on which palette is assigned to it. If two palettes have different colors at the same slot positions, one tile image renders correctly with both.

### Color-Isomorphic Tiles

Porytiles identifies **color-isomorphic tiles** — tiles that share the same pixel shape (which pixels form which regions) but assign different colors to those regions. For example:

- A tile with a red triangle on a green background
- A tile with a blue triangle on a green background

These two tiles have identical geometry (the triangle occupies the same pixels), just with different colors in some regions. They are candidates for tile sharing.

### Slot Alignment

For sharing to work, corresponding colors must occupy the **same slot index** in their respective palettes. Consider:

```
Palette 0:  [ transparent | green | brown | RED   | ... ]
Palette 1:  [ transparent | green | brown | BLUE  | ... ]
              slot 0        slot 1  slot 2  slot 3
```

With this layout, an indexed tile where the triangle pixels are `3` renders as red with Palette 0 and blue with Palette 1 — using a single tile image. But if blue ended up at slot 7 instead of slot 3, you would need two separate tile images. That wastes a tile slot.

### The Indirect Link System

Porytiles uses an **indirect link** mechanism to align palette slots. Rather than dictating "put this color at slot 5," the system creates links between corresponding colors: "this red in palette 0 and this blue in palette 1 should share the same slot index." The actual slot number is determined later during palette construction.

This indirection is what makes the system flexible — it doesn't need to know final slot positions in advance.

## How Alignment Works

The `greedy` alignment pipeline has four stages. Understanding these helps explain the diagnostic messages you may see. We will walk through a concrete example to illustrate each stage. (The `optimal` alignment mode, not yet implemented, will use a different approach based on constraint satisfaction rather than this staged pipeline.)

**Example setup:** Suppose you have two color-isomorphic tiles — a red house and a blue house with the same pixel shape. Both use transparent, brown, and green, but differ in their accent color (red vs. blue). After packing, the red house lands in Palette 0 and the blue house lands in Palette 1.

### Stage 1: Build Draft Palettes

Colors are assigned to palette slots sequentially, with no sharing considerations. This produces a "draft" palette layout that the system uses to map each tile to its hardware palette.

In our example, the draft palettes look like this (JASC `.pal` format — each line is one slot):

```
Palette 00.pal (draft):               Palette 01.pal (draft):
  Slot 0:  0 128 0     (transparent)      Slot 0:  0 128 0     (transparent)
  Slot 1:  139 90 43   (brown)            Slot 1:  50 180 50   (green)
  Slot 2:  220 40 40   (red)              Slot 2:  139 90 43   (brown)
  Slot 3:  50 180 50   (green)            Slot 3:  40 40 220   (blue)
  Slot 4:  255 255 0   (yellow)           Slot 4:  255 105 180 (pink)
  ...                                     ...
```

Notice that the non-shared colors (yellow, pink) are mixed in, and the corresponding colors land at **different slots**:
brown is at slot 1 in Palette 0 but slot 2 in Palette 1.
This means the red house tile indexes as `{1, 2, 3}` (brown, red, green) while the blue house indexes as `{2, 3, 1}` (brown, blue, green) —
different indexed tiles, so they can't share yet.

### Stage 2: Generate Indirect Links

For each group of color-isomorphic tiles that span multiple palettes, the system identifies corresponding colors and creates indirect links between them. One member of the group is chosen as the **reference** — its palette slot layout becomes the target that other members align to.

The system picks the reference member that minimizes conflicts with prefilled (locked) palette slots in other palettes, since those slots cannot be moved.

In our example, Palette 0 is chosen as the reference. Three indirect links are created:

```
brown in Palette 1 → brown in Palette 0   ("put brown at whatever slot Palette 0's brown gets")
blue  in Palette 1 → red   in Palette 0   ("put blue at whatever slot Palette 0's red gets")
green in Palette 1 → green in Palette 0   ("put green at whatever slot Palette 0's green gets")
```

Links reference colors, not slot numbers. This is important: it means the links remain valid even if other (non-shared) colors shift around during final palette construction.

### Stage 3: Rebuild Palettes with Links

Palettes are rebuilt from scratch with the indirect links applied:

1. Colors that are **not** involved in any sharing link get assigned slots sequentially (same as the draft).
2. Colors with indirect links are resolved: follow the link to find where the reference color landed, and place the linked color at the same slot.
3. If the target slot is already occupied by a non-locked color, the occupant is **evicted** to the next available slot.

In our example, Palette 0 is the reference palette, so it rebuilds identically — its colors weren't linked *from* anywhere. Palette 1 is rebuilt as follows:

1. **Sequential fill for non-linked colors**: pink is not involved in any link, so it fills sequentially → slot 1.
2. **Resolve brown**: brown in Palette 1 is linked to brown in Palette 0, which is at slot 1. But slot 1 is occupied by pink! Pink is **evicted** to the next free slot (slot 4). Brown is placed at slot 1.
3. **Resolve blue**: blue is linked to red in Palette 0, which is at slot 2. Slot 2 is free → blue is placed at slot 2.
4. **Resolve green**: green is linked to green in Palette 0, which is at slot 3. Slot 3 is free → green is placed at slot 3.

The final palettes:

```
Palette 00.pal (final):               Palette 01.pal (final):
  Slot 0:  0 128 0     (transparent)      Slot 0:  0 128 0     (transparent)
  Slot 1:  139 90 43   (brown)            Slot 1:  139 90 43   (brown)       ← moved here via link
  Slot 2:  220 40 40   (red)              Slot 2:  40 40 220   (blue)        ← aligned with red's slot
  Slot 3:  50 180 50   (green)            Slot 3:  50 180 50   (green)       ← aligned with green's slot
  Slot 4:  255 255 0   (yellow)           Slot 4:  255 105 180 (pink)        ← evicted here from slot 1
  ...                                     ...
```

Now brown, the accent color (red/blue), and green occupy the same slots (1, 2, 3) in both palettes.

This stage can also produce **shared color conflicts** and **prefilled source conflicts**.
When multiple shape groups share a common color (e.g., brown) in the same palette, each group creates a link for that color pointing to a different reference palette.
The system applies links in order — the first group's link wins, and later groups' links for the same color are silently dropped.
The losing group's alignment fails because the shared color ends up at a slot chosen by the winning group, not the slot the losing group needed.
The diagnostic reports these as "Shared color conflict" failures under each affected group (see [Shared Color Conflicts](#shared-color-conflicts) below).
Additionally, if a link's source color is prefilled (locked) in its palette, the link is dropped entirely — see [Prefilled Source Conflicts](#prefilled-source-conflicts).

### Stage 4: Verify Alignment

Each color-isomorphic group is checked against the final palettes. The system indexes each member's tile against its assigned palette and checks whether all members produce identical indexed output. Groups where every member matches are confirmed as sharing-aligned, and the duplicate tiles are removed.

Verification can be **partial** — not all members of a group may produce matching indexed output. If some members' indexed tiles diverge from the reference (e.g., due to link resolution failures affecting only some palettes), those members are dropped from the sharing result. The group can still succeed with the remaining subset, as long as at least two members across at least two palettes still align. In this case, the group is reported as "partially succeeded" rather than "succeeded."

In our example, both the red house and blue house now index as `{1, 2, 3}` — identical indexed tiles. One tile image is stored in `tiles.png`, and the GBA renders it with Palette 0 (showing red) or Palette 1 (showing blue) as needed. One tile slot saved.

## Configuration

Tile sharing is controlled by two configuration options that work together: one controls how tiles are distributed across palettes during packing, and the other controls whether palette slot alignment is attempted.

### Packing

**CLI:** `--tile-sharing-packing <mode>`
**YAML:** `tileset.tiles.sharing.packing`

Packing
: `off` (default)
: Packing ignores tile sharing entirely. Color-isomorphic tiles may end up in the same palette or different palettes by chance. Any sharing that occurs is coincidental.

: `biased`
: The packer applies a soft cost penalty that steers color-isomorphic tiles toward **different** palettes. This creates more sharing opportunities by ensuring tile variants are spread across palettes rather than clustered in one.

: `optimal`
: Hard constraint that rejects placing color-isomorphic tiles in the same palette. *Not yet implemented.*

### Alignment

**CLI:** `--tile-sharing-alignment <mode>`
**YAML:** `tileset.tiles.sharing.alignment`

Alignment
: `off` (default)
: Palettes are filled sequentially with no sharing alignment. Any slot alignment that occurs is coincidental.

: `greedy`
: Best-effort alignment via indirect links. The system attempts to align palette slots for all detected color-isomorphic groups. Recommended for most users who want tile sharing.

: `optimal`
: Globally optimal alignment using constraint satisfaction. *Not yet implemented.*

### Recommended Configuration

For maximum tile sharing, use both options together:

```yaml
tileset:
  tiles:
    sharing:
      packing: biased
      alignment: greedy
```

Or via CLI flags:

```
--tile-sharing-packing biased --tile-sharing-alignment greedy
```

Using `biased` packing is the single biggest improvement — it actively distributes color-isomorphic tiles across palettes, giving the alignment system more opportunities to work with.

## Reading the Diagnostics

Porytiles emits several diagnostic remarks during tile sharing analysis. Each is tagged with a name you can use to filter output (see [Filtering Diagnostics](#filtering-diagnostics)).

### `tile-sharing-shareable-tiles-<N>`

Shows all detected color-isomorphic tile groups. For each group, you will see:

- ASCII art of each distinct **color version** (the different color variants of the same shape)
- Which metatile entries reference these tiles

This remark is always emitted when shape groups are detected, regardless of your configuration. It tells you: "these tiles *could* share if alignment succeeds."

### `tile-sharing-shareable-tiles-summary`

Emitted after all Phase 1 per-group remarks. Shows how many shareable shape groups were detected in total:

> Tile sharing detection: '17' shareable shape group(s) found.

### `tile-sharing-palette-partition-<N>`

After palette packing, shows which palettes each color version landed in. Groups where members span two or more palettes are **eligible** for sharing (a tile can only be shared across palettes, not within the same one).

If your packing is `off`, this remark includes a caveat explaining that the palette distribution is coincidental and may improve with `biased` packing.

### `tile-sharing-palette-partition-summary`

Emitted after all Phase 2 per-group remarks. Shows how many of the detected groups survived palette packing — i.e., ended up spanning multiple palettes:

> Tile sharing partition: '9' of '17' shape group(s) eligible for sharing after palette packing.

### `tile-sharing-result-<N>`

Shows groups that were **successfully aligned** — tiles that will actually be deduplicated in the output. For each group, you will see a representative tile per palette and the metatile entries that reference it.

There are two outcomes:

- **Full success** ("Tile sharing succeeded"): All eligible members produced matching indexed tiles and will share a single tile image.
- **Partial success** ("Tile sharing partially succeeded"): Some members aligned, but others diverged and were dropped. The remark shows how many color versions diverged, separated by a `--------` divider. The group still shares tiles among the aligned subset.

If your alignment is `off`, this remark includes a caveat explaining that any alignment is coincidental and may improve with `greedy` alignment.

### `tile-sharing-result-summary`

The aggregate summary, showing the full pipeline funnel — how many groups were detected, how many were eligible after packing, and how many were ultimately aligned. For example:

> Tile sharing summary:
> '17' detected → '9' eligible after packing → '9' aligned.

When any groups are partially aligned, the aligned count includes a breakdown:

> Tile sharing summary:
> '17' detected → '9' eligible after packing → '9' aligned ('8' fully, '1' partially).

A "Partially aligned groups" sub-section appears before any unaligned groups, showing per-group dropped color version counts:

> Partially aligned groups:
>   Group '16': '3' color version(s) dropped.

If any groups failed to align entirely, the summary provides additional detail:

- **Unaligned group listing with per-group failures** — Each unaligned group is shown with its color versions, which palette(s) each version ended up in (e.g., "Version '1' assigned to palette(s): '03.pal'."), and an inline failure breakdown showing why *that specific group* failed to align. For example:

  > Unaligned group (group id '5') — '2' color version(s):
  >   [tile art]
  >   Version '1' assigned to palette(s): '03.pal'.
  >   Version '2' assigned to palette(s): '01.pal'.
  >   '3' link failure(s) for this group:
  >     Prefilled destination conflict: '1'.
  >       Palette '03.pal' slot '5': color (...) blocked by locked color (...).
  >     Shared color conflict: '2'.
  >       '01.pal': color (...) linked to '03.pal' by group '0',
  >         this group wanted ref color (...) in '05.pal'.
  >       '01.pal': color (...) linked to '03.pal' by group '2',
  >         this group wanted ref color (...) in '05.pal'.

- **Aggregate total** — After all unaligned groups, a one-line summary of total link resolution failures across all groups, followed by actionable suggestions. See [Understanding Alignment Failures](#understanding-alignment-failures) for what each failure type means.

(understanding-alignment-failures)=
## Understanding Alignment Failures

When alignment is active, each failure is attributed to the shape group that caused it.
Failures appear inline under each unaligned group in the `tile-sharing-result-summary` remark,
with counts and detail lines specific to that group.

(shared-color-conflicts)=
### Shared Color Conflicts

A very common type of alignment failure. Under each affected group, the diagnostic will show a count followed by per-record detail lines:

> Shared color conflict: 'N'.
>   '01.pal': color '(R, G, B)' linked to '03.pal' by group '0',
>     this group wanted ref color '(R, G, B)' in '05.pal'.

Each detail line shows both sides of the conflict: which group won the color's link (and to which reference palette), and which reference the losing group wanted instead.

This happens when multiple shape groups share a common color in the same palette — common colors like brown, green, or gray often appear in many tile groups. Each group creates an indirect link for the shared color pointing to a different reference palette and target slot. Since a color can only have one link, the system applies the first link it encounters and silently drops subsequent ones (first-writer-wins).

The losing group's alignment fails because the shared color lands at the slot chosen by the winning group, not the slot the losing group needed.

```{note}
When two groups both link the same color to the *same* reference (same palette, same color), the links are **compatible** — the existing link already satisfies both groups. Compatible links are automatically detected and are **not** reported as conflicts. Only genuinely incompatible links (different reference palette or different reference color) appear in the diagnostic output.

In practice, color variants of the same visual element — for example, a red building and a blue building with identical tile geometry — naturally produce compatible links. Their shape groups all create links pointing in the same direction for any shared colors, so no conflicts arise. Conflicts typically occur between shape groups from *different* visual elements that happen to share a common color in the same palette. For example, a building's shape group might link a shared green to a brown in another palette (because green and brown are corresponding colors in the building's two variants), while a tree's shape group links that same green to a yellow in a third palette (because green and yellow correspond in the tree's variants). Same source color, different destinations — that is a conflict.
```

**This is a fundamental limitation of greedy alignment.** The `optimal` alignment (not yet implemented) would resolve these conflicts globally using constraint satisfaction, finding slot assignments that satisfy all groups simultaneously rather than processing them one at a time.

(prefilled-source-conflicts)=
### Prefilled Source Conflicts

A color that needs to be linked to a reference in another palette is itself **prefilled (locked)** in its source palette. Under each affected group, the diagnostic shows which palette and colors are involved:

> Prefilled source conflict: 'N'.
>   Palette '01.pal': prefilled color '(R, G, B)' could not be linked to color '(R, G, B)' in palette '00.pal'.

Because the color is locked at its current slot, the alignment system cannot reassign it to follow the reference color's slot position. The link is dropped entirely and the shape group's alignment fails.

This is distinct from a [prefilled destination conflict](#prefilled-destination-conflicts), where the *destination* slot is blocked by a locked color. Here, the *source* color itself is locked and cannot participate in linking at all.

If the prefilled color is not critical at its current position, rearranging or wildcarding it in your palette files may allow the link to be applied.

(prefilled-destination-conflicts)=
### Prefilled Destination Conflicts

A color needs to go at a specific slot to match another palette, but that destination slot is already occupied by a **prefilled (locked)** color from your input palettes. Under each affected group, the diagnostic shows exactly which palette, slot, and colors are involved:

> Prefilled destination conflict: 'N'.
>   Palette '03.pal' slot '5': color '(R, G, B)' blocked by locked color '(R, G, B)'.

Prefilled slots are colors you explicitly placed in your palette files. They cannot be moved by the alignment system. If these slots are blocking alignment, you may be able to rearrange them (see [Improving Tile Sharing Results](#improving-tile-sharing-results)).

### Post-Resolution Slot Mismatch

All indirect links for this group were applied and resolved successfully, but the final slot positions don't match. This happens when a *later* resolution step (for a different group or different palette) evicts a color from the slot it was placed at, displacing it to a different position. Under each affected group, the diagnostic shows where each color ended up versus where it should have been:

> Post-resolution slot mismatch: 'N'.
>   '01.pal': color '(R, G, B)' ended at slot '15', but ref color '(R, G, B)' in '03.pal' is at slot '14'.

The greedy alignment processes palettes sequentially (palette 0 first, then 1, 2, ...). When palette 1 resolves its links against palette 3's current state, and palette 3 is later processed and its own resolutions evict colors to different slots, palette 1's already-resolved positions become stale. This is a fundamental limitation of the sequential greedy approach — the `optimal` alignment (not yet implemented) would resolve all palettes globally and avoid these cascading evictions.

(improving-tile-sharing-results)=
## Improving Tile Sharing Results

Tile sharing is **best-effort**. Not every color-isomorphic group will align successfully, and that is normal. Individual groups can also partially succeed — some members share a tile while others fall back to separate tiles due to alignment divergence. Even partial sharing can significantly reduce your tile count. Here are ways to improve results:

**Use `biased` packing.** This is the single most impactful change. It actively distributes color-isomorphic tiles across different palettes, giving the alignment system more groups to work with. Without it, tiles may cluster in the same palette where sharing is impossible.

**If you see prefilled destination conflicts,** the diagnostic tells you exactly which palette slots are blocking alignment and which colors are involved. If those prefilled colors are not critical to your tileset layout, rearranging them to different slot positions may allow more groups to align.

**If you see prefilled source conflicts,** a color that needs to be linked is itself locked in its palette. The diagnostic shows which prefilled color is blocking the link. If that color is not critical at its current position, rearranging or wildcarding it may allow the link to be applied.

**If you see shared color conflicts,** the detail lines show which groups are competing and what reference each wanted. Multiple shape groups are competing for the same color's slot position. This is a fundamental limitation of greedy alignment — the `optimal` alignment (not yet implemented) would resolve these globally. In the meantime, shared color conflicts are expected and usually harmless; the groups that *did* align represent genuine savings. Note that compatible links (where two groups want the same reference) are automatically detected and not reported as conflicts.

**If you see post-resolution slot mismatches,** colors were displaced by eviction after they were already successfully placed. The detail lines show the final slot positions for each mismatched color pair. This is an inherent limitation of the sequential greedy approach. The `optimal` alignment (not yet implemented) would avoid these cascading evictions by considering all palette constraints simultaneously.

**Design tiles with sharing in mind.** Tiles that share the same geometric pattern (identical pixel layout, different colors) are sharing candidates. When creating color variants of buildings, terrain, or other elements, keeping the pixel shape exactly the same maximizes sharing potential. Even a single pixel difference breaks the color-isomorphic relationship.

(filtering-diagnostics)=
## Filtering Diagnostics

You can control which tile sharing diagnostics appear in the output using the `--diagnostic-remarks-exclude` and `--diagnostic-remarks-include` CLI flags (or their YAML equivalents). These accept regex patterns matched against the remark tag names.

Both flags are list-valued — repeat them on the CLI to specify multiple patterns:

```
--diagnostic-remarks-exclude 'pattern1' --diagnostic-remarks-exclude 'pattern2'
```

Or in YAML:

```yaml
diagnostic:
  remarks:
    exclude:
      - 'pattern1'
      - 'pattern2'
```

**Suppress all tile sharing remarks:**

```
--diagnostic-remarks-exclude 'tile-sharing-.*'
```

**Show only the final summary:**

```
--diagnostic-remarks-exclude 'tile-sharing-.*' --diagnostic-remarks-include 'tile-sharing-result-summary'
```

**Show only the per-phase summaries (skip per-group details):**

```
--diagnostic-remarks-exclude 'tile-sharing-.*' \
  --diagnostic-remarks-include 'tile-sharing-shareable-tiles-summary' \
  --diagnostic-remarks-include 'tile-sharing-palette-partition-summary' \
  --diagnostic-remarks-include 'tile-sharing-result-summary'
```

**Or expressed more succinctly:**

```
--diagnostic-remarks-exclude 'tile-sharing-.*' --diagnostic-remarks-include 'tile-sharing-.*-summary'
```

Include patterns override exclude patterns, so you can exclude broadly and then selectively re-enable specific tags.

## Acknowledgments

Porytiles' tile sharing system draws significant design inspiration from [borytiles](https://github.com/ishax-kos/borytiles) by ishax-kos, a Rust-based tileset compiler for GBA Pokémon decomp projects. Three core ideas in Porytiles' tile sharing pipeline originated in borytiles:

- **Color isomorphism detection.** Borytiles introduced the concept of representing tiles as shape-indexed structures (mapping pixel regions to color indices) and grouping them by canonical shape. Porytiles2 adapts borytiles' `Shape_indexable_tile` and `get_ideal_flip` canonicalization into its own `ShapeTile`, `ShapeMask`, and `CanonicalShapeTile` types.

- **Indirect position linking.** Borytiles' `Position_in_palette` enum demonstrated that palette slot assignment can be decoupled from palette construction by linking colors to other colors rather than to absolute slot indices. This insight — that links referencing colors remain valid even when non-shared colors shift around — is the foundation of Porytiles' `IndirectPosition` system.

- **Greedy alignment algorithm.** Borytiles' `account_for_palette_swaps` function showed how to detect same-shape tiles across different palettes and emit indirect links pairing their corresponding colors. Porytiles2 extends this approach with a conflict-minimization heuristic for reference member selection and integrates the link generation into a multi-phase pipeline with diagnostic reporting.

Thank you to ishax-kos for the creative and well-engineered work in borytiles that made Porytiles' tile sharing possible.
