import argparse

import pytest
from conftest import FIXTURES, highlight_of, strip_ansi, table_rows
from fakes import FakeEbirdClient, observation
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from ebird_cli.main import handle_input, setup_key_bindings

PROGRAM_ARGS = argparse.Namespace(region="CA-QC-MR", locale="fr")

OBSERVATIONS = [
    observation("Canard colvert", "2026-10-12 07:00", loc_name="Étang Hertel"),
    observation("Geai bleu", "2026-10-13 08:00", loc_name="Parc Jarry"),
    observation("Grand Héron", "2026-10-14 09:00", loc_name="Marais de la Rivière-aux-Cerises"),
    observation("Bécasseau semipalmé", "2026-10-15 10:00", loc_name="Parc Jarry"),
]


def found(make_cli, capsys, text, observations=OBSERVATIONS):
    """The output of finding text in the Last result of a recent query of observations."""
    cli = make_cli(FakeEbirdClient(get_observations=observations))
    cli.run("recent regional")
    capsys.readouterr()
    cli.run(f"find {text}")
    return capsys.readouterr().out


def test_find_prints_only_the_matching_observations_out_of_the_last_result(make_cli, capsys):
    output = found(make_cli, capsys, "Geai")

    assert table_rows(output) == [["2026-10-13", "Geai bleu", "Parc Jarry"]]
    assert strip_ansi(output).rstrip().endswith("Total: 1 of 4")


@pytest.mark.parametrize(
    ("text", "name"),
    [("geai", "Geai bleu"), ("BLEU", "Geai bleu"), ("becasseau", "Bécasseau semipalmé"), ("HERON", "Grand Héron")],
)
def test_find_ignores_case_and_accents(make_cli, capsys, text, name):
    assert [row[1] for row in table_rows(found(make_cli, capsys, text))] == [name]


def test_find_matches_the_location(make_cli, capsys):
    assert [row[1] for row in table_rows(found(make_cli, capsys, "jarry"))] == ["Geai bleu", "Bécasseau semipalmé"]


def test_find_matches_the_region(make_cli, capsys):
    observations = [
        observation("Canard colvert", "2026-10-12", subnational2_name="Montréal"),
        observation("Geai bleu", "2026-10-13", subnational2_name="Laval"),
    ]

    assert table_rows(found(make_cli, capsys, "laval", observations)) == [
        ["2026-10-13", "Geai bleu", "Parc de l'Île-Saint-Quentin", "Laval"]
    ]


@pytest.mark.parametrize(
    ("list_option", "text", "name", "colour"),
    [("life_list", "heron", "Grand Héron", "red"), ("year_list", "bleu", "Geai bleu", "green")],
)
def test_find_shows_matches_in_their_life_and_year_target_colours(make_cli, capsys, list_option, text, name, colour):
    cli = make_cli(
        FakeEbirdClient(get_observations=OBSERVATIONS), **{list_option: str(FIXTURES / f"{list_option}.csv")}
    )
    cli.run("recent regional")
    capsys.readouterr()

    cli.run(f"find {text}")

    assert highlight_of(name, capsys.readouterr().out) == colour


def test_find_says_so_when_nothing_matches(make_cli, capsys):
    assert found(make_cli, capsys, "harfang") == 'No observations match "harfang".\n'


def test_find_does_not_search_the_date(make_cli, capsys):
    assert found(make_cli, capsys, "2026-10-13") == 'No observations match "2026-10-13".\n'


@pytest.mark.parametrize("observations", [OBSERVATIONS, []], ids=["observations", "none"])
def test_find_without_text_reprints_the_last_result_as_it_was_shown(make_cli, capsys, observations):
    cli = make_cli(FakeEbirdClient(get_observations=observations))
    cli.run("recent regional")
    shown = capsys.readouterr().out

    cli.run("find")

    assert capsys.readouterr().out == shown


def test_find_matches_several_words_as_one_phrase(make_cli, capsys):
    observations = [
        observation("Grand Héron", "2026-10-12", loc_name="Parc Jarry"),
        observation("Grand Pic", "2026-10-13", loc_name="Marais du héron"),
    ]

    assert [row[1] for row in table_rows(found(make_cli, capsys, "grand heron", observations))] == ["Grand Héron"]


