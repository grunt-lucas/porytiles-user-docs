# How the GBA + Gen III Decomp Tileset System Works

Porytiles exists so you don't have to hand-manage most of the systems described in this page.
However, they're still important to know.
The tile limits, palette slots, file conventions, and error messages
you will run into all trace back to how the Game Boy Advance draws the overworld.
Once you know the hardware underneath, a diagnostic with GBA jargon like like "ran out of palette slots"
will feel a lot less frustrating.

This page uses `pokeemerald` as its reference.
FireRed/LeafGreen (`pokefirered`) differences are called out where relevant,
and everything here applies to `pokeemerald-expansion` as well.

```{tip}
You do not need to memorize this page before using Porytiles.
Read through it once to understand the basics, then come back
when a diagnostic or another docs page mentions a concept you don't fully understand.
```

## Start with the hardware

The GBA has a 240x160 pixel screen, and the Gen III games draw the overworld with the
console's **tiled background** hardware. Instead of storing a full-screen image, the game
hands the Advanced Picture Processing Unit (PPU) a collection of small tile images plus a grid that says which tile
goes where. The PPU assembles the picture live, every frame.

```{note}
TODO: insert cool pic of GBA screen
```

There are three key facts about the hardware setup.
If you understand these, everything else will start to make sense.

1. Tiles are 8x8 pixels and use *indexed* color.
2. Each cell of the background grid is a fancy 16-bit pointer: 10 bits to name the tile at the given cell
   and 4 bits to name the palette.
3. There are four background layers, and the games use three of them for the map.

The rest of this page walks you all the way up from the hardware to the decomp system:
tiles, then the tilemap entries that place them, then metatiles,
then the primary/secondary tileset split, and finally the files on disk
where all of this actually lives in your decomp project.

```{note}
For exhausting details, the classic reference is the
[Tonc tutorial](https://gbadev.net/tonc/), especially its chapter on regular (tiled)
backgrounds. This page summarizes just the parts that matter for decomp tilesets.
```

## Tiles and palettes: indexed color

A **tile** is an 8x8 pixel image.

```{note}
TODO: insert screencap of a tile
```

Important: each pixel is not actually a color. It is a number from 0 to 15
that points into a **palette** of 16 colors. When the hardware draws the tile, it looks
up each pixel's number in whichever palette the tile was assigned (more on this later)
and paints the color it finds there.
At 4 bits per pixel, a tile occupies just 32 bytes of video memory.

The GBA provides 16 of these background palettes. Each color slot is a 15-bit value
(5 bits each for red, green, and blue), which gives two important takeaways:

- There are only 32,768 distinct colors. When your source art uses ordinary 8-bit RGB
  channels, each channel gets quantized down to 5 bits, so two RGBA colors that differ
  only slightly can collapse into the same hardware color.
- **Slot 0 of every palette means transparent.** A pixel with value 0 shows whatever is
  behind it (a lower background layer, or the backdrop). This is why a 16-color palette
  really gives you 15 usable colors.

Indexed color has a neat consequence of which the whole system makes use: the same tile image rendered
with two different palettes produces two differently colored results for free. A red roof
and a blue roof can be one tile. Porytiles allows you to automatically exploit this in some cases;
see {doc}`tile-sharing`.

```{note}
TODO: insert screencap of tile shared roof tiles
```

## Tilemap entries: how tiles reach the screen

A background layer is a grid of 16-bit **tilemap entries**, one per 8x8 screen cell.
Every entry has the same bit layout:

| Bits  | Field           | Meaning                                        |
|-------|-----------------|------------------------------------------------|
| 0-9   | Tile index      | Which tile image to draw (0 through 1023)      |
| 10    | Horizontal flip | Mirror the tile left-to-right                  |
| 11    | Vertical flip   | Mirror the tile top-to-bottom                  |
| 12-15 | Palette         | Which of the 16 palettes colors this tile      |

This one value is the most important piece of the entire tileset system, and its bit
widths are where the famous limits come from:

