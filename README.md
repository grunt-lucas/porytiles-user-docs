# Porytiles User Documentation

User-facing documentation for Porytiles, including tutorials, CLI reference, and usage guides.

📖 **Read the docs**: https://grunt-lucas.github.io/porytiles-user-docs/

## Building Locally

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Build HTML documentation
cd docsrc
uv run make html

# View locally
open _build/html/index.html
```

## Viewing Docs For Other Versions

The public site at https://grunt-lucas.github.io/porytiles-user-docs/ always shows the latest stable release's documentation. To view docs for a different version, check out the desired branch or tag in your local clone:

- Released version: `git checkout v1.0.0` (or any other released tag)
- In-progress snapshot: `git checkout develop`

Then follow the [Building Locally](#building-locally) steps above. The version label in the rendered docs reflects the `VERSION` file at the checked-out commit.

## Deploying to GitHub Pages

```bash
cd docsrc
uv run make github
```

This builds the HTML and copies it to the `docs/` directory. Commit and push to deploy.

## Adding Content

- Add `.rst` or `.md` files to `docsrc/`
- Update `index.rst` to include new pages in the toctree
- Rebuild with `uv run make html`

## Structure

```
├── docsrc/           # Sphinx source files
│   ├── conf.py       # Sphinx configuration
│   ├── Makefile      # Build commands
│   ├── index.rst     # Landing page
│   └── _static/      # Static assets (CSS, images)
├── docs/             # Built HTML for GitHub Pages
└── pyproject.toml    # Python dependencies
```