def test_each_find_searches_the_whole_last_result_not_the_previous_matches(make_cli, capsys):
    cli = make_cli(FakeEbirdClient(get_observations=OBSERVATIONS))
    cli.run("recent regional")
    cli.run("find geai")
    capsys.readouterr()

    cli.run("find jarry")

    assert [row[1] for row in table_rows(capsys.readouterr().out)] == ["Geai bleu", "Bécasseau semipalmé"]


def test_a_query_that_shows_no_observations_becomes_the_last_result(make_cli, capsys):
    cli = make_cli(FakeEbirdClient(get_observations=OBSERVATIONS, get_notable_observations=[]))
    cli.run("recent regional")
    cli.run("notable regional")
    capsys.readouterr()

    cli.run("find geai")

    assert capsys.readouterr().out == 'No observations match "geai".\n'


@pytest.mark.parametrize("failing", ["recent everywhere", "recent nearby", "settings now"])
def test_a_command_that_fails_keeps_the_last_result(make_cli, capsys, failing):
    cli = make_cli(FakeEbirdClient(get_observations=OBSERVATIONS), lat=None, long=None)
    handle_input("recent regional", cli.commands, PROGRAM_ARGS)
    handle_input(failing, cli.commands, PROGRAM_ARGS)
    capsys.readouterr()

    handle_input("find geai", cli.commands, PROGRAM_ARGS)

    assert table_rows(capsys.readouterr().out) == [["2026-10-13", "Geai bleu", "Parc Jarry"]]


def recent_cli(make_cli):
    cli = make_cli(FakeEbirdClient(get_observations=OBSERVATIONS))
    cli.run("recent regional")
    return cli


def test_find_offers_the_species_then_the_location_names_of_the_last_result_once_each(make_cli):
    assert recent_cli(make_cli).completions("find ") == [
        "Canard colvert",
        "Geai bleu",
        "Grand Héron",
        "Bécasseau semipalmé",
        "Étang Hertel",
        "Parc Jarry",
        "Marais de la Rivière-aux-Cerises",
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("find par", ["Parc Jarry"]),
        ("find BEC", ["Bécasseau semipalmé"]),
        ("find riviere", ["Marais de la Rivière-aux-Cerises"]),
    ],
)
def test_find_offers_the_names_containing_what_was_typed_ignoring_case_and_accents(make_cli, text, expected):
    assert recent_cli(make_cli).completions(text) == expected


@pytest.mark.parametrize("typed", ["grand h", "grand  h"])
def test_find_completion_replaces_every_word_typed_after_find(make_cli, typed):
    text = f"find {typed}"

    completions = list(recent_cli(make_cli).completer.get_completions(Document(text, len(text)), CompleteEvent()))

    assert [(completion.text, completion.start_position) for completion in completions] == [
        ("Grand Héron", -len(typed))
    ]


def test_find_offers_nothing_before_any_recent_or_notable_query(cli):
    assert cli.completions("find ") == []


CTRL_F = "\x06"


def typed_line(cli, keys: str) -> str:
    """The line a prompt session set up like main's returns after these keystrokes."""
    with create_pipe_input() as pipe:
        pipe.send_text(keys)
        session = PromptSession(
            input=pipe, output=DummyOutput(), completer=cli.completer, key_bindings=setup_key_bindings()
        )
        return session.prompt()


def test_ctrl_f_starts_a_find(make_cli):
    assert typed_line(recent_cli(make_cli), f"{CTRL_F}geai\r") == "find geai"


def test_ctrl_f_replaces_what_was_typed_with_a_find(make_cli):
    assert typed_line(recent_cli(make_cli), f"recent reg{CTRL_F}jarry\r") == "find jarry"


def test_find_before_any_recent_or_notable_query_says_there_is_nothing_to_search(cli, capsys):
    cli.run("find geai")

    assert capsys.readouterr().out == "No observations to search yet; run recent or notable first.\n"
