import json
import re

input_file = 'ca-qc_hotspots_raw.json'
output_file = 'ca-qc_hotspots.json'

with open(input_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

for obj in data:
    if "locName" in obj:
        sanitized_name = obj["locName"]
        sanitized_name = sanitized_name.split(",")[0]
        sanitized_name = re.sub(r"\([^)]*\)", "", sanitized_name)
        obj['locName'] = sanitized_name.strip()

with open(output_file, 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print(f"Modified JSON has been written to {output_file}")
