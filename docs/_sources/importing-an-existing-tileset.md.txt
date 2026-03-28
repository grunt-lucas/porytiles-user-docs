# Importing an Existing Tileset

```{admonition} Page Status
:class: warning
This page is a placeholder. Content coming soon.
```

Tutorial for bringing pre-existing tilesets under Porytiles management:

- When to import vs create
- Running `porytiles2 import-tileset gTileset_General`
- What happens: Porytiles reads Porymap artifacts, decompiles to RGBA layers + `attributes.csv`, creates manifest
- Verifying the import: re-compile and diff, or visual inspection in Porymap
- Import transparency options (`import_transparency`: alpha, extrinsic, mixed)
- Limitations: pokeruby import not currently supported
- Brief note on importing animation-bearing tilesets

**Cross-references:** {doc}`porytiles-concepts` for managed vs unmanaged, {doc}`compile-decompile-workflow` for ongoing workflow, {doc}`animations` for animation import
