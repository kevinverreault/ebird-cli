from ebird_cli.domain.region import Region


def test_derives_national_subnational_and_regional_codes():
    region = Region("CA-QC-MR")

    assert (region.national, region.subnational, region.regional) == ("CA", "CA-QC", "CA-QC-MR")
