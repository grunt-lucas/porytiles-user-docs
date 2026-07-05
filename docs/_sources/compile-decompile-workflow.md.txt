# The Compile/Decompile Workflow

```{admonition} Page Status
:class: warning
This page is a placeholder. Content coming soon.
```

The daily-use workflow guide (assumes user already has at least one managed tileset):

- The daily loop: edit Porytiles assets, compile, view in Porymap; or edit in Porymap, decompile back
- `compile-tileset`: what it does, when to run it, what artifacts it writes
- `decompile-tileset`: what it does, when to run it, what it regenerates
- Edit modes in practice: how locked/patch/optimize affect compilation
- Checksum verification: what happens on external edit detection, how to resolve
- Integrating with build systems (Makefile rules)
- Using `dump-tileset-config` to debug configuration
- Using `list-tilesets` to see project state

**Cross-references:** {doc}`porytiles-concepts` for edit modes, {doc}`configuration` for config tuning, {doc}`diagnostics` for reading output
