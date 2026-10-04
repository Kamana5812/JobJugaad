"""Private PDF lifecycle checks against explicitly approved local PostgreSQL.

All accounts, offers and files are controlled fixtures. No live records,
external notification services, or real personal documents are touched.
"""
import hashlib
import json
import os
import subprocess
import sys
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, insert, select, text, update
from sqlalchemy.exc import DBAPIError

from auth import hash_password, issue_token
from database import SessionLocal, engine, initialize_schema, tenant_session
from engines import offers, offer_documents, document_pdf as document_validator
from main import app
from models import (AccountAccess, Company, Interview, Job, Notification, Offer,
    OfferDocument, OfferDocumentEvent, OfferEvent, Student, User)
from schemas import JobInput
from upload_limits import MAX_UPLOAD_BODY_BYTES


def document_pdf(page_count=1, blank=False, encrypted=False, size=None, catalog_extra=b"", orphan_extra=None):
    """Small real PDFs, including blank pages and a password-protected header."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R " + catalog_extra + b" >>", b""]
    pages = []
    for index in range(page_count):
        page_id = len(objects) + 1
        stream_id = page_id + 1
        pages.append(page_id)
        stream = b"" if blank else b"BT /F1 12 Tf 50 750 Td (Controlled local offer document.) Tj ET"
        objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
            b"/Contents " + str(stream_id).encode() + b" 0 R >>")
        objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    objects[1] = b"<< /Type /Pages /Kids [" + b" ".join(str(p).encode() + b" 0 R" for p in pages) + b"] /Count " + str(page_count).encode() + b" >>"
    if orphan_extra:
        objects.append(orphan_extra)
    encrypt_id = None
    if encrypted:
        encrypt_id = len(objects) + 1
        objects.append(b"<< /Filter /Standard /V 1 /R 2 /Length 40 /P -4 "
            b"/O <" + b"00" * 32 + b"> /U <" + b"11" * 32 + b"> >>")
    result, offsets = b"%PDF-1.4\n", [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += str(index).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    position = len(result)
    result += b"xref\n0 " + str(len(objects) + 1).encode() + b"\n0000000000 65535 f \n"
    result += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    result += b"trailer\n<< /Size " + str(len(objects) + 1).encode() + b" /Root 1 0 R"
    if encrypt_id:
        result += b" /Encrypt " + str(encrypt_id).encode() + b" 0 R /ID [<" + b"22" * 16 + b"><" + b"22" * 16 + b">]"
    result += b" >>\nstartxref\n" + str(position).encode() + b"\n"
    if size:
        # A PDF comment leaves offsets intact and preserves the closing marker.
        padding = size - len(result) - len(b"%%EOF")
        if padding < 2:
            raise ValueError("Requested PDF size is too small.")
        result += b"%" + b"x" * (padding - 2) + b"\n"
    return result + b"%%EOF"


class OfferDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine is None
                or engine.url.host not in ("127.0.0.1", "localhost")
                or engine.url.database not in ("jobjugaad_test", "jobjugaad_test_utf8")):
            raise RuntimeError("Explicit isolated localhost document test database required.")
        initialize_schema()
        cls.client = TestClient(app)
        cls.suffix = uuid.uuid4().hex[:12]
        cls.password_hash = hash_password("Local-document-fixture-2026")
        cls.accounts = []
        for college in (10226, 10229):
            with tenant_session(college) as session:
                account = dict(college=college)
                for label, role, state in (("admin", "admin", "approved"),
                        ("recruiter", "recruiter", "approved"), ("student", "student", "approved"),
                        ("other", "student", "approved"), ("pending", "student", "pending")):
                    user = User(college_id=college, role=role,
                        email=f"documents-{label}-{cls.suffix}-{college}@test.invalid", password_hash=cls.password_hash)
                    session.add(user); session.flush()
                    session.add(AccountAccess(college_id=college, user_id=user.id,
                        email_verified_at=datetime.now(timezone.utc), approval_status=state))
                    student = None
                    if role == "student":
                        student = Student(college_id=college, user_id=user.id,
                            name=f"Local document {label} {cls.suffix}", branch="CSE", cgpa=8)
                        session.add(student); session.flush()
                    token = issue_token(user, student=student, session=session).access_token
                    account[label] = dict(user_id=user.id, student_id=student.id if student else None,
                        email=user.email, headers={"Authorization": "Bearer " + token})
                company = Company(college_id=college, recruiter_user_id=account["recruiter"]["user_id"],
                    name=f"Local document company {cls.suffix}", industry="Testing")
                session.add(company); session.flush(); account["company_id"] = company.id
            cls.accounts.append(account)
        cls.allowlist = patch.dict(os.environ, {"ADMIN_ACCOUNTS": json.dumps([
            dict(email=a["admin"]["email"], college_id=a["college"]) for a in cls.accounts])})
        cls.allowlist.start()

    @classmethod
    def tearDownClass(cls):
        try:
            # A fresh controlled draft is useful for independent local browser
            # rehearsal; no live account, token or deployment secret is exported.
            case = cls()
            row = case.new_offer(cls.accounts[0])
            a = cls.accounts[0]
            local = Path(__file__).resolve().parents[2] / ".local"
            (local / "offer-documents-preview.json").write_text(json.dumps(dict(
                database_name=engine.url.database, college_id=a["college"], offer_id=row["id"], student_id=a["student"]["student_id"],
                admin_email=a["admin"]["email"], student_email=a["student"]["email"],
                recruiter_email=a["recruiter"]["email"], password="Local-document-fixture-2026"),indent=2),encoding="utf-8")
            (local / "offer-document-preview.pdf").write_bytes(document_pdf())
        finally:
            cls.allowlist.stop()

    def setUp(self):
        self.a, self.b = self.accounts
        self.rows = [self.new_offer(account) for account in self.accounts]
        self.row = self.rows[0]
        self.pdf = document_pdf()

    def new_offer(self, account):
        body = JobInput(title=f"Local private document drive {self.suffix}", ctc=6,
            min_cgpa=5, eligible_branches=["CSE"], required_skills=[dict(skill_name="python", min_proficiency=60)]).model_dump()
        with tenant_session(account["college"]) as session:
            job = Job(college_id=account["college"], company_id=account["company_id"], **body)
            session.add(job); session.flush()
            start = datetime.now(timezone.utc) - timedelta(days=2)
            interview = Interview(college_id=account["college"], job_id=job.id,
                student_id=account["student"]["student_id"], scheduled_time=start,
                end_time=start + timedelta(minutes=30), venue="Local document room",
                panel_id="Local document panel", status="selected")
            session.add(interview); session.flush(); identity = interview.id
        response = self.client.post("/admin/offers", headers=account["admin"]["headers"],
            json=dict(interview_id=identity, reason="Controlled local selected interview"))
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def base(self, row=None, account=None, role="admin"):
        row, account = row or self.row, account or self.a
        if role == "admin":
            return f"/admin/offers/{row['id']}"
        return f"/students/{account[role]['student_id']}/offers/{row['id']}"

    def upload_response(self, row=None, account=None, role="admin", content=None, key=None,
            filename="local-evidence.pdf", replacement=None, content_type="application/pdf", **fields):
        row, account = row or self.row, account or self.a
        data = dict(version=str(row["version"]), reason="Controlled local upload evidence",
            label="Local evidence", idempotency_key=key or str(uuid.uuid4()),
            kind="offer_letter" if role == "admin" else "supporting_document")
        if replacement is not None:
            data["replaces_document_id"] = str(replacement)
        data.update({k: str(v) for k, v in fields.items()})
        return self.client.post(self.base(row, account, role) + "/documents", headers=account[role]["headers"],
            data=data, files={"file": (filename, self.pdf if content is None else content, content_type)})

    def upload(self, row=None, expected=201, **kwargs):
        response = self.upload_response(row=row, **kwargs)
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def review(self, row, document, status="verified", expected=200, account=None):
        account = account or self.a
        response = self.client.post(self.base(row, account) + f"/documents/{document['id']}/review",
            headers=account["admin"]["headers"], json=dict(version=row["version"], review_status=status,
                reason="Controlled human document review"))
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def admin_change(self, row, stage, value, expected=200, account=None):
        account = account or self.a
        response = self.client.put(f"/admin/offers/{row['id']}", headers=account["admin"]["headers"],
            json=dict(version=row["version"], stage=stage, value=value, reason="Controlled offer stage evidence"))
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def student_change(self, row, action, expected=200):
        response = self.client.post(self.base(row, role="student") + "/actions", headers=self.a["student"]["headers"],
            json=dict(version=row["version"], action=action, reason="Controlled student offer response"))
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def get_row(self, row=None, account=None):
        row, account = row or self.row, account or self.a
        result = self.client.get("/admin/offers", headers=account["admin"]["headers"], params={"limit":50})
        self.assertEqual(result.status_code, 200, result.text)
        return next(item for item in result.json()["offers"] if item["id"] == row["id"])

    def documents(self, row=None, account=None, **params):
        account = account or self.a
        result = self.client.get(self.base(row, account) + "/documents", headers=account["admin"]["headers"], params=params)
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def counts(self, row=None, account=None):
        row, account = row or self.row, account or self.a
        with tenant_session(account["college"]) as session:
            return tuple(session.scalar(select(func.count()).select_from(model).where(
                model.college_id == account["college"], model.offer_id == row["id"]))
                for model in (OfferDocument, OfferDocumentEvent, OfferEvent))

    def issue_with_file(self):
        result = self.upload()
        reviewed = self.review(result["offer"], result["document"])
        return self.admin_change(reviewed["offer"], "offer_letter_status", "issued"), reviewed["document"]

    def assert_same_stages(self, first, second):
        for key in offers.STAGES:
            self.assertEqual(first[key], second[key], key)

    def test_durable_private_bytes_metadata_and_attachment_headers(self):
        result = self.upload(filename="..\\folder\\local-evidence.pdf")
        row, document = result["offer"], result["document"]
        self.assert_same_stages(self.row, row)
        self.assertEqual(row["version"], self.row["version"] + 1)
        self.assertEqual(document["uploaded_offer_version"], row["version"])
        self.assertEqual(document["size_bytes"], len(self.pdf))
        self.assertEqual(document["sha256"], hashlib.sha256(self.pdf).hexdigest())
        self.assertEqual(document["page_count"], 1)
        self.assertEqual(document["review_status"], "pending")
        self.assertTrue(document["is_active"])
        self.assertNotIn("\\", document["original_filename"])
        self.assertNotIn("/", document["original_filename"])
        self.assertNotIn("content", document)
        self.assertNotIn("storage_url", document)
        student_base = self.base(row, role="student") + "/documents"
        student_listing = self.client.get(student_base, headers=self.a["student"]["headers"])
        self.assertEqual(student_listing.status_code, 200, student_listing.text)
        self.assertEqual(student_listing.json()["total"], 0)
        for suffix in (f"/{document['id']}/download", f"/{document['id']}/events"):
            self.assertEqual(self.client.get(student_base + suffix, headers=self.a["student"]["headers"]).status_code, 404)
        student_offers = self.client.get(f"/students/{self.a['student']['student_id']}/offers", headers=self.a["student"]["headers"]).json()
        hidden = next(item for item in student_offers["offers"] if item["id"] == row["id"])
        self.assertNotIn("document_uploaded", [event["action"] for event in hidden["audit"]])
        for role in ("admin",):
            response = self.client.get(self.base(row, role=role) + f"/documents/{document['id']}/download",
                headers=self.a[role]["headers"])
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.content, self.pdf)
            self.assertEqual(response.headers["content-type"].split(";")[0], "application/pdf")
            self.assertIn("attachment", response.headers["content-disposition"])
            self.assertNotIn("\\", response.headers["content-disposition"])
            self.assertNotIn("../", response.headers["content-disposition"])
            self.assertIn("no-store", response.headers["cache-control"])
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(self.get_row(row)["version"], row["version"])
        # Independent Python process has no shared sessions, parser memory or
        # application cache; its digest must come from committed private bytes.
        source = ("import hashlib,sys; from database import tenant_session; from models import OfferDocument; "
            "from sqlalchemy import select; "
            "\nwith tenant_session(int(sys.argv[1])) as s:\n"
            " r=s.scalar(select(OfferDocument).where(OfferDocument.college_id==int(sys.argv[1]),OfferDocument.id==int(sys.argv[2]))); "
            "print(hashlib.sha256(r.content).hexdigest())")
        process = subprocess.run([sys.executable, "-c", source, str(self.a["college"]), str(document["id"])],
            env=os.environ.copy(), cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stdout.strip(), document["sha256"])
        with tenant_session(self.a["college"]) as session:
            stored = session.scalar(select(OfferDocument).where(OfferDocument.college_id == self.a["college"], OfferDocument.id == document["id"]))
            self.assertNotIn("content", stored.__dict__)  # deferred byte column
        listing = self.documents(row)
        self.assertEqual((listing["total"], listing["offer_version"]), (1, row["version"]))
        self.assertTrue(listing["limits"] and listing["explanation"])
        events = self.client.get(self.base(row) + f"/documents/{document['id']}/events", headers=self.a["admin"]["headers"]).json()
        self.assertIn("document_uploaded", [e["action"] for e in events["items"]])
        self.assertIn("download_requested", [e["action"] for e in events["items"]])
        reviewed = self.review(row, document)
        issued = self.admin_change(reviewed["offer"], "offer_letter_status", "issued")
        response = self.client.get(self.base(issued, role="student") + f"/documents/{document['id']}/download",
            headers=self.a["student"]["headers"])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.content, self.pdf)

    def test_blank_pdf_is_valid_evidence_without_automatic_verification(self):
        row = self.admin_change(self.row, "offer_letter_status", "issued")
        result = self.upload(row=row, role="student", content=document_pdf(blank=True))
        self.assertEqual(result["document"]["kind"], "supporting_document")
        self.assertEqual(result["document"]["page_count"], 1)
        self.assert_same_stages(row, result["offer"])
        self.assertEqual(result["document"]["review_status"], "pending")
        self.assertIsNone(result["document"]["reviewed_by"])

    def test_invalid_and_bounded_pdf_failures_are_atomic(self):
        initial = self.counts()
        for content in (b"", b"not a PDF", b"%PDF-1.4\ntruncated", document_pdf(encrypted=True), document_pdf(page_count=21)):
            with self.subTest(size=len(content)):
                self.upload(content=content, expected=422)
                self.assertEqual(self.counts(), initial)
        with patch.object(offer_documents, "validate_document_pdf") as parser:
            response = self.upload_response(content=b"%PDF-" + b"x" * (2 * 1024 * 1024),
                **{"version":self.row["version"]})
            self.assertEqual(response.status_code, 413, response.text)
            parser.assert_not_called()
        self.assertEqual(self.counts(), initial)
        self.assertEqual(self.get_row()["version"], self.row["version"])

    def test_body_limit_rejects_before_multipart_with_production_cors(self):
        initial = self.counts()
        headers = {**self.a["admin"]["headers"], "Origin":"https://jobjugaad.vercel.app",
            "Content-Type":"multipart/form-data; boundary=local-test"}
        with patch.object(offer_documents, "validate_document_pdf") as parser:
            oversized = b"x" * (MAX_UPLOAD_BODY_BYTES + 1)
            for request_headers, content in ((headers, oversized),
                    ({**headers,"Content-Length":"0"}, oversized),
                    (headers, iter((oversized[:100],oversized[100:])))):
                response = self.client.post(self.base() + "/documents", headers=request_headers, content=content)
                self.assertEqual(response.status_code, 413, response.text)
                self.assertEqual(response.headers.get("access-control-allow-origin"), "https://jobjugaad.vercel.app")
            for lengths in (("invalid",),("0","0"),("9"*21,)):
                duplicate_headers = list(headers.items()) + [("Content-Length",value) for value in lengths]
                response = self.client.post(self.base()+"/documents",headers=duplicate_headers,content=b"x")
                self.assertEqual(response.status_code,400,response.text)
            unauthorized = self.client.post(self.base()+"/documents",headers={"Origin":headers["Origin"]},content=oversized)
            self.assertEqual(unauthorized.status_code,401,unauthorized.text)
            parser.assert_not_called()
        self.assertEqual(self.counts(), initial)

    def test_pdf_actions_attachments_filename_and_media_type_checks(self):
        before=self.counts()
        for content in (document_pdf(catalog_extra=b"/OpenAction << /S /JavaScript /JS (test) >>"),
                document_pdf(catalog_extra=b"/Names << /EmbeddedFiles << /Names [] >> >>"),
                document_pdf(orphan_extra=b"<< /Type /EmbeddedFile /Length 0 >>\nstream\n\nendstream")):
            self.upload(content=content,expected=422)
        for filename in ("payload.exe", "evidence.pdf.exe", "x"*256+".pdf"):
            self.upload(filename=filename,expected=422)
        self.upload(content_type="image/png",expected=422)
        self.assertEqual(self.counts(),before)
        result=self.upload(filename="local-файл.pdf",content_type="application/octet-stream")
        self.assertEqual(result["document"]["original_filename"],"local-файл.pdf")
        download=self.client.get(self.base(result["offer"])+f"/documents/{result['document']['id']}/download",headers=self.a["admin"]["headers"])
        self.assertEqual(download.status_code,200,download.text)
        self.assertTrue(download.headers["content-disposition"].isascii())

    def test_parser_deadline_terminates_worker_and_failed_spawn_is_safe(self):
        parent, child, worker, context = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        parent.poll.return_value = False
        worker.pid = 123
        worker.is_alive.side_effect = [True, False]
        context.Pipe.return_value = (parent, child)
        context.Process.return_value = worker
        with patch.object(document_validator.multiprocessing, "get_context", return_value=context):
            with self.assertRaises(HTTPException) as failure:
                document_validator.validate_document_pdf(self.pdf)
        self.assertEqual(failure.exception.status_code, 422)
        self.assertIn("too long", failure.exception.detail)
        parent.poll.assert_called_once_with(document_validator.PARSER_SECONDS)
        worker.terminate.assert_called_once()
        parent.close.assert_called_once()
        self.assertTrue(child.close.called)
        # Process startup failure must not pretend the file passed validation.
        parent, child, worker, context = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        worker.pid = None
        worker.start.side_effect = OSError("controlled local startup failure")
        context.Pipe.return_value = (parent, child)
        context.Process.return_value = worker
        with patch.object(document_validator.multiprocessing, "get_context", return_value=context):
            with self.assertRaises(HTTPException) as failure:
                document_validator.validate_document_pdf(self.pdf)
        self.assertEqual(failure.exception.status_code, 503)
        self.assertNotIn("controlled local", failure.exception.detail)
        parent.close.assert_called_once()

    def test_multipart_inputs_and_role_bound_kind(self):
        before=self.counts()
        for fields in (dict(version="0"), dict(version="true"), dict(reason="tiny"), dict(label="a"),
                dict(idempotency_key="not-a-uuid"), dict(kind="unsupported"), dict(replaces_document_id="0")):
            with self.subTest(fields=fields):
                self.upload(expected=422, **fields)
                self.assertEqual(self.counts(),before)
        self.upload(kind="supporting_document", expected=422)
        # A student's multipart data may never create an administrator letter.
        row = self.admin_change(self.row, "offer_letter_status", "issued")
        response = self.upload_response(row=row, role="student", kind="offer_letter")
        if response.status_code == 201:
            self.assertEqual(response.json()["document"]["kind"], "supporting_document")
        else:
            self.assertIn(response.status_code, (403,422), response.text)

    def test_roles_owner_college_and_anonymous_denials(self):
        result = self.upload(); row, document = result["offer"], result["document"]
        paths = [self.base(row) + "/documents", self.base(row) + f"/documents/{document['id']}/download",
            self.base(row) + f"/documents/{document['id']}/events"]
        for path in paths:
            self.assertEqual(self.client.get(path).status_code, 401)
            for role in ("student", "recruiter"):
                self.assertEqual(self.client.get(path, headers=self.a[role]["headers"]).status_code, 403)
            self.assertEqual(self.client.get(path, headers=self.b["admin"]["headers"]).status_code, 404)
        for role, account, expected in (("other",self.a,404),("student",self.b,404),("recruiter",self.a,403)):
            student_id = account[role]["student_id"] or self.a["student"]["student_id"]
            base = f"/students/{student_id}/offers/{row['id']}/documents"
            for suffix in ("", f"/{document['id']}/download", f"/{document['id']}/events"):
                self.assertEqual(self.client.get(base+suffix, headers=account[role]["headers"]).status_code, expected)
        for role in ("student", "recruiter"):
            self.assertEqual(self.client.post(paths[0], headers=self.a[role]["headers"], data=dict(version=row["version"],
                reason="Unauthorized upload denied", label="Evidence", idempotency_key=str(uuid.uuid4()), kind="offer_letter"),
                files={"file":("local.pdf",self.pdf,"application/pdf")}).status_code,403)
            self.assertEqual(self.client.post(self.base(row)+f"/documents/{document['id']}/review", headers=self.a[role]["headers"],
                json=dict(version=row["version"],review_status="verified",reason="Unauthorized review denied")).status_code,403)
        self.upload(row=row, account=self.b, expected=404)
        self.review(row,document,account=self.b,expected=404)

    def test_real_admission_and_current_role_are_rechecked(self):
        row = self.admin_change(self.row, "offer_letter_status", "issued")
        for state in ("pending", "rejected"):
            with tenant_session(self.a["college"]) as session:
                session.execute(update(AccountAccess).where(AccountAccess.college_id == self.a["college"],
                    AccountAccess.user_id == self.a["student"]["user_id"]).values(approval_status=state))
            try:
                self.upload(row=row, role="student", expected=403)
                self.assertEqual(self.client.get(self.base(row,role="student")+"/documents",headers=self.a["student"]["headers"]).status_code,403)
            finally:
                with tenant_session(self.a["college"]) as session:
                    session.execute(update(AccountAccess).where(AccountAccess.college_id == self.a["college"],
                        AccountAccess.user_id == self.a["student"]["user_id"]).values(approval_status="approved"))
        with tenant_session(self.a["college"]) as session:
            session.execute(update(User).where(User.college_id == self.a["college"],User.id == self.a["student"]["user_id"]).values(role="recruiter"))
        try:
            self.upload(row=row,role="student",expected=401)
        finally:
            with tenant_session(self.a["college"]) as session:
                session.execute(update(User).where(User.college_id == self.a["college"],User.id == self.a["student"]["user_id"]).values(role="student"))

    def test_letter_review_is_human_and_issuance_requires_verified_active_file(self):
        result = self.upload(); row, document = result["offer"], result["document"]
        self.admin_change(row,"offer_letter_status","issued",expected=409)
        rejected = self.review(row,document,status="rejected")
        self.assert_same_stages(row,rejected["offer"])
        self.assertEqual(rejected["document"]["reviewed_by"],self.a["admin"]["user_id"])
        self.assertTrue(rejected["document"]["reviewed_at"] and rejected["document"]["review_reason"])
        self.review(rejected["offer"],rejected["document"],expected=409)
        self.admin_change(rejected["offer"],"offer_letter_status","issued",expected=409)
        replacement = self.upload(row=rejected["offer"],replacement=document["id"],filename="revised-letter.pdf")
        reviewed = self.review(replacement["offer"],replacement["document"])
        self.assert_same_stages(replacement["offer"],reviewed["offer"])
        issued = self.admin_change(reviewed["offer"],"offer_letter_status","issued")
        self.assertEqual(issued["offer_letter_status"],"issued")
        self.upload(row=issued,expected=409)
        for event in reviewed["offer"]["audit"]:
            if event["action"] in ("document_uploaded","document_reviewed"):
                self.assert_same_stages(event["snapshot"]["before"],event["snapshot"]["after"])

    def test_control_characters_do_not_write_metadata_or_review(self):
        before=self.counts()
        for fields in (dict(label="NUL\x00label"),dict(reason="Controlled NUL\x00reason")):
            self.upload(expected=422,**fields)
            self.assertEqual(self.counts(),before)
            self.assertEqual(self.get_row()["version"],self.row["version"])
        reason="Human review\tcontext\nSecond line."
        result=self.upload(reason=reason)
        self.assertEqual(result["offer"]["audit"][-1]["reason"],reason)
        row,document=result["offer"],result["document"]
        before=self.counts()
        invalid=self.client.post(self.base(row)+f"/documents/{document['id']}/review",headers=self.a["admin"]["headers"],
            json=dict(version=row["version"],review_status="verified",reason="Controlled NUL\x00review"))
        self.assertEqual(invalid.status_code,422,invalid.text)
        self.assertEqual(self.counts(),before)
        self.assertEqual(self.get_row()["version"],row["version"])
        self.assertEqual(self.documents()["items"][0]["review_status"],"pending")

    def test_supporting_review_submission_verification_and_correction_require_new_evidence(self):
        row,_ = self.issue_with_file()
        # Existing letter evidence establishes file workflow; supporting files
        # then establish supporting-document preconditions for this offer.
        one = self.upload(row=row,role="student")
        two = self.upload(row=one["offer"],role="student",filename="second-support.pdf")
        row = two["offer"]
        self.review(row,one["document"],expected=409)
        row = self.student_change(row,"submit_documents")
        first = self.review(row,one["document"])
        self.admin_change(first["offer"],"verification_status","verified",expected=409)
        second = self.review(first["offer"],two["document"])
        row = self.admin_change(second["offer"],"verification_status","verified")
        row = self.admin_change(row,"documents_status","changes_requested")
        self.assertEqual(row["verification_status"],"pending")
        self.student_change(row,"submit_documents",expected=409)
        self.upload(row=second["offer"],role="student",expected=409)
        replacement = self.upload(row=row,role="student",replacement=one["document"]["id"],filename="corrected-support.pdf")
        self.assertGreater(replacement["document"]["uploaded_offer_version"],row["version"])
        row = self.student_change(replacement["offer"],"submit_documents")
        self.admin_change(row,"verification_status","verified",expected=409)
        revised = self.review(row,replacement["document"])
        row = self.admin_change(revised["offer"],"verification_status","verified")
        row = self.student_change(row,"accept")
        row = self.admin_change(row,"joining_status","joined")
        self.assertEqual(row["joining_status"],"joined")
        self.upload(row=row,role="student",expected=409)

    def test_replacement_preserves_original_bytes_and_paginated_history(self):
        first = self.upload(content=document_pdf(blank=True))
        second = self.upload(row=first["offer"],replacement=first["document"]["id"],filename="new-letter.pdf")
        document = second["document"]
        self.assertEqual(document["supersedes_document_id"],first["document"]["id"])
        listing = self.documents(second["offer"],limit=1,offset=0)
        other = self.documents(second["offer"],limit=1,offset=1)
        self.assertEqual(listing["total"],2)
        items = listing["items"]+other["items"]
        self.assertEqual({item["id"] for item in items},{first["document"]["id"],document["id"]})
        old = next(item for item in items if item["id"]==first["document"]["id"])
        self.assertFalse(old["is_active"])
        self.assertEqual(old["sha256"],first["document"]["sha256"])
        self.review(second["offer"],old,expected=409)
        response = self.client.get(self.base(second["offer"])+f"/documents/{old['id']}/download",headers=self.a["admin"]["headers"])
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.content,document_pdf(blank=True))
        path=self.base(second["offer"])+f"/documents/{old['id']}/events"
        first_page=self.client.get(path,headers=self.a["admin"]["headers"],params={"limit":1,"offset":0}).json()
        rest=self.client.get(path,headers=self.a["admin"]["headers"],params={"limit":50,"offset":1}).json()
        events=first_page["items"]+rest["items"]
        self.assertEqual(len(events),first_page["total"])
        self.assertEqual(len({e['id'] for e in events}),len(events))
        self.assertIn("document_superseded",[e["action"] for e in events])
        self.assertTrue(all(e["actor_user_id"] and e["reason"] for e in events))

    def test_idempotent_upload_replay_and_changed_payload_rejection(self):
        key=str(uuid.uuid4())
        result=self.upload(key=key)
        counts=self.counts()
        replay=self.upload(key=key)
        self.assertEqual(replay["document"]["id"],result["document"]["id"])
        self.assertEqual(self.counts(),counts)
        self.assertEqual(self.get_row()["version"],result["offer"]["version"])
        for change in (dict(filename="different.pdf"),dict(content=document_pdf(blank=True)),dict(label="Different label"),dict(reason="Different audit context")):
            self.upload(key=key,expected=409,**change)
        self.assertEqual(self.counts(),counts)
        # The saved idempotency identity remains stable after a later review.
        reviewed=self.review(result["offer"],result["document"])
        replay=self.upload(key=key)
        self.assertEqual(replay["document"]["id"],result["document"]["id"])
        self.assertEqual(replay["offer"]["version"],reviewed["offer"]["version"])

    def test_concurrent_retries_and_new_uploads_cannot_overwrite_versions(self):
        key=str(uuid.uuid4())
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.upload_response(key=key),range(2)))
        self.assertEqual([r.status_code for r in results],[201,201])
        self.assertEqual(len({r.json()["document"]["id"] for r in results}),1)
        self.assertEqual(self.counts()[0],1)
        row=self.new_offer(self.a)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.upload_response(row=row),range(2)))
        self.assertEqual(sorted(r.status_code for r in results),[201,409])
        self.assertEqual(self.counts(row)[0],1)
        self.assertEqual(self.get_row(row)["version"],row["version"]+1)

    def test_review_racing_stage_change_keeps_both_guards_and_audits(self):
        result=self.upload();row,document=result["offer"],result["document"]
        def run(action):
            if action=="review":
                return self.client.post(self.base(row)+f"/documents/{document['id']}/review",headers=self.a["admin"]["headers"],
                    json=dict(version=row["version"],review_status="verified",reason="Concurrent human document review"))
            return self.client.put(self.base(row),headers=self.a["admin"]["headers"],
                json=dict(version=row["version"],stage="offer_letter_status",value="issued",reason="Concurrent offer letter issuance"))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(run,("review","issue")))
        self.assertEqual([r.status_code for r in results],[200,409])
        current=self.get_row()
        self.assertEqual(current["offer_letter_status"],"draft")
        self.assertEqual(current["version"],row["version"]+1)
        self.review(row,document,expected=409)
        self.admin_change(current,"offer_letter_status","issued")

    def test_notification_failure_rolls_back_bytes_review_and_offer_audit(self):
        row = self.admin_change(self.row,"offer_letter_status","issued")
        before=self.counts()
        with patch.object(offers,"notify_student",side_effect=HTTPException(503,"Controlled local notification failure")):
            self.upload(row=row,role="student",expected=503)
        self.assertEqual(self.counts(),before)
        self.assertEqual(self.get_row()["version"],row["version"])
        result=self.upload(row=row,role="student")
        submitted=self.student_change(result["offer"],"submit_documents")
        before=self.counts()
        with patch.object(offers,"notify_student",side_effect=HTTPException(503,"Controlled local notification failure")):
            self.review(submitted,result["document"],expected=503)
        self.assertEqual(self.counts(),before)
        self.assertEqual(self.get_row()["version"],submitted["version"])
        self.assertEqual(self.documents()["items"][0]["review_status"],"pending")

    def test_retained_count_includes_replaced_history(self):
        result=self.upload()
        for index in range(9):
            result=self.upload(row=result["offer"],replacement=result["document"]["id"],filename=f"revision-{index}.pdf")
        self.assertEqual(self.documents()["total"],10)
        initial=self.counts()
        self.upload(row=result["offer"],replacement=result["document"]["id"],expected=413)
        self.assertEqual(self.counts(),initial)

    def test_retained_byte_limit_counts_active_and_superseded_files(self):
        row=self.admin_change(self.row,"offer_letter_status","issued")
        content=document_pdf(size=2*1024*1024)
        self.assertEqual(len(content),2*1024*1024)
        # Quota checks use real stored bytes. Parsing is already exercised with
        # real PDFs above; this case isolates the exact retained-byte boundary.
        with patch.object(offer_documents,"validate_document_pdf",return_value=1):
            for index in range(5):
                result=self.upload(row=row,role="student",content=content,filename=f"quota-{index}.pdf")
                row=result["offer"]
            counts=self.counts()
            self.upload(row=row,role="student",replacement=result["document"]["id"],expected=413)
            self.assertEqual(self.counts(),counts)
        with tenant_session(self.a["college"]) as session:
            total=session.scalar(select(func.sum(OfferDocument.size_bytes)).where(
                OfferDocument.college_id==self.a["college"],OfferDocument.offer_id==row["id"]))
            self.assertEqual(total,10*1024*1024)

    def test_legacy_external_stages_and_closed_offer_reads_remain_compatible(self):
        # Offers without file records retain the existing external exchange path.
        row=self.admin_change(self.row,"offer_letter_status","issued")
        row=self.student_change(row,"submit_documents")
        row=self.admin_change(row,"verification_status","verified")
        row=self.student_change(row,"accept")
        row=self.admin_change(row,"joining_status","joined")
        self.assertEqual(row["joining_status"],"joined")
        self.upload(row=row,role="student",expected=409)
        result=self.upload(row=self.rows[1],account=self.b)
        closed=self.admin_change(result["offer"],"offer_letter_status","withdrawn",account=self.b)
        self.review(closed,result["document"],account=self.b,expected=409)
        listing=self.documents(closed,account=self.b)
        self.assertEqual(listing["total"],1)
        response=self.client.get(self.base(closed,self.b)+f"/documents/{result['document']['id']}/download",headers=self.b["admin"]["headers"])
        self.assertEqual(response.status_code,200)

    def test_force_rls_unfiltered_reads_and_cross_tenant_insert_update_denial(self):
        documents=[self.upload(row=row,account=account)["document"] for row,account in zip(self.rows,self.accounts)]
        models=(OfferDocument,OfferDocumentEvent)
        copies={}
        for account in self.accounts:
            with tenant_session(account["college"]) as session:
                for model in models:
                    rows=session.scalars(select(model)).all()  # Intentionally omit app filters to exercise RLS alone.
                    self.assertTrue(rows)
                    self.assertTrue(all(row.college_id==account["college"] for row in rows))
                    if account is self.b:
                        row=session.execute(select(*model.__table__.columns).where(model.college_id==account["college"],
                            model.offer_id==self.rows[1]["id"])).mappings().first()
                        copies[model]={key:value for key,value in row.items() if key!="id"}
        with SessionLocal() as session:
            for model in models:
                self.assertEqual(session.scalars(select(model)).all(),[])
        with engine.connect() as connection:
            policies=connection.execute(text("SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,p.policyname,p.qual,p.with_check "
                "FROM pg_class c JOIN pg_policies p ON p.tablename=c.relname WHERE c.relname IN ('offer_documents','document_events')")).all()
            self.assertEqual(len(policies),2)
            for name,enabled,forced,policy,using,check in policies:
                self.assertTrue(enabled and forced,name)
                self.assertEqual(policy,"college_isolation")
                self.assertIn("college_id",using)
                self.assertIn("college_id",check)
        for model in models:
            with self.subTest(table=model.__tablename__,operation="insert"):
                with self.assertRaises(DBAPIError) as failure:
                    with tenant_session(self.a["college"]) as session:
                        session.execute(insert(model).values(**copies[model]))
                self.assertIn("row-level security",str(failure.exception).lower())
            with self.subTest(table=model.__tablename__,operation="update"):
                with self.assertRaises(DBAPIError) as failure:
                    with tenant_session(self.a["college"]) as session:
                        row=session.scalar(select(model).where(model.college_id==self.a["college"],model.offer_id==self.row["id"]))
                        session.execute(update(model).where(model.college_id==self.a["college"],model.id==row.id).values(college_id=self.b["college"]))
                self.assertIn("row-level security",str(failure.exception).lower())
        self.assertEqual(self.documents()["items"][0]["id"],documents[0]["id"])


if __name__=="__main__":
    unittest.main()
