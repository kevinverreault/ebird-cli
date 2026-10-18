import os
import sys
from datetime import datetime
from pathlib import Path

import requests


def download_csv(session, session_id, download_url, output_file):
    headers = {"User-Agent": "Mozilla/5.0"}

    response = session.get(download_url, cookies={"EBIRD_SESSIONID": session_id}, headers=headers)

    if response.status_code == 200:
        output_path = Path(output_file)

        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_bytes(response.content)
    else:
        print(f"Failed to download file. HTTP Status Code: {response.status_code}")
        print("Response:", response.text)


def main(argv=None, session=None):
    argv = sys.argv[1:] if argv is None else argv

    if len(argv) != 2:
        print("Usage: ebird-cli-download-lists <session_id> <output_dir>")
        sys.exit(1)

    session_id, output_dir = argv
    session = requests.Session() if session is None else session

    download_csv(
        session,
        session_id,
        "https://ebird.org/lifelist?r=world&time=life&fmt=csv",
        os.path.join(output_dir, "life_list.csv"),
    )
    current_year = datetime.now().year
    download_csv(
        session,
        session_id,
        f"https://ebird.org/lifelist?r=world&time=year&year={current_year}&fmt=csv",
        os.path.join(output_dir, "year_list.csv"),
    )


if __name__ == "__main__":
    main()
