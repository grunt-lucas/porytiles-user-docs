# Inserting a Tileset Manually

Before Porytiles, decomp developers inserted every custom tileset into their project by hand.
This page walks through that manual process from start to finish:
preparing the art, indexing it, creating palette files, painting metatiles in Porymap,
and wiring up animations in the C code.

Why document the manual way in a Porytiles guidebook? A few reasons:

1. **This is the process that Porytiles automates.** Once you have seen the manual steps, the tool's behavior and its diagnostics stop being mysterious.
2. **Manual work is still occasionally the right choice.** A couple of edge cases remain where a human beats the compiler. They are covered at the end of this page.
3. **Most older community tutorials teach this process.** If you learned tileset insertion years ago, this page maps that knowledge onto the terms used throughout these docs.
4. **You might actually enjoy manual insertion.** It's still important to know how this process actually works, and some folks find manual insertion relaxing and fun. If that's you, this tutorial will help you get started, and you can come back to Porytiles later if you ever need help speeding things along.

This page assumes you know the material in {doc}`gba-decomp-tileset-system`:
tiles, palettes, tilemap entries, metatiles, the primary/secondary split,
and the four files each tileset keeps on disk.
Read that page first if you have not.

```{note}
The classic community reference for this workflow is the
[tile inserting & animating tutorial](https://www.pokecommunity.com/threads/tile-inserting-animating-tutorial.422362/)
on PokéCommunity. This page covers the same topic
but updated to match the current decomp file layouts.
 Some details in older tutorials have changed as the decomps evolved.
```

## What you have to to produce

Manual insertion means manually producing, with a varied set of tools, everything Porytiles would automatically generate:

| Artifact                    | What produces it manually                          |
|-----------------------------|-----------------------------------------------------|
| `tiles.png`                 | You, in an image editor, possibly with help from TileMapStudio |
| `palettes/00.pal` - `15.pal`| You, exported from your image editor or typed by hand     |
| `metatiles.bin`             | Porymap's Tileset Editor                            |
| `metatile_attributes.bin`   | Porymap's Tileset Editor                            |
| C registration (`headers.h`, `graphics.h`, `metatiles.h`) | Porymap and a text editor |
| Animation code              | You, in `src/tileset_anims.c`                       |

The steps below go in dependency order.
In practice you will loop through them many times,
which is most of the reason this process is so tedious.

## Your tools

### [Porymap](https://github.com/huderlem/porymap)
You'll use this to create the tileset skeleton, paint metatiles, and edit attributes.

### [Tilemap Studio](https://github.com/Rangi42/tilemap-studio)
You'll use this to deduplicate tiles from a mockup image, accounting for flips.

### An image editor with indexed-color support
You'll use this to draw the art, convert it to indexed color, assemble `tiles.png`, and possibly export palettes.

The community typically recommends:

