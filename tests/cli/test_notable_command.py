import pytest
from conftest import LAT, LONG, table_rows
from fakes import Call, FakeEbirdClient, observation

from ebird_cli.cli.grammar import CommandLineError


def test_notable_nearby_requests_nearby_notable_observations(cli):
    cli.run("notable nearby")

    assert cli.client.calls == [Call("get_nearby_notable", (LAT, LONG, 50), back="7", hotspot=True)]


@pytest.mark.parametrize(
    ("line", "region_ids"),
    [
        ("notable regional -region Côte-Nord", ["CA-QC-CN"]),
        ("notable subnational -region Québec", ["CA-QC"]),
        ("notable hotspot -region Parc national de la Mauricie", ["L2002"]),
        ("notable regional", ["CA-QC-MR"]),
        ("notable subnational", ["CA-QC"]),
    ],
)
def test_notable_requests_notable_observations_for_the_resolved_region(cli, line, region_ids):
    cli.run(line)

    assert cli.client.calls == [Call("get_notable_observations", (region_ids,), back="7", hotspot=True)]


def test_notable_passes_back_to_ebird(cli):
    cli.run("notable subnational -region Québec -back 30")

    assert cli.client.calls[0].back == "30"


def test_notable_rejects_a_species_flag_as_an_invalid_argument(cli):
    with pytest.raises(CommandLineError, match="unrecognized arguments: -species Harfang des neiges"):
        cli.run("notable nearby -species Harfang des neiges")

    assert cli.client.calls == []


def test_notable_keeps_the_first_observation_per_location_and_species_oldest_first(make_cli, capsys):
    cli = make_cli(
        FakeEbirdClient(
            get_notable_observations=[
                observation("Harfang des neiges", "2026-10-15 08:00", loc_name="Aéroport de Trois-Rivières"),
                observation("Pygargue à tête blanche", "2026-10-12", loc_name="Parc de l'Île-Saint-Quentin"),
                observation("Harfang des neiges", "2026-10-16 09:30", loc_name="Aéroport de Trois-Rivières"),
                observation("Harfang des neiges", "2026-10-11 10:00", loc_name="Parc de l'Île-Saint-Quentin"),
            ]
        )
    )

    cli.run("notable regional")

    assert table_rows(capsys.readouterr().out) == [
        ["2026-10-11", "Harfang des neiges", "Parc de l'Île-Saint-Quentin"],
        ["2026-10-12", "Pygargue à tête blanche", "Parc de l'Île-Saint-Quentin"],
        ["2026-10-15", "Harfang des neiges", "Aéroport de Trois-Rivières"],
    ]
