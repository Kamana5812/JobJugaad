"""Shared parser saturation/release checks without starting child parsers."""
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from engines import document_pdf, resume
from engines.pdf_budget import PARSER_SLOTS

class PdfBudgetTests(unittest.TestCase):
    def test_resume_and_document_share_saturation_boundary(self):
        self.assertIs(resume.PARSER_SLOTS, document_pdf.PARSER_SLOTS)
        PARSER_SLOTS.acquire()
        try:
            for function in (resume.extract_resume, document_pdf.validate_document_pdf):
                with self.assertRaises(HTTPException) as failure:
                    function(b'%PDF-1.4\n%%EOF')
                self.assertEqual(failure.exception.status_code, 503)
                self.assertEqual(failure.exception.headers['Retry-After'], '3')
        finally:
            PARSER_SLOTS.release()

    def test_failed_parser_releases_shared_slot(self):
        for module, function, target in ((resume, resume.extract_resume, '_extract_bounded'),
            (document_pdf, document_pdf.validate_document_pdf, '_validate_bounded')):
            with patch.object(module, target, side_effect=HTTPException(422, 'Controlled parser rejection')):
                with self.assertRaises(HTTPException):
                    function(b'%PDF-1.4\n%%EOF')
            self.assertTrue(PARSER_SLOTS.acquire(blocking=False))
            PARSER_SLOTS.release()
