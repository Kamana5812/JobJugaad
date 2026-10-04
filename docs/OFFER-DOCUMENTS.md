# Private offer and supporting-document PDFs

Release verification is recorded in MEMORY.md. This guide describes the new workflow; do not infer a live end-to-end check from documentation alone.

## What changes

The five offer stages remain distinct. Uploading a PDF never issues a letter, submits documents, verifies the offer, accepts it or records joining. Each change requires an authorized human action and reason. Existing offers without uploaded files retain their external-document declaration workflow.

Administrators can upload and replace an offer letter while the offer is **draft**. The owning student cannot see that draft file, its review or related file-action reasons. An administrator must review the active letter before issuing it when a letter file exists. Issuance makes the letter available to its owning student. Withdrawal closes further changes but retains authorized access to previously issued files and their history.

After issuance, the owning student can upload supporting PDFs while Documents is **pending** or **changes_requested**. Replacements retain earlier bytes, filename, checksum and history. Each new revision starts with a pending review. The student separately records **documents submitted**, then an administrator downloads and reviews every active supporting PDF. Overall verification requires every active supporting file to be verified when uploaded supporting files exist. After corrections are requested, resubmission requires a new upload/replacement, rather than submitting unchanged files again.

## Click-by-click workflow

Use a newly created synthetic draft offer from a selected test interview. The completed Phase 4 fixture (#2385) is already joined and cannot be used for new file uploads. Never modify a real person's offer to rehearse.

1. Administrator: **Command Center → Offers**, expand the draft offer's **Private PDFs and human file review** panel. Choose a plain synthetic PDF, enter a label and reason, then click **Store private PDF**. Confirm the file is pending review; Offer letter remains draft.
2. Administrator: click **Download private PDF #…**, inspect its contents, choose **Record file verified by human review** or **Record file rejected by human review**, enter a review reason and click **Record human file review**. This is a human declaration, not independent or automatic certification. A rejected letter needs a replacement and new review.
3. Administrator: separately choose **Record letter issued** in Record an action, provide a reason and click **Confirm action**. Refresh and confirm Offer letter is issued.
4. Owning student: **My offers → Private PDFs and human file review**, download the issued letter, then upload a synthetic supporting PDF with a label and reason using **Store private PDF**. Confirm its pending review. Separately choose **Record documents submitted** and **Confirm action**; uploading alone does not submit that stage.
5. Administrator: download each active supporting file, inspect it and record each review with a reason. If correction is needed, reject that file and separately record **Request document corrections**. Student replaces it, then records resubmission; staff reviews the replacement.
6. Administrator: after all active supporting PDFs are verified, separately choose **Record documents verified** and **Confirm action**. Student separately chooses **Accept offer** or **Decline offer**. Record joining only when the existing issued/accepted/verified prerequisites are met.
7. Refresh both portals. Inspect **File history** and **Stage history**, including superseded revisions and reasons. Download history records a request, not proof that someone read or saved a file. Hiring notifications remain in-app only.

## Limits and access

- One PDF per upload, at most **2 MiB** and **20 pages**. Scanned PDFs are accepted without OCR. Complete PDF header/ending, parser checks, encryption and embedded-action checks apply; a filename or MIME claim alone is insufficient.
- At most **10 retained files** and **10 MiB of stored PDF bytes per offer**, including superseded revisions. Failed uploads do not consume quota. Replacing a file retains its bytes and consumes another revision slot.
- A bounded request body precedes multipart parsing. A disposable PDF parser has a 12-second wall-time limit; Linux also applies memory/CPU bounds. These are format and resource checks, not antivirus or authenticity verification. A PDF can still contain unsafe content that those checks do not detect; organizational malware scanning remains a deployment limitation.
- Private bytes are stored as PostgreSQL `bytea`, not in Render's ephemeral application filesystem or frontend assets. Listing metadata/history does not load the deferred PDF bytes.
- Downloads require a current authorized account, college filter, student ownership where applicable and FORCE RLS. No public file URL or token in a download URL is created. The server returns an attachment with a generated ASCII filename, PDF content type, `nosniff`, sandbox policy and private/no-store caching.
- File changes lock and version the offer. A retry identifier recognizes an unchanged upload even if its first response was lost; after leaving/reloading, inspect history before retrying. A stale version or changed reuse is rejected.
- There is no file deletion endpoint, retention scheduler or automated document certification. Retained files share database capacity and backups; this bounded storage design is not a demonstrated production-scale document service. Confirm database continuity and backup/restore before using sensitive institutional files.

Both `offer_documents` and `document_events` carry `college_id`, composite tenant foreign keys, application college filters and ENABLE/FORCE `college_isolation` policies with read/write predicates. Current account approval and role are checked on protected requests; a JWT's historical role alone is insufficient.

Design references: [OWASP file-upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) and [FastAPI UploadFile documentation](https://fastapi.tiangolo.com/tutorial/request-files/). Their guidance informs the limits and authenticated private storage; implementing those checks does not establish a complete security certification.
