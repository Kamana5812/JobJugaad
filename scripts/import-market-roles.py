"""Curate an attributed historical reference catalogue; no tenant records or scores."""
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

csv.field_size_limit(2_000_000)

SOURCE = "https://www.kaggle.com/datasets/arshkon/linkedin-job-postings"
GROUPS = {
    "Software": r"software|developer|programmer|web engineer",
    "Data": r"data analyst|data engineer|data scien|business analyst",
    "Mechanical": r"mechanical|manufacturing engineer|industrial engineer",
    "Electrical": r"electrical|electronics|embedded|controls engineer",
    "Civil": r"civil engineer|structural engineer|construction engineer",
    "IT & networks": r"network engineer|systems engineer|it support|cybersecurity|security analyst",
}
KEYWORDS = ["Python", "Java", "JavaScript", "TypeScript", "SQL", "React", "AWS", "Azure", "Linux", "Excel", "AutoCAD", "MATLAB", "SolidWorks", "C++", "CAD", "PLC", "TCP/IP", "Git", "Power BI", "Tableau"]

def curate(archive):
    roles, counts, seen = [], Counter(), set()
    with zipfile.ZipFile(archive) as z:
        with z.open("postings.csv") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        with z.open("postings.csv") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", newline=""))
            for row in reader:
                title = row.get("title", "").strip()
                experience = row.get("formatted_experience_level", "").strip()
                if experience not in {"Entry level", "Internship"}: continue
                if "*" in title or re.search(r"\b(senior|sr|manager|director|lead|principal|chief)\b", title, re.I): continue
                group = next((g for g, pattern in GROUPS.items() if re.search(pattern, title, re.I)), None)
                if not group or counts[group] >= 6: continue
                description = row.get("description", "").strip()
                location = row.get("location", "").strip()
                url = row.get("job_posting_url", "").strip()
                parsed = urlparse(url)
                if parsed.scheme != "https" or parsed.hostname not in {"www.linkedin.com", "linkedin.com"} or not parsed.path.startswith("/jobs/view/"): continue
                if not description or not location: continue
                key = (title.casefold(), row.get("company_name", "").casefold(), location.casefold())
                if key in seen: continue
                try:
                    listed = datetime.fromtimestamp(float(row["original_listed_time"]) / 1000, timezone.utc).date().isoformat()
                except (ValueError, KeyError, OverflowError): continue
                if not listed.startswith(("2023-", "2024-")): continue
                tags = [tag for tag in KEYWORDS if re.search(r"(?<![\w])" + re.escape(tag) + r"(?![\w])", description, re.I)]
                seen.add(key); counts[group] += 1
                roles.append({"id": row["job_id"], "title": title, "company": row.get("company_name", "").strip(), "location": location,
                    "experience": experience, "work_type": row.get("formatted_work_type", "").strip(), "listed_date": listed,
                    "original_url": url, "description": description[:5000], "description_truncated": len(description) > 5000,
                    "keyword_tags": tags, "category": group})
    if len(roles) < 12: raise RuntimeError("Too few qualifying source records; review the archive schema.")
    return {"source_url": SOURCE, "source_version": 13, "source_file": "postings.csv", "source_sha256": digest,
        "license": "CC BY-SA 4.0", "historical": True, "selection": "First six qualifying unique rows per title category in source order; entry-level or internship labels only; obvious senior/manager and masked titles excluded. Not representative.",
        "roles": sorted(roles, key=lambda r: (r["category"], r["title"], r["id"]))}

if __name__ == "__main__":
    result = curate(Path(sys.argv[1]))
    dest = Path("frontend/src/assets/market/roles.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(result["roles"]), "categories": dict(Counter(r["category"] for r in result["roles"])), "source_sha256": result["source_sha256"]}))
