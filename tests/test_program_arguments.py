import argparse

import pytest

from ebird_cli.main import read_settings, setup_parser


def parse(*argv, saved=None):
    """The settings a launch with argv and saved settings resolves."""
    parser = argparse.ArgumentParser()
    setup_parser(parser)
    return read_settings(parser, parser.parse_args(list(argv)), saved)


def test_reads_every_option_from_flags():
    args = parse(
        "--api-key",
        "flag-key",
        "--region",
        "CA-QC-MR",
        "--locale",
        "en",
        "--lat",
        "46.35",
        "--long",
        "-72.55",
        "--year-list",
        "year.csv",
        "--life-list",
        "life.csv",
        "--aggregations",
        "aggregations.json",
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


def test_optional_options_default_to_none_and_locale_to_fr():
    args = parse("--api-key", "flag-key", "--region", "CA-QC-MR")

    assert args.locale == "fr"
    assert [args.lat, args.long, args.year_list, args.life_list, args.aggregations] == [None] * 5


@pytest.mark.parametrize("region", ["CA-QC", "ca-qc-mr", "QC-MR", "CA-QC-MONT", "CA-QC-MR-X", "CA-QUEB-MR"])
def test_region_must_be_a_subnational_level_2_code(region):
    with pytest.raises(SystemExit):
        parse("--api-key", "flag-key", "--region", region)


@pytest.mark.parametrize("region", ["CA-QC-MR", "US-NY-061", "JP-01-177", "GB-ENG-LND", "CA-Q1-MR"])
def test_region_accepts_letter_and_number_subnational_level_2_codes(region):
    assert parse("--api-key", "flag-key", "--region", region).region == region


@pytest.mark.parametrize(
    ("argv", "flag"),
    [(("--region", "CA-QC-MR"), "--api-key"), (("--api-key", "flag-key"), "--region")],
    ids=["api key missing", "region missing"],
)
def test_api_key_and_region_are_required_without_their_flag_or_saved_settings(argv, flag, capsys):
    with pytest.raises(SystemExit):
        parse(*argv)

    error = capsys.readouterr().err.splitlines()[-1]
    assert error.endswith(f"error: {flag} is required: set it or run ebird-cli settings")


def test_region_from_saved_settings_must_be_a_subnational_level_2_code():
    with pytest.raises(SystemExit):
        parse(saved={"api_key": "saved-key", "region": "CA-QC"})


SAVED = {
    "api_key": "saved-key",
    "region": "CA-QC-CN",
    "locale": "es",
    "lat": "48.13",
    "long": "-69.72",
    "year_list": "saved/year_list.csv",
    "life_list": "saved/life_list.csv",
    "aggregations": "saved/aggregations.json",
}


def test_saved_settings_supply_every_option_without_flags():
    assert vars(parse(saved=SAVED)) == SAVED


def test_flags_override_saved_settings():
    args = parse("--api-key", "flag-key", "--region", "CA-QC-MR", "--locale", "en", saved=SAVED)

    assert (args.api_key, args.region, args.locale, args.lat) == ("flag-key", "CA-QC-MR", "en", "48.13")


def test_settings_missing_from_saved_settings_fall_back_to_their_default():
    args = parse(saved={"api_key": "saved-key", "region": "CA-QC-CN"})

    assert args.locale == "fr"
    assert [args.lat, args.long, args.year_list, args.life_list, args.aggregations] == [None] * 5


def test_version_prints_the_version_declared_in_pyproject(capsys, declared_version):
    with pytest.raises(SystemExit) as exit_info:
        parse("--version")

    assert exit_info.value.code == 0
    assert capsys.readouterr().out == f"ebird-cli {declared_version}\n"
