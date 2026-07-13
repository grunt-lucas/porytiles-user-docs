# Configuration Reference

Porytiles works out of the box with no configuration at all.
Every value described here has a sensible default,
and the basic fieldmap configuration values are read from your decomp project's source files,
so you can theoretically compile new tilesets without a single line of YAML.

Configuration allows you to change advanced settings like:
- lock tiles or palettes so you can edit vanilla tilesets without breaking dependent tilesets,
- pick a different palette-packing algorithm,
- silence a class of annoying warnings,
- point Porytiles at non-standard asset directories.

This page is an exhaustive reference.
If you just want a simple introduction, the {doc}`quickstart` doc has a shorter overview.

## How configuration is resolved

Porytiles builds each tileset's configuration from eight sources.
For **every individual key**, it walks the list below from top to bottom and uses the first source that provides a value.
Resolution is per-key, not per-file:
a command-line option can override one key while the rest still come from your YAML or the built-in defaults.

|    Priority | Source                 | Where the value comes from                            |
|------------:|------------------------|-------------------------------------------------------|
| 1 (highest) | Command-line option    | A `--key value` flag any of the relevant commands     |
|           2 | Per-tileset local YAML | `porytiles/tilesets/<tileset_name>/config.local.yaml` |
|           3 | Per-tileset YAML       | `porytiles/tilesets/<tileset_name>/config.yaml`       |
|           4 | Project local YAML     | `porytiles/config.local.yaml`                         |
|           5 | Project YAML           | `porytiles/config.yaml`                               |
|           6 | Fieldmap header        | The `#define`s in `include/fieldmap.h`                |
|  7 (lowest) | Built-in default       | The default baked into Porytiles                      |

Two critical consequences worth reiterating:

- **Per-tileset beats project-wide, and local beats committed.** A key set in a tileset's `config.yaml` overrides the same key in the project-wide `config.yaml`, and either `config.local.yaml` overrides its committed sibling at the same scope.
- **The `fieldmap.*` values come from your project for free.** Source 6 reads your decomp project's own `include/fieldmap.h`, so the tile, metatile, and palette limits already match your build. The metatile attribute sizes and schema are likewise derived from your project's own attribute masks and declarations whenever you leave those keys unset (see {doc}`metatile-attributes`). You only set them by hand when for some reason, your project diverges from those sources.

## Where configuration YAML files live

All configuration YAML files live under the `porytiles/` management directory at your project root:

```text
porytiles/
├── config.yaml              # project-wide, committed
├── config.local.yaml        # project-wide, machine-local (gitignore-friendly)
└── tilesets/
    └── gTileset_Example/
        ├── config.yaml        # per-tileset, committed
        └── config.local.yaml  # per-tileset, machine-local
```

Every one of these files is optional.
Create only the ones you need.

The `config.local.yaml` files are meant for overrides you don't want to commit:
a temporary path tweak, or a noisier diagnostic filter while you debug, etc.
Add `config.local.yaml` to your `.gitignore` and your committed `config.yaml` stays clean for the rest of the team.

### File format

Each file is YAML, organized under a few top-level keys that mirror the {ref}`value reference <value-reference>` below:
`fieldmap`, `tileset`, `diagnostics`, and the standalone `verify_checksums`.
Nest keys to match the dotted paths in this document, so `tileset.tiles.edit_mode` becomes:

```yaml
tileset:
  tiles:
    edit_mode: patch
```

```{caution}
Porytiles validates every key in your YAML against the set of known configuration paths.
An unrecognized key is a hard error (`unknown-config-key`),
so a typo like `tileset.tile.edit_mode` stops the compile instead of being ignored.
```

(cli-overrides)=
## Overriding values on the command line

Nearly every value can be set with a command-line option, which is handy for one-off compiles where you don't want to touch any YAML.
The command-line is the highest-priority source, so for that one run it overrides every file and the built-in default:

```bash
porytiles compile-tileset gTileset_Example --tiles-edit-mode optimize --packing-strategy best-fusion
```