- 10 bits of tile index means **at most 1024 tiles** can be available for the map at any
  moment. That is the ceiling the primary/secondary split (below) divides up.
- 4 bits of palette means at most 16 palettes, and the games reserve some of those for
  UI drawn over the map.
- The flip bits enable free mirroring. A staircase that climbs left and one that climbs right
  can share a single tile image. Porytiles checks flips automatically when deduplicating
  tiles.

```{note}
TODO: insert screencap of flipped tiles
```

## Metatiles: the map-building unit

Overworld maps are not laid out one 8x8 tile at a time. Instead, the games group tiles into
**metatiles**: 16x16 pixel blocks, each a 2x2 arrangement of tiles. Map layouts are grids
of metatile IDs, and metatiles are what you paint with in Porymap.

A metatile is defined by a list of tilemap entries, in row-major order per layer:

```text
   subtile order            a dual-layer metatile = 8 entries
   +---+---+
   | 0 | 1 |                entries 0-3: the metatile's first layer
   +---+---+                entries 4-7: the metatile's second layer
   | 2 | 3 |
   +---+---+
```

Note that each metatile carries **two** layers of tile entries. What those layers mean is
the next piece of the puzzle.

```{note}
TODO: insert screencap of a few metatiles, show layer breakdown
```

### Three screen layers, two metatile layers

The overworld reserves background layer 0 for text boxes and menus, then draws the map
with the other three:

| Screen layer | GBA background | Draw order                                  |
|--------------|----------------|---------------------------------------------|
| Top          | BG1            | In front of the player and other sprites    |
| Middle       | BG2            | Behind sprites                              |
| Bottom       | BG3            | Behind everything                           |

Player and NPC sprites render above the middle layer but below the top layer. That is the
trick that allows "3D" perspective. It's why the player sprites walks *behind* a tree canopy or under an archway:
the tree canopy art lives on the top layer.

A dual-layer metatile only has content for two of these three screen layers. Which two is
decided by the metatile's **layer type**, a value stored in its attributes:

| Layer type          | First layer (entries 0-3) shows on | Second layer (entries 4-7) shows on | Unused screen layer |
|---------------------|------------------------------------|-------------------------------------|---------------------|
| `NORMAL` (value 0)  | Middle                             | Top                                 | Bottom              |
| `COVERED` (value 1) | Bottom                             | Middle                              | Top                 |
| `SPLIT` (value 2)   | Bottom                             | Top                                 | Middle              |

```{tip}
You can easily see the layer type for any given metatile by inspecting it in Porymap's metatile picker.

TODO: include a screencap
```

So a patch of flowers is typically `COVERED` (ground plus flowers, nothing drawn
over the player), while a tree canopy is typically `SPLIT` (background grass below the player, canopy above).

```{caution}
In vanilla Emerald, the unused screen layer of a `NORMAL` metatile is filled with a
garbage tile rather than a transparent one. You normally never see it, but if a `NORMAL`
metatile's first layer has transparent pixels, the garbage can peek through. This is a
quirk of the game engine, not of your tileset.

You can see it for yourself in `pokeemerald`: look at the `DrawMetatile` function in
`src/field_camera.c`, in the `METATILE_LAYER_TYPE_NORMAL` case. It writes the tilemap
entry `0x3014` to the bottom background layer. Decoded with the bit layout from earlier,
`0x3014` means tile `0x14` with palette 3:
an arbitrary tile from the primary tileset, not transparency.
```

### Dual-layer vs. triple-layer

Some projects modify the game engine so that every metatile carries all three layers: 12
tilemap entries instead of 8, no layer type needed, content allowed everywhere. This is
the **triple-layer metatiles** modification, and both Porymap and Porytiles support it
(`fieldmap.num_tiles_per_metatile` set to `12`; see {doc}`configuration`).

