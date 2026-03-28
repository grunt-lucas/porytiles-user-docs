# Animations

```{admonition} Page Status
:class: warning
This page is a placeholder. Content coming soon.
```

The most complex subsystem --- needs significant depth:

- What tile animations are on the GBA: frame sequences swapping tile data at runtime
- Animation directory structure: frame PNGs, `key.png`, `anim.json`
- Frame linking modes: automatic (key.png), manual (anim.json), hybrid (NYI)
- Palette resolution strategies: `scan_local_metatiles`, `palette-00`--`palette-15`, `internal-png-palette`, `scan-all-tilesets` (NYI)
- Key frame resolution: `error`, `warning`, `mangle`
- Multi-palette subtile resolution: `error`, `warning`, `split` (NYI)
- Per-animation overrides: the three-tier cascade (per-tile > per-animation > global)
- `wire_anim_code`: automatic vs manual wiring into `tileset_anims.c/h`
- Worked example: importing an animated tileset, modifying an animation

**Cross-references:** {doc}`porytiles-concepts` for base game differences, {doc}`configuration` for animation config, {doc}`importing-an-existing-tileset` for animation import
