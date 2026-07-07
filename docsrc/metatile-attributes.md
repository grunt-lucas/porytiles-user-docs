# Metatile Attributes Reference

```{important}
This page is quite detailed, but for 90% of use-cases, Porytiles's default behavior will be sufficient.
It tries really hard to infer the attribute schema from your decomp code,
and editing the `attributes.csv` should be intuitive in most cases (especially if you have used `porytiles-legacy` before).
Only read this page if your project needs heavy customization.
```

Every metatile in a tileset carries an **attribute value**:
a small packed integer that tells the game engine about various metadata values for that metatile.
The most important piece is the **behavior** (tall grass, water, a ledge, a door),
but the attribute value also stores the **layer type** and, depending on the game, extra fields like terrain and encounter type.

In a Porytiles-managed tileset you edit attributes in a plain text file, `porytiles_src/attributes.csv`.
When you compile, Porytiles packs that CSV into the `metatile_attributes.bin` binary that Porymap and the game read.
This page documents the full system:
the CSV format, the layer type rules, the **attribute schema** that defines which fields exist,
and the configuration options that give you the ability to fully customize everything.

For metatile basics (what a metatile is, how layers work), read {doc}`gba-decomp-tileset-system` first.

```{note}
TODO: insert screencap of Porymap's Tileset Editor showing the metatile behavior and layer type fields
```

## What's an attribute value?

The GBA's video hardware never sees metatile attributes.
Tiles, palettes, and tilemaps are hardware concepts; attributes are pure game-engine data.
The engine looks up a metatile's attribute value and extracts fields from it with bit masks and shifts
(see `GetMetatileAttributeFromRawMetatileBehavior` and friends in `src/fieldmap.c`).
Because the format is just an agreement between `metatile_attributes.bin` and the engine's field-map code,
different games pack it differently, and you can modify your project to pack it however you want.
That is why Porytiles treats the layout as data, not as a hardcoded rule.

One common confusion:
**collision and elevation are not metatile attributes.**
Those live in each map's block data, packed next to the metatile ID
(`MAPGRID_COLLISION_MASK` and `MAPGRID_ELEVATION_MASK` in `include/global.fieldmap.h`),
and you edit them per map square in Porymap.
Attributes describe the metatile itself. It's the same everywhere the metatile is placed.

### Stock layouts

Ruby, Sapphire, and Emerald use a 2-byte attribute per metatile:

| Bits | Mask | Field |
|------|------|-------|
| 0-7 | `0x00FF` | behavior (`MB_*` constants) |
| 8-11 | `0x0F00` | unused |
| 12-15 | `0xF000` | layer type |

FireRed and LeafGreen use a 4-byte attribute and pack in more fields:

| Bits | Mask | Field |
|------|------|-------|
| 0-8 | `0x000001FF` | behavior (`MB_*` constants) |
| 9-13 | `0x00003E00` | terrain (`TILE_TERRAIN_*`: normal, grass, water, waterfall) |
| 14-17 | `0x0003C000` | unused (`attribute_2`) |
| 18-23 | `0x00FC0000` | unused (`attribute_3`) |
| 24-26 | `0x07000000` | encounter type (`TILE_ENCOUNTER_*`: none, land, water) |
| 27-28 | `0x18000000` | unused (`attribute_5`) |
| 29-30 | `0x60000000` | layer type |
| 31 | `0x80000000` | unused (`attribute_7`) |

