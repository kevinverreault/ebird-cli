import pytest
from conftest import FIXTURES, highlight_of, strip_ansi, table_header, table_rows
from fakes import FakeEbirdClient, observation

MAURICIE_OBSERVATIONS = [
    observation("Canard colvert", "2026-10-12 07:00", subnational2_name="Mauricie"),
    observation("Geai bleu", "2026-10-13 08:00", subnational2_name="Mauricie"),
    observation("Merle d'Amérique", "2026-10-14 09:00", subnational2_name="Mauricie"),
    observation("Harfang des neiges", "2026-10-15 10:00", subnational2_name="Mauricie"),
]


def recent_cli(make_cli, observations, **options):
    return make_cli(FakeEbirdClient(get_observations=observations), **options)


def test_table_has_date_observation_and_location_columns_and_a_total(make_cli, capsys):
    cli = recent_cli(make_cli, MAURICIE_OBSERVATIONS[:2])

    cli.run("recent regional")

    output = capsys.readouterr().out
    assert table_header(output) == ["Date", "Observation", "Location"]
    assert table_rows(output) == [
        ["2026-10-12", "Canard colvert", "Parc de l'Île-Saint-Quentin"],
        ["2026-10-13", "Geai bleu", "Parc de l'Île-Saint-Quentin"],
    ]
    assert strip_ansi(output).rstrip().endswith("Total: 2")


def test_no_observations_prints_an_empty_table_and_zero_total(cli, capsys):
    cli.run("recent regional")

    output = capsys.readouterr().out
    assert table_header(output) == ["Date", "Observation", "Location"]
    assert table_rows(output) == []
    assert strip_ansi(output).rstrip().endswith("Total: 0")


def test_location_and_names_are_cleaned_for_display(make_cli, capsys):
    cli = recent_cli(make_cli, [
        observation("Canard colvert (Domestique)", "2026-10-12", loc_name="Étang Hertel, Montréal, QC"),
    ])

    cli.run("recent regional")

    assert table_rows(capsys.readouterr().out) == [["2026-10-12", "Canard colvert", "Étang Hertel"]]


def test_region_column_appears_when_observations_span_several_regions(make_cli, capsys):
    cli = recent_cli(make_cli, [
        observation("Canard colvert", "2026-10-12", subnational2_name="Mauricie"),
        observation("Geai bleu", "2026-10-13", subnational2_name="Montréal"),
    ])

    cli.run("recent subnational")

    output = capsys.readouterr().out
    assert table_header(output) == ["Date", "Observation", "Location", "Region"]
    assert table_rows(output) == [
        ["2026-10-12", "Canard colvert", "Parc de l'Île-Saint-Quentin", "Mauricie"],
        ["2026-10-13", "Geai bleu", "Parc de l'Île-Saint-Quentin", "Montréal"],
    ]


def test_region_column_is_hidden_when_observations_are_in_one_region(make_cli, capsys):
    cli = recent_cli(make_cli, MAURICIE_OBSERVATIONS)

    cli.run("recent regional")

    assert table_header(capsys.readouterr().out) == ["Date", "Observation", "Location"]


def test_notable_output_matches_recent_output(make_cli, capsys):
    cli = make_cli(FakeEbirdClient(
        get_observations=MAURICIE_OBSERVATIONS,
        get_notable_observations=MAURICIE_OBSERVATIONS,
    ))

    cli.run("recent regional")
    recent_output = capsys.readouterr().out
    cli.run("notable regional")

    assert capsys.readouterr().out == recent_output


def test_no_highlighting_without_year_or_life_list(make_cli, capsys):
    cli = recent_cli(make_cli, MAURICIE_OBSERVATIONS)

    cli.run("recent regional")

    output = capsys.readouterr().out
    assert [highlight_of(name, output) for name in ["Canard colvert", "Geai bleu", "Harfang des neiges"]] == [
        "white",
        "white",
        "white",
    ]


def test_species_missing_from_year_list_are_green(make_cli, capsys):
    cli = recent_cli(make_cli, MAURICIE_OBSERVATIONS, year_list=str(FIXTURES / "year_list.csv"))

    cli.run("recent regional")

    output = capsys.readouterr().out
    assert highlight_of("Canard colvert", output) == "white"
    assert highlight_of("Geai bleu", output) == "green"
    assert highlight_of("Harfang des neiges", output) == "green"


def test_species_missing_from_life_list_are_red(make_cli, capsys):
    cli = recent_cli(make_cli, MAURICIE_OBSERVATIONS, life_list=str(FIXTURES / "life_list.csv"))

    cli.run("recent regional")

    output = capsys.readouterr().out
    assert highlight_of("Canard colvert", output) == "white"
    assert highlight_of("Geai bleu", output) == "white"
    assert highlight_of("Harfang des neiges", output) == "red"


@pytest.mark.parametrize(
    ("name", "highlight"),
    [
        ("Canard colvert", "white"),
        ("Geai bleu", "green"),
        ("Merle d'Amérique", "green"),
        ("Harfang des neiges", "red"),
    ],
)
def test_life_target_highlight_takes_precedence_over_year_target(make_cli, capsys, name, highlight):
    cli = recent_cli(
        make_cli,
        MAURICIE_OBSERVATIONS,
        year_list=str(FIXTURES / "year_list.csv"),
        life_list=str(FIXTURES / "life_list.csv"),
    )

    cli.run("recent regional")

    assert highlight_of(name, capsys.readouterr().out) == highlight