The flag names are listed alongside each value in the reference below, and `porytiles compile-tileset --help` prints the authoritative set.
A few conventions:

- **Boolean values** also get a `--no-` form to turn them off, for example `--no-verify-checksums` or `--no-pal-hints-enabled`.
- **List values** (such as `--primary-pairing-partners` or `--diagnostic-warnings-exclude`) accept multiple arguments.
- **Five values are YAML-only.** Palette hints, packing strategy parameters, per-animation overrides, and the metatile attribute field lists (`metatile_attribute_fields` and `metatile_attribute_field_overrides`) are too structured to express as a flag, so they can only be set in a config file. They're marked *YAML-only* in the reference.

```{tip}
Option names don't always match the YAML path one-to-one.
A few are abbreviated (`tileset.palettes.edit_mode` is `--pals-edit-mode`,
`tileset.animations.palette_resolution_strategy` is `--anim-pal-resolution-strategy`).
When in doubt, trust the reference tables below or `--help` rather than guessing from the path.
You can also set up shell completion to make it even easier, see {doc}`installation`.
```

(dump-config)=
## Inspecting the resolved configuration

Because values come from up to seven places, "what is this key actually set to, and why?" is a real question.
`dump-tileset-config` provides the answer for a specific tileset:

```bash
porytiles dump-tileset-config gTileset_Example
```

For each key it prints the resolved value, the exact source it came from, and the full provider chain:

```text
Number Of Tiles In Primary
--------------------------
  'Number Of Tiles In Primary' is '512' due to configuration:

  NUM_TILES_IN_PRIMARY = 512
  Source: ./include/fieldmap.h:8

      7:
  ➞   8:   #define NUM_TILES_IN_PRIMARY 512
      9:   #define NUM_METATILES_IN_PRIMARY 512

  Provider Chain:
    ○ CliOptionProvider (not provided)
    ○ YamlFileProvider (not provided)
    ✓ HeaderDefineProvider = 512
    ○ DefaultProvider = 512
```

Read the **Provider Chain** from top to bottom:
`✓` marks the source that won,
`○` marks a source that either had nothing to offer for this key
or had a value that wasn't selected.
You can see in the above example
that some providers did not provide a value for the key at all,
while others provided a value but were superseded by a provider with higher priority.
For a value that fell through to its default, the source reads `default value` and only `DefaultProvider` is checked.

This is the fastest way to debug a surprising result.
Just dump the config, find the relevant key, and the chain shows you which file (or flag) to change.

The tileset has to exist in the project, so a misspelled name errors out instead of dumping
a plausible-looking chain of project-level values.
To preview the config a not-yet-created tileset would inherit,
pass `--allow-missing-tileset` which overrides this behavior.

```{important}
The chain collapses all four YAML files into a single `YamlFileProvider` row,
but the **Source** line above it always names the exact file and line a value came from,
so you can tell project YAML from per-tileset YAML at a glance.
```

(value-reference)=
## Configuration value reference

The rest of this page lists every configuration value, grouped by its top-level YAML key.
For each value you get its YAML path, its CLI flag (or *YAML-only*), the default, and what it does.
Each group links to the guide that explains the underlying subsystem in depth.

### `fieldmap` — hardware layout

These describe your tile, metatile, and palette budget.
Porytiles reads all of them from `include/fieldmap.h` automatically,
so in a normal decomp project you never set them by hand.
Override them only when you explicitly want a particular run's values to differ from that header.

