from enum import StrEnum


class EbirdFields(StrEnum):
    observation_date = "obsDt"
    location_name = "locName"
    location_id = "locId"
    common_name = "comName"
    sub_subnational_name = "subnational2Name"
    sub_subnational_code = "subnational2Code"


class ExportFields(StrEnum):
    common_name = "Common Name"


class RegionFields(StrEnum):
    location_id = "LocationId"
    subnational_name = "Subnational1"
    sub_subnational_name = "Subnational2"
    name = "Name"


# class Color(StrEnum):
#     RED = auto()
#     BLUE = auto()
