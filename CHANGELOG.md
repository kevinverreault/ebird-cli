# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-10-18

### Upgrading from 0.1.0

`EBIRD*` environment variables are no longer read. The first launch after upgrading runs setup, which asks for your eBird API key and Home Region again; `ebird-cli settings` changes them later. You can remove the variables from your shell profile.

### Added

- First-launch setup: the first time `ebird-cli` starts without saved settings, it asks for each setting and saves them to `settings.json` in the user config directory.
- `ebird-cli settings` changes the saved settings without contacting eBird, so it also fixes a wrong API key or Home Region.
- The `settings` prompt command changes the saved settings without leaving the prompt. The changes apply on the next launch.
- Home Regions with numeric codes, such as `US-NY-061` and `JP-01-177`, are accepted.
- The test suite runs in CI on pushes to `main` and on pull requests.

### Changed

- Each setting is read from its command-line argument, else the saved settings, else its default.
- Home Region codes with trailing text, such as `CA-QC-MR-X`, are rejected.
- Error messages point at flags and settings instead of environment variables.

### Removed

- **Breaking:** the `EBIRDAPIKEY`, `EBIRDDEFAULTREGION`, `EBIRDLOCALE`, `EBIRDLAT`, `EBIRDLONG`, `EBIRDYEARLIST`, `EBIRDLIFELIST` and `EBIRDAGGREGATIONS` environment variables.

## [0.1.0] - 2026-10-18

First release on PyPI.

### Added

- `recent` and `notable` commands that fetch observations in the nearby, hotspot, regional and subnational scopes, shown as Rich tables.
- Autocompletion for command names, scopes, flags, region names, species names and `-back` values.
- `-back` sets how many days back to search, from 1 to 30 (default 7).
- `-species` filters recent observations to one species, using the cached taxonomy in the configured locale.
- Aggregations: custom named groups of hotspots in the hotspot scope.
- Year list and life list targets are highlighted when list files are given.
- `ebird-cli-download-lists` downloads the life and year list CSV files from eBird.
- Location data and taxonomy are cached in the user cache directory; hotspots are fetched again once their cache is more than 30 days old.
- Settings from command-line arguments or `EBIRD*` environment variables.
- `ebird-cli --version` prints the installed version.
- The app log is written to the user log directory.

[0.2.0]: https://github.com/kevinverreault/ebird-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kevinverreault/ebird-cli/releases/tag/v0.1.0