| YAML key                            | CLI flag                     | Default | Description                                         |
|-------------------------------------|------------------------------|---------|-----------------------------------------------------|
| `fieldmap.num_tiles_in_primary`     | `--num-tiles-in-primary`     | `512`   | Tiles reserved for the primary tileset.             |
| `fieldmap.num_tiles_total`          | `--num-tiles-total`          | `1024`  | Total tile capacity (primary plus secondary).       |
| `fieldmap.num_metatiles_in_primary` | `--num-metatiles-in-primary` | `512`   | Metatiles reserved for the primary tileset.         |
| `fieldmap.num_metatiles_total`      | `--num-metatiles-total`      | `1024`  | Total metatile capacity.                            |
| `fieldmap.num_palettes_in_primary`  | `--num-pals-in-primary`      | `6`     | Hardware palettes reserved for the primary tileset. |
| `fieldmap.num_palettes_total`       | `--num-pals-total`           | `13`    | Total hardware palettes available.                  |
| `fieldmap.max_map_data_size`        | `--max-map-data-size`        | `10240` | The `MAX_MAP_DATA_SIZE` map-buffer limit.           |
| `fieldmap.num_tiles_per_metatile`   | `--num-tiles-per-metatile`   | `8`     | `8` for dual-layer tilesets, `12` for triple-layer. |

### `fieldmap` — metatile attributes

These control the metatile attribute schema: which fields exist in each metatile's packed attribute value,
how wide each attribute entry is, and how the `attributes.csv` layer type column behaves.
The schema is a project-level property (a project has exactly one attribute layout, shared by every tileset),
so set these keys in `porytiles/config.yaml`, not per tileset.
Setting these keys to different values in different tilesets can result in inconsistent, buggy behavior.
The whole system, including the field and override formats, is documented in {doc}`metatile-attributes`;
this table is just the key listing.

| YAML key                                        | CLI flag                                | Default                             | Description                                                                                  |
|-------------------------------------------------|-----------------------------------------|-------------------------------------|----------------------------------------------------------------------------------------------|
| `fieldmap.metatile_attribute_size`              | `--metatile-attribute-size`             | (inferred)                          | The size in bytes of each metatile attribute entry (`1`, `2`, or `4`).                       |
| `fieldmap.metatile_attribute_declaration_size`  | `--metatile-attribute-declaration-size` | (inferred, then the attribute size) | The declared element width of generated `gMetatileAttributes_*` arrays (`1`, `2`, or `4`).   |
| `fieldmap.metatile_attribute_fields`            | *YAML-only*                             | (inferred)                          | Declare the attribute field list yourself, replacing schema inference.                       |
| `fieldmap.metatile_attribute_field_overrides`   | *YAML-only*                             | (none)                              | Adjust individual fields on top of the inferred or declared list.                            |
| `fieldmap.role_pins`                            | *YAML-only*                             | (none)                              | Emit and honor a trailing pin column in `attributes.csv` for a schema role.                  |

`fieldmap.role_pins` is an exception to the project-level rule:
it never touches the binary attribute layout, only the CSV pin columns,
so setting it per tileset is fine and often what you want.

**`metatile_attribute_size`** normally stays unset:
Porytiles derives the attribute width from the attribute masks your project declares
(the `METATILE_ATTR_*_MASK` defines and the `sMetatileAttrMasks` table).
Two situations require it:
1. `pokeemerald-expansion`, which declares both the emerald and FRLG mask layouts and picks one per build (`make` vs `make firered`),
   so you must set the size explicitly and it selects the matching layout (`2` for emerald, `4` for FRLG).
2. Projects whose `struct Tileset` declares a wider element type than the masks need,
   where the two sources contradict each other and Porytiles asks for the size rather than guessing.

See {doc}`metatile-attributes` for more details.

**`metatile_attribute_declaration_size`** normally stays unset:
Porytiles infers the declared element width from `struct Tileset`'s `metatileAttributes` member
in `include/global.fieldmap.h`, and it defaults to the attribute size when that inference finds nothing.
The case where the two differ is Expansion's FRLG flavor,
whose 4-byte attribute entries are declared as `const u16` arrays.

**`metatile_attribute_fields`** and **`metatile_attribute_field_overrides`** normally stay unset:
Porytiles infers the attribute schema from your project's own declarations,
including the layer-type field, which is an ordinary schema field marked with `role: layer_type`.
Set `metatile_attribute_field_overrides` to tweak individual fields (a mask, a default, a value-name provider, the role),
and use the full `metatile_attribute_fields` list
only if your project's attribute layout is sufficiently customized that inference cannot describe it.

