import json

import pytest
from fakes import ENTER, ScriptedAsk

from ebird_cli import settings as settings_module
from ebird_cli.settings import SettingsError, SettingsFile, run_setup

LABELS = [
    "eBird API key",
    "Home Region",
    "Locale",
    "Latitude",
    "Longitude",
    "Year list path",
    "Life list path",
    "Aggregations path",
]

EVERY_SETTING = {
    "api_key": "typed-key",
    "region": "CA-QC-MR",
    "locale": "en",
    "lat": "46.35",
    "long": "-72.55",
    "year_list": "year.csv",
    "life_list": "life.csv",
    "aggregations": "aggregations.json",
}


def asked_labels(ask: ScriptedAsk) -> list[str]:
    """The setting each question named, without its hint."""
    return [label.split(" (")[0] for label, _default in ask.questions]


def test_setup_asks_for_every_setting_in_order_and_returns_the_answers():
    ask = ScriptedAsk(*EVERY_SETTING.values())

    assert run_setup({}, ask) == EVERY_SETTING
    assert asked_labels(ask) == LABELS


def test_setup_pre_fills_each_answer_so_enter_keeps_it():
    ask = ScriptedAsk(*[ENTER] * len(EVERY_SETTING))

    assert run_setup(EVERY_SETTING, ask) == EVERY_SETTING
    assert [default for _label, default in ask.questions] == list(EVERY_SETTING.values())


def test_settings_left_empty_are_not_answered():
    ask = ScriptedAsk("typed-key", "CA-QC-MR", *[ENTER] * 6)

    assert run_setup({}, ask) == {"api_key": "typed-key", "region": "CA-QC-MR"}


def test_setup_re_asks_for_the_api_key_until_one_is_given(capsys):
    ask = ScriptedAsk("", "  ", "typed-key", "CA-QC-MR", *[ENTER] * 6)

    assert run_setup({}, ask)["api_key"] == "typed-key"
    assert asked_labels(ask)[:4] == ["eBird API key", "eBird API key", "eBird API key", "Home Region"]
    assert capsys.readouterr().out.count("eBird API key is required.") == 2


@pytest.mark.parametrize("region", ["", "CA-QC", "ca-qc-mr", "QC-MR", "CA-QC-MONT", "CA-QC-MR-X"])
def test_setup_re_asks_for_the_home_region_until_it_is_a_subnational_level_2_code(capsys, region):
    ask = ScriptedAsk("typed-key", region, "CA-QC-MR", *[ENTER] * 6)

    assert run_setup({}, ask)["region"] == "CA-QC-MR"
    assert asked_labels(ask)[1:3] == ["Home Region", "Home Region"]
    assert "Home Region" in capsys.readouterr().out


def test_setup_accepts_a_home_region_whose_last_part_is_a_number():
    ask = ScriptedAsk("typed-key", "US-NY-061", *[ENTER] * 6)

    assert run_setup({}, ask)["region"] == "US-NY-061"
    assert asked_labels(ask).count("Home Region") == 1


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt, EOFError])
def test_interrupting_setup_raises_it_to_the_caller(interrupt):
    with pytest.raises(interrupt):
        run_setup({}, ScriptedAsk("typed-key", interrupt))


def test_settings_file_loads_nothing_before_it_is_saved(tmp_path):
    assert SettingsFile(tmp_path / "settings.json").load() is None


def test_saved_settings_load_back_from_a_new_directory(tmp_path):
    path = tmp_path / "config" / "ebird_cli" / "settings.json"

    SettingsFile(path).save(EVERY_SETTING)

    assert SettingsFile(path).load() == EVERY_SETTING
    assert json.loads(path.read_text(encoding="utf-8")) == EVERY_SETTING


def test_saving_overwrites_the_previous_settings(tmp_path):
    settings_file = SettingsFile(tmp_path / "settings.json")
    settings_file.save(EVERY_SETTING)

    settings_file.save({"api_key": "new-key", "region": "CA-QC-CN"})

    assert settings_file.load() == {"api_key": "new-key", "region": "CA-QC-CN"}


def test_settings_file_lives_in_the_user_config_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "user_config_dir", lambda appname: str(tmp_path / "config" / appname))

    assert SettingsFile().path == tmp_path / "config" / "ebird_cli" / "settings.json"


@pytest.mark.parametrize(
    "saved_text",
    ["not json", '["typed-key"]', '{"api_key": "typed-key", "lat": 46.35}'],
    ids=["invalid json", "not an object", "not a text value"],
)
def test_unreadable_saved_settings_are_reported_as_a_settings_error(tmp_path, saved_text):
    path = tmp_path / "settings.json"
    path.write_text(saved_text, encoding="utf-8")

    with pytest.raises(SettingsError, match="settings.json"):
        SettingsFile(path).load()
