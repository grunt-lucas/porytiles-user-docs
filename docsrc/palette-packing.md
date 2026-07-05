# Palette Packing

```{admonition} Page Status
:class: warning
This page is a placeholder. Content coming soon.
```

Deep guide structured as "basics first, tuning later":

- What palette packing is: assigning tiles to hardware palettes under the 15-color constraint
- The three strategies: `best_fusion` (fast greedy), `backtracking` (default, BFS/DFS), `overload_and_remove` (multi-start retries)
- When to use each strategy
- Per-strategy tuning parameters:
  - backtracking: `search_algorithm`, `node_cutoff`, `best_branches`, `smart_prune`
  - overload_and_remove: `max_attempts`, `seed`, `shuffle_strategy`
- Palette hints: what they are, YAML syntax, when they help
- `pal_hints_enabled` toggle
- How to troubleshoot, common failure causes
- Relationship to tile sharing packing modes

**Cross-references:** {doc}`tile-sharing`, {doc}`configuration` for YAML syntax, {doc}`diagnostics` for packing diagnostics
