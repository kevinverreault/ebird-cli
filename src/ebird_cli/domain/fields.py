from enum import StrEnum


class EbirdFields(StrEnum):
    observation_date = "obsDt"
    location_name = "locName"
    location_id = "locId"
    common_name = "comName"
    country_code = "countryCode"
    subnational_name = "subnational1Name"
    subnational_code = "subnational1Code"
    sub_subnational_name = "subnational2Name"
    sub_subnational_code = "subnational2Code"
    name = "name"
    code = "code"


class ExportFields(StrEnum):
    common_name = "Common Name"
