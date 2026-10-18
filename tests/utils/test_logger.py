import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ebird_cli.main import main
from ebird_cli.utils import logger as logger_module
from ebird_cli.utils.logger import configure_logging, logger


@pytest.fixture(autouse=True)
def detach_log_handlers():
    """Close the file handlers a test attached, so later tests do not write to its temporary log file."""
    yield
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    logger.setLevel(logging.NOTSET)


def test_creates_the_missing_log_directory_and_writes_debug_records_to_it(tmp_path):
    log_dir = tmp_path / "user" / "logs"

    configure_logging(str(log_dir))
    logger.debug("user input: recent")

    assert "user input: recent" in (log_dir / "app.log").read_text(encoding="utf-8")


def test_appends_to_the_log_of_previous_launches(tmp_path):
    (tmp_path / "app.log").write_text("previous launch\n", encoding="utf-8")

    configure_logging(str(tmp_path))
    logger.debug("this launch")

    lines = (tmp_path / "app.log").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "previous launch"
    assert "this launch" in lines[1]


def test_launching_logs_to_the_user_log_directory_not_the_working_directory(tmp_path, monkeypatch):
    user_logs = tmp_path / "user-logs"
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)
    monkeypatch.setattr(logger_module, "user_log_dir", lambda appname: str(user_logs / appname))
    monkeypatch.setattr(sys, "argv", ["ebird-cli", "--help"])

    with pytest.raises(SystemExit):
        main()

    assert (user_logs / "ebird_cli").is_dir()
    assert list(working_dir.iterdir()) == []


def test_importing_the_package_attaches_no_log_handler_and_writes_no_file(tmp_path):
    src = Path(__file__).parents[2] / "src"
    script = (
        "import logging, ebird_cli.main\n"
        "assert logging.getLogger().handlers == [], logging.getLogger().handlers\n"
        "assert logging.getLogger('ebird_cli_logger').handlers == []\n"
    )

    subprocess.run([sys.executable, "-c", script], cwd=tmp_path, env={**os.environ, "PYTHONPATH": str(src)}, check=True)

    assert list(tmp_path.iterdir()) == []
