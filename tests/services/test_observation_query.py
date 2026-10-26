import pytest
from conftest import LAT, LONG
from fakes import Call, FakeEbirdClient, observation

from ebird_cli.domain.region import Region
from ebird_cli.domain.regional_scopes import RegionalScopes
from ebird_cli.services.location_catalogue import LocationCatalogue
from ebird_cli.services.observation_query import ObservationKind, ObservationQuery

CATALOGUE = LocationCatalogue(
    Region("CA-QC-MR"),
    subnationals=[{"code": "CA-QC", "name": "Québec"}],
    regionals=[{"code": "CA-QC-MR", "name": "Mauricie"}, {"code": "CA-QC-MO", "name": "Montréal"}],
    hotspots=[{"locId": "L1001", "locName": "Dunes de Tadoussac"}],
    aggregations={"Technoparc": ["L3001", "L3002"]},
)


def make_query(client, lat=LAT, long=LONG) -> ObservationQuery:
    return ObservationQuery(client, CATALOGUE, lat, long)


def summary(observations) -> list[tuple[str, str, str]]:
    return [(obs.observation_date, obs.name, obs.location) for obs in observations]


def test_recent_in_a_named_region_keeps_the_latest_observation_per_species_oldest_first():
    client = FakeEbirdClient(
        get_observations=[
            observation("Geai bleu", "2026-10-15 09:00", loc_name="Parc national de la Mauricie"),
            observation("Canard colvert", "2026-10-12", loc_name="Parc de l'Île-Saint-Quentin"),
            observation("Geai bleu", "2026-10-13 07:30", loc_name="Parc de l'Île-Saint-Quentin"),
        ]
    )

    observations = make_query(client).observations(ObservationKind.RECENT, RegionalScopes.REGIONAL, "Montréal", back=3)

    assert client.calls == [Call("get_observations", (["CA-QC-MO"],), back=3, hotspot=True)]
    assert summary(observations) == [
        ("2026-10-12", "Canard colvert", "Parc de l'Île-Saint-Quentin"),
        ("2026-10-15", "Geai bleu", "Parc national de la Mauricie"),
    ]


def test_recent_nearby_requests_observations_within_50_km_of_the_coordinates():
    client = FakeEbirdClient()

    make_query(client).observations(ObservationKind.RECENT, RegionalScopes.NEARBY)

    assert client.calls == [Call("get_nearby_observations", (LAT, LONG, 50), back=7, hotspot=True)]


@pytest.mark.parametrize("kind", list(ObservationKind))
@pytest.mark.parametrize(("lat", "long"), [(None, None), (LAT, None), (None, LONG)])
def test_nearby_without_coordinates_is_refused_without_calling_ebird(kind, lat, long):
    client = FakeEbirdClient()

    with pytest.raises(ValueError, match="--lat and --long"):
        make_query(client, lat, long).observations(kind, RegionalScopes.NEARBY)

    assert client.calls == []


def test_notable_in_a_hotspot_keeps_the_first_observation_per_location_and_species_oldest_first():
    client = FakeEbirdClient(
        get_notable_observations=[
            observation("Harfang des neiges", "2026-10-15 08:00", loc_name="Aéroport de Trois-Rivières"),
            observation("Pygargue à tête blanche", "2026-10-12", loc_name="Parc de l'Île-Saint-Quentin"),
            observation("Harfang des neiges", "2026-10-16 09:30", loc_name="Aéroport de Trois-Rivières"),
            observation("Harfang des neiges", "2026-10-11 10:00", loc_name="Parc de l'Île-Saint-Quentin"),
        ]
    )

    observations = make_query(client).observations(ObservationKind.NOTABLE, RegionalScopes.HOTSPOT, "Technoparc")

    assert client.calls == [Call("get_notable_observations", (["L3001", "L3002"],), back=7, hotspot=True)]
    assert summary(observations) == [
        ("2026-10-11", "Harfang des neiges", "Parc de l'Île-Saint-Quentin"),
        ("2026-10-12", "Pygargue à tête blanche", "Parc de l'Île-Saint-Quentin"),
        ("2026-10-15", "Harfang des neiges", "Aéroport de Trois-Rivières"),
    ]


def test_notable_nearby_requests_notable_observations_within_50_km_of_the_coordinates():
    client = FakeEbirdClient()

    make_query(client).observations(ObservationKind.NOTABLE, RegionalScopes.NEARBY, back=30)

    assert client.calls == [Call("get_nearby_notable", (LAT, LONG, 50), back=30, hotspot=True)]


def test_recent_species_in_a_region_keeps_the_latest_observation_per_location_oldest_first():
    client = FakeEbirdClient(
        get_species_observations=[
            observation("Harfang des neiges", "2026-10-15 08:00", loc_name="Aéroport de Trois-Rivières"),
            observation("Harfang des neiges", "2026-10-11", loc_name="Parc de l'Île-Saint-Quentin"),
            observation("Harfang des neiges", "2026-10-13 12:00", loc_name="Aéroport de Trois-Rivières"),
        ]
    )

    observations = make_query(client).observations(
        ObservationKind.RECENT, RegionalScopes.SUBNATIONAL, species_code="snoowl1"
    )

    assert client.calls == [Call("get_species_observations", ("snoowl1", ["CA-QC"]), back=7, hotspot=True)]
    assert summary(observations) == [
        ("2026-10-11", "Harfang des neiges", "Parc de l'Île-Saint-Quentin"),
        ("2026-10-15", "Harfang des neiges", "Aéroport de Trois-Rivières"),
    ]


def test_recent_species_nearby_requests_species_observations_around_the_coordinates():
    client = FakeEbirdClient()

    make_query(client).observations(ObservationKind.RECENT, RegionalScopes.NEARBY, species_code="mallar3")

    assert client.calls == [Call("get_nearby_species", ("mallar3", LAT, LONG, 50), back=7, hotspot=True)]


@pytest.mark.parametrize("scope", [RegionalScopes.NEARBY, RegionalScopes.REGIONAL])
def test_notable_for_a_species_is_refused_without_calling_ebird(scope):
    client = FakeEbirdClient()

    with pytest.raises(ValueError, match="notable"):
        make_query(client).observations(ObservationKind.NOTABLE, scope, species_code="snoowl1")

    assert client.calls == []