These tables come from each decomp's source:
the masks are declared in `include/global.fieldmap.h` and `src/fieldmap.c`.
Recent `pokeemerald-expansion` versions contain *both* layouts
(`sMetatileAttrMasks` for FRLG and `sMetatileAttrMasksEmerald` in `src/fieldmap.c`)
and pick one per map layout at runtime,
so a single Expansion project can host Emerald-style and FRLG-style maps side by side.
Porytiles handles that case too; see [Emerald-style and FireRed-style layouts in one project](#emerald-style-and-firered-style-layouts-in-one-project).

## The attribute schema

Porytiles describes an attribute layout with a schema that is an ordered list of named fields.
Each field has:

- **name**: the CSV column header, for example `behavior` or `terrain`.
- **mask**: the bits the field occupies in the packed attribute value.
  A mask must be a single contiguous run of bits, and fields must not overlap.
- **default**: the value used for metatiles that have no row in `attributes.csv` (0 unless configured otherwise).
- **provider** (optional): where the field's named constants live.
  A provider points at a C header and a name prefix,
  for example `include/constants/metatile_behaviors.h` with prefix `MB_`.
  A field with a provider takes constant names in its CSV column.
  A field without one, i.e. a *raw field*, takes plain integers.

```{important}
The **layer type is not a schema field**.
Its position is inferred from the base game rather than declared in your schema:
Porytiles reads `METATILE_ATTR_LAYER_MASK` or the `METATILE_ATTRIBUTE_LAYER_TYPE` entry of `sMetatileAttrMasks` and uses that mask.
If the base game declares no layer-type mask, Porytiles falls back to a **size-based default** taken from the vanilla games:
bits 12-15 for 2-byte attributes (the Emerald position), bits 29-30 for 4-byte attributes (the FRLG position), and disabled for 1-byte attributes.
Porymap defaults to the same masks, though it selects them by base game version rather than by size.
You can override the mask with `fieldmap.metatile_layer_type_mask` (and its FRLG variant); see
[Configuration](configuration.md).
A mask of `0` **disables** the layer type entirely.
Porytiles manages the layer type automatically, including the disabled case; see [Layer types](#layer-types) below.
It rejects any field whose mask overlaps a non-zero layer-type mask.
```

The attribute size itself (1, 2, or 4 bytes) is not something you declare in the Porytiles config.
For the primary layout, Porytiles reads the C type of the `gMetatileAttributes_*` declarations in
`src/data/tilesets/metatiles.h`
(`const u8` means 1 byte, `const u16` means 2, `const u32` means 4).
This width is fixed by your game code.
Every tileset in a decomp project uses
the same defined `const uN *metatileAttributes` pointer from `struct Tileset` in `include/global.fieldmap.h`,
so the attribute width is shared across all tilesets, not chosen per tileset.

A field mask (or an explicit layer-type mask)
that needs *more* bits than the declared width is a misconfiguration.
Porytiles reports it as an error and asks you to either narrow the mask,
or change the `gMetatileAttributes_*` declarations to the wider type.
A common way to hit this is by pasting a FireRed mask (for example the `0x60000000` layer type mask)
into an Emerald-width (`const u16`) project.

The FRLG alternate layout is the exception: when a tileset resolves the FRLG masks,
its attribute size is always 4 bytes, no matter what `metatiles.h` declares,
and Porytiles says so in a remark when that overrides a narrower declared width.
[Emerald-style and FireRed-style layouts in one project](#emerald-style-and-firered-style-layouts-in-one-project)
explains why the declared type does not count there.

If `metatiles.h` is missing or Porytiles cannot recognize its attribute declarations,
there is no declared width to honor.
For the primary layout, Porytiles assumes 2 bytes and warns about the assumption.
In that case only, the field masks are the sole evidence of the true width,
so a mask using bits above 15 widens the assumed size to 4 bytes.
Even then masks only ever widen the assumed size, never narrow it.
So a 4-byte project whose fields all sit in the low bits needs its `metatiles.h` declarations recognizable.
If you hit that warning on a 4-byte project,
declare your `gMetatileAttributes_*` arrays as `const u32`,
or configure at least one field whose mask uses a bit at or above bit 16.

```{attention}
Earlier Porytiles versions had a `fieldmap.metatile_attribute_size` config key.
It no longer exists; the size now follows from `metatiles.h` and the field masks.
```

## Where the schema comes from

You almost never have to write a schema yourself.
Porytiles resolves it per tileset, in this order:

1. **Explicit config.**
   If `fieldmap.metatile_attr_fields` is set in your Porytiles YAML config, it wins.
2. **Inference from your project.**
   Otherwise Porytiles reads the layout your decomp code already declares (details below).
3. **Error.**
   If neither produces fields, compilation stops with an error telling you to
   either add a `metatile_attr_fields` list or restore the engine declarations so inference can succeed.
   There is no silent fallback.

In every case, `fieldmap.metatile_attr_field_overrides` is then merged on top,
so you can adjust individual fields without redeclaring the whole layout.
Both keys are documented in [Customizing the schema](#customizing-the-schema).

### Schema inference

For a vanilla or lightly modified project, inference produces the right schema with zero configuration.
It scans:

| File | What Porytiles reads from it |
|------|------------------------------|
| `include/global.fieldmap.h` | the `METATILE_ATTRIBUTE_*` enum (which fields exist, in order) and any `METATILE_ATTR_*_MASK` defines |
| `src/fieldmap.c` | the `sMetatileAttrMasks` and `sMetatileAttrShifts` tables (mask values per field) |
| `src/data/tilesets/metatiles.h` | the primary-layout attribute size (`const u16` vs `const u32`) |
| `include/constants/metatile_behaviors.h` | the `MB_*` behavior constants (as defines or enum members) |

Field names come from the enum:
`METATILE_ATTRIBUTE_BEHAVIOR` becomes `behavior`,
`METATILE_ATTRIBUTE_TERRAIN` becomes `terrain`,
and a numbered entry like `METATILE_ATTRIBUTE_2` becomes the raw field `attribute_2`.
`METATILE_ATTRIBUTE_LAYER_TYPE` is dropped, since the layer type is not a schema field (see earlier note).

Inference also attaches providers where it can find them:

- `behavior` gets the `MB_` constants from `include/constants/metatile_behaviors.h`
  (skipping `MB_INVALID`, which is a sentinel rather than a real behavior).
- Other named fields are searched against the `global.fieldmap.h` enums by prefix:
  `terrain` finds `TILE_TERRAIN_*`, `encounter_type` finds `TILE_ENCOUNTER_*`.
- Numbered fields (`attribute_2` and friends) stay raw.

Vanilla `pokeemerald` and `pokeruby` declare no mask table for their simple 2-byte layout,
so there is a special case:
if the project is 2-byte and declares only behavior and layer type,
the behavior mask is filled in as `0x00FF` silently.
Any *other* field whose mask cannot be determined is a fatal error,
with a message listing your options
(restore `sMetatileAttrMasks[]`, add a `METATILE_ATTR_<NAME>_MASK` define, or set the mask in Porytiles config).

Disagreements are handled conservatively:
if a `METATILE_ATTR_*_MASK` define and the `sMetatileAttrMasks` table disagree, the define wins and Porytiles warns.
If an `sMetatileAttrShifts` entry does not match its mask's bit position, the mask wins and Porytiles warns.

(checking-the-resolved-schema)=
### Checking the resolved schema

`dump-tileset-config` prints the schema Porytiles resolved for a tileset,
after config, inference, overrides, and layout selection have all been applied.
Run it whenever you are unsure which fields your CSV needs:

```bash
porytiles dump-tileset-config gTileset_General
```

Against a vanilla `pokefirered` project, the tail of the output looks like this:

```text
Resolved Metatile Attribute Schema
==================================

  Layout: primary
  Attribute size: 4 bytes

  Fields:
    behavior  mask=0x1FF  offset=0 width=9  default=0 provider=include/constants/metatile_behaviors.h (MB_)
    terrain  mask=0x3E00  offset=9 width=5  default=0 provider=include/global.fieldmap.h (TILE_TERRAIN_)
    attribute_2  mask=0x3C000  offset=14 width=4  default=0
    attribute_3  mask=0xFC0000  offset=18 width=6  default=0
    encounter_type  mask=0x7000000  offset=24 width=3  default=0 provider=include/global.fieldmap.h (TILE_ENCOUNTER_)
    attribute_5  mask=0x18000000  offset=27 width=2  default=0
    attribute_7  mask=0x80000000  offset=31 width=1  default=0
```

## The `attributes.csv` file

`attributes.csv` lives in each tileset's `porytiles_src/` directory,
next to the layer PNGs.
Porytiles reads in on compile and writes it on decompile/import.

The format:

- **Header row (required).**
  `id`, then one column per schema field, in schema order,
  then optionally a trailing `layer_type` column (see [Layer types](#layer-types)).
  For stock Emerald it is `id,behavior`.
  For stock FireRed it is `id,behavior,terrain,attribute_2,attribute_3,encounter_type,attribute_5,attribute_7`.
  The header is checked against the resolved schema,
  and a mismatch generates an error that prints the expected header.
- **Every data row must match the header.**
  A row with too few cells, or with extra cells past the last header column, is an error.
  A CSV written for a wider schema throws an error instead of silently dropping the extra values.
- **`id` column.**
  The metatile index the row applies to.
  Row order does not matter, it's the `id` value that decides the metatile to which the row applies.
  Decimal, hex (`0x10`), and octal (leading `0`) notations are all supported.
  Duplicate ids are an error.
- **Missing rows are fine.**
  A metatile with no row gets every field's default value and an inferred layer type.
  When Porytiles writes the file, it omits all-default rows,
  so a mostly-plain tileset produces a short CSV.
- **Fields with a provider** take full constant names, exactly as declared in the header: `MB_TALL_GRASS`, `TILE_TERRAIN_GRASS`.
  Names are case-sensitive, and raw integers are not accepted in these columns.
  An unknown name generates an error pointing at the offending line.
- **Raw fields** (no provider) take unsigned integers, again in decimal, hex, or octal.
  Values are range-checked against the field's bit width.
- Cells are trimmed of surrounding whitespace, blank lines are skipped,
  and there is no comment syntax.
  Empty cells are only allowed in the `layer_type` column.

A stock Emerald example:

```text
id,behavior
0x00,MB_NORMAL
0x01,MB_TALL_GRASS
0x0E,MB_POND_WATER
0x22,MB_JUMP_SOUTH
```

A stock FireRed example:

```text
id,behavior,terrain,attribute_2,attribute_3,encounter_type,attribute_5,attribute_7
0x01,MB_TALL_GRASS,TILE_TERRAIN_GRASS,0,0,TILE_ENCOUNTER_LAND,0,0
0x10,MB_POND_WATER,TILE_TERRAIN_WATER,0,0,TILE_ENCOUNTER_WATER,0,0
```

(layer-types)=
## Layer types

The layer type controls which screen layers a dual-layer metatile's two tile layers render on.
{doc}`gba-decomp-tileset-system` explains the three values (`normal`, `covered`, `split`) and what they look like in game.
This section covers how Porytiles decides which one each metatile gets.

### Inference

By default there is no layer type column in `attributes.csv` at all.
Porytiles infers each metatile's layer type from which of your three layer PNGs
(`bottom.png`, `middle.png`, `top.png`) contain non-transparent content for that metatile:

| Layers with content | Inferred layer type |
|---------------------|---------------------|
| bottom only, or bottom + middle | `covered` |
| bottom + top | `split` |
| anything else (middle only, middle + top, top only, empty) | `normal` |

In other words, you just draw each metatile on the layers where it belongs,
and the layer type follows automatically.
Triple-layer tilesets skip all of this:
in triple-layer mode every metatile renders all three layers and the stored layer type is always `normal`.

```{note}
If the layer-type mask is disabled via `fieldmap.metatile_layer_type_mask: 0x0` or your base game has no
layer-type mask and a 1-byte attribute layout, every metatile is stored as `normal` and no layer-type
bits are written. This matches Porymap's behavior when its `metatile_layer_type_mask` is `0`.
```

```{note}
TODO: insert screencap of a metatile drawn across two layer PNGs and the resulting layer type in Porymap
```

### Pinning with the `layer_type` column

Inference covers basically every real metatile.
For the rare case where for some reason you need a specific layer type that inference would not pick,
enable the optional CSV column:

```yaml
fieldmap:
  write_layer_type_column: true
```

With the setting on:

- `attributes.csv` gains a trailing `layer_type` column,
  and Porytiles writes one row per metatile so every metatile has a cell to fill.
- A filled cell (`normal`, `covered`, or `split`, case-insensitive) **pins** that metatile's layer type.
  A pinned value beats inference.
- A blank cell means "infer as usual", and stays blank when Porytiles rewrites the file,
  so pins survive compile/decompile round trips.

With the setting off (the default), a `layer_type` column in the file is ignored:
Porytiles warns once per file and infers as usual.

If a pinned (or inferred) layer type drops a layer that actually contains visible tiles,
Porytiles warns that those tiles will be discarded.
That warning usually means the pin is wrong, or content is drawn on a layer it should not be.

This is a per-tileset kind of setting,
so you should prefer setting it in `porytiles/tilesets/<tileset_name>/config.yaml` rather than project-wide
(see {doc}`configuration` for config file locations and layering).

(emerald-style-and-firered-style-layouts-in-one-project)=
## Emerald-style and FireRed-style layouts in one project

The `pokeemerald-expansion` decomp base can host Emerald-style and FRLG-style map layouts in the same game,
selected per layout via `layout_version` in `data/layouts/layouts.json`.
A tileset used by FRLG layouts needs its attributes packed with the FRLG masks;
a tileset used by Emerald layouts needs the Emerald masks.

Porytiles resolves this per tileset with the `fieldmap.use_frlg_alternate_masks` key:

- `automatic` (the default): Porytiles cross-references `layouts.json`.
  If every layout using the tileset says `layout_version: "frlg"`, the tileset gets the FRLG masks.
  If they all say `"emerald"` (or omit the key), or the tileset appears in no layout, it gets the primary masks.
  A tileset referenced by *both* kinds of layout is an error,
  and Porytiles asks you to decide by setting the key explicitly for that tileset.
- `always`: force the FRLG masks (`true` works as an alias).
- `never`: force the primary masks (`false` works as an alias).

Like the layer type column config, this is really a per-tileset setting,
so you should set it in `porytiles/tilesets/<tileset_name>/config.yaml`.

Under the hood, every field carries up to two masks:
`mask` for the primary layout and `frlg_mask` for the FRLG layout.
Inference fills both automatically from Expansion's dual mask tables and `METATILE_ATTR_*_MASK_FRLG` defines,
and once a layout is selected, fields that have no mask for that layout are excluded.
On a stock Expansion project, an Emerald-layout tileset keeps just `behavior` at the declared 2-byte width,
while a FRLG-layout tileset gets the full field set (masks reaching bit 31)
at the fixed 4-byte width (the FRLG exception in the attribute size rules above).

This is different from how `pokefirered` handles its attribute size.
`pokefirered` declares its attributes as `const u32`,
so the declaration and the runtime agree: the FRLG masks fit the declared 4-byte width directly.
Expansion instead declares *all* its attributes as `const u16`, FRLG tilesets included,
and selects the real entry width per map layout at runtime:
`src/fieldmap.c` casts the attribute pointer to `const u32 *` for FRLG layouts
and `const u16 *` for Emerald layouts.
Porytiles mirrors both conventions: a FRLG-layout tileset resolves 4 bytes regardless of the declaration
and emits 4-byte `metatile_attributes.bin` entries
(Expansion's included `general_frlg/metatile_attributes.bin` is 2560 bytes, 640 metatiles at 4 bytes each),
while generated `INCBIN` declarations keep the declared `u16` convention.

```{note}
`pokeemerald-expansion` documents this setup in its own `docs/tutorials/how_to_frlg.md`,
and its `frlg_metatile_behavior_converter.py` migration script reads and writes 4-byte entries.
```

As elsewhere, `dump-tileset-config` shows what's going on:
the selected layout, the resolved size, and which fields were excluded.
On a stock Expansion project, `porytiles dump-tileset-config gTileset_General` yields:

```text
Resolved Metatile Attribute Schema
==================================

  Layout: primary
  Attribute size: 2 bytes

  Fields:
    behavior  mask=0xFF  offset=0 width=8  default=0 provider=include/constants/metatile_behaviors.h (MB_)

  Excluded for this layout: terrain, attribute_2, attribute_3, encounter_type, attribute_5, attribute_7
```

Running it against `gTileset_General_Frlg` instead reports `Layout: frlg`, `Attribute size: 4 bytes`,
and all seven fields, matching the `pokefirered` output shown in
[Checking the resolved schema](#checking-the-resolved-schema).

(customizing-the-schema)=
## Customizing the schema

Two YAML-only config keys control the schema.
Both work at project scope (`porytiles/config.yaml`) or tileset scope
(`porytiles/tilesets/<tileset_name>/config.yaml`), see {doc}`configuration`.

| YAML key | CLI flag | Default | Description |
|----------|----------|---------|-------------|
| `fieldmap.metatile_attr_fields` | *YAML-only* | inferred | Declare the full field list yourself, replacing inference |
| `fieldmap.metatile_attr_field_overrides` | *YAML-only* | empty | Adjust individual fields on top of the global baseline |
| `fieldmap.write_layer_type_column` | `--write-layer-type-column` | `false` | Emit and honor the `layer_type` CSV column |
| `fieldmap.use_frlg_alternate_masks` | `--use-frlg-alternate-masks` | `automatic` | Select the FRLG alternate masks for a tileset |

### Overriding individual fields

`metatile_attr_field_overrides` lets you make small adjustments.
It merges onto the resolved baseline, inferred or explicit,
so you can keep the inferred values and change only what you explicitly want overridden.
Each entry may set `mask`, `frlg_mask`, `default`, and `provider`;
anything you do not set falls through to the baseline.

```yaml
fieldmap:
  metatile_attr_field_overrides:
    # Repurpose FireRed's unused attribute_3 bits and give them a default
    attribute_3:
      default: 1
    # Enter terrain as raw integers instead of TILE_TERRAIN_ names
    terrain:
      provider: null
```

Provider overrides are themselves partial:
you can set just `prefix`, just `header`, `skipped`, or `format`,
and the rest of the values will carry over from the global default.
`provider: null` removes the provider entirely, turning the field into a raw integer column.
Note that a `skipped` list replaces the baseline skip list wholesale rather than adding to it.
Overriding a field that does not exist in the baseline is an error
(the message lists the fields that do exist).

### Declaring fields from scratch

If your project's attribute layout is sufficiently customized that inference cannot describe it,
declare the whole layout explicitly with `metatile_attr_fields`.
Each entry takes `name`, `mask`, optional `frlg_mask`, optional `default`, and an optional `provider` map
with `header`, `prefix`, optional `skipped`, and optional `format`
(`defines-only`, `enums-only`, or `either`; the default is `either`).

Here is a custom 4-byte layout for a project that added a light level and a room type to its attributes:

```yaml
fieldmap:
  metatile_attr_fields:
    - name: behavior
      mask: 0x000001FF
      provider:
        header: include/constants/metatile_behaviors.h
        prefix: MB_
        skipped: [ MB_INVALID ]
    - name: light_level
      mask: 0x00000E00
      default: 0
    - name: room_type
      mask: 0x0F000000
      provider:
        header: include/constants/room_types.h
        prefix: ROOM_
        format: defines-only
```

Porytiles validates the result the same way regardless of where it came from:

- every mask must be a single contiguous run of bits
- masks must not overlap each other or the structural layer type bits
  (bits 12-15 of a 2-byte attribute, bits 29-30 of a 4-byte attribute)
- field names must be unique
- every default must fit its field's width
- every named constant a provider finds must fit the field's width;
  the error shows the offending constant,
  and you must fix it by widening the field's mask or adding the constant to the provider's `skipped` list

Remember that the schema only controls how Porytiles packs the binary.
If you change the layout, your decomp codebase `src/fieldmap.c` must agree with it,
or the game will read garbage.
The safest workflow is the reverse:
change the decomp code first, then let inference pick the change up.

## `metatile_attributes.bin` encoding

For completeness, the exact binary format Porytiles writes:

- One attribute value per metatile, in the same order as `metatiles.bin`
- Each value is 2 or 4 bytes (the resolved attribute size), stored in [little-endian byte order](https://en.wikipedia.org/wiki/Endianness)
- Each field's value is shifted to its mask position and masked in;
  the layer type value (`normal` = 0, `covered` = 1, `split` = 2) is packed into the structural layer type bits
- On decompile, Porytiles extracts exactly the schema fields plus the layer type;
  bits covered by neither are dropped, not preserved
- When parsing an existing binary, the file size must be a multiple of the attribute size,
  and layer type bits must decode to 0, 1, or 2

## Common behaviors

Behaviors are the field you will touch most,
so here is a quick tour of frequently used constants from vanilla `pokeemerald`.
The authoritative list is always your own project's `include/constants/metatile_behaviors.h`.
Names (and numeric values) vary between games and between Expansion versions,
which is why `attributes.csv` stores names instead of raw values.

| Constant | Effect |
|----------|--------|
| `MB_NORMAL` | No special behavior. The default for every metatile without a CSV row. |
| `MB_TALL_GRASS` | Wild encounters, grass rustle animation. |
| `MB_LONG_GRASS` | Taller grass variant with its own animation. |
| `MB_POND_WATER` | Surfable water. |
| `MB_DEEP_WATER` | Surfable deep water; Dive can be used here. |
| `MB_WATERFALL` | Climbable with the Waterfall field move. |
| `MB_PUDDLE` | Splash effect when walked through. |
| `MB_SAND` | Leaves footprints. |
| `MB_ICE` | Player slides across. |
| `MB_JUMP_EAST` (and the other `MB_JUMP_*`) | Ledges; hop in the named direction. |
| `MB_IMPASSABLE_EAST` (and the other `MB_IMPASSABLE_*`) | Blocks movement in the named direction. |
| `MB_ANIMATED_DOOR` | Door with an open/close animation on entry. |
| `MB_LADDER` | Ladder; triggers the climbing warp animation. |

```{tip}
When you need to know what a behavior actually does, grep the decomp for it.
`MB_TALL_GRASS` in `src/` leads you straight to the relevant encounter and animation code that actually checks the value.
```
