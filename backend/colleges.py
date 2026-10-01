"""Public college reference registry, not tenant-owned records or enrollment proof."""
import json
from pathlib import Path
DIRECTORY=json.loads((Path(__file__).parent / "data/colleges/bput.json").read_text(encoding="utf-8"))
COLLEGES={row["id"]:row for row in DIRECTORY["colleges"]}
def valid_college(value):
    return type(value) is int and value in COLLEGES
def college_name(value):
    return COLLEGES[value]["name"]
