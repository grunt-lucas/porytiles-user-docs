# Quick Start

This page gives just enough info to install Porytiles, understand its core ideas, and do something real on your project.
It is a deliberately high-level overview
that sits alongside the rest of the documentation.
When you want depth on any topic covered here,
follow the included cross-references.

```{tip}
You do not need to read the documentation front-to-back to get started.
Skim this page, run a command or two, and branch off into the deeper guides only when a specific question comes up.
```

## What it is

Porytiles is a command-line **overworld tileset compiler** for the Gen III decompilation projects
(`pokeemerald`, `pokefirered`, `pokeruby`, and `pokeemerald-expansion`).
You edit your tilesets as plain RGBA PNG layers,
and Porytiles builds the Porymap-ready binaries (`metatiles.bin`, `tiles.png`, palettes, etc.) for you.

For background details on metatiles, tiles, palettes, and more, see {doc}`gba-decomp-tileset-system`.

## The mental model: `src` ⇄ `bin`

Every Porytiles-managed tileset has two sides:

| Side | Directory | Who owns it | Contents |
|------|-----------|-------------|----------|
| **Source** | `porytiles_src/` | **You edit this** | `bottom.png`, `middle.png`, `top.png`, `attributes.csv`, optional `anim/` |
| **Binary** | `porytiles_bin/` | **Porytiles generates this** | `metatiles.bin`, `metatile_attributes.bin`, `tiles.png`, `tiles.4bpp`, `tiles.4bpp.lz`, `palettes/` --- this is what Porymap reads |

Two commands move data between them, and they are exact inverses:

- **`compile-tileset`** → reads `porytiles_src/`, writes `porytiles_bin/` (make the Porymap assets match your source).
- **`decompile-tileset`** → reads `porytiles_bin/`, writes `porytiles_src/` (make your source match the Porymap assets).

The day-to-day rhythm of these two commands is covered in {doc}`compile-decompile-workflow`.

## Install / sanity check