**`role_pins`** adds a trailing pin column to `attributes.csv` for a schema role (currently only `layer_type`),
letting you pin a metatile's layer type instead of relying on inference.
The column header defaults to the role name but can be renamed with a `column:` key.
This is the one key in this group that makes sense per tileset,
so prefer setting it in `porytiles/tilesets/<tileset_name>/config.yaml`.
See {doc}`metatile-attributes` for more on pinning.

### `tileset.paths` — asset directories

Where each tileset's source and binary assets live, relative to the project root.
`src` holds the editable `porytiles_src/` assets; `bin` holds the generated `porytiles_bin/` files that Porymap reads.

| YAML key                      | CLI flag                        | Default                   | Description                              |
|-------------------------------|---------------------------------|---------------------------|------------------------------------------|
| `tileset.paths.primary.src`   | `--tileset-paths-primary-src`   | `data/tilesets/primary`   | Source directory for primary tilesets.   |
| `tileset.paths.primary.bin`   | `--tileset-paths-primary-bin`   | `data/tilesets/primary`   | Binary directory for primary tilesets.   |
| `tileset.paths.secondary.src` | `--tileset-paths-secondary-src` | `data/tilesets/secondary` | Source directory for secondary tilesets. |
| `tileset.paths.secondary.bin` | `--tileset-paths-secondary-bin` | `data/tilesets/secondary` | Binary directory for secondary tilesets. |

### `tileset` — transparency

| YAML key                         | CLI flag                         | Default                   | Description                                                                    |
|----------------------------------|----------------------------------|---------------------------|--------------------------------------------------------------------------------|
| `tileset.extrinsic_transparency` | `--extrinsic-transparency R,G,B` | `[255, 0, 255]` (magenta) | The RGB color treated as transparent during compilation. Must be fully opaque. |

Pixels in this color (or with an alpha of 0) become transparent in the compiled tileset.
The mental model for source layers is covered in the {doc}`quickstart`.

### `tileset` — layer mode content

| YAML key                              | CLI flag                        | Default | Description                                                                                |
|---------------------------------------|---------------------------------|---------|--------------------------------------------------------------------------------------------|
| `tileset.ignore_triple_layer_content` | `--ignore-triple-layer-content` | `false` | Demote the triple-layer-content-in-dual-mode error to a warning, dropping one layer group. |

By default, a dual-layer compile hard-errors when a metatile has visible content on all three layers.
Turning this on demotes that error to a warning
and lets the compilation proceed by dropping one layer group per offending metatile.
Which group is dropped follows the metatile's effective layer type:
a `fieldmap.role_pins` `layer_type` pin if you set one,
otherwise a fallback to Layer Type Normal that drops the bottom group.
See {doc}`metatile-attributes` for more information.

### `tileset.tiles` — the `tiles.png` artifact

| YAML key                          | CLI flag                   | Default      | Description                                                |
|-----------------------------------|----------------------------|--------------|------------------------------------------------------------|
| `tileset.tiles.edit_mode`         | `--tiles-edit-mode`        | `optimize`   | How much `tiles.png` may change during a compile.          |
| `tileset.tiles.palette_mode`      | `--tiles-pal-mode`         | `true-color` | The color mode used when writing `tiles.png`.              |
| `tileset.tiles.sharing.packing`   | `--tile-sharing-packing`   | `off`        | Whether the packer accounts for tile-sharing shape groups. |
| `tileset.tiles.sharing.alignment` | `--tile-sharing-alignment` | `off`        | The palette-slot alignment strategy for tile sharing.      |

**`edit_mode`** controls how freely a compile may rewrite the tiles artifact:

- `locked` — the artifact can't change; the compiler must reuse what's already in the base tileset.
- `patch` — the compiler may fill open (transparent) slots but won't disturb existing tiles.
- `optimize` *(default)* — the artifact is cleared and packed from scratch (the original Porytiles behavior).

**`palette_mode`**:

