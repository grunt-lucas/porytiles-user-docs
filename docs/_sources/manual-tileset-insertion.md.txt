# Inserting a Tileset Manually

```{admonition} Page Status
:class: warning
This page is a placeholder. Content coming soon.
```

This page covers the manual (non-Porytiles) tileset creation process. Manual insertion is not just historical --- it is still needed for certain edge-case optimizations that Porytiles cannot handle.

- Tools involved: TilemapStudio, Aseprite, Porymap, text editor
- Creating a new tileset via Porymap
- Creating indexed `tiles.png` manually: converting RGBA to 4bpp indexed, arranging 8x8 tiles
- Building JASC-format `.pal` files by hand
- `metatiles.bin`: how metatile entries encode tile index, palette, flip flags
- `metatile_attributes.bin` for behaviors
- How to edit `metatiles.bin` and `metatile_attributes.bin` via Porymap (binary editing is not necessary)
- Pain points: re-indexing when palettes change, manual palette slot assignment, tedious metatile painting
- When manual is still the right choice (specific optimizations, edge cases Porytiles does not cover)

**Cross-references:** {doc}`gba-decomp-tileset-system` for terminology, {doc}`creating-your-first-tileset` for the Porytiles alternative
