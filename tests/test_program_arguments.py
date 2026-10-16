import argparse

import pytest

from ebird_cli.main import setup_parser

ENV_VARIABLES = {
    "EBIRDAPIKEY": "env-key",
    "EBIRDDEFAULTREGION": "CA-QC-MO",
    "EBIRDLOCALE": "en",
    "EBIRDLAT": "45.50",
    "EBIRDLONG": "-73.57",
    "EBIRDYEARLIST": "~/ebird_data/year_list.csv",
    "EBIRDLIFELIST": "~/ebird_data/life_list.csv",
    "EBIRDAGGREGATIONS": "~/ebird_data/aggregations.json",
}


@pytest.fixture(autouse=True)
def no_ebird_env(monkeypatch):
    for name in ENV_VARIABLES:
        monkeypatch.delenv(name, raising=False)


def parse(*argv):
    """Build the parser after the environment is set: defaults and required are read at setup time."""
    parser = argparse.ArgumentParser()
    setup_parser(parser)
    return parser.parse_args(list(argv))


def test_reads_every_option_from_flags():
    args = parse(
        "--api-key", "flag-key",
        "--region", "CA-QC-MR",
        "--locale", "en",
        "--lat", "46.35",
        "--long", "-72.55",
        "--year-list", "year.csv",
        "--life-list", "life.csv",
        "--aggregations", "aggregations.json",
    )

    assert vars(args) == {
        "api_key": "flag-key",
        "region": "CA-QC-MR",
        "locale": "en",
        "lat": "46.35",
        "long": "-72.55",
        "year_list": "year.csv",
        "life_list": "life.csv",
        "aggregations": "aggregations.json",
    }


def test_reads_every_option_from_environment_variables(monkeypatch):
    for name, value in ENV_VARIABLES.items():
        monkeypatch.setenv(name, value)

    assert vars(parse()) == {
        "api_key": "env-key",
        "region": "CA-QC-MO",
        "locale": "en",
        "lat": "45.50",
        "long": "-73.57",
        "year_list": "~/ebird_data/year_list.csv",
        "life_list": "~/ebird_data/life_list.csv",
        "aggregations": "~/ebird_data/aggregations.json",
    }


def test_flags_override_environment_variables(monkeypatch):
    monkeypatch.setenv("EBIRDAPIKEY", "env-key")
    monkeypatch.setenv("EBIRDDEFAULTREGION", "CA-QC-MO")

    args = parse("--api-key", "flag-key", "--region", "CA-QC-MR")

    assert (args.api_key, args.region) == ("flag-key", "CA-QC-MR")


def test_optional_options_default_to_none_and_locale_to_fr():
    args = parse("--api-key", "flag-key", "--region", "CA-QC-MR")

    assert args.locale == "fr"
    assert [args.lat, args.long, args.year_list, args.life_list, args.aggregations] == [None] * 5


@pytest.mark.parametrize("region", ["CA-QC", "ca-qc-mr", "QC-MR", "CA-Q1-MR"])
def test_region_must_be_a_subnational_level_2_code(region):
    with pytest.raises(SystemExit):
        parse("--api-key", "flag-key", "--region", region)


@pytest.mark.parametrize(
    "argv",
    [("--region", "CA-QC-MR"), ("--api-key", "flag-key")],
    ids=["api key missing", "region missing"],
)
def test_api_key_and_region_are_required_without_their_environment_variables(argv):
    with pytest.raises(SystemExit):
        parse(*argv)


def test_api_key_and_region_are_optional_with_their_environment_variables(monkeypatch):
    monkeypatch.setenv("EBIRDAPIKEY", "env-key")
    monkeypatch.setenv("EBIRDDEFAULTREGION", "CA-QC-MR")

    args = parse()

    assert (args.api_key, args.region) == ("env-key", "CA-QC-MR")