- `true-color` *(default)* — write an 8-bit indexed PNG that carries the real palette colors, handy for visually debugging tile layout. Porymap 5.2.0 and later fully supports this format, as does `gbagfx` (it only checks the bottom four bits when building `tiles.4bpp`).
- `greyscale` — map indices to greyscale, matching the vanilla game tileset convention

**`sharing.packing`** and **`sharing.alignment`** tune tile-sharing deduplication:

- `sharing.packing`: `off` *(default)*, `biased` (a soft penalty steers shape-group siblings toward different palettes), or `optimal` *(planned)*.
- `sharing.alignment`: `off` *(default)*, `greedy` (best-effort slot alignment via indirect link resolution), or `optimal` *(planned)*.

The full mechanism is explained in {doc}`tile-sharing`.

### `tileset.palettes` — palette packing

| YAML key                                   | CLI flag              | Default        | Description                                             |
|--------------------------------------------|-----------------------|----------------|---------------------------------------------------------|
| `tileset.palettes.edit_mode`               | `--pals-edit-mode`    | `optimize`     | How much the palette files may change during a compile. |
| `tileset.palettes.packing.strategy`        | `--packing-strategy`  | `backtracking` | The palette-packing algorithm.                          |
| `tileset.palettes.packing.strategy_params` | *YAML-only*           | (preset)       | Per-strategy tuning parameters.                         |
| `tileset.palettes.packing.hints_enabled`   | `--pal-hints-enabled` | `true`         | Whether palette hints are fed to the packer.            |
| `tileset.palettes.packing.hints`           | *YAML-only*           | (none)         | Named color groups the packer should keep together.     |

**`edit_mode`** takes the same `locked` / `patch` / `optimize` values as `tiles.edit_mode` above, applied to the palette files.

**`packing.strategy`** selects the algorithm:

- `backtracking` *(default)* — DFS/BFS backtracking search; handles the widest range of inputs.
- `best-fusion` — fast greedy weighted-cost packing, no retries; may fail on hard inputs.
- `overload-and-remove` — greedy with multi-start retries to escape local optima.

**`packing.strategy_params`** tunes the selected strategy.
Only the block matching the active strategy is read; `best-fusion` takes no parameters.
When omitted, each strategy uses a built-in preset:

```yaml
tileset:
  palettes:
    packing:
      strategy: backtracking
      strategy_params:
        backtracking:
          search_algorithm: bfs       # dfs or bfs
          node_cutoff: 5000           # max nodes to explore before giving up
          best_branches: 3            # keep the top-N branches at each level
          smart_prune: true           # enable heuristic pruning
        overload_and_remove:
          max_attempts: 100           # number of multi-start retries
          seed: 42                    # RNG seed, for reproducibility
          shuffle_strategy: noisy-ffd # single-ffd, noisy-ffd, or random
```

**`packing.hints`** tells the packer that certain colors should land in the same hardware palette.
Each hint is a named group of RGB colors; the packer injects them as synthetic tiles to bias color grouping.
This is useful when you know certain colors co-occur within a tile and want to guarantee they share a palette:

```yaml
tileset:
  palettes:
    packing:
      hints_enabled: true
      hints:
        - name: foliage
          colors:
            - [12, 190, 20]
            - [40, 210, 10]
```

The packing algorithms and when to tune them are covered in {doc}`palette-packing`.

### `tileset.animations` — animation handling

