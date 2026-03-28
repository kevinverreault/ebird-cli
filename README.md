# eBird CLI

A command-line interface for exploring eBird bird observation data.

## Prerequisites

- Python 3.10+
- eBird API Key (obtainable with free eBird account)

## Installation

1. Clone the repository
2. Set up a virtual environment
3. Install dependencies
4. Configure your eBird API key

## Configuration

### Command-Line Arguments

The CLI supports the following arguments:

| Argument      | Description                           | Default                           | Required |
|---------------|---------------------------------------|-----------------------------------|----------|
| `--api-key`   | eBird API key                         | From `EBIRDAPIKEY` env var        | **Yes**  |
| `--region`    | eBird subnational level 2 region code | From `EBIRDDEFAULTREGION` env var | **Yes**  |
| `--locale`    | Language locale                       | From `EBIRDLOCALE` (or `fr`)      | No       |
| `--lat`       | Latitude                              | From `EBIRDLAT` env var           | No       |
| `--long`      | Longitude                             | From `EBIRDLONG` env var          | No       |
| `--year-list` | Path to year observations list        | From `EBIRDYEARLIST` env var      | No       |
| `--life-list` | Path to lifetime observations list    | From `EBIRDLIFELIST` env var      | No       |

### Environment Variables

You can configure the CLI using the following environment variables to avoid manual parameter entry:

- `EBIRDAPIKEY`: Your eBird API key
- `EBIRDDEFAULTREGION`: Default region for default search and hotspots filtering (`CA-QC-MR`)
- `EBIRDLOCALE`: Preferred language locale (`en`)
- `EBIRDLAT`: Latitude for location-based searches (`47.87`)
- `EBIRDLONG`: Longitude for location-based searches (`-72.17`)
- `EBIRDYEARLIST`: Path to your year observations list (`~/ebird_data/year_list.csv`)
- `EBIRDLIFELIST`: Path to your lifetime observations list (`~/ebird_data/life_list.csv`)

## Usage

### Launching the CLI

   ```bash
   python -m ebird_cli.main --api-key <ebird-api-key> [optional arguments]
   ```

### Available Commands

When launched, the CLI will display a menu of available commands:
- `recent <scope, -region> [-back]`: Fetch recent bird observations
- `notable <scope, -region> [-back]`: Fetch notable bird observations

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

### Search length

Use the optional `-back` parameter to change the number of days back to fetch observations.

- Values: from 1 to 30
- Default: 7

   ```
   notable subnational -region Québec -back 30 
   ```

### List highlighting

When using `--year-list` and `--life-list`:
- Year list targets are highlighted in **green**
- Life list targets are highlighted in **red**

### Obtaining list files

The eBird API does not expose life list or year list data, so these CSV files must be downloaded manually from the eBird website. A helper script is provided to facilitate the process:

```bash
python src/tools/download_lists.py session_id output_dir
```

This requires a valid eBird session cookie (`EBIRD_SESSIONID`), which can be obtained from your browser after logging in to ebird.org. The script must be re-run whenever your lists change.

> **Note:** The life list only changes when you see a species for the first time ever, making it infrequent and easy to manage. The year list changes with every new species seen in the current year and resets annually, requiring more frequent re-runs of the script.

## Development setup

### Virtual environment

1. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

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
