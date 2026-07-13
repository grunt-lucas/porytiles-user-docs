# Metatile Attributes Reference

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
An attribute describes the metatile itself. It's the same everywhere the metatile is placed.

### Stock layouts

Ruby, Sapphire, and Emerald use a 2-byte attribute per metatile:

| Bits  | Mask     | Field                       |
|-------|----------|-----------------------------|
| 0-7   | `0x00FF` | behavior (`MB_*` constants) |
| 8-11  | `0x0F00` | unused                      |
| 12-15 | `0xF000` | layer type                  |

FireRed and LeafGreen use a 4-byte attribute and pack in more fields:

| Bits  | Mask         | Field                                                       |
|-------|--------------|-------------------------------------------------------------|
| 0-8   | `0x000001FF` | behavior (`MB_*` constants)                                 |
| 9-13  | `0x00003E00` | terrain (`TILE_TERRAIN_*`: normal, grass, water, waterfall) |
| 14-17 | `0x0003C000` | unused (`attribute_2`)                                      |
| 18-23 | `0x00FC0000` | unused (`attribute_3`)                                      |
| 24-26 | `0x07000000` | encounter type (`TILE_ENCOUNTER_*`: none, land, water)      |
| 27-28 | `0x18000000` | unused (`attribute_5`)                                      |
| 29-30 | `0x60000000` | layer type                                                  |
| 31    | `0x80000000` | unused (`attribute_7`)                                      |

These tables come from each decomp's source:
the masks are declared in `include/global.fieldmap.h` and `src/fieldmap.c`.

```{caution}
Recent `pokeemerald-expansion` versions declare *both* layouts in their source tree,
but a built ROM only ever uses one of them.
Running `make` produces an Emerald-format game and `make firered` a FRLG-format one,
and the build filters out every map layout belonging to the other format.
Porytiles handles that case with a little manual fiddling; see [Expansion's two build flavors](#expansions-two-build-flavors).
```

(the-attribute-schema)=
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
- **role** (optional): marks a field whose value Porytiles itself manages.
  The only role today is `layer_type`.

```{important}
The **layer type is a schema field like any other**, distinguished by its `role: layer_type` marker.
Its mask comes from wherever the rest of the schema comes from:
inference reads `METATILE_ATTR_LAYER_MASK` or the `METATILE_ATTRIBUTE_LAYER_TYPE` entry of `sMetatileAttrMasks`,
and an explicit `metatile_attribute_fields` list declares the field directly.
What sets the role field apart is its *value*: you never type it in the way you type a `behavior` cell.
Porytiles computes each metatile's layer type at compile time from its layer PNGs,
so the role field takes no `default` and no `provider`,
and it gets no data column in `attributes.csv` the way every other field does.
At most one field may carry the role,
and a schema with **no** role field has layer types disabled: no layer-type bits are written or read.

Two different things share the name `layer_type`, so keep them apart:
the schema *field* described here, which is part of the packed binary layout and never appears as a data column,
and an optional trailing **pin column** in `attributes.csv`,
enabled by a `fieldmap.role_pins` entry for the `layer_type` role (off by default),
which lets you hand-pick individual metatiles' layer types instead of accepting the computed value.
The pin column's header defaults to the role's name, `layer_type`, but you can rename it with a `column:` key.
The pin column is an input to the layer-type computation, not the schema field itself;
[Layer types](#layer-types) covers both.
A schema field may only be named `layer_type` if it also carries the role,
so the bare name always refers to the role, never a plain value column.
```

The attribute size itself (1, 2, or 4 bytes) is normally not something you declare in the Porytiles config.
Porytiles derives it from the resolved field masks:
the smallest of 1, 2, or 4 bytes that covers every mask
(Emerald's `0xF000` layer mask needs 2 bytes; FireRed's masks reach bit 31, so 4).
This width is a project-level fact, shared by every tileset:
they all feed the same `metatileAttributes` pointer in `struct Tileset`,
and the engine reads every tileset's attributes at the same width.
Porymap models it the same way (`metatile_attributes_size` in `porymap.project.cfg`),
and the two settings should agree.

