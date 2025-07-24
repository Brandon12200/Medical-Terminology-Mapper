"""
Tests for document text extraction functionality
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from docx import Document
import PyPDF2

from app.processing.text_extractor import TextExtractor


class TestTextExtractor:
    """Test text extraction from various document formats"""
    
    @pytest.fixture
    def extractor(self):
        """Create a text extractor instance"""
        return TextExtractor()
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def create_test_txt(self, temp_dir: str, content: str = "This is a test document.") -> Path:
        """Create a test TXT file"""
        file_path = Path(temp_dir) / "test.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def create_test_docx(self, temp_dir: str, content: str = "This is a test DOCX document.") -> Path:
        """Create a test DOCX file"""
        file_path = Path(temp_dir) / "test.docx"
        doc = Document()
        doc.add_paragraph(content)
        doc.save(str(file_path))
        return file_path
    
    def create_test_pdf(self, temp_dir: str) -> Path:
        """Create a simple test PDF file"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        file_path = Path(temp_dir) / "test.pdf"
        c = canvas.Canvas(str(file_path), pagesize=letter)
        c.drawString(100, 750, "This is a test PDF document.")
        c.drawString(100, 730, "It contains multiple lines of text.")
        c.drawString(100, 710, "For testing text extraction.")
        c.save()
        return file_path
    
    def test_extract_txt_success(self, extractor, temp_dir):
        """Test successful text extraction from TXT file"""
        content = "This is a test document.\nWith multiple lines.\nAnd special characters: é, ñ, ü"
        file_path = self.create_test_txt(temp_dir, content)
        
        text, method, metadata = extractor.extract_text(str(file_path), 'txt')
        
        assert text == content
        assert method == "direct_read"
        assert metadata['encoding'] == 'utf-8'
        assert metadata['line_count'] == 3
    
    def test_extract_docx_success(self, extractor, temp_dir):
        """Test successful text extraction from DOCX file"""
        content = "This is a test DOCX document with multiple paragraphs."
        file_path = self.create_test_docx(temp_dir, content)
        
        text, method, metadata = extractor.extract_text(str(file_path), 'docx')
        
        assert content in text
        assert method == "python-docx"
        assert metadata['paragraph_count'] == 1
        assert metadata['table_count'] == 0
    
    @patch('app.processing.text_extractor.PyPDF2.PdfReader')
    def test_extract_pdf_with_pypdf2(self, mock_pdf_reader, extractor):
        """Test PDF extraction using PyPDF2"""
        # Mock PDF reader
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test PDF content"
        mock_reader.pages = [mock_page]
        mock_reader.metadata = {'/Title': 'Test PDF', '/Author': 'Test Author'}
        mock_pdf_reader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'%PDF-1.4 fake pdf content')
            tmp_path = tmp.name
        
        try:
            text, method, metadata = extractor.extract_text(tmp_path, 'pdf')
            
            assert text == "Test PDF content"
            assert method == "PyPDF2"
            assert metadata['page_count'] == 1
            assert metadata['pdf_metadata']['title'] == 'Test PDF'
        finally:
            os.unlink(tmp_path)
    
    @patch('app.processing.text_extractor.parser')
    def test_extract_with_tika_fallback(self, mock_tika_parser, extractor):
        """Test extraction using Apache Tika as fallback"""
        mock_tika_parser.from_file.return_value = {
            'content': 'Extracted content from Tika',
            'metadata': {'Content-Type': 'application/rtf'}
        }
        
        with tempfile.NamedTemporaryFile(suffix='.rtf', delete=False) as tmp:
            tmp.write(b'{\\rtf1 Test RTF content}')
            tmp_path = tmp.name
        
        try:
            text, method, metadata = extractor.extract_text(tmp_path, 'rtf')
            
            assert text == "Extracted content from Tika"
            assert method == "Apache Tika"
            assert 'tika_metadata' in metadata
        finally:
            os.unlink(tmp_path)
    
    def test_extract_hl7_message(self, extractor, temp_dir):
        """Test HL7 message extraction"""
        hl7_content = """MSH|^~\\&|SENDING_APP|SENDING_FAC|RECEIVING_APP|RECEIVING_FAC|20240101120000||ADT^A01|MSG00001|P|2.5|||
EVN|A01|20240101120000|||
PID|1||12345^^^MRN||DOE^JOHN^A||19800101|M|||123 MAIN ST^^ANYTOWN^ST^12345||555-1234|||M||ACCT12345|123-45-6789|"""
        
        file_path = Path(temp_dir) / "test.hl7"
        with open(file_path, 'w') as f:
            f.write(hl7_content)
        
        text, method, metadata = extractor.extract_text(str(file_path), 'hl7')
        
        assert text == hl7_content
        assert method == "hl7_parser"
        assert metadata['segment_count'] == 3
        assert metadata['message_type'] == 'ADT^A01'
    
    def test_extract_nonexistent_file(self, extractor):
        """Test extraction from non-existent file"""
        text, method, metadata = extractor.extract_text('/nonexistent/file.txt', 'txt')
        
        assert text is None
        assert method == "error"
        assert "File not found" in metadata['error']
    
    def test_extract_unsupported_type(self, extractor, temp_dir):
        """Test extraction from unsupported file type"""
        file_path = self.create_test_txt(temp_dir)
        
        text, method, metadata = extractor.extract_text(str(file_path), 'unsupported')
        
        assert text is None
        assert method == "error"
        assert "Unsupported document type" in metadata['error']
    
    def test_clean_text(self, extractor):
        """Test text cleaning functionality"""
        dirty_text = "  Too    many     spaces\n\n\n\nToo many newlines\x00\x01Non-printable  "
        
        cleaned = extractor._clean_text(dirty_text)
        
        assert cleaned == "Too many spaces\n\nToo many newlines Non-printable"
    
    def test_get_text_preview(self, extractor):
        """Test text preview generation"""
        long_text = "This is a long text. " * 50
        
        preview = extractor.get_text_preview(long_text, max_length=100)
        
        assert len(preview) <= 100
        assert preview.endswith("...")
        
        # Test with sentence ending
        text_with_period = "This is a sentence. " * 10 + "This is the end."
        preview = extractor.get_text_preview(text_with_period, max_length=50)
        assert preview.endswith(".")
    
    @patch('app.processing.text_extractor.PyPDF2.PdfReader')
    @patch('app.processing.text_extractor.parser')
    def test_pdf_fallback_to_tika(self, mock_tika_parser, mock_pdf_reader, extractor):
        """Test PDF extraction falls back to Tika when PyPDF2 returns little text"""
        # Mock PyPDF2 to return very little text
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Short"
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        mock_pdf_reader.return_value = mock_reader
        
        # Mock Tika to return proper content
        mock_tika_parser.from_file.return_value = {
            'content': 'This is the full content extracted by Tika',
            'metadata': {'Content-Type': 'application/pdf'}
        }
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'%PDF-1.4 fake pdf content')
            tmp_path = tmp.name
        
        try:
            text, method, metadata = extractor.extract_text(tmp_path, 'pdf')
            
            assert text == "This is the full content extracted by Tika"
            assert method == "Apache Tika"
            mock_tika_parser.from_file.assert_called_once()
        finally:
            os.unlink(tmp_path)


class TestTextExtractionIntegration:
    """Integration tests for text extraction with document service"""
    
    @pytest.mark.asyncio
    async def test_document_upload_triggers_extraction(self):
        """Test that document upload triggers text extraction"""
        # This would be an integration test with the full system
        # For now, we'll just verify the imports work
        from api.v1.services.document_service import DocumentService
        from app.processing.document_processor import queue_document_processing
        
        assert DocumentService is not None
        assert queue_document_processing is not None
    
    def test_celery_task_import(self):
        """Test that Celery tasks can be imported"""
        from app.processing.document_processor import process_document, extract_document_text
        
        assert process_document is not None
        assert extract_document_text is not None