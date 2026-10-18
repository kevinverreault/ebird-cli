import argparse

import pytest
from conftest import strip_ansi, table_rows
from fakes import ENTER, FakeEbirdClient, ScriptedAsk, observation

from ebird_cli.cli.grammar import CommandLineError
from ebird_cli.main import handle_input

PROGRAM_ARGS = argparse.Namespace(region="CA-QC-MR", locale="fr")


@pytest.mark.parametrize("line", ["exit", "e", "EXIT", "E", "Exit"])
def test_exit_ends_the_session(cli, capsys, line):
    assert handle_input(line, cli.commands, PROGRAM_ARGS) is False
    assert capsys.readouterr().out == "Exiting eBird CLI.\n"


def test_empty_input_reprints_the_menu_and_continues(cli, capsys):
    assert handle_input("", cli.commands, PROGRAM_ARGS) is True

    menu = strip_ansi(capsys.readouterr().out)
    assert "eBird CLI" in menu
    assert "region: CA-QC-MR" in menu
    assert "locale: fr" in menu
    assert "Available commands:" in menu


def test_menu_lists_each_commands_mandatory_and_optional_parameters(cli, capsys):
    handle_input("", cli.commands, PROGRAM_ARGS)

    lines = [" ".join(line.split()) for line in strip_ansi(capsys.readouterr().out).splitlines()]
    assert "recent <scope> [-region, -species, -back]" in lines
    assert "notable <scope> [-region, -back]" in lines
    assert "settings" in lines


def test_menu_is_reprinted_after_running_a_command_now_that_program_args_are_kept(cli, capsys):
    # Fixed while extracting handle_input: the old loop overwrote the program args with the typed words,
    # so the menu failed with "An error occurred: 'list' object has no attribute 'region'".
    handle_input("recent nearby", cli.commands, PROGRAM_ARGS)
    capsys.readouterr()

    handle_input("", cli.commands, PROGRAM_ARGS)

    assert "region: CA-QC-MR" in strip_ansi(capsys.readouterr().out)


def test_whitespace_only_input_prints_nothing_and_continues(cli, capsys):
    assert handle_input("   ", cli.commands, PROGRAM_ARGS) is True
    assert capsys.readouterr().out == ""


def test_unknown_command_is_reported(cli, capsys):
    assert handle_input("rare nearby", cli.commands, PROGRAM_ARGS) is True
    assert capsys.readouterr().out == "Unknown command.\n"


def test_known_command_is_dispatched_with_its_arguments(make_cli, capsys):
    cli = make_cli(FakeEbirdClient(get_nearby_observations=[observation("Geai bleu", "2026-10-14 08:15")]))

    assert handle_input("recent nearby -back 3", cli.commands, PROGRAM_ARGS) is True

    assert cli.client.calls[0].back == "3"
    assert table_rows(capsys.readouterr().out) == [["2026-10-14", "Geai bleu", "Parc de l'Île-Saint-Quentin"]]


def test_command_error_is_reported_without_ending_the_session(make_cli, capsys):
    cli = make_cli(lat=None, long=None)

    assert handle_input("recent nearby", cli.commands, PROGRAM_ARGS) is True
    assert capsys.readouterr().out == (
        "An error occurred: nearby needs coordinates: set --lat and --long, or save them with settings\n"
    )


def test_invalid_scope_is_reported_as_invalid_argument(cli, capsys):
    assert handle_input("recent everywhere", cli.commands, PROGRAM_ARGS) is True
    assert capsys.readouterr().out == (
        "Invalid argument: argument scope: invalid choice: 'everywhere' "
        "(choose from 'hotspot', 'nearby', 'regional', 'subnational')\n"
    )
    assert cli.client.calls == []


def test_missing_scope_is_reported_as_invalid_argument(cli, capsys):
    assert handle_input("recent -back 3", cli.commands, PROGRAM_ARGS) is True
    assert capsys.readouterr().out == "Invalid argument: the following arguments are required: scope\n"
    assert cli.client.calls == []


def test_command_line_error_is_reported_as_invalid_argument(capsys):
    class RejectingCommand:
        def handle_command(self, *_args):
            raise CommandLineError("bad value")

    assert handle_input("reject now", {"reject": RejectingCommand()}, PROGRAM_ARGS) is True
    assert capsys.readouterr().out == "Invalid argument: bad value\n"


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("recent regional -back", "argument -back: expected one argument"),
        ("recent regional -back 3 4", "unrecognized arguments: 4"),
        ("recent regional -back 99", "argument -back: invalid choice: '99' (choose from 1 to 30)"),
        ("recent regional -h", "unrecognized arguments: -h"),
    ],
)
def test_flag_errors_are_reported_as_invalid_argument(cli, capsys, line, message):
    assert handle_input(line, cli.commands, PROGRAM_ARGS) is True
    assert capsys.readouterr().out == f"Invalid argument: {message}\n"
    assert cli.client.calls == []


def test_a_flag_can_be_abbreviated(cli):
    handle_input("recent regional -b 3 -reg Côte-Nord", cli.commands, PROGRAM_ARGS)

    assert [(call.args, call.back) for call in cli.client.calls] == [((["CA-QC-CN"],), "3")]


NEW_ANSWERS = ["new-key", "CA-QC-CN", "", "", "", "", "", ""]


def test_settings_reconfigures_and_says_the_changes_apply_on_the_next_launch(make_cli, capsys):
    cli = make_cli(ask=ScriptedAsk(*NEW_ANSWERS))
    cli.settings_file.save({"api_key": "saved-key", "region": "CA-QC-MR"})

    assert handle_input("settings", cli.commands, PROGRAM_ARGS) is True

    assert cli.settings_file.load() == {"api_key": "new-key", "region": "CA-QC-CN"}
    assert cli.ask.questions[0] == ("eBird API key (required): ", "saved-key")
    assert capsys.readouterr().out.splitlines()[-2:] == [
        f"Settings saved to {cli.settings_file.path}.",
        "Changes apply on the next launch.",
    ]
    assert cli.client.calls == []


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt, EOFError])
def test_interrupting_settings_returns_to_the_prompt_with_the_saved_settings_untouched(make_cli, capsys, interrupt):
    cli = make_cli(ask=ScriptedAsk(ENTER, interrupt))
    cli.settings_file.save({"api_key": "saved-key", "region": "CA-QC-MR"})

    assert handle_input("settings", cli.commands, PROGRAM_ARGS) is True

    assert cli.settings_file.load() == {"api_key": "saved-key", "region": "CA-QC-MR"}
    assert capsys.readouterr().out == "Settings unchanged.\n"


def test_settings_takes_no_arguments(cli, capsys):
    assert handle_input("settings now", cli.commands, PROGRAM_ARGS) is True
    assert capsys.readouterr().out == "Invalid argument: unrecognized arguments: now\n"
