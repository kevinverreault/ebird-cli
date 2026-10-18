import logging
import os

from appdirs import user_log_dir

logger = logging.getLogger("ebird_cli_logger")


def configure_logging(log_dir: str | None = None):
    """Append the app log to app.log in log_dir, the user log directory by default. Called at launch, not import."""
    log_dir = log_dir or user_log_dir("ebird_cli")
    os.makedirs(log_dir, exist_ok=True)

    handler = logging.FileHandler(os.path.join(log_dir, "app.log"), mode="a", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
