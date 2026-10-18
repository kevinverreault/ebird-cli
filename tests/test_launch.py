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


SAVED = {"api_key": "saved-key", "region": "CA-QC-MR", "locale": "es", "lat": "48.13"}
NEW_ANSWERS = ["new-key", "CA-QC-CN", "", "", "", "", "", ""]


def test_settings_reruns_setup_pre_filled_with_the_saved_settings_and_overwrites_them(ebird, settings_file):
    settings_file.save(SAVED)
    ask = ScriptedAsk(*NEW_ANSWERS)

    main(["settings"], ask=ask, settings_file=settings_file)

    assert [default for _label, default in ask.questions] == ["saved-key", "CA-QC-MR", "es", "48.13", "", "", "", ""]
    assert settings_file.load() == {"api_key": "new-key", "region": "CA-QC-CN"}


def test_settings_is_pre_filled_from_saved_settings_not_flags_or_environment_variables(
    ebird, settings_file, monkeypatch
):
    settings_file.save(SAVED)
    monkeypatch.setenv("EBIRDLAT", "45.50")
    ask = ScriptedAsk(*[ENTER] * len(SETTINGS))

    main(["--locale", "en", "settings"], ask=ask, settings_file=settings_file)

    assert settings_file.load() == SAVED


def test_settings_starts_empty_without_saved_settings_and_checks_answers_like_setup(ebird, settings_file, capsys):
    ask = ScriptedAsk("", "new-key", "CA-QC", "CA-QC-CN", *[ENTER] * 6)

    main(["settings"], ask=ask, settings_file=settings_file)

    assert all(default == "" for _label, default in ask.questions)
    assert "eBird API key is required." in capsys.readouterr().out
    assert settings_file.load() == {"api_key": "new-key", "region": "CA-QC-CN"}


@pytest.mark.parametrize(
    "saved_text",
    ['{"api_key": "revoked-key", "region": "nonsense"}', "not json"],
    ids=["invalid region", "invalid file"],
)
def test_settings_works_with_invalid_saved_settings_without_contacting_ebird(ebird, settings_file, saved_text):
    settings_file.path.parent.mkdir(parents=True)
    settings_file.path.write_text(saved_text, encoding="utf-8")

    main(["settings"], ask=ScriptedAsk(*NEW_ANSWERS), settings_file=settings_file)

    assert ebird == []
    assert settings_file.load() == {"api_key": "new-key", "region": "CA-QC-CN"}


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt, EOFError])
def test_interrupting_settings_leaves_the_saved_settings_untouched(ebird, settings_file, capsys, interrupt):
    settings_file.save(SAVED)

    main(["settings"], ask=ScriptedAsk("new-key", interrupt), settings_file=settings_file)

    assert settings_file.load() == SAVED
    assert "Settings unchanged." in capsys.readouterr().out


def test_settings_names_each_saved_setting_an_environment_variable_overrides(ebird, settings_file, capsys, monkeypatch):
    monkeypatch.setenv("EBIRDAPIKEY", "env-key")
    monkeypatch.setenv("EBIRDLOCALE", "en")
    monkeypatch.setenv("EBIRDLONG", "-73.57")

    main(["settings"], ask=ScriptedAsk("new-key", "CA-QC-CN", "es", *[ENTER] * 5), settings_file=settings_file)

    lines = capsys.readouterr().out.splitlines()
    assert lines[-3:] == [
        f"Settings saved to {settings_file.path}.",
        "EBIRDAPIKEY is set, so it overrides the saved eBird API key.",
        "EBIRDLOCALE is set, so it overrides the saved Locale.",
    ]


def test_the_next_launch_after_settings_uses_the_new_values(ebird, settings_file):
    settings_file.save(SAVED)
    main(["settings"], ask=ScriptedAsk(*NEW_ANSWERS), settings_file=settings_file)

    with pytest.raises(ContactedEbird):
        main([], ask=ScriptedAsk(), settings_file=settings_file)

    assert ebird == [("new-key", "fr")]


def test_help_lists_the_settings_subcommand(ebird, settings_file, capsys):
    with pytest.raises(SystemExit):
        main(["--help"], ask=ScriptedAsk(), settings_file=settings_file)

    help_text = capsys.readouterr().out
    assert "{settings}" in help_text
    assert any(line.split()[:1] == ["settings"] for line in help_text.splitlines())
