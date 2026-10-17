import argparse

import pytest
from conftest import strip_ansi, table_rows
from fakes import FakeEbirdClient, observation

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
        "An error occurred: nearby needs coordinates: set --lat and --long, or EBIRDLAT and EBIRDLONG\n"
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


def test_argument_error_is_reported_as_invalid_argument(capsys):
    class RejectingCommand:
        def handle_command(self, *_args):
            raise argparse.ArgumentError(None, "bad value")

    assert handle_input("reject now", {"reject": RejectingCommand()}, PROGRAM_ARGS) is True
    assert capsys.readouterr().out == "Invalid argument: bad value\n"
