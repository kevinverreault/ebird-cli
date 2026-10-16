from datetime import datetime

from fakes import observation

from ebird_cli.domain import Observation


def test_parses_date_time_observation_date():
    obs = Observation(observation("Geai bleu", "2026-10-14 08:15"))

    assert obs.observation_date == "2026-10-14"
    assert obs.observation_datetime == datetime(2026, 10, 14, 8, 15)


def test_parses_date_only_observation_date():
    obs = Observation(observation("Geai bleu", "2026-10-14"))

    assert obs.observation_date == "2026-10-14"
    assert obs.observation_datetime == datetime(2026, 10, 14)


def test_strips_parenthesised_text_from_common_name():
    assert Observation(observation("Canard colvert (Domestique)", "2026-10-14")).name == "Canard colvert"


def test_cuts_location_name_at_the_first_comma():
    obs = Observation(observation("Geai bleu", "2026-10-14", loc_name="Étang Hertel, Montréal, QC"))

    assert obs.location == "Étang Hertel"


def test_strips_parenthesised_text_from_location_but_currently_keeps_the_space_before_it():
    obs = Observation(observation("Geai bleu", "2026-10-14", loc_name="Parc de la Gorge (secteur nord), Coaticook"))

    assert obs.location == "Parc de la Gorge "


def test_truncates_location_name_to_55_characters():
    long_name = "Réserve nationale de faune du Lac-Saint-François--sentier de la digue"

    obs = Observation(observation("Geai bleu", "2026-10-14", loc_name=long_name))

    assert obs.location == "Réserve nationale de faune du Lac-Saint-François--senti"
    assert len(obs.location) == 55


def test_reads_subnational_level_2_name_when_present():
    assert Observation(observation("Geai bleu", "2026-10-14", subnational2_name="Mauricie")).subname == "Mauricie"
    assert Observation(observation("Geai bleu", "2026-10-14")).subname == ""
