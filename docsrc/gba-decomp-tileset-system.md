# How the GBA + Gen III Decomp Tileset System Works

```{admonition} Page Status
:class: warning
This page is a placeholder. Content coming soon.
```

This page covers GBA hardware and Gen III decomp fundamentals for users new to tilesets:

- 8x8 tiles, 4bpp indexed color, palette slots 0--15 with slot 0 as transparency
- Metatiles: 16x16 composites of 8x8 subtiles (2x2 tiles); tilemap entries (tile index + palette index + flip flags)
- Metatile dual vs triple layer concept
- Primary vs secondary tilesets: tile count limits, palette allocation (primary gets palettes 0--5, secondary gets 6--12 in default emerald)
- The `fieldmap.h` constants and what they control at a high level
- Artifact files: `tiles.png`, `palettes/*.pal`, `metatiles.bin`, `metatile_attributes.bin`
- How Porymap fits in as the visual editor --- Porytiles + Porymap together are a complementary "super suite" of tools, and Porytiles is designed with this in mind

**Cross-references:** {doc}`configuration` for fieldmap constants, {doc}`metatile-attributes` for attribute details
