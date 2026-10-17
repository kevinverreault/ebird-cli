# eBird CLI

An interactive prompt for looking up recent and notable bird observations from eBird around the user's home Region.

## Places

**Region**:
An eBird area identified by a code at one of three levels: country (`CA`), subnational (`CA-QC`), or regional (`CA-QC-MR`).
_Avoid_: area, zone

**Home Region**:
The regional-level Region the user configures as their default; every other default place is derived from it.
_Avoid_: default region (as a noun)

**Hotspot**:
A public eBird birding site with its own location id (`L…`), lying inside a Region.
_Avoid_: site, spot

**Aggregation**:
A user-defined, named group of Hotspots that is treated as a single Hotspot.
_Avoid_: hotspot group, cluster

**Location**:
Any place the user can name in a query: a Region, a Hotspot or an Aggregation.
_Avoid_: place, area

**Location catalogue**:
Every Location the user can name around their Home Region, organised by Regional scope.
_Avoid_: location service, location cache

## Queries

**Regional scope**:
The kind of place a query targets: `hotspot`, `regional`, `subnational`, or `nearby` (around the user's coordinates).
_Avoid_: level, region type

**Observation kind**:
Which observations a query asks eBird for: `recent` (every species reported, or one species' reports) or `notable` (species eBird flags as rare or unusual for the place).
_Avoid_: query type, endpoint

**Observation query**:
Observations of one Observation kind at a Location or nearby, with repeat reports collapsed: recent keeps the latest per species (or, for one species, per Location), notable the first per species at each Location.
_Avoid_: observation service