| YAML key                                                       | CLI flag                                       | Default                | Description                                                                |
|----------------------------------------------------------------|------------------------------------------------|------------------------|----------------------------------------------------------------------------|
| `tileset.animations.frame_linking`                             | `--frame-linking`                              | `automatic`            | How animation frames link to metatile entries.                             |
| `tileset.animations.wire_anim_code`                            | `--tileset-animations-wire-anim-code`          | `true`                 | Whether Porytiles wires generated animation code into `tileset_anims.c/h`. |
| `tileset.animations.cross_tileset_linking`                     | `--cross-tileset-anim-linking`                 | `true`                 | Match secondary tiles against a primary's animation key frames.            |
| `tileset.animations.palette_resolution_strategy`               | `--anim-pal-resolution-strategy`               | `scan-local-metatiles` | Which palette to use for animation tiles when decompiling.                 |
| `tileset.animations.key_frame_resolution_strategy`             | `--anim-key-frame-resolution-strategy`         | `error`                | How to handle duplicate key-frame tiles when decompiling.                  |
| `tileset.animations.multi_palette_subtile_resolution_strategy` | `--anim-multi-pal-subtile-resolution-strategy` | `error`                | How to handle subtiles referenced with multiple palettes when decompiling. |
| `tileset.animations.per_animation_overrides`                   | *YAML-only*                                    | (none)                 | Per-animation settings, keyed by animation name.                           |

**`frame_linking`**: `automatic` *(default,* uses `key.png`*)*, `manual` (uses explicit overrides in `anim.json`), or `hybrid` *(planned)*.

The three `*_resolution_strategy` values only matter when **decompiling** animations:

- **`palette_resolution_strategy`**: `scan-local-metatiles` *(default)*, `palette-00` through `palette-15` (use that index directly), `internal-png-palette`, or `scan-all-tilesets` *(planned)*.
- **`key_frame_resolution_strategy`**: `error` *(default)*, `warning`, or `mangle` (de-duplicate identical key-frame tiles).
- **`multi_palette_subtile_resolution_strategy`**: `error` *(default)*, `warning` (continue using the lowest palette index), or `split` *(planned)*.

**`per_animation_overrides`** lets a single animation depart from the global settings above.
Each key is an animation name; animations not listed fall back to the global values:

```yaml
tileset:
  animations:
    per_animation_overrides:
      flower:
        frame_linking: automatic
        key_frame_resolution_strategy: mangle
        multi_palette_subtile_resolution_strategy: warning
        palette_resolution_strategy: palette-00
        # One entry per subtile; "_" falls back to the strategy above
        per_tile_palette_resolution_strategies: [ _, scan-local-metatiles, _, _ ]
```

The animation pipeline is documented in {doc}`animations`.

### `tileset.primary_pairing` — pairing a secondary with its primary

When you compile a secondary tileset, Porytiles needs the compiled primary to produce correct global tile indices and palette references.

| YAML key                           | CLI flag                     | Default     | Description                                           |
|------------------------------------|------------------------------|-------------|-------------------------------------------------------|
| `tileset.primary_pairing.mode`     | `--primary-pairing-mode`     | `automatic` | How the partner primary is resolved.                  |
| `tileset.primary_pairing.partners` | `--primary-pairing-partners` | (none)      | Partner primary tileset names, used in `manual` mode. |

**`mode`**: `automatic` *(default,* scans layout metadata to find the partner primary*)*, `manual` (use the names in `partners`), or `off` (compile as a standalone secondary).
`partners` is only consulted when `mode` is `manual`.
Primary pairing is introduced in {doc}`creating-your-first-tileset`.

### `diagnostics` — warning and remark filters

Filter Porytiles' warnings and remarks by tag.
Each value is a list of regex patterns matched against diagnostic tags.
Within a category, `include` is applied **after** `exclude`, so you can silence everything and then re-enable a few specific tags.

| YAML key                       | CLI flag                        | Default | Description                                                      |
|--------------------------------|---------------------------------|---------|------------------------------------------------------------------|
| `diagnostics.warnings.exclude` | `--diagnostic-warnings-exclude` | (none)  | Regex patterns for warning tags to suppress.                     |
| `diagnostics.warnings.include` | `--diagnostic-warnings-include` | (none)  | Regex patterns for warning tags to keep (applied after exclude). |
| `diagnostics.remarks.exclude`  | `--diagnostic-remarks-exclude`  | (none)  | Regex patterns for remark tags to suppress.                      |
| `diagnostics.remarks.include`  | `--diagnostic-remarks-include`  | (none)  | Regex patterns for remark tags to keep (applied after exclude).  |