Install via [Homebrew](https://brew.sh),
which works on Linux, macOS, and WSL:

```bash
# Latest versioned release:
brew install grunt-lucas/porytiles/porytiles

# Or the latest rolling snapshot (newest changes, less stable):
brew install grunt-lucas/porytiles/porytiles-snapshot
```

Homebrew automatically puts the `porytiles` binary on your `PATH`.

If you don't want to use Homebrew,
you can manually [download a release from the Releases page.](https://github.com/grunt-lucas/porytiles/releases)
Put the binary somewhere on your `PATH`.

For more installation details, including building from source and shell completion setup, see {doc}`installation`.

Confirm it runs:

```bash
porytiles --version
porytiles --help
```

Every subcommand has its own help as well:

```bash
porytiles compile-tileset --help
```

## Running it: project root

Porytiles operates on a decomp project.
Run it **from your project root**, or point it there explicitly:

```bash
# From inside the project:
cd path/to/pokeemerald-expansion
porytiles list-tilesets

# Or from anywhere, with -C / --project-root:
porytiles -C path/to/pokeemerald-expansion list-tilesets
```

It looks for the `porytiles/` management directory, `include/fieldmap.h`, and your tilesets relative to that root.

```{note}
Tileset names are the **struct names** from `src/data/tilesets/headers.h`, e.g. `gTileset_General`, `gTileset_PetalburgWoods`.
```

## The commands

| Command | What it does |
|---------|--------------|
| `list-tilesets` | List tilesets in the project. Flags: `--filter all\|managed\|unmanaged`, `--prefix <str>`. |
| `import-tileset <name>` | Bring an existing Porymap tileset under Porytiles management (one-time adoption). |
| `decompile-tileset <name>` | Regenerate editable `porytiles_src/` from the compiled Porymap tileset files. |
| `compile-tileset <name>` | Compile `porytiles_src/` to Porymap-ready `porytiles_bin/`. The main command you'll use most often. |
| `create-tileset <name>` | Create a brand-new Porytiles-managed tileset from scratch. Add `--secondary` for a secondary tileset. |
| `dump-tileset-config <name>` | Print the full, resolved config for a tileset (great for "why did it do that?"). |
| `completion <bash\|zsh\|fish>` | Generate a shell completion script. |

Global flags: `-V` / `--version`, `--help`, and `-C` / `--project-root <dir>` (default `.`).

For the complete, authoritative command and flag listing, see {doc}`cli-reference`.

## Three common flows

### Flow 1 --- Adopt an existing tileset and recompile it

The fastest way to see Porytiles do something real on your project:

```bash
# See what's there
porytiles list-tilesets

# Bring an existing Porymap tileset under Porytiles management
porytiles import-tileset gTileset_SecretBase

# Edit data/tilesets/primary/secret_base/porytiles_src/ (the layer PNGs, attributes.csv)...
# ...then rebuild the Porymap assets:
porytiles compile-tileset gTileset_SecretBase
```

```{important}
If you try `gTileset_General`, you'll see some import errors.
Those can easily be resolved, but that is covered in {doc}`importing-an-existing-tileset`.
```

Open the map in Porymap and your edits are there.
For a deeper walkthrough of the first-time import process, see {doc}`importing-an-existing-tileset`.

### Flow 2 --- Create a new tileset from scratch

```bash
porytiles create-tileset gTileset_TeamAquaHideout
```

This creates the `porytiles/` management entry, the `data/tilesets` asset directories,
and modifies the relevant C source files so your tileset is ready-to-edit.
It also populates `porytiles_src/` with some sample assets
and internally compiles them so you have `porytiles_bin/` as well, a complete tileset.
Refresh Porymap and it will start working immediately.


You can then edit the assets in `porytiles_src/`:
```
porytiles_src/
├── bottom.png        # bottom render layer
├── middle.png        # middle render layer
├── top.png           # top render layer
├── attributes.csv    # per-metatile behaviors (see below)
└── anim/             # optional animations
```

and compile your edits:

```bash
porytiles compile-tileset gTileset_TeamAquaHideout
```

Refresh Porymap again to see your edits.

For a secondary tileset (one that layers on top of a primary), add `--secondary`:

```bash
porytiles create-tileset gTileset_TeamAquaTokuHideout --secondary --primary-pairing-mode manual --primary-pairing-partners gTileset_TeamAquaHideout
```

The primary pairing mechanics are covered in {doc}`creating-your-first-tileset`.

The full new-tileset tutorial, including primary pairing mechanics, viewing your work in Porymap, and fixing common first-time errors,
is in {doc}`creating-your-first-tileset`.

### Flow 3 --- Inspect what config is actually in effect

Config comes from several layers (see the YAML config section below). To see the final resolved values for a tileset:

```bash
porytiles dump-tileset-config gTileset_TeamAquaHideout
```

Many more details about the configuration system can be found in {doc}`configuration`.

## Input files (what *you* put in `porytiles_src/`)

- **`bottom.png`, `middle.png`, `top.png`** --- your three layer images, as RGBA (or indexed) PNGs.
  For transparent pixels, use your configured transparency color (default magenta `[255, 0, 255]`) or set the pixel alpha value to 0. Both styles are supported.
- **`attributes.csv`** --- per-metatile behavior, with header `id,behavior`. Behavior names are the constants from your project's `include/constants/metatile_behaviors.h`:

  ```text
  id,behavior
  1,MB_TALL_GRASS
  63,MB_PUDDLE
  ```

  See {doc}`metatile-attributes` for the full attribute format and base-game differences.

- **`anim/`** (optional) --- one subdirectory per animation. Each holds a `key.png` (marks which tiles animate) plus numbered frames `00.png`, `01.png`, `02.png`, …:

  ```
  anim/
  └── flower_red/
      ├── key.png
      ├── 00.png
      ├── 01.png
      └── 02.png
  ```

  Animations are covered in detail in {doc}`animations`.

You can browse complete, working examples in the repo under `resources/examples/` (e.g. TODO create some non-legacy example tilesets).

## Output files (what Porytiles writes to `porytiles_bin/`)

These files are what Porymap actually cares about:

```
porytiles_bin/
├── metatiles.bin
├── metatile_attributes.bin
├── tiles.png
└── palettes/
    ├── 00.pal   00.gbapal
    ├── 01.pal   01.gbapal
    └── …         (through 15)
```

You don't need to hand-edit these, they're regenerated on every `compile-tileset`.
That said, if you do hand-edit these, or edit them via Porymap,
you can sync those changes back into the tileset's Porytiles component (`porytiles_src/`) via the `decompile-tileset` command.
For more details, see {doc}`compile-decompile-workflow`.

## Directory layout (a managed tileset)

Putting it together, a Porytiles-managed tileset spans two trees in the project:

```
pokeemerald-expansion/
├── porytiles/                                  # management tree (config + metadata)
│   ├── config.yaml                             # project-wide config (optional)
│   ├── config.local.yaml                       # project-wide LOCAL overrides (optional, gitignore-friendly)
│   └── tilesets/
│       └── gTileset_TeamAquaHideout/
│           ├── config.yaml                     # per-tileset config (optional)
│           ├── config.local.yaml               # per-tileset LOCAL overrides (optional)
│           └── tileset-manifest.json           # {"imported": false, "version": 1}
│
└── data/tilesets/primary/team_aqua_hideout/    # asset tree
    ├── porytiles_src/                          # ← you edit
    └── porytiles_bin/                          # ← Porytiles generates (Porymap reads)
```

Note the two names: the CLI uses the **struct name** (`gTileset_TeamAquaHideout`) for the management dir,
while the assets live under the matching **snake_case** dir (`team_aqua_hideout/`).
The managed-vs-unmanaged distinction and the rest of this layout are explained in {doc}`porytiles-concepts`.

## Configuration

Config is optional when you first start out; Porytiles has sensible layered defaults.
But you'll need it for most advanced use-cases, so you should start to get familiar with it.
You can set things project-wide or per-tileset, with `config.local.yaml` for machine-local overrides you don't want to commit:

- Project-wide: `porytiles/config.yaml` and `porytiles/config.local.yaml`
- Per-tileset: `porytiles/tilesets/<gTileset_Name>/config.yaml` and `config.local.yaml`

Per-tileset configs take precedence over project-wide configs on a **per-key basis**.
So you can easily override just one config value for a specific tileset and still fall back to your project-wide config for the rest.

A minimal real per-tileset config might look like this:

```yaml
tileset:
  # [255, 0, 255] is the default, but I explicitly specified it here for sake of example
  extrinsic_transparency: [255, 0, 255]
  palettes:
    edit_mode: locked
  tiles:
    edit_mode: patch
```

There are a ton of possible configurations, see {doc}`configuration` for more details.

### CLI Overrides

Nearly every config value can also be set directly on the command line,
which is handy for one-off compiles where you don't want to touch any YAML.
The flag name is just the config key in kebab-case
(for example, `tiles.edit_mode` becomes `--tiles-edit-mode`):

```bash
porytiles compile-tileset gTileset_TeamAquaHideout --tiles-edit-mode optimize
```

A CLI flag is the highest-priority config source:
for that one run it overrides every YAML file and the built-in defaults.
A few structurally complex values (palette hints, packing strategy params, per-animation overrides)
are YAML-only and have no flag.

For the full list of config sources and their precedence order,
plus the complete flag-to-key mapping, see {doc}`configuration`.

Porytiles also ships shell completion scripts that allow you to:

```bash
# Example: tap your shell's completion key here to auto-complete all relevant options
porytiles compile-tileset gTileset_TeamAquaHideout --<TAB>
```

and quickly auto-complete every CLI option.

See {doc}`installation` for more info on how to install shell completions.

### Where to see every option

The source repo [contains a **fully annotated example** that documents every key](https://github.com/grunt-lucas/porytiles/blob/develop/porytiles/config_templates/porytiles.example.yaml) with its allowed values and defaults.

For explanations of each section, again see {doc}`configuration`.
To verify what's actually in effect after layering, use `porytiles dump-tileset-config <name>`.

## Getting unstuck

- What's that flag name again? `porytiles --help` and `porytiles <command> --help`
- What's that YAML key again? `porytiles/config_templates/porytiles.example.yaml`
- Why is my config not what I expected? `porytiles dump-tileset-config <name>`
- Where can I see some example tilesets? `resources/examples/`
- What does this diagnostic message mean? {doc}`diagnostics`
