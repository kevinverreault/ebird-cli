from datetime import date

import pytest
from fakes import FakeHttpSession, FakeResponse

from ebird_cli.download_lists import main

LIFE_LIST_URL = "https://ebird.org/lifelist?r=world&time=life&fmt=csv"
YEAR_LIST_URL = f"https://ebird.org/lifelist?r=world&time=year&year={date.today().year}&fmt=csv"


@pytest.mark.parametrize("argv", [[], ["session-id"], ["session-id", "lists", "extra"]])
def test_wrong_argument_count_prints_usage_naming_the_command(argv, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(argv)

    assert exit_info.value.code == 1
    assert capsys.readouterr().out == "Usage: ebird-cli-download-lists <session_id> <output_dir>\n"


def test_writes_the_life_list_and_the_current_year_list_into_a_new_output_dir(tmp_path):
    http_session = FakeHttpSession(
        {
            LIFE_LIST_URL: FakeResponse(200, b"life rows"),
            YEAR_LIST_URL: FakeResponse(200, b"year rows"),
        }
    )
    output_dir = tmp_path / "ebird_data"

    main(["session-id", str(output_dir)], http_session)

    assert (output_dir / "life_list.csv").read_bytes() == b"life rows"
    assert (output_dir / "year_list.csv").read_bytes() == b"year rows"
    assert [cookies for _url, cookies in http_session.requests] == [{"EBIRD_SESSIONID": "session-id"}] * 2


def test_a_refused_download_reports_the_status_and_writes_no_file(tmp_path, capsys):
    http_session = FakeHttpSession(
        {
            LIFE_LIST_URL: FakeResponse(403, text="Forbidden"),
            YEAR_LIST_URL: FakeResponse(200, b"year rows"),
        }
    )

    main(["expired-session", str(tmp_path)], http_session)

    assert "Failed to download file. HTTP Status Code: 403\nResponse: Forbidden\n" in capsys.readouterr().out
    assert [path.name for path in tmp_path.iterdir()] == ["year_list.csv"]
