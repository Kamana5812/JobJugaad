# Historical market reference catalogue

Source: [LinkedIn Job Postings (2023–2024)](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings), Arsh Koneru, version 13 (published 2024-08-19). The publisher credits Zoey Yuzou for additional scraping. Source collection claims are publisher-reported, not independently verified. Kaggle metadata retrieved 2026-10-02 lists **CC BY-SA 4.0**.

The adapted `roles.json` is distributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Retain attribution, this notice, and the same license for adaptations of this catalogue. This notice applies to the data catalogue, not as a blanket license for application code. No endorsement is implied.

Reproduce with `backend/venv/Scripts/python.exe scripts/import-market-roles.py <downloaded-version-13-archive>`. The archive is not committed. Source filename and SHA-256 of the uncompressed CSV are recorded in roles.json.

Selection: the first six unique title/company/location records per fixed engineering/technology title category, with a recorded Entry level or Internship experience label, nonempty description/location, 2023–2024 timestamp, and HTTPS LinkedIn job URL. Obvious senior/manager/leadership and masked titles are excluded even when source labels say entry-level. Recorded experience labels are not independently validated. This is a small, deliberately selected sample, not a representative jobs survey.

Changes: copied source title/company/location/experience/work type, converted Unix timestamp to UTC date, retained original posting URL, excerpted descriptions at 5,000 characters, and added explicitly labeled keyword tags by fixed text rules. Tags do not claim mandatory requirements. Salaries, campus eligibility, skills proficiency, applications, and hiring availability are not inferred.

Historical links may expire or require login. These companies are not represented as partners. Data is a shared public static reference asset with no account or college fields; it never enters tenant tables, matching, offers, or analytics. The source carries no verified current-vacancy status.
