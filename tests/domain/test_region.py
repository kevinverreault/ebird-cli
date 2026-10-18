from ebird_cli.domain.region import Region


def test_derives_national_subnational_and_regional_codes():
    region = Region("CA-QC-MR")

    assert (region.national, region.subnational, region.regional) == ("CA", "CA-QC", "CA-QC-MR")


def test_derives_codes_from_a_regional_code_whose_parts_are_numbers():
    region = Region("JP-01-177")

    assert (region.national, region.subnational, region.regional) == ("JP", "JP-01", "JP-01-177")
