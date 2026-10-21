# Developing eBird CLI

How to work on the code of [eBird CLI](https://github.com/kevinverreault/ebird-cli). To use it, see the [README](README.md).

## Virtual environment

1. Clone the repository and create a virtual environment in it:
   ```bash
   git clone https://github.com/kevinverreault/ebird-cli.git
   cd ebird-cli
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`

3. Install the project in editable mode with the dev tools (`requirements-dev.txt` adds the test, lint and build tools to the pinned runtime dependencies):
   ```bash
   pip install -e . -r requirements-dev.txt
   ```
   The tests read the version from the installed package, so they need this editable install.

## Tests

The test suite runs offline: it never calls the eBird API, needs no API key and never touches your user cache, log or config directory.

```bash
python -m pytest
```

Tests live in `tests/`, mirroring the source layout:

- `tests/cli/`: the `recent` and `notable` commands and autocompletion, driven through their public entry points
- `tests/services/`, `tests/domain/`: cache, location and taxonomy services and domain value parsing
- `tests/utils/`: whether and where the app log is written
- `tests/test_prompt_dispatch.py`, `tests/test_program_arguments.py`: prompt input handling and program arguments
- `tests/test_settings.py`, `tests/test_launch.py`: the setup questions and settings file, and launching with or without saved settings
- `tests/conftest.py`: shared fixtures, including `make_cli`, which wires real services and commands the way `main` does
- `tests/fakes.py`: the test doubles: the in-memory fake eBird client, a fake HTTP session and scripted answers to the setup questions
- `tests/fixtures/`: small hand-written cache, list and aggregation files for the `CA-QC-MR` region

Tests named `..._currently_...` pin behaviour that looks accidental, so changing it is a deliberate test change.

## Demo GIFs

The GIFs in the README are recorded with [VHS](https://github.com/charmbracelet/vhs) from the tapes in `docs/demo/`. They call the live eBird API, so they need saved settings with your API key. `config.tape` holds the shared settings and launches the CLI out of frame.

On Windows, install VHS and its terminal dependency, then re-record a GIF from the repository root:

```bash
winget install charmbracelet.vhs tsl0922.ttyd
```

```bash
vhs docs/demo/overview.tape
```

VHS also needs `ffmpeg` on the `PATH`.

## Log file

The log file is off by default. Launch with `--log` to append debug messages to `app.log` in the platform-appropriate user log directory, created by the first launch that uses it:

```bash
ebird-cli --log
```

- Windows: `%LOCALAPPDATA%\ebird_cli\ebird_cli\Logs\app.log`
- Linux: `~/.cache/ebird_cli/log/app.log` (under `$XDG_CACHE_HOME` instead of `~/.cache` when it is set)
- macOS: `~/Library/Logs/ebird_cli/app.log`

The file is never rotated or trimmed; delete it at any time.

## Cutting a release

Releases are published to [PyPI](https://pypi.org/project/ebird-cli/) by the `Release` workflow (`.github/workflows/release.yml`) through trusted publishing; no API token is involved.

1. Bump `version` in `pyproject.toml` and merge it to `main`.
2. Optionally, do a dry run: run the `Release` workflow manually from the Actions tab. It uploads that version to [TestPyPI](https://test.pypi.org/project/ebird-cli/), which accepts each version only once. Check the upload installs:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ebird-cli
   ```
3. Tag the release commit `vX.Y.Z`, matching the version, and push the tag.
4. Publish a GitHub release from that tag. The workflow uploads it to PyPI, and fails without uploading if the tag doesn't match the version in `pyproject.toml`.