1. [Aseprite](https://www.aseprite.org/) - Highly recommended, but it does cost $20 USD. It's free if you compile it yourself from source: [GitHub Link.](https://github.com/aseprite/aseprite)
2. [LibreSprite](https://libresprite.github.io/#!/) - Forked from Aseprite at some point, it's totally free.
3. [GIMP](https://www.gimp.org/) - GIMP is completely free and cross platform.
4. [GraphicsGale](https://graphicsgale.com/us/) - GraphicsGale is free, but Windows-only. It does work in Wine, but can be a bit buggy.

Use whichever you prefer. The rest of this tutorial will show Aseprite, so you'll need to translate functionality to your preferred tool.
 
### Text editor
You'll need one to edit the C registration and animation code. I recommend [VS Code](https://code.visualstudio.com/), but any editor will do.

## Step 1: create the tileset skeleton

Porymap can create a new empty tileset for you.
In the main window, choose **File > New Tileset...** (Ctrl+Shift+N),
pick a name like `gTileset_MyTileset`, and choose primary or secondary.

```{note}
TODO: insert screencap
```

Porymap then does the boring part. It creates:

- the `data/tilesets/{primary,secondary}/my_tileset/` directory
- a blank `tiles.png`
- empty metatiles in `metatiles.bin`
- default attributes in `metatile_attributes.bin`
- 16 all-black palette files

It also registers the tileset in `src/data/tilesets/headers.h`, `src/data/tilesets/graphics.h`, and `src/data/tilesets/metatiles.h`.

The `headers.h` entry is the `struct Tileset` described in
{doc}`gba-decomp-tileset-system`, and the other two files place the on-disk
artifacts into the ROM. For Emerald's General tileset they look like this:

```c
// src/data/tilesets/headers.h
const struct Tileset gTileset_General =
{
    .isCompressed = TRUE,
    .isSecondary = FALSE,
    .tiles = gTilesetTiles_General,
    .palettes = gTilesetPalettes_General,
    .metatiles = gMetatiles_General,
    .metatileAttributes = gMetatileAttributes_General,
    .callback = InitTilesetAnim_General,
};

// src/data/tilesets/metatiles.h
const u16 gMetatiles_General[] = INCBIN_U16("data/tilesets/primary/general/metatiles.bin");
const u16 gMetatileAttributes_General[] = INCBIN_U16("data/tilesets/primary/general/metatile_attributes.bin");
```

If you prefer, you can do all of this with a text editor instead:
create the directory, copy placeholder files from an existing tileset,
and add the three registration entries yourself.
Porymap saves you the typing and prevents dumb mistakes, so it's recommended you just let Porymap handle it.

```{caution}
The include macros in `graphics.h` have changed over decomp history.
Older trees use `INCBIN_U32("data/tilesets/.../tiles.4bpp.lz")` and list the
conversion in a Makefile rule; current `pokeemerald` uses `INCGFX_U32` with the
`.png` path and conversion arguments (including a `-num_tiles` count you may
need to bump as your sheet grows) inline. Copy whatever pattern your tree
already uses for the vanilla tilesets.
```

Porymap does not wire up animations.
A fresh tileset has no animation callback.
You have to add that later by hand in C.

## Step 2: plan your palettes

This is probably the hardest part of manual insertion,
and the step where mistakes are most tedious to fix,
because everything after it depends on the palette layout.

Recall the budget from {doc}`gba-decomp-tileset-system`.
In Emerald, a primary tileset owns palette slots 0-5 and a secondary owns
slots 6-12; each palette holds 15 usable colors plus transparent slot 0.
FireRed/LeafGreen splits the same 13 slots differently: 0-6 for primary and 7-12 for secondary.

Now look at your artwork and partition it:

1. Group the art into regions that will share a palette.
   Every 8x8 tile must draw all of its colors from a single palette,
   so regions must be chosen along tile boundaries.
2. Count unique colors per group, and keep each group at 15 or fewer.
   Remember that the GBA quantizes each channel to 5 bits,
   so two colors that differ only slightly may count as one in the end.
3. If you are building a secondary tileset, check the paired primary first.
   Its palettes are available to you for free, and every slot you can borrow
   is a slot you keep for the art that really needs it.

```{note}
TODO: insert screencap
```

If you get this wrong or change your mind later, then the indexing work in the next
step has to be redone for every affected tile.

```{seealso}
This planning problem is what Porytiles calls palette packing,
and solving it automatically is one of the tool's main jobs; see {doc}`palette-packing`.

For the computer science technical nerds, palette packing is an NP-hard problem known as "bin packing",
specifically a variant of bin packing often called "VM packing" or the "pagination problem."
Check out [this academic paper](https://arxiv.org/abs/1605.00558) for more information.
The [Wikipedia page](https://en.wikipedia.org/wiki/Bin_packing_problem) is also quite helpful.
```

## Step 3: index the art and build `tiles.png`

Most people start out by creating art on an RGB PNG, or with an indexed PNG and a large palette.
The tile sheet, though, must be an **indexed** PNG whose pixel values are
palette slot numbers from 0 to 15.
Getting from one to the other can be tricky,
since you'll have to ensure that each 8x8 tile on your sheet has the right pixel values (palette slot numbers)
such that they correspond to the contents of your `.pal` files.

For each palette group from Step 2:

1. Convert the region to indexed color mode in your editor
   (in GIMP: Image > Mode > Indexed; in Aseprite: Sprite > Color Mode > Indexed).
2. Arrange the resulting 16-color palette in the **exact slot order** you will
   write into the `.pal` file, with transparency at slot 0.
   The PNG stores index values, so if your editor puts a color at index 3 but
   your palette file lists it at line 5, every pixel of that color renders wrong in game.

Then assemble the sheet:

1. Cut the indexed art into 8x8 tiles and lay them out 16 tiles per row
   (128 pixels wide), matching the vanilla sheets.
2. Deduplicate as you go. Two tiles that are identical, or that are mirror
   images of each other, should appear in the sheet once; the flip bits in the
   metatile entries recover the variants for free.
3. By convention, leave tile 0 fully transparent so there is an obvious
   "empty" tile to paint with.

```{note}
TODO: insert screencap
```

Deduplication by eye is error-prone, and this is where
[Tilemap Studio](https://github.com/Rangi42/tilemap-studio) earns its place in
the toolbox: its **Image to Tiles** function (Ctrl+X) converts a mockup image
into a deduplicated tile sheet, taking X/Y flips into account, and can export
a palette at the same time.
You will still need to massage the output into your planned multi-palette
layout, but it beats comparing tiles by hand.

Two ways to get the finished sheet into the project:

- Save it directly as `data/tilesets/.../my_tileset/tiles.png`, or
- use Porymap's Tileset Editor: **Tools > Import Tiles Image...**,
  which accepts an indexed PNG of 8x8 tiles.

```{warning}
Once metatiles reference the sheet, tile positions are load-bearing.
Inserting a tile in the middle shifts the index of every tile after it and
silently breaks every metatile that referenced those indices.
Manual workflows always append new tiles at the end,
which is why hand-built sheets tend to fragment over time.
```

Remember from {doc}`gba-decomp-tileset-system` that a hand-built `tiles.png`
usually looks like a greyscale jumble in an image viewer:
the PNG can embed only one palette, but the game will render the tiles with
up to 13 different ones.
Only the index values matter.

## Step 4: write the palette files

Each palette slot gets one JASC-format `.pal` file, named `00.pal` through `15.pal`
(the exact format is shown in {doc}`gba-decomp-tileset-system`).
All sixteen files must exist even though the game only reads your half of the split;
leave the rest as placeholders.

You can produce these files three ways:

- export them from your image editor, if it speaks JASC,
- type them by hand (they are short text files), or
- edit them in Porymap's Palette Editor, which offers sliders, hex input,
  an eyedropper, and imports from JASC `.pal`, Adobe `.act`,
  Tile Layer Pro `.tpl`, and Advance PE files.

```{note}
TODO: insert screencap
```

Colors are written as 0-255 RGB and rounded down to the GBA's 5-bit channels
at build time, so what you see in your editor is not exactly what the game shows.
Keep the slot order identical to the order you indexed against in Step 3.

## Step 5: paint metatiles in Porymap

With tiles and palettes in place, open Porymap's
[Tileset Editor](https://huderlem.github.io/porymap/manual/tileset-editor.html)
and build the metatiles.
For each one:

1. Select a tile from the sheet, choose which palette should color it,
   and set X/Y flip as needed.
2. Paint it into the metatile's 2x2 cells, once for each of the two layers.
3. Set the metatile's **layer type** (`NORMAL`, `COVERED`, or `SPLIT`)
   so the layers land on the right screen planes.

```{note}
TODO: insert screencap
```

Every click here writes a 16-bit tilemap entry into `metatiles.bin`
using the encoding described in {doc}`gba-decomp-tileset-system`.
Porymap is the reason you never hex-edit that file:
it *is* a `metatiles.bin` editor with a graphical front end.

This step is not intellectually hard, just slow.
You are hunting for tiles in a 128-pixel-wide sheet where related tiles may
have been deduplicated apart from each other, and assigning a palette to
every single placement.
A full 512-metatile tileset means up to 4096 of these placements.

## Step 6: set the attributes

Still in the Tileset Editor, give each metatile its **behavior**
(`MB_TALL_GRASS`, `MB_PUDDLE`, and so on;
FireRed/LeafGreen adds terrain and encounter types).
Porymap writes these plus the layer type into `metatile_attributes.bin`.

At this point the tileset is functional.
Build the ROM, open a map that uses the tileset, and check your work in an
emulator: wrong colors usually mean a palette slot or index-order mistake in
Steps 3-4, and garbage pixels usually mean a tile was indexed against the
wrong palette.

## Step 7: animations, the hard part

Static tilesets end at Step 6.
Animations are where manual insertion turns into real programming,
because the decomps implement tile animation in C, per tileset, with
hard-coded tile indices.

The mechanism (described in {doc}`gba-decomp-tileset-system`) is:
the tileset's `callback` runs every frame and, on a schedule, copies
replacement tile graphics over a fixed range of tile slots in video memory.
Metatiles never change; the tiles underneath them do.

Manually wiring an animation means:

1. **Reserve tile slots.** Decide which tile indices the animation owns,
   and put the first frame's tiles there in `tiles.png`.
   Your animated metatiles reference these indices like any other tile.
2. **Draw the frames.** Each frame is a small indexed PNG containing just the
   animated tiles, indexed against the same palette as the static versions.
   They live in the tileset's `anim/` directory,
   for example `data/tilesets/primary/general/anim/flower/0.png`
   (a 16x16 image: the four flower tiles).
3. **Write the C code** in `src/tileset_anims.c`, following the pattern of a
   vanilla tileset such as `gTileset_General`:

```c
// Include each frame's graphics.
const u16 sTilesetAnims_MyTileset_Flower_Frame0[] = INCGFX_U16("data/tilesets/primary/my_tileset/anim/flower/0.png", ".4bpp");
const u16 sTilesetAnims_MyTileset_Flower_Frame1[] = INCGFX_U16("data/tilesets/primary/my_tileset/anim/flower/1.png", ".4bpp");
const u16 sTilesetAnims_MyTileset_Flower_Frame2[] = INCGFX_U16("data/tilesets/primary/my_tileset/anim/flower/2.png", ".4bpp");

// The frame sequence. Entries may repeat to shape the cycle:
// vanilla's flower plays 0, 1, 0, 2.
const u16 *const sTilesetAnims_MyTileset_Flower[] = {
    sTilesetAnims_MyTileset_Flower_Frame0,
    sTilesetAnims_MyTileset_Flower_Frame1,
    sTilesetAnims_MyTileset_Flower_Frame0,
    sTilesetAnims_MyTileset_Flower_Frame2,
};

// Copy the current frame over the reserved tile slots.
// 508 is the first reserved tile index; 4 tiles are overwritten.
static void QueueAnimTiles_MyTileset_Flower(u16 timer)
{
    u16 i = timer % ARRAY_COUNT(sTilesetAnims_MyTileset_Flower);
    AppendTilesetAnimToBuffer(sTilesetAnims_MyTileset_Flower[i],
                              (u16 *)(BG_VRAM + TILE_OFFSET_4BPP(508)),
                              4 * TILE_SIZE_4BPP);
}

// Runs every frame; the modulo sets the animation speed
// (here: advance one frame step every 16 game frames).
static void TilesetAnim_MyTileset(u16 timer)
{
    if (timer % 16 == 0)
        QueueAnimTiles_MyTileset_Flower(timer / 16);
}

// The entry point referenced by the tileset header.
void InitTilesetAnim_MyTileset(void)
{
    sPrimaryTilesetAnimCounter = 0;
    sPrimaryTilesetAnimCounterMax = 256;
    sPrimaryTilesetAnimCallback = TilesetAnim_MyTileset;
}
```

4. **Hook it up.** Declare `InitTilesetAnim_MyTileset` in
   `include/tileset_anims.h`, and set it as the `.callback` in the tileset's
   `headers.h` entry.
   (Secondary tilesets use the `sSecondaryTilesetAnim*` counterparts;
   again, copy a vanilla example like `gTileset_Mauville`.)

The fragile part is the coupling:
the tile index in the C code, the tiles in `tiles.png`, and the metatiles
painted in Porymap must all agree, and nothing checks this for you.
Move the animation's tiles in the sheet and forget to update the C constant,
and the animation cheerfully overwrites the wrong tiles at runtime.

Porytiles replaces all of this with frame images plus a `key.png`,
generates or updates the C wiring, and keeps the indices consistent;
see {doc}`animations`.

## Why people automate this

None of the steps above is impossible.
The problem is the loop.
Some sample scenarios that each restart a chunk of the process:

- **Any palette change re-opens Step 3.**
  Add one color, and the affected group's tiles must be re-indexed;
  reorder slots, and every tile that used that palette renders wrong until fixed.
- **Any new art re-opens Steps 3-5.**
  New tiles must be indexed, deduplicated against the existing sheet by eye,
  appended (never inserted!), and painted into metatiles palette-by-palette.
- **Any animation layout change re-opens Step 7,**
  with the failure mode being silent graphical corruption rather than an error.

Multiply this across the dozens of tilesets a full project needs,
and the appeal of describing your tileset as three RGBA layer images and
letting a compiler handle the rest becomes obvious.
That workflow is the subject of {doc}`creating-your-first-tileset`.

## When manual is still the right choice

A compiler works within the rules it models.
Two situations remain where experienced tileset authors reach past Porytiles:

- **Cross-tileset sharing tricks.**
  As explained in {doc}`gba-decomp-tileset-system`, a primary metatile *can*
  reference secondary tile indices, provided every secondary paired with that
  primary keeps identical content at the borrowed slots.
  Porytiles deliberately does not model this kind of arrangement;
  maintaining one is manual work by definition.
- **Hand-tuned squeezing.**
  When a tileset sits right at the edge of its tile or palette budget,
  a human who knows the art can sometimes out-pack the optimizer:
  restructuring art so regions share palettes, or reshaping tiles so more of
  them deduplicate.
  Porytiles has knobs to guide its packing (see {doc}`palette-packing`),
  but the last few percent can still favor hand work.

Expect this list to shrink.
Porytiles development keeps chipping away at these cases,
and the goal is for manual insertion to be a hobby rather than a necessity:
something you do because you enjoy it, not because the tooling made you.

Even when part of a tileset is hand-tuned, you rarely have to choose sides
permanently: `import-tileset` and `decompile-tileset` can bring manually
built assets under Porytiles management later
(see {doc}`importing-an-existing-tileset`).