Masks can only prove a *minimum* width, though,
so Porytiles cross-checks the element type of `struct Tileset`'s `metatileAttributes` member:
an attribute entry is never narrower than the array element it is stored in.
If that declared element type is *wider* than the masks need
(say, low-byte masks in a `const u32 *` array),
the two sources contradict each other and Porytiles cannot tell which width the project actually reads.
It stops with an error asking you to set `fieldmap.metatile_attribute_size` to settle it.

When inference is impossible or wrong, set `fieldmap.metatile_attribute_size`
(or pass `--metatile-attribute-size`) to pin the width explicitly; an explicit size always wins over inference.
The main case that *requires* it is `pokeemerald-expansion`,
which declares two complete mask layouts in one source tree.
No project file records which build flavor you target (it's a `make` argument),
so Porytiles cannot infer the size there and stops with an error naming this key.
See [Expansion's two build flavors](#expansions-two-build-flavors).

An explicit size is checked in both directions:

- A field mask that needs *more* bits than the pinned width is an error.
  A common way to hit this is by pasting a FireRed mask (for example the `0x60000000` layer-type mask)
  into an Emerald-width project.
  Porytiles asks you to narrow the mask,
  or raise `metatile_attribute_size` if the project really uses a wider attribute.
- A pinned size *wider* than both the masks and the scanned `struct Tileset` declaration is allowed,
  matching Porymap (the unused high bits simply stay zero),
  but Porytiles warns, since nothing in the project corroborates the extra width.

(the-declaration-size)=
### The declaration size

There is a second, related width: the C element type of the `gMetatileAttributes_*` array declarations
Porytiles generates in `src/data/tilesets/metatiles.h` (`const u16` / `INCBIN_U16` and so on).
On most projects it equals the attribute size, and you never think about it.
Porytiles infers it from the pointed-to type of `struct Tileset`'s `metatileAttributes` member
in `include/global.fieldmap.h`
(`const u16 *` on `pokeemerald` and Expansion, `const u32 *` on `pokefirered`),
and falls back to the attribute size when that inference finds nothing.

The case where the two differ is Expansion's FRLG flavor:
attribute entries are 4 bytes, but the arrays are still declared `const u16`
(the engine casts the pointer at runtime).
Porytiles gets that right automatically via the struct inference.
If you need to force it, set `fieldmap.metatile_attribute_declaration_size`
(or pass `--metatile-attribute-declaration-size`).

Note the asymmetry between the two widths.
An attribute entry can span *several* array elements (Expansion's FRLG flavor), but never less than one,
so the declaration scanned from `struct Tileset` acts as a lower bound on the attribute size,
as described above.
The explicit `metatile_attribute_declaration_size` knob has no such effect:
it only changes the generated declarations, never the attribute size.

## Where the schema comes from

You almost never have to write a schema yourself.
Porytiles resolves one schema per project, in this order:

1. **Explicit config.**
   If `fieldmap.metatile_attribute_fields` is set in your Porytiles YAML config, it wins,
   and inference is never consulted for the field content.
   When the project's source still declares a usable layout that disagrees with the explicit list,
   Porytiles warns so you know you are overriding your project's own declarations;
   the explicit fields are used as declared.
2. **Inference from your project.**
   Otherwise Porytiles reads the mask layouts your decomp code already declares (details below).
   A single declared layout is used directly.
   A project that declares more than one (like `pokeemerald-expansion`) must set
   `fieldmap.metatile_attribute_size`, and the size selects the matching layout.
3. **Error.**
   If neither produces fields, compilation stops with an error telling you to
   either add a `metatile_attribute_fields` list or restore the engine declarations so inference can succeed.
   There is no silent fallback.

In every case, `fieldmap.metatile_attribute_field_overrides` is then merged on top,
so you can adjust individual fields without redeclaring the whole layout.
Both keys are documented in [Customizing the schema](#customizing-the-schema).

### Schema inference

For a vanilla or lightly modified project, inference produces the right schema with zero configuration.
It scans:

| File                                     | What Porytiles reads from it                                                                                                                    |
|------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| `include/global.fieldmap.h`              | the `METATILE_ATTRIBUTE_*` enum (which fields exist, in order), any `METATILE_ATTR_*_MASK` defines, and `struct Tileset` (the declaration size) |
| `src/fieldmap.c`                         | the `sMetatileAttrMasks` and `sMetatileAttrShifts` tables (mask values per field)                                                               |
| `include/constants/metatile_behaviors.h` | the `MB_*` behavior constants (as defines or enum members)                                                                                      |

Field names come from the enum:
`METATILE_ATTRIBUTE_BEHAVIOR` becomes `behavior`,
`METATILE_ATTRIBUTE_TERRAIN` becomes `terrain`,
and a numbered entry like `METATILE_ATTRIBUTE_2` becomes the raw field `attribute_2`.
`METATILE_ATTRIBUTE_LAYER_TYPE` becomes the field `layer_type` carrying the `layer_type` role
(see the earlier note); it never gets a provider or a default.

Inference also attaches providers where it can find them:

- `behavior` gets the `MB_` constants from `include/constants/metatile_behaviors.h`
  (skipping `MB_INVALID`, which is a sentinel rather than a real behavior).
- Other named fields are searched against the `global.fieldmap.h` enums by prefix:
  `terrain` finds `TILE_TERRAIN_*`, `encounter_type` finds `TILE_ENCOUNTER_*`.
- Numbered fields (`attribute_2` and friends) stay raw.

Most projects declare exactly one mask layout, and inference just uses it.
A project can declare more than one:
`pokeemerald-expansion`'s bare `METATILE_ATTR_*_MASK` defines describe its 2-byte Emerald layout,
while its `*_MASK_FRLG` defines and `sMetatileAttrMasks` table describe the 4-byte FRLG layout.
Inference keeps every layout it finds,
and with more than one, resolution stops with an error unless `fieldmap.metatile_attribute_size` is set:
the size selects the layout whose required width matches it
(a layout that merely fits inside a wider configured size is accepted when it is the only one that fits),
so on Expansion the explicit size doubles as the layout selector.
See [Expansion's two build flavors](#expansions-two-build-flavors).

Every field needs a mask declared somewhere in the source.
A field whose mask cannot be determined is a fatal error,
with a message listing your options
(restore `sMetatileAttrMasks[]`, add a `METATILE_ATTR_<NAME>_MASK` define, or declare the layout in Porytiles config).
A project that declares no attribute masks at all fails the same way:
there is nothing to infer from, so Porytiles asks you to restore the mask declarations
or write a `metatile_attribute_fields` list.

Disagreements are handled conservatively:
if a `METATILE_ATTR_*_MASK` define and the `sMetatileAttrMasks` table disagree, the define wins and Porytiles warns.
If an `sMetatileAttrShifts` entry does not match its mask's bit position, the mask wins and Porytiles warns.

(checking-the-resolved-schema)=
### Checking the resolved schema

`dump-attribute-schema` prints the schema Porytiles resolved,
after config, inference, overrides, and mask-layout selection have all been applied.
Run it whenever you are unsure which fields your CSV needs:

```bash
porytiles dump-attribute-schema gTileset_General
```

Against a vanilla `pokefirered` project, the output looks like this:

```text
Resolved Metatile Attribute Schema
==================================

  Attribute size: 4 bytes (inferred from the sMetatileAttrMasks table (./include/global.fieldmap.h))
  Declaration size: 4 bytes (const u32, inferred from struct Tileset's metatileAttributes member (./include/global.fieldmap.h))
  Fields from: the sMetatileAttrMasks table

  Fields:
    behavior  mask=0x1FF  offset=0 width=9  default=0 provider=include/constants/metatile_behaviors.h (MB_)
    terrain  mask=0x3E00  offset=9 width=5  default=0 provider=include/global.fieldmap.h (TILE_TERRAIN_)
    attribute_2  mask=0x3C000  offset=14 width=4  default=0
    attribute_3  mask=0xFC0000  offset=18 width=6  default=0
    encounter_type  mask=0x7000000  offset=24 width=3  default=0 provider=include/global.fieldmap.h (TILE_ENCOUNTER_)
    attribute_5  mask=0x18000000  offset=27 width=2  default=0
    layer_type  mask=0x60000000  offset=29 width=2  default=0  role=layer_type
    attribute_7  mask=0x80000000  offset=31 width=1  default=0
```

The `layer_type` row carries `role=layer_type`:
it is part of the packed layout, but Porytiles fills its value in itself,
so it gets no data column in `attributes.csv`
(the optional trailing pin column is a separate mechanism; see [Layer types](#layer-types)).

When no schema can be resolved
(stock Expansion without `fieldmap.metatile_attribute_size`, for example),
the command prints the reason instead of a schema.
To see the config values feeding into resolution,
`dump-tileset-config` shows each `fieldmap.*` key with the full provenance chain that produced it;
see {ref}`dump-config`.

## The `attributes.csv` file

`attributes.csv` lives in each tileset's `porytiles_src/` directory,
next to the layer PNGs.
Porytiles reads in on compile and writes it on decompile/import.

The format:

- **Header row (required).**
  `id`, then one column per schema field in schema order
  (excluding the `layer_type` role field, whose value Porytiles computes itself),
  then one trailing **pin column** for each `fieldmap.role_pins` entry, in config order
  (its header comes from the entry's `column:` key, or the role's name when that key is omitted;
  see [Layer types](#layer-types)).
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
  Empty cells are only allowed in a trailing pin column.

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

| Layers with content                                        | Inferred layer type |
|------------------------------------------------------------|---------------------|
| bottom only, or bottom + middle                            | `covered`           |
| bottom + top                                               | `split`             |
| anything else (middle only, middle + top, top only, empty) | `normal`            |

In other words, you just draw each metatile on the layers where it belongs,
and the layer type follows automatically.
Triple-layer tilesets skip all of this:
in triple-layer mode every metatile renders all three layers and the stored layer type is always `normal`.

```{note}
If the resolved schema has no `layer_type` role field
(your project's source declares no layer-type mask,
or your explicit `metatile_attribute_fields` list omits the field),
layer types are disabled: every metatile is treated as `normal` and no layer-type bits are written.
This matches Porymap's behavior when its `metatile_layer_type_mask` is `0`.
```

```{note}
TODO: insert screencap of a metatile drawn across two layer PNGs and the resulting layer type in Porymap
```

### Pinning with `role_pins`

This is the pin column that [The attribute schema](#the-attribute-schema) warned shares its name
with the `layer_type` role field.
The role field is where the layer-type bits live in the packed binary;
the pin column is an optional CSV affordance for hand-setting the value Porytiles packs there.

Inference covers basically every real metatile.
For the rare case where you need a specific layer type that inference would not pick,
pin the `layer_type` role with a `fieldmap.role_pins` entry:

```yaml
fieldmap:
  role_pins:
    - role: layer_type
```

With the role pinned:

- `attributes.csv` gains a trailing pin column (named `layer_type` by default),
  and Porytiles writes one row per metatile so every metatile has a cell to fill.
- A filled cell (`normal`, `covered`, or `split`, case-insensitive) **pins** that metatile's layer type.
  A pinned value beats inference.
- A blank cell means "infer as usual", and stays blank when Porytiles rewrites the file,
  so pins survive compile/decompile round trips.

To give the column a different header (for example, to make it obvious the column belongs to Porytiles,
or to match a column name your own tooling already expects), add a `column:` key:

```yaml
fieldmap:
  role_pins:
    - role: layer_type
      column: my_layer_type
```

The custom name becomes a literal CSV header cell,
so it cannot contain commas or line breaks, and cannot start or end with whitespace.
It also cannot be `id` or collide with any attribute field name.

When the `layer_type` role is **not** pinned (the default), a `layer_type` column in the file is ignored:
Porytiles emits a one-time `role-pin-column` warning and infers as usual.
The same warning fires for a stale `layer_type` column left over after you pin the role under a different `column:` name.

If a pinned (or inferred) layer type drops a layer that actually contains visible tiles,
Porytiles warns (tag `dual-layer-drop`) that those tiles will be discarded.
That warning usually means the pin is wrong, or content is drawn on a layer it should not be.

This is a per-tileset kind of setting,
so you should prefer setting it in `porytiles/tilesets/<tileset_name>/config.yaml` rather than project-wide
(see {doc}`configuration` for config file locations and layering).

### Round-tripping the pin column

Import and decompile fill the pin column deliberately, so it survives a round trip:

- **Import, or decompile with no `attributes.csv`:** every row is pinned to the layer type decoded from
  `metatile_attributes.bin`. A fresh import therefore hands you a fully-pinned column you can edit.
- **Decompile with `attributes.csv` present:**
  - If the pin column is missing, Porytiles adds it and pins every row from the bin (same as a fresh import).
  - If the pin column is present, Porytiles preserves each row's state: a blank cell stays blank
    (inference is trusted), and a filled cell stays pinned with its value refreshed from the bin.
  - A row that was deleted from the file comes back unpinned (blank), like any other row you left blank.

### Triple-layer content in a dual-layer tileset

A metatile with non-transparent content on all three layers can only render in a triple-layer tileset.
In a dual-layer compile that is an error by default:
Porytiles points at the offending subtiles and suggests either enabling triple-layer metatiles or the escape hatch below.

Setting `tileset.ignore_triple_layer_content: true` (or `--ignore-triple-layer-content`)
demotes the error to a warning and compiles anyway, dropping one layer group per offending metatile.
Which group is dropped follows that metatile's *effective* layer type.
A `fieldmap.role_pins` `layer_type` pin, if you set one, chooses the group directly.
Without a pin there is nothing to infer from all-three-layers content,
so it falls back to `normal`, which drops the bottom layer.
Note that this fallback is not a real inference:
a genuinely triple metatile has no discernible layer type,
so unpinned it always resolves to `normal`.

(expansions-two-build-flavors)=
## Expansion's two build flavors

The `pokeemerald-expansion` decomp base can be built in two flavors:
`make` produces a game with Emerald-format metatile attributes,
and `make firered` one with FRLG-format attributes.
The source tree permanently declares *both* mask layouts
(the bare `METATILE_ATTR_*_MASK` defines for Emerald,
the `*_MASK_FRLG` defines and `sMetatileAttrMasks` table for FRLG),
and each map layout in `data/layouts/layouts.json` carries a `layout_version` tag.
At build time, the map-data generator skips every layout whose tag disagrees with the flavor being built,
so a single ROM only ever links one attribute format.

Because the flavor is a `make` argument, no project file records which one you target,
and Porytiles cannot infer the attribute size on Expansion.
You must set it explicitly, and the size doubles as the layout selector:

```yaml
# porytiles/config.yaml on pokeemerald-expansion
fieldmap:
  metatile_attribute_size: 2   # emerald flavor; use 4 for the firered flavor
```

With `2`, Porytiles selects the Emerald mask layout: `behavior` (mask `0x00FF`)
plus the `layer_type` role field (mask `0xF000`), packed into 2-byte entries.
With `4`, it selects the FRLG layout: the full eight-field set with masks reaching bit 31,
including the `layer_type` role field at `0x60000000`, and 4-byte entries.
Without the key, Porytiles stops with an error naming it.

One Expansion quirk Porytiles handles automatically:
`pokefirered` declares its attribute arrays `const u32`, so declaration and entry width agree,
but Expansion declares *all* its attribute arrays `const u16`, FRLG flavor included,
and `src/fieldmap.c` casts the pointer to `const u32 *` at runtime for FRLG layouts.
So on the FRLG flavor, `metatile_attributes.bin` entries are 4 bytes
(Expansion's included `general_frlg/metatile_attributes.bin` is 2560 bytes, 640 metatiles at 4 bytes each)
while the generated `INCBIN` declarations stay `const u16`.
Porytiles reads that convention from `struct Tileset` (see [The declaration size](#the-declaration-size)),
so the generated declarations match the surrounding code without any extra configuration.

```{note}
`pokeemerald-expansion` documents this setup in its own
[`docs/tutorials/how_to_frlg.md`](https://github.com/rh-hideout/pokeemerald-expansion/blob/upcoming/docs/tutorials/how_to_frlg.md),
and its
[`frlg_metatile_behavior_converter.py`](https://github.com/rh-hideout/pokeemerald-expansion/blob/upcoming/migration_scripts/frlg_metatile_behavior_converter.py)
migration script reads and writes 4-byte entries.
```

As elsewhere, `dump-attribute-schema` shows what's going on.
On a stock Expansion project,
`porytiles dump-attribute-schema gTileset_General --metatile-attribute-size 2` yields:

```text
Resolved Metatile Attribute Schema
==================================

  Attribute size: 2 bytes (CLI)
  Declaration size: 2 bytes (const u16, inferred from struct Tileset's metatileAttributes member (./include/global.fieldmap.h))
  Fields from: the bare METATILE_ATTR_*_MASK defines

  Fields:
    behavior  mask=0xFF  offset=0 width=8  default=0 provider=include/constants/metatile_behaviors.h (MB_)
    layer_type  mask=0xF000  offset=12 width=4  default=0  role=layer_type
```

Running it with `--metatile-attribute-size 4` instead reports `Attribute size: 4 bytes (CLI)`,
a declaration size still of 2 bytes (`const u16`),
and all eight FRLG fields, matching the `pokefirered` output shown in
[Checking the resolved schema](#checking-the-resolved-schema)
(except for the declaration size, which is 4 bytes there).

(customizing-the-schema)=
## Customizing the schema

Two YAML-only config keys control the schema:
`metatile_attribute_fields` and `metatile_attribute_field_overrides`.
The schema is a project-level property (one attribute layout per project),
so set those two in `porytiles/config.yaml`; see {doc}`configuration`.
A third key, `role_pins`, appears alongside them below but does not control the schema:
it only controls the CSV pin columns, never the binary layout, so it makes sense per tileset.
All three are YAML-only (there is no CLI flag; the old `--write-layer-type-column` flag was removed in favor of
`role_pins`).

| YAML key                                      | CLI flag    | Default  | Description                                                 |
|-----------------------------------------------|-------------|----------|-------------------------------------------------------------|
| `fieldmap.metatile_attribute_fields`          | *YAML-only* | inferred | Declare the full field list yourself, replacing inference   |
| `fieldmap.metatile_attribute_field_overrides` | *YAML-only* | empty    | Adjust individual fields on top of the global baseline      |
| `fieldmap.role_pins`                          | *YAML-only* | empty    | Emit and honor a trailing pin column per role (see below)   |

### Overriding individual fields

`metatile_attribute_field_overrides` lets you make small adjustments.
It merges onto the resolved baseline, inferred or explicit,
so you can keep the inferred values and change only what you explicitly want overridden.
Each entry may set `mask`, `default`, `provider`, and `role`;
anything you do not set falls through to the baseline.

```yaml
fieldmap:
  metatile_attribute_field_overrides:
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

The `role` member works the same way:
`role: layer_type` puts the layer-type role on a field, and `role: null` clears it.
Overrides apply per field, so to *move* the role you need both,
`role: null` on the field that has it and `role: layer_type` on the new one
(two fields carrying the role at once is an error).
Clearing the role without assigning it elsewhere disables layer types.

### Declaring fields from scratch

If your project's attribute layout is sufficiently customized that inference cannot describe it,
declare the whole layout explicitly with `metatile_attribute_fields`.
Each entry takes `name`, `mask`, optional `default`, optional `role`, and an optional `provider` map
with `header`, `prefix`, optional `skipped`, and optional `format`
(`defines-only`, `enums-only`, or `either`; the default is `either`).

Here is a custom 4-byte layout for a project that added a light level and a room type to its attributes:

```yaml
fieldmap:
  metatile_attribute_fields:
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
    - name: layer_type
      mask: 0x60000000
      role: layer_type
```

The explicit list is the complete layout, taken exactly as declared.
Two consequences of that:

- **Omitting the layer_type role field disables layer types**, with no error or warning;
  the resolved-schema remark simply reports "layer type disabled".
- **If the project's source still declares a usable mask layout that differs from your list**,
  Porytiles warns with a summary of the differences
  (fields present on only one side, masks that disagree, role mismatches).
  The explicit fields win; the warning is a heads-up that your config
  disagrees with your own engine declarations.

Porytiles validates the result the same way regardless of where it came from:

- every mask must be a single contiguous run of bits
- masks must not overlap each other
- field names must be unique
- at most one field may carry `role: layer_type`,
  and a role field takes no `default` and no `provider`
- a field may be named `layer_type` only if it carries the role
  (the bare name is reserved for the CSV pin column)
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
- Each value is 1, 2, or 4 bytes (the resolved attribute size), stored in [little-endian byte order](https://en.wikipedia.org/wiki/Endianness)
- Each field's value is shifted to its mask position and masked in;
  the layer type value (`normal` = 0, `covered` = 1, `split` = 2) is packed through the
  `layer_type` role field's mask like any other field
- On decompile, Porytiles extracts exactly the schema fields
  (the role field decodes into the metatile's layer type rather than a CSV column);
  bits covered by no field are dropped, not preserved
- When parsing an existing binary, the file size must be a multiple of the attribute size,
  and the layer-type bits must decode to 0, 1, or 2

## Common behaviors

Behaviors are the field you will touch most,
so here is a quick tour of frequently used constants from vanilla `pokeemerald`.
The authoritative list is always your own project's `include/constants/metatile_behaviors.h`.
Names (and numeric values) vary between games and between Expansion versions,
which is why `attributes.csv` stores names instead of raw values.

| Constant                                               | Effect                                                                 |
|--------------------------------------------------------|------------------------------------------------------------------------|
| `MB_NORMAL`                                            | No special behavior. The default for every metatile without a CSV row. |
| `MB_TALL_GRASS`                                        | Wild encounters, grass rustle animation.                               |
| `MB_LONG_GRASS`                                        | Taller grass variant with its own animation.                           |
| `MB_POND_WATER`                                        | Surfable water.                                                        |
| `MB_DEEP_WATER`                                        | Surfable deep water; Dive can be used here.                            |
| `MB_WATERFALL`                                         | Climbable with the Waterfall field move.                               |
| `MB_PUDDLE`                                            | Splash effect when walked through.                                     |
| `MB_SAND`                                              | Leaves footprints.                                                     |
| `MB_ICE`                                               | Player slides across.                                                  |
| `MB_JUMP_EAST` (and the other `MB_JUMP_*`)             | Ledges; hop in the named direction.                                    |
| `MB_IMPASSABLE_EAST` (and the other `MB_IMPASSABLE_*`) | Blocks movement in the named direction.                                |
| `MB_ANIMATED_DOOR`                                     | Door with an open/close animation on entry.                            |
| `MB_LADDER`                                            | Ladder; triggers the climbing warp animation.                          |

```{tip}
When you need to know what a behavior actually does, grep the decomp for it.
`MB_TALL_GRASS` in `src/` leads you straight to the relevant encounter and animation code that actually checks the value.
```
