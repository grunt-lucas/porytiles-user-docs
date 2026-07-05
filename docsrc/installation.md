# Installation

This page covers every way to install Porytiles,
how to confirm it worked,
and how to turn on shell completion.
The simplest and recommended method is [Homebrew](#homebrew-recommended).

## Supported platforms

Porytiles publishes prebuilt binaries for the platforms below.
Anything not on this list can still run Porytiles by [building from source](#building-from-source).

| Platform | Prebuilt binary | Homebrew |
|----------|-----------------|----------|
| Linux x86_64 | Yes (`porytiles-linux-amd64.zip`) | Yes |
| Linux ARM64 | Yes (`porytiles-linux-arm64.zip`) | Yes |
| macOS (Apple Silicon) | Yes (`porytiles-macos-arm64.zip`) | Yes |
| macOS (Intel) | No | No (build from source) |
| Windows | No native build; use [WSL](https://learn.microsoft.com/windows/wsl/) with the Linux binary | Yes, inside WSL |

```{note}
On Windows, run Porytiles inside the Windows Subsystem for Linux (WSL).
A WSL environment is a Linux environment,
so the Linux instructions on this page apply there directly,
including Homebrew.
```

(homebrew-recommended)=
## Homebrew (recommended)

[Homebrew](https://brew.sh) is the simplest option on Linux, macOS, and WSL.
It downloads the right prebuilt binary for your platform and puts `porytiles` on your `PATH` automatically.

```bash
# Latest versioned release (recommended for most users):
brew install grunt-lucas/porytiles/porytiles

# Or the latest rolling snapshot (newest changes, less stable):
brew install grunt-lucas/porytiles/porytiles-snapshot
```

To update later:

```bash
brew upgrade porytiles
```

```{tip}
The `grunt-lucas/porytiles/` prefix is the tap-qualified formula name,
so the commands above work without tapping first.
If you prefer, you can `brew tap grunt-lucas/porytiles` once
and then refer to the formula as just `porytiles`.
```

## Download release binaries

If you would rather not use Homebrew,
download a release archive directly from the
[Releases page](https://github.com/grunt-lucas/porytiles/releases).

Each archive is named for its platform:

- Linux x86_64: `porytiles-linux-amd64.zip`
- Linux ARM64: `porytiles-linux-arm64.zip`
- macOS (Apple Silicon): `porytiles-macos-arm64.zip`

Unzip the archive and copy the `porytiles` binary somewhere on your `PATH`,
for example `~/.local/bin`:

```bash
unzip porytiles-linux-amd64.zip
cd porytiles-linux-amd64
cp porytiles ~/.local/bin/
# If you also want the legacy compiler:
cp porytiles-legacy ~/.local/bin/
```

The archive contains some extra files (test binaries, example resources, the README, and the license).
You only need the `porytiles` binary itself (and the `porytiles-legacy` binary if you want it).

```{tip}
On macOS, a binary downloaded through your browser is quarantined by Gatekeeper,
so the first run may be blocked.
Clear the quarantine flag once and it will run normally:

    xattr -d com.apple.quarantine ./porytiles

A `No such xattr` message just means it was never quarantined, which is fine.
`xattr -c ./porytiles` is guaranteed to succeed but clears every attribute, so it is overkill.
Installing through Homebrew avoids this step entirely.
```

(building-from-source)=
## Building from source

Build from source when you are on a platform without a prebuilt binary (such as an Intel Mac),
when you want changes that aren't in the latest snapshot,
or when you intend to modify Porytiles yourself.

You will need:

- A C++23 compiler (Clang 17+ or GCC 14+)
- CMake 3.20 or newer
- [`uv`](https://docs.astral.sh/uv/) (used for the code-generation scripts in the build)

Clone, build, and install:

```bash
git clone https://github.com/grunt-lucas/porytiles.git
cd porytiles
cmake -S . -B porytiles-build-release -DCMAKE_BUILD_TYPE=Release
cmake --build porytiles-build-release -j4
cmake --install porytiles-build-release --prefix ~/.local
```

This installs `porytiles` to `~/.local/bin`,
so make sure that directory is on your `PATH`.

For the full build walkthrough, including platform-specific compiler notes,
running the test suite, and troubleshooting first-build issues,
see the
[development environment setup guide](https://grunt-lucas.github.io/porytiles-dev-docs/dev-environment-setup.html)
in the developer documentation.

## Verifying the installation

Confirm Porytiles is installed and on your `PATH`:

```bash
porytiles --version
porytiles --help
```

`--version` prints the release you installed,
and `--help` lists every subcommand.
Each subcommand has its own help as well:

```bash
porytiles compile-tileset --help
```

```{note}
If your shell reports that `porytiles` is not found,
the binary is not on your `PATH`.
Homebrew handles this for you;
for a manual install or a build from source,
make sure the directory you copied `porytiles` into
(for example `~/.local/bin`) is listed in your `PATH`.
```

## Shell completion

Porytiles can generate completion scripts for bash, zsh, and fish.
Completions cover every command and config flag,
and they fill in tileset names by querying your project,
so they offer only the tilesets that make sense for each command
(for example, only managed tilesets for `compile-tileset`).

```{note}
A future version of Porytiles will bundle these completion scripts with the Homebrew formula,
so completions install automatically alongside the binary.
Until then, set them up manually as described below.
```

Pick the section for your shell.

### bash

Add this line to your `~/.bashrc`:

```bash
eval "$(porytiles completion bash)"
```

### zsh

Add this line to your `~/.zshrc`:

```zsh
eval "$(porytiles completion zsh)"
```

### fish

Fish does not handle `eval` of the script reliably,
so write it to your completions directory instead:

```fish
porytiles completion fish > ~/.config/fish/completions/porytiles.fish
```

Then restart fish, or source the file in your current session:

```fish
source ~/.config/fish/completions/porytiles.fish
```

Once completion is set up, press your shell's completion key to fill in commands, flags, and tileset names:

```bash
porytiles compile-tileset gTileset_<TAB>
```

## Next steps

With Porytiles installed, you are ready to build a tileset.
Continue with {doc}`creating-your-first-tileset`.
