"""Import public institutional facts; preserve source codes and snapshot year."""
import csv, hashlib, json, sys
from pathlib import Path
raw=Path(sys.argv[1]).read_bytes()
rows=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
colleges=[]
for row in rows:
    code=row["COL_CODE"].strip()
    if not code.isdigit(): continue
    colleges.append(dict(id=10000+int(code),code=code,name=row["NAME OF THE COLLEGE"].strip(),
        district=row["DISTRICT"].strip(),courses=row["COURSES OFFERED"].strip().split("\\"),category=row["TYPE"].strip(),kind="bput_directory"))
assert len(colleges)>50 and len({c["id"] for c in colleges})==len(colleges)
result=dict(source_url="https://docs.google.com/spreadsheets/d/10dYEIBxKmSYQFH5GspqzsVCylfChE6er/edit",
    university_url="https://www.bput.ac.in/index1.php",source_year="2022–23",source_sha256=hashlib.sha256(raw).hexdigest(),
    note="Official BPUT directory snapshot, 2022–23. Current affiliation and account-holder enrollment are not verified. Listing does not imply partnership.",
    colleges=[dict(id=1,name="Demo College 1",code=None,district="Demo",courses=[],category="Demo",kind="demo"),dict(id=2,name="Demo College 2",code=None,district="Demo",courses=[],category="Demo",kind="demo")]+sorted(colleges,key=lambda c:c["name"].casefold()))
for dest in ["backend/data/colleges/bput.json","frontend/src/assets/bput-colleges.json"]:
 p=Path(dest);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Imported",len(colleges),"BPUT directory records; demo IDs preserved.")
