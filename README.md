# eBird CLI

A command-line interface for exploring eBird bird observation data.

![Notable observations in a region, with life and year list targets highlighted](https://raw.githubusercontent.com/kevinverreault/ebird-cli/main/docs/demo/overview.gif)

## Prerequisites

- Python 3.11+
- eBird API Key (obtainable with free eBird account)

## Installation

1. Install the [`ebird-cli` package](https://pypi.org/project/ebird-cli/) from PyPI, which provides the `ebird-cli` and `ebird-cli-download-lists` commands:
   ```bash
   pip install ebird-cli
   ```
   To keep the CLI in its own environment, install it with [pipx](https://pipx.pypa.io/) instead:
   ```bash
   pipx install ebird-cli
   ```
2. Run `ebird-cli`. The first launch asks for your eBird API key, Home Region and the other settings, and saves them (see [First-launch setup](#first-launch-setup))

To upgrade to the latest release, run `pip install --upgrade ebird-cli` (or `pipx upgrade ebird-cli`). To work on the code instead, see [Development setup](#development-setup).

## Configuration

Each setting is read from the first of these sources that has it:

1. its command-line argument
2. its environment variable
3. the saved settings
4. its default (only the locale has one: `fr`)

The eBird API key and the Home Region are required, but the saved settings always hold them once first-launch setup is done.

### First-launch setup

The first time `ebird-cli` starts without saved settings, it asks for each setting before it contacts eBird: eBird API key, Home Region, locale, latitude, longitude, year list path, life list path and aggregations path. Each answer is pre-filled with the value a command-line argument or environment variable already gives it, so press Enter to keep it. The API key and the Home Region (a subnational level 2 code like `CA-QC-MR` or `US-NY-061`) are required; leave any other setting empty with Enter. Interrupting setup with Ctrl+C (or Ctrl+D on an empty answer) saves nothing, and setup starts again on the next launch.

The answers are saved to `settings.json` in the platform-appropriate user config directory, and every later launch reads them without asking again:

- Windows: `%LOCALAPPDATA%\ebird_cli\ebird_cli\settings.json`
- Linux: `~/.config/ebird_cli/settings.json` (under `$XDG_CONFIG_HOME` instead of `~/.config` when it is set)
- macOS: `~/Library/Application Support/ebird_cli/settings.json`

This directory is apart from the [data cache](#data-cache), so deleting the cache keeps your settings. Setup never writes environment variables.

### Changing settings

Run `ebird-cli settings` to change the saved settings at any time:

```bash
ebird-cli settings
```

It asks the same questions as first-launch setup, pre-filled with the saved settings, then overwrites them and exits; the next `ebird-cli` launch uses the new values. It never contacts eBird, so it also fixes a wrong saved API key or Home Region. Ctrl+C (or Ctrl+D on an empty answer) leaves the saved settings untouched. Because environment variables outrank saved settings, it names each saved setting that an environment variable you have set overrides.

### Command-Line Arguments

The CLI supports the following arguments:

| Argument         | Description                           | Otherwise from                               | Required |
| ---------------- | ------------------------------------- | -------------------------------------------- | -------- |
| `--api-key`      | eBird API key                         | `EBIRDAPIKEY` env var, saved settings        | **Yes**  |
| `--region`       | eBird subnational level 2 region code | `EBIRDDEFAULTREGION` env var, saved settings | **Yes**  |
| `--locale`       | Language locale                       | `EBIRDLOCALE` env var, saved settings, `fr`  | No       |
| `--lat`          | Latitude                              | `EBIRDLAT` env var, saved settings           | No       |
| `--long`         | Longitude                             | `EBIRDLONG` env var, saved settings          | No       |
| `--year-list`    | Path to year observations list        | `EBIRDYEARLIST` env var, saved settings      | No       |
| `--life-list`    | Path to lifetime observations list    | `EBIRDLIFELIST` env var, saved settings      | No       |
| `--aggregations` | Path to aggregations JSON file        | `EBIRDAGGREGATIONS` env var, saved settings  | No       |

### Environment Variables

The following environment variables override the saved settings and are overridden by the command-line arguments:

- `EBIRDAPIKEY`: Your eBird API key
- `EBIRDDEFAULTREGION`: Default region for default search and hotspots filtering (`CA-QC-MR`)
- `EBIRDLOCALE`: Preferred language locale (`fr`)
- `EBIRDLAT`: Latitude for location-based searches (`47.87`)
- `EBIRDLONG`: Longitude for location-based searches (`-72.17`)
- `EBIRDYEARLIST`: Path to your year observations list (`~/ebird_data/year_list.csv`)
- `EBIRDLIFELIST`: Path to your lifetime observations list (`~/ebird_data/life_list.csv`)
- `EBIRDAGGREGATIONS`: Path to your aggregations JSON file (`~/ebird_data/aggregations.json`)

## Usage

### Launching the CLI

```bash
ebird-cli [optional arguments]
```

Any argument overrides the saved setting for that launch only.

`ebird-cli --version` prints the installed version.

### Available Commands

When launched, the CLI will display a menu of available commands:

- `recent <scope, -region> [-back, -species]`: Fetch recent bird observations
- `notable <scope, -region> [-back]`: Fetch notable bird observations
- `settings`: Change the saved settings without leaving the prompt, as [`ebird-cli settings`](#changing-settings) does. The running session keeps its settings; the changes apply on the next launch. Ctrl+C (or Ctrl+D on an empty answer) returns to the prompt with the saved settings untouched.

### Autocompletion

Suggestions appear as you type: command names, scopes, flags, region names for the chosen scope, species names and `-back` values. Press Tab to accept the first suggestion, or press it again to cycle through them.

![Building a full command from autocompletion suggestions](https://raw.githubusercontent.com/kevinverreault/ebird-cli/main/docs/demo/autocomplete.gif)

### Search Scopes

Bird observations can be searched in multiple scopes.

1. **Nearby**: Based on provided latitude and longitude
   - Requires `--lat` and `--long` program arguments
   - Shows observations near the specified geographic coordinates
   - `recent nearby`

2. **Hotspot**: eBird-defined hotspots
   - `recent hotspot -region Dunes de Tadoussac`

3. **Regional**: eBird Subnational Level 2
   - `recent regional -region Montréal`

4. **Subnational**: eBird Subnational Level 1
   - `recent subnational -region Québec`

The `-region` flag supports context-sensitive autocompletion based on the selected scope. If no `-region` flag is provided, default region will be used.

![Autocompleting a hotspot name and fetching its recent observations](https://raw.githubusercontent.com/kevinverreault/ebird-cli/main/docs/demo/hotspot-autocomplete.gif)

### Search length

Use the optional `-back` parameter to change the number of days back to fetch observations.

- Values: from 1 to 30
- Default: 7

  ```
  notable subnational -region Québec -back 30
  ```

### Aggregations

Aggregations allow you to define custom named groups of hotspots that appear alongside eBird hotspots when using the `hotspot` scope. This is useful for combining multiple nearby locations under a single name.

Provide the path to your aggregations file at setup, or via `--aggregations` or the `EBIRDAGGREGATIONS` environment variable:

```bash
ebird-cli --aggregations ~/ebird_data/aggregations.json
```

The aggregations file is a JSON array where each element maps a custom name to a list of eBird location IDs:

```json
[
  {
    "Technoparc": ["L9980102", "L4886900", "L11363355"]
  }
]
```

Once configured, aggregation names are available in the `-region` autocomplete when using the `hotspot` scope:

```
recent hotspot -region Technoparc
```

### Species filter

Use the optional `-species` flag with the `recent` command to filter observations to a single species.

```
recent nearby -species Canard colvert
recent regional -region Montréal -species Harfang des neiges
```

The `-species` flag supports context-sensitive autocompletion using the cached taxonomy. Start typing a common name and press Tab to see matching species.

![Autocompleting a species name and filtering recent observations to it](https://raw.githubusercontent.com/kevinverreault/ebird-cli/main/docs/demo/species-filter.gif)

> **Note:** Autocompletion and lookup use the locale specified by `--locale` / `EBIRDLOCALE`. Species names must be typed in the configured locale.

### List highlighting

When using `--year-list` and `--life-list`:

- Year list targets are highlighted in **green**
- Life list targets are highlighted in **red**

### Obtaining list files

The eBird API does not expose life list or year list data, so these CSV files must be downloaded from the eBird website. The `ebird-cli-download-lists` command, installed alongside `ebird-cli`, downloads both into `output_dir` as `life_list.csv` and `year_list.csv`:

```bash
ebird-cli-download-lists session_id output_dir
```

This requires a valid eBird session cookie (`EBIRD_SESSIONID`), which can be obtained from your browser after logging in to ebird.org. The command must be re-run whenever your lists change.

> **Note:** The life list only changes when you see a species for the first time ever, making it infrequent and easy to manage. The year list changes with every new species seen in the current year and resets annually, requiring more frequent re-runs of the command.

## Data cache

To avoid redundant API calls to eBird, the CLI caches reference data locally on first run. The cache is stored in the platform-appropriate user cache directory (e.g. `%LOCALAPPDATA%\ebird_cli\ebird_cli\Cache` on Windows, `~/.cache/ebird_cli` on Linux/macOS).

The following data is cached:

- **Location data** (per region): subnational level 1 regions, subnational level 2 regions, and every hotspot in the subnational region — stored as JSON files under `location/<national>/` and `location/<national>/<subnational>/`
- **Taxonomy** (per locale and national region): the full eBird taxonomy filtered to species observed in the configured country — stored as CSV files under `taxonomy/<national>/`

Hotspots are fetched again on launch once their cached file is more than 30 days old, so new hotspots appear; if eBird can't be reached, the older file is used. All other cached data is written once and reused on every subsequent launch. To force a refresh (e.g. after a new eBird taxonomy release or a region change), delete the relevant files or the entire cache directory; your saved settings live outside it and are kept (on Windows, delete the `Cache` folder, not its parent, which holds `settings.json`).

## Log file

Each launch appends debug messages to `app.log` in the platform-appropriate user log directory, created on first launch:

- Windows: `%LOCALAPPDATA%\ebird_cli\ebird_cli\Logs\app.log`
- Linux: `~/.cache/ebird_cli/log/app.log` (under `$XDG_CACHE_HOME` instead of `~/.cache` when it is set)
- macOS: `~/Library/Logs/ebird_cli/app.log`

The file is never rotated or trimmed; delete it at any time.

## Development setup

### Virtual environment

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

### Tests

The test suite runs offline: it never calls the eBird API, needs no API key and never touches your user cache, log or config directory.

```bash
python -m pytest
```

Tests live in `tests/`, mirroring the source layout:

- `tests/cli/`: the `recent` and `notable` commands and autocompletion, driven through their public entry points
- `tests/services/`, `tests/domain/`: cache, location and taxonomy services and domain value parsing
- `tests/utils/`: where the app log is written
- `tests/test_prompt_dispatch.py`, `tests/test_program_arguments.py`: prompt input handling and program arguments
- `tests/test_settings.py`, `tests/test_launch.py`: the setup questions and settings file, and launching with or without saved settings
- `tests/conftest.py`: shared fixtures, including `make_cli`, which wires real services and commands the way `main` does
- `tests/fakes.py`: the test doubles: the in-memory fake eBird client, a fake HTTP session and scripted answers to the setup questions
- `tests/fixtures/`: small hand-written cache, list and aggregation files for the `CA-QC-MR` region

Tests named `..._currently_...` pin behaviour that looks accidental, so changing it is a deliberate test change.

### Demo GIFs

The GIFs in this README are recorded with [VHS](https://github.com/charmbracelet/vhs) from the tapes in `docs/demo/`. They call the live eBird API, so they need your API key and environment variables set. `config.tape` holds the shared settings and launches the CLI out of frame.

On Windows, install VHS and its terminal dependency, then re-record a GIF from the repository root:

```bash
winget install charmbracelet.vhs tsl0922.ttyd
```

```bash
vhs docs/demo/overview.tape
```

VHS also needs `ffmpeg` on the `PATH`.

### Cutting a release

Releases are published to [PyPI](https://pypi.org/project/ebird-cli/) by the `Release` workflow (`.github/workflows/release.yml`) through trusted publishing; no API token is involved.

1. Bump `version` in `pyproject.toml` and merge it to `main`.
2. Optionally, do a dry run: run the `Release` workflow manually from the Actions tab. It uploads that version to [TestPyPI](https://test.pypi.org/project/ebird-cli/), which accepts each version only once. Check the upload installs:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ebird-cli
   ```
3. Tag the release commit `vX.Y.Z`, matching the version, and push the tag.
4. Publish a GitHub release from that tag. The workflow uploads it to PyPI, and fails without uploading if the tag doesn't match the version in `pyproject.toml`.

## Credits

Bird observation data and the eBird platform are provided by the [Cornell Lab of Ornithology](https://www.birds.cornell.edu/). This project would not be possible without their freely available [eBird API](https://documenter.getpostman.com/view/664302/S1ENwy59).

This project relies on the following open-source packages:

- [ebird-api](https://pypi.org/project/ebird-api/) — Python wrapper for the eBird API
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) — Interactive command-line interface with autocompletion
- [rich](https://rich.readthedocs.io/) — Terminal formatting and highlighted output
- [pandas](https://pandas.pydata.org/) — CSV observation list parsing
- [colorama](https://pypi.org/project/colorama/) — Cross-platform terminal color support
- [requests](https://requests.readthedocs.io/) — HTTP requests to the eBird API

## License

MIT License
