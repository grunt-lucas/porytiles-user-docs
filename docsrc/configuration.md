# Configuration Reference

```{admonition} Page Status
:class: warning
This page is a placeholder. Content coming soon.
```

The exhaustive config reference:

- The layered provider system (5 layers in priority order): CLI > YAML per-tileset local > YAML per-tileset > YAML project local > YAML project > Header defines > Defaults
- YAML file locations and precedence
- How to use `dump-tileset-config` to inspect provenance
- Which values are YAML-only (palette hints, strategy params, per-animation overrides)
- **Full config value listing**, organized by YAML path group:
  - `fieldmap.*` (9 values)
  - `tileset.extrinsic_transparency`, `tileset.import_transparency`
  - `tileset.tiles.*` (edit_mode, palette_mode, sharing.packing, sharing.alignment)
  - `tileset.palettes.*` (edit_mode, packing.strategy, packing.strategy_params, packing.hints_enabled, packing.hints)
  - `tileset.animations.*` (all animation config + per_animation_overrides)
  - `tileset.paths.*` (primary/secondary src/bin)
  - `diagnostics.*` (warning/remark filters)
  - `verify_checksums`
- For each value: canonical name, YAML path, CLI flag (or "YAML-only"), type, default, description, link to relevant guide
- Cross-field validation rules
- The example YAML file (reproduce or reference `porytiles.example.yaml`)

**Cross-references:** Every config value links to its conceptual guide page
