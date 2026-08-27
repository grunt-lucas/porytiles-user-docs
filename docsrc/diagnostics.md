# Understanding Diagnostics

```{admonition} Page Status
:class: warning
This page is a placeholder. Content coming soon.
```

How to read and control Porytiles output:

- Four severity levels: remarks, warnings, errors, fatal
- How to read error chain output (proximate, steps, root cause)
- Tag-based regex filtering: warnings and remarks are opt-in (hidden unless included), how exclude overrides include
- CLI flags: `--diagnostic-warnings-exclude`, `--diagnostic-warnings-include`, `--diagnostic-remarks-exclude`, `--diagnostic-remarks-include`
- YAML equivalents
- Common diagnostic tags overview table (with links to topic-specific pages)
- Enabling all warnings/remarks with a wildcard include, selectively enabling specific tags

**Cross-references:** {doc}`tile-sharing` for tile-sharing diagnostics, {doc}`configuration` for diagnostic config values
