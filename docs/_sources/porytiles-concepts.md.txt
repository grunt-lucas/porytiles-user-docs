# Porytiles Concepts and Terminology

```{admonition} Page Status
:class: warning
This page is a placeholder. Content coming soon.
```

This page bridges GBA background knowledge to hands-on tutorials. It introduces Porytiles-specific concepts that span multiple guides:

- **Managed vs unmanaged tilesets**: what makes a tileset "managed" (`tileset-manifest.json`), how `list-tilesets` shows them
- **Project directory structure**: `porytiles/config.yaml`, `porytiles/config.local.yaml`, `porytiles/tilesets/<name>/config.yaml`, `porytiles/tilesets/<name>/config.local.yaml`, `tileset-manifest.json`
- **Porytiles component vs Porymap component**: `porytiles_src/` (RGBA layer PNGs + `attributes.csv`) vs `porytiles_bin/` (indexed artifacts)
- **The compile/decompile duality**: Porytiles assets as "source of truth"
- **Extrinsic transparency**: what it is, why it exists, how to configure
- **Edit modes**: locked / patch / optimize --- when each is appropriate
- **Checksum verification**: anti-clobber protection
- **Supported base games**: pokeruby (limited), pokefirered (full, terrain/encounter types), pokeemerald, pokeemerald-expansion

**Cross-references:** {doc}`gba-decomp-tileset-system` for GBA terms, {doc}`configuration` for setting extrinsic transparency and edit modes
