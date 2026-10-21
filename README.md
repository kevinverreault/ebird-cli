# eBird CLI

A command-line interface for exploring eBird bird observation data.

![Notable observations in a region, with life and year list targets highlighted](https://raw.githubusercontent.com/kevinverreault/ebird-cli/main/docs/demo/overview.gif)

## Prerequisites

- Python 3.11+
- An eBird API key and the code of your Home Region, the only two required settings (see [eBird API key and codes](#ebird-api-key-and-codes))

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

To upgrade to the latest release, run `pip install --upgrade ebird-cli` (or `pipx upgrade ebird-cli`). To work on the code instead, see [Development](#development).

## Configuration

Only two settings are required:

- **eBird API key**: lets the CLI call the eBird API
- **Home Region**: the eBird region code of your county or regional municipality, like `CA-QC-MR` or `US-NY-061`, which every query uses unless you name another region or hotspot

Every other setting is optional and turns on one feature:

- **Locale**: the language of species names (default `fr`)
- **Latitude** and **longitude**: the [`nearby` scope](#search-scopes)
- **Year list** and **life list**: [list highlighting](#list-highlighting)
- **Aggregations**: [your own groups of hotspots](#aggregations)

Each setting is read from the first of these sources that has it:

1. its command-line argument
2. the saved settings
3. its default (only the locale has one: `fr`)

Once first-launch setup is done, the saved settings always hold the two required ones.

### eBird API key and codes

eBird names every region and hotspot with a code, which you can read from the address of its page on [ebird.org](https://ebird.org):

- **Region codes** name a country (`CA`), a subnational level 1 region such as a state or province (`CA-QC`), or a subnational level 2 region such as a county or regional municipality (`CA-QC-MR`). Your Home Region must be a subnational level 2 code. To find it, search for your county on [eBird's Explore page](https://ebird.org/explore) and open it: the code follows `/region/` in its page address, as in `https://ebird.org/region/CA-QC-MR`.
- **Location IDs** name a hotspot and start with `L`, as in `L1234567`. Open the hotspot's page on eBird: the ID follows `/hotspot/` in its address, as in `https://ebird.org/hotspot/L1234567`. You only need them for [aggregations](#aggregations); the CLI looks hotspots up by name.

To get an API key, sign in to your free eBird account and request one at [ebird.org/api/keygen](https://ebird.org/api/keygen). eBird shows the key on that page.

### First-launch setup

The first time `ebird-cli` starts without saved settings, it asks for each setting before it contacts eBird: eBird API key, Home Region, locale, latitude, longitude, year list path, life list path and aggregations path. Each answer is pre-filled with the value a command-line argument already gives it, so press Enter to keep it. The API key and the Home Region (a subnational level 2 code like `CA-QC-MR` or `US-NY-061`; see [eBird API key and codes](#ebird-api-key-and-codes)) are required; leave any other setting empty with Enter. Interrupting setup with Ctrl+C (or Ctrl+D on an empty answer) saves nothing, and setup starts again on the next launch.

The answers are saved to `settings.json` in the platform-appropriate user config directory, and every later launch reads them without asking again:

- Windows: `%LOCALAPPDATA%\ebird_cli\ebird_cli\settings.json`
- Linux: `~/.config/ebird_cli/settings.json` (under `$XDG_CONFIG_HOME` instead of `~/.config` when it is set)
- macOS: `~/Library/Application Support/ebird_cli/settings.json`

This directory is apart from the [data cache](#data-cache), so deleting the cache keeps your settings.

### Changing settings

Run `ebird-cli settings` to change the saved settings at any time:

```bash
ebird-cli settings
```

It asks the same questions as first-launch setup, pre-filled with the saved settings, then overwrites them and exits; the next `ebird-cli` launch uses the new values. It never contacts eBird, so it also fixes a wrong saved API key or Home Region. Ctrl+C (or Ctrl+D on an empty answer) leaves the saved settings untouched.

### Command-Line Arguments

The CLI supports the following arguments:

| Argument         | Description                           | Otherwise from       | Required |
| ---------------- | ------------------------------------- | -------------------- | -------- |
| `--api-key`      | eBird API key                         | saved settings       | **Yes**  |
| `--region`       | eBird subnational level 2 region code | saved settings       | **Yes**  |
| `--locale`       | Language locale                       | saved settings, `fr` | No       |
| `--lat`          | Latitude                              | saved settings       | No       |
| `--long`         | Longitude                             | saved settings       | No       |
| `--year-list`    | Path to year observations list        | saved settings       | No       |
| `--life-list`    | Path to lifetime observations list    | saved settings       | No       |
| `--aggregations` | Path to aggregations JSON file        | saved settings       | No       |
| `--log`          | Write a log file for this launch      | off                  | No       |

## Usage

### Launching the CLI

```bash
ebird-cli [optional arguments]
```

Any argument overrides the saved setting for that launch only.

`ebird-cli --version` prints the installed version.

`ebird-cli --log` writes debug messages to a log file, which is off by default (see [Log file](https://github.com/kevinverreault/ebird-cli/blob/main/DEVELOPMENT.md#log-file)).

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
   - Requires a latitude and longitude, from `--lat` and `--long` or the saved settings
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

Aggregations are similar to eBird's hotspot groups, but you set them yourself in a file, while eBird's regional administrators manage hotspot groups. Use one to group hotspots that eBird does not, or to name the group the way you like.

Provide the path to your aggregations file at setup, or via `--aggregations`:

```bash
ebird-cli --aggregations ~/ebird_data/aggregations.json
```

The aggregations file is a JSON array where each element maps a custom name to a list of eBird [location IDs](#ebird-api-key-and-codes):

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

> **Note:** Autocompletion and lookup use the locale specified by `--locale` or the saved settings. Species names must be typed in the configured locale.

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

## Development

To work on the code, run the tests, re-record the demo GIFs, turn on the log file or cut a release, see [DEVELOPMENT.md](https://github.com/kevinverreault/ebird-cli/blob/main/DEVELOPMENT.md).

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
