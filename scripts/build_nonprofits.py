"""Build data/nonprofits.json: top 100 NYC nonprofits by revenue.

Source: IRS Exempt Organizations Business Master File for NY
(https://www.irs.gov/pub/irs-soi/eo_ny.csv). Pass the downloaded CSV path:

    python scripts/build_nonprofits.py /path/to/eo_ny.csv

NTEE major-group letters are mapped onto the UI interest categories in
app.INTEREST_OPTIONS; everything else keeps its NTEE group name so new
UI categories can be added without re-pulling the data.
"""

import csv
import json
import sys
from pathlib import Path

# NYC zip prefixes: Manhattan 100-102, Staten Island 103, Bronx 104,
# Queens 111/113/114/116, Brooklyn 112
NYC_ZIP_PREFIXES = ("100", "101", "102", "103", "104", "111", "112", "113", "114", "116")

# NTEE major group letter -> interest category used by the profile UI
NTEE_TO_INTEREST = {
    "B": "education",
    "C": "environment",
    "D": "animals",
}

# remaining NTEE major groups, kept for future UI categories
NTEE_GROUP_NAMES = {
    "A": "arts", "E": "health", "F": "mental-health", "G": "disease",
    "H": "medical-research", "I": "crime-legal", "J": "employment",
    "K": "food-agriculture", "L": "housing", "M": "disaster-safety",
    "N": "recreation-sports", "O": "youth-development", "P": "human-services",
    "Q": "international", "R": "civil-rights", "S": "community-improvement",
    "T": "philanthropy", "U": "science-tech", "V": "social-science",
    "W": "public-benefit", "X": "religion", "Y": "mutual-benefit",
    "Z": "unknown",
}


def category_for(ntee_cd):
    letter = ntee_cd[:1].upper()
    return NTEE_TO_INTEREST.get(letter) or NTEE_GROUP_NAMES.get(letter, "unknown")


def main(csv_path):
    orgs = []
    with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if row["STATE"] != "NY" or not row["ZIP"].startswith(NYC_ZIP_PREFIXES):
                continue
            try:
                revenue = int(float(row["REVENUE_AMT"] or 0))
            except ValueError:
                continue
            if revenue <= 0:
                continue
            orgs.append({
                "ein": row["EIN"],
                "name": row["NAME"].strip(),
                "city": row["CITY"].strip().title(),
                "revenue": revenue,
                "ntee": row["NTEE_CD"].strip(),
                "category": category_for(row["NTEE_CD"].strip()),
            })

    orgs.sort(key=lambda o: o["revenue"], reverse=True)
    top = orgs[:100]
    for rank, org in enumerate(top, start=1):
        org["rank"] = rank

    out = Path(__file__).resolve().parent.parent / "data" / "nonprofits.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(top, indent=2) + "\n")

    counts = {}
    for org in top:
        counts[org["category"]] = counts.get(org["category"], 0) + 1
    print(f"Wrote {len(top)} nonprofits to {out}")
    for cat, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {cat}: {n}")


if __name__ == "__main__":
    main(sys.argv[1])
