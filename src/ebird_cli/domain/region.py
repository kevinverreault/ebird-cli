class Region:
    def __init__(self, ebird_region: str):
        region_segments = ebird_region.split('-')
        self.national = region_segments[0]
        self.subnational = f"{region_segments[0]}-{region_segments[1]}"
        self.regional = ebird_region