If you want to enable triple-layer metatiles in your own project, the
[pret wiki guide](https://github.com/pret/pokeemerald/wiki/Triple-layer-metatiles)
walks through the required engine changes, and Porymap's
[settings and options page](https://huderlem.github.io/porymap/manual/settings-and-options.html)
covers the corresponding "Enable Triple Layer Metatiles" project setting.

Porytiles always presents your tileset source as three full-size layer images
(`bottom.png`, `middle.png`, `top.png`), which correspond exactly to the three screen
layers. On a stock dual-layer game, each individual metatile may only have art in two of
the three, and Porytiles infers the correct layer type from which two you used. On a
triple-layer game there is no restriction. Details live in {doc}`metatile-attributes`.

## Primary and secondary tilesets

Every map layout names exactly two tilesets: a **primary** and a **secondary**. In the
game source, a tileset is a small struct
(`include/global.fieldmap.h`) tying together everything covered so far:

```c
struct Tileset
{
    bool8 isCompressed;
    bool8 isSecondary;
    const u32 *tiles;              // the tile images       (from tiles.png)
    const u16 (*palettes)[16];     // 16 palettes, 16 colors (from palettes/*.pal)
    const u16 *metatiles;          // tilemap entries        (from metatiles.bin)
    const u16 *metatileAttributes; // behavior + layer type  (from metatile_attributes.bin)
    TilesetCB callback;            // per-frame hook, used for tile animations
};
```

(The `callback` is for animations: water ripples, flower breeze movement, etc. It's a function that copies new tile
frames into video memory on a schedule. See {doc}`animations`.)

When a map loads, the game copies *both* tilesets into video memory and palette memory at
fixed positions. The hardware budgets are split between the pair. In Emerald:

| Resource  | Total          | Primary share       | Secondary share      |
|-----------|----------------|---------------------|----------------------|
| Tiles     | 1024           | 512 (indices 0-511) | 512 (indices 512-1023) |
| Metatiles | 1024           | 512 (IDs 0-511)     | 512 (IDs 512-1023)   |
| Palettes  | 16 (13 usable) | 6 (slots 0-5)       | 7 (slots 6-12)       |

Palette slots 13-15 are off limits: the game engine keeps them for things it draws over
the map, such as message box frames and battle transition effects.

FireRed/LeafGreen splits the same totals differently: the primary gets 640 tiles, 640
metatiles, and 7 palettes (slots 0-6), leaving 384 tiles, 384 metatiles, and 6 palettes
(slots 7-12) for the secondary.

### Secondaries borrow from their primary

Because both tilesets sit in video memory at the same time, and tilemap entries use
absolute indices, nothing stops a secondary metatile from referencing the primary's tiles
and palettes. This is not just allowed, it is the normal case. A town's building
metatiles sit on the primary's grass and path tiles, and secondary tiles routinely color
themselves with primary palettes instead of spending one of the secondary's own slots.

Porytiles understands this pairing. When you compile a secondary tileset, it resolves
the partner primary and reuses primary tiles and palettes automatically where it can.
See {doc}`configuration` for how the partner primary is resolved (`tileset.primary_pairing`).

The relationship only goes one way, though. A primary is shared by many maps, and each
map pairs it with a different secondary. If a primary metatile referenced tile 700, it
would draw whatever the *current* map's secondary keeps at index 700: a rock wall on one
map, a building window on the next. So in practice, primary metatiles stick to primary
tiles and palettes. (Projects occasionally break this rule on purpose, but that only
works if every secondary paired with that primary keeps identical content at the
borrowed indices. It's a very deliberate, carefully maintained setup.)

### Why the split exists

The primary tileset holds the shared basics for a whole region: paths, grass, water,
ledges. Nearly every outdoor Hoenn map uses `gTileset_General` as its primary. The
secondary holds what makes an area distinct: a town's buildings, a cave's rock walls, etc.

This division is what makes connected maps work. As you walk from route to town, both
maps usually share the same primary, so all the common ground renders identically on both
sides of the border while the game loads in the new secondary. It's also ROM space optimization:
hundreds of maps reuse one copy of the general tiles instead of each carrying their own.

For your own project the takeaway is: **primary tilesets are shared infrastructure,
secondary tilesets are where per-area special decoration goes.** A primary edit touches every map
that uses it; a secondary edit is usually local to a handful of maps.

## The `fieldmap.h` header file

The split described above is defined by a set of macros in your project's `include/fieldmap.h`.
Both the game code and your tools must agree on them:

| Constant                    | Emerald | FRLG  | What it controls                                        |
|-----------------------------|---------|-------|---------------------------------------------------------|
| `NUM_TILES_IN_PRIMARY`      | 512     | 640   | Tiles reserved for the primary                          |
| `NUM_TILES_TOTAL`           | 1024    | 1024  | Total tile capacity (fixed by the 10-bit tile index)    |
| `NUM_METATILES_IN_PRIMARY`  | 512     | 640   | Metatiles reserved for the primary                      |
| `NUM_METATILES_TOTAL`       | 1024    | 1024  | Total metatile capacity                                 |
| `NUM_PALS_IN_PRIMARY`       | 6       | 7     | Palette slots reserved for the primary                  |
| `NUM_PALS_TOTAL`            | 13      | 13    | Palette slots available to tilesets (rest are engine's) |
| `NUM_TILES_PER_METATILE`    | 8       | 8     | 8 for dual-layer metatiles, 12 for triple-layer         |
| `MAX_MAP_DATA_SIZE`         | 10240   | 10240 | Size of the map layout buffer (not tileset related)     |

Don't treat this as a simple config file. Raising some of the limits here without corresponding
game-engine changes will not necessarily work. Established engine modifications (like triple-layer metatiles)
come with instructions for which constants to change.

Porytiles and Porymap read all of these from your project automatically, so the limits will always match
your build. You can override them for specific use cases.
Don't worry about that now, it will make more sense later as you play with the tool.
See {doc}`configuration` for how overriding works.

## The files on disk

Each tileset lives in its own directory under `data/tilesets/primary/` or
`data/tilesets/secondary/`. Using Emerald's general tileset as the example:

```text
data/tilesets/primary/general/
├── tiles.png                  # the tile sheet (indexed PNG)
├── palettes/
│   ├── 00.pal ... 15.pal      # one JASC palette file per hardware slot
├── metatiles.bin              # tilemap entries for every metatile
├── metatile_attributes.bin    # behavior + layer type for every metatile
└── anim/                      # (some tilesets) frames for tile animations
```

These four artifacts map onto the `struct Tileset` fields shown earlier.
The project's build system converts them into raw GBA formats (and LZ77-compresses the tiles
when `isCompressed` is set) as part of compiling the ROM.

### `tiles.png`

The main tile sheet: every unique 8x8 tile for the tileset.
The tiles are laid out 16 tiles per row, for 128 pixels wide.
It is a 4-bit indexed PNG, and its pixel values are the palette slot
numbers described above, not colors.

If you open `tiles.png` in an image viewer it usually looks like a greyscale jumble.
That is expected. A PNG can only embed one palette, but these tiles will be rendered with
up to 13 different palettes in game, so the embedded palette is a meaningless
placeholder. Only the index values matter.

```{tip}
By default, the Porytiles-generated `tiles.png` avoids the greyscale jumble. Porytiles
writes the file in **true-color mode**: an 8-bit indexed PNG whose embedded palette holds
the tileset's real palettes, back to back. Each pixel's upper four bits select a palette
and its lower four bits are the usual color index, so the sheet opens in any ordinary
image viewer in its actual colors. (Porytiles picks each tile's display palette from the
first metatile that uses it; a tile reused under several palettes displays with the first
one found.)

Nothing downstream changes, because the lower four bits still hold the same index values
as a vanilla `tiles.png`. The decomp's `gbagfx` tool reads only those four bits when
building the ROM, and Porymap (5.2.0 and later) understands the format natively. If you
want the vanilla greyscale look instead, set `tileset.tiles.palette_mode` to `greyscale`
(see {doc}`configuration`).

TODO: show a "before and after" pic
```

### `palettes/00.pal` through `15.pal`

One text file per hardware palette slot, in JASC format:

```text
JASC-PAL
0100
16
24 41 82
255 255 255
...14 more lines, one R G B triple per slot
```

All 16 files exist for every tileset, but the game engine only references the relevant ones for a given tileset.
In other words, a primary tileset's `00.pal` through `05.pal` and a secondary's `06.pal` through `12.pal` (Emerald numbers).
The rest are placeholders that the game never reads.
Colors are written as 0-255 RGB but get downsampled to the GBA's 5-bit channels at build time.

### `metatiles.bin`

The metatile definitions: a flat array of little-endian 16-bit tilemap entries, 8 per
metatile (12 on triple-layer projects), in the subtile order diagrammed earlier. A
dual-layer metatile is exactly 16 bytes, so Emerald's 512-metatile general tileset
produces an 8192-byte file.

```{note}
TODO: include a diagram of the binary layout
```

### `metatile_attributes.bin`

One attribute value per metatile, in the same order as `metatiles.bin`. In Emerald and
Ruby this is 2 bytes per metatile: bits 0-7 hold the **behavior** (the gameplay meaning
of the metatile, like `MB_TALL_GRASS` or `MB_PUDDLE`) and bits 12-15 hold the layer type.
FireRed/LeafGreen uses 4 bytes per metatile and packs in two extra fields, terrain type
and encounter type. Porytiles and Porymap both support robust customizations.
All the details (for Porytiles at least) are documented in {doc}`metatile-attributes`.

```{note}
TODO: include a diagram of the binary layout
```

## Where Porymap and Porytiles fit

[Porymap](https://github.com/huderlem/porymap) is the visual editor for this system. It
reads the four artifacts, renders metatiles with their real palettes, lets you paint them
onto map layouts, and its Tileset Editor allows you to edits `metatiles.bin`
`metatile_attributes.bin` directly, so you never need to touch those binaries by hand.

What Porymap does not do is create the artifacts from your artwork. Getting from an RGBA
mockup to a valid indexed `tiles.png` plus `.pal` files means choosing at most 15 colors
per palette, deciding which palette each tile uses, hand-indexing every pixel, and
deduplicating tiles across flips. Done manually, this is the most tedious and
error-prone part of creating a tileset (described in {doc}`manual-tileset-insertion`).
Tools like TileMapStudio certainly can speed things up, but the process is still quite tedious
when multiplied across the dozens of custom tilesets you might need for your decomp project.

That gap is exactly what Porytiles fills. You draw the three background layers as ordinary
RGBA images, and `compile-tileset` produces all four artifacts: it quantizes and packs
your colors into palettes ({doc}`palette-packing`), indexes and deduplicates the tiles,
builds the metatile entries, and assembles attributes from your
`attributes.csv`. Porymap then consumes the result as if you had made it by hand.

The two tools are designed to be complementary: Porytiles turns art into tilesets,
Porymap turns tilesets into maps. A comfortable workflow uses both side by side, and
Porytiles' `decompile-tileset` command keeps edits made through Porymap in sync with your
source images (see {doc}`compile-decompile-workflow`). Sometimes it's easier to make a quick edit
on the Porymap side, Porytiles lets you easily sync those edits back so you can continue working uninterrupted.

## Quick glossary

| Term               | Meaning                                                                          |
|--------------------|----------------------------------------------------------------------------------|
| Tile               | 8x8 pixel image; each pixel is a 4-bit index into a palette                       |
| Palette            | 16 colors (slot 0 = transparent); the GBA has 16 background palettes              |
| Tilemap entry      | 16-bit value: tile index, horizontal/vertical flip, palette number                |
| Metatile           | 16x16 map-building block: 2x2 tiles across two (or three) layers                  |
| Layer type         | Per-metatile attribute choosing which two screen layers a dual-layer metatile uses |
| Behavior           | Per-metatile attribute giving its gameplay meaning (grass, water, door, ...)      |
| Primary tileset    | The shared half of a map's tileset pair (region-wide basics)                      |
| Secondary tileset  | The area-specific half of a map's tileset pair                                    |
| `fieldmap.h`       | Header defining how the tile/metatile/palette budgets are split                   |
