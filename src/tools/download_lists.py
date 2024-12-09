import os

import requests
import sys
from pathlib import Path


def download_csv(session_id, download_url, output_file):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    session = requests.Session()

    response = session.get(download_url, cookies={'EBIRD_SESSIONID': session_id}, headers=headers)

    if response.status_code == 200:
        output_path = Path(output_file)

        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_bytes(response.content)
    else:
        print(f"Failed to download file. HTTP Status Code: {response.status_code}")
        print("Response:", response.text)


def main():
    if len(sys.argv) != 3:
        print("Usage: python download_lists.py <session_id> <output_dir>")
        sys.exit(1)

    session_id = sys.argv[1]
    output_dir = sys.argv[2]

    download_csv(session_id, 'https://ebird.org/lifelist?r=world&time=life&fmt=csv', os.path.join(output_dir, "life_list.csv"))
    download_csv(session_id, 'https://ebird.org/lifelist?r=world&time=year&year=2024&fmt=csv', os.path.join(output_dir, "year_list.csv"))


if __name__ == "__main__":
    main()
