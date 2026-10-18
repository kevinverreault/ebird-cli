import pytest
from fakes import ENTER, ScriptedAsk

from ebird_cli import main as main_module
from ebird_cli.main import main
from ebird_cli.settings import SETTINGS, SettingsFile

ANSWERS = ["typed-key", "CA-QC-MR", "en", "46.35", "-72.55", "year.csv", "life.csv", "aggregations.json"]


class ContactedEbird(Exception):
    """Raised by the stub eBird client, so a launch stops where it would first contact eBird."""


@pytest.fixture
def ebird(monkeypatch):
    """Stub out every launch step past the settings: record the eBird client's settings, then stop the launch."""
    clients = []

    def client(api_key, locale):
        clients.append((api_key, locale))
        raise ContactedEbird

    def forbidden(*_args, **_kwargs):
        raise AssertionError("the launch went past creating the eBird client")

    for setting in SETTINGS:
        monkeypatch.delenv(setting.env_variable, raising=False)
    monkeypatch.setattr(main_module, "configure_logging", lambda: None)
    monkeypatch.setattr(main_module, "use_certifi_ca_bundle", lambda: None)
    monkeypatch.setattr(main_module, "EbirdClient", client)
    monkeypatch.setattr(main_module, "CacheService", forbidden)
    monkeypatch.setattr(main_module, "LocationCatalogue", forbidden)
    return clients


@pytest.fixture
def settings_file(tmp_path) -> SettingsFile:
    return SettingsFile(tmp_path / "config" / "settings.json")


def test_first_launch_runs_setup_and_saves_the_answers_before_contacting_ebird(ebird, settings_file):
    with pytest.raises(ContactedEbird):
        main([], ask=ScriptedAsk(*ANSWERS), settings_file=settings_file)

    assert settings_file.load() == dict(zip([setting.name for setting in SETTINGS], ANSWERS, strict=True))
    assert ebird == [("typed-key", "en")]


def test_first_launch_setup_is_pre_filled_from_flags_and_environment_variables(ebird, settings_file, monkeypatch):
    monkeypatch.setenv("EBIRDDEFAULTREGION", "CA-QC-MO")
    monkeypatch.setenv("EBIRDLAT", "45.50")
    ask = ScriptedAsk(*[ENTER] * len(SETTINGS))

    with pytest.raises(ContactedEbird):
        main(["--api-key", "flag-key", "--lat", "46.35"], ask=ask, settings_file=settings_file)

    assert [default for _label, default in ask.questions] == ["flag-key", "CA-QC-MO", "", "46.35", "", "", "", ""]
    assert settings_file.load() == {"api_key": "flag-key", "region": "CA-QC-MO", "lat": "46.35"}


def test_launches_with_saved_settings_skip_setup_and_need_no_api_key_or_region_flags(ebird, settings_file):
    settings_file.save({"api_key": "saved-key", "region": "CA-QC-MR", "locale": "es"})

    with pytest.raises(ContactedEbird):
        main([], ask=ScriptedAsk(), settings_file=settings_file)

    assert ebird == [("saved-key", "es")]


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt, EOFError])
def test_interrupting_setup_saves_nothing_exits_cleanly_and_shows_setup_on_the_next_launch(
    ebird, settings_file, capsys, interrupt
):
    main([], ask=ScriptedAsk("typed-key", interrupt), settings_file=settings_file)

    assert settings_file.load() is None
    assert ebird == []
    assert "nothing was saved" in capsys.readouterr().out

    next_launch = ScriptedAsk(*ANSWERS)
    with pytest.raises(ContactedEbird):
        main([], ask=next_launch, settings_file=settings_file)
    assert len(next_launch.questions) == len(SETTINGS)