```yaml
diagnostics:
  warnings:
    exclude: [ ".*" ]          # silence every warning...
    include:                   # ...then re-enable just these two
      - layer-mode-warning
      - tile-color-count-warning
  remarks:
    exclude: [ ".*" ]          # silence all remarks
```

The catalog of diagnostic tags and what each one means is in {doc}`diagnostics`.

### Top-level keys

| YAML key           | CLI flag             | Default | Description                                   |
|--------------------|----------------------|---------|-----------------------------------------------|
| `verify_checksums` | `--verify-checksums` | `true`  | Verify artifact checksums during compilation. |

### Validation rules

Some values are checked individually, and a few are checked against each other.
A violation stops the compile with an explanatory error:

- Every `fieldmap.*` count must be greater than zero.
- `fieldmap.num_tiles_in_primary` ≤ `fieldmap.num_tiles_total`.
- `fieldmap.num_metatiles_in_primary` ≤ `fieldmap.num_metatiles_total`.
- `fieldmap.num_palettes_in_primary` ≤ `fieldmap.num_palettes_total`.
- `fieldmap.num_tiles_per_metatile` must be `8` or `12`.
- `fieldmap.metatile_attribute_size` must be `1`, `2`, or `4`.
- `tileset.extrinsic_transparency` must be fully opaque (alpha `255`).
- `tileset.tiles.sharing.packing` requires `tileset.palettes.packing.strategy` to be `backtracking`.

The metatile attribute schema has its own validation rules
(contiguous masks, no overlaps, defaults in range, and so on),
listed in {doc}`metatile-attributes`.

(not-yet-implemented)=
## Not yet implemented

The [annotated example file](https://github.com/grunt-lucas/porytiles/blob/develop/porytiles/config_templates/porytiles.example.yaml)
previews two keys that aren't wired up yet:

- `tileset.import_transparency` — transparency handling for import.
- `tileset.palettes.match_candidate_top_n` — how many near-miss palettes to show when a `locked` palette compile fails to find a match.

A handful of enum values are also reserved for future work and listed above as *(planned)*:
`tile-sharing` `optimal` (both packing and alignment),
`frame_linking` `hybrid`,
`palette_resolution_strategy` `scan-all-tilesets`,
and `multi_palette_subtile_resolution_strategy` `split`.

```{warning}
These keys exist only in the annotated example, which is a documentation template Porytiles never loads.
Don't copy them into a real `config.yaml` yet:
because they aren't recognized configuration paths, the validator rejects them as `unknown-config-key`
and the compile fails. Use the example as a reading reference, not a starter file.
```

## A worked example

A minimal project-wide config that locks palettes and lets tile compiles patch open slots:

```yaml
# porytiles/config.yaml — applies to every tileset in the project
tileset:
  extrinsic_transparency: [255, 0, 255]
  palettes:
    edit_mode: locked
  tiles:
    edit_mode: patch
```

To change just one value for a single tileset, add a per-tileset file and leave the rest to fall back to the project config:

```yaml
# porytiles/tilesets/gTileset_Example/config.yaml
tileset:
  tiles:
    edit_mode: optimize   # this one tileset re-packs from scratch
```

For a single file that exercises every key with inline comments, see the
[fully annotated example](https://github.com/grunt-lucas/porytiles/blob/develop/porytiles/config_templates/porytiles.example.yaml)
in the source repository, and remember the {ref}`not-yet-implemented <not-yet-implemented>` caveat above.

## See also

- {doc}`quickstart` — the short tour of the configuration system.
- {doc}`cli-reference` — the complete command and flag listing.
- {doc}`palette-packing`, {doc}`tile-sharing`, {doc}`animations`, {doc}`diagnostics`, {doc}`metatile-attributes` — the subsystems behind the values above.
- `porytiles dump-tileset-config <name>` — confirm what's actually in effect for a tileset.
- `porytiles dump-attribute-schema <name>` — see the metatile attribute schema those values resolve to.
