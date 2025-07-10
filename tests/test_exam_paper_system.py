"""
Comprehensive tests for the exam paper upload and processing system
"""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from services.exam_paper_processor import (
    OCRService,
    PDFProcessor,
    QuestionExtractor,
    SolutionGenerator,
    get_exam_paper_processor,
)
from services.user_collections import (
    get_legal_protection,
    get_sharing_service,
    get_user_collections_service,
)


class TestExamPaperProcessor:
    """Test the main exam paper processing service"""

    @pytest.fixture
    def processor(self):
        return get_exam_paper_processor()

    @pytest.fixture
    def mock_hybrid_ai(self):
        with patch("services.exam_paper_processor.get_hybrid_ai_service") as mock:
            ai_service = MagicMock()
            ai_service.generate_response = AsyncMock()
            mock.return_value = ai_service
            yield ai_service

    @pytest.fixture
    def mock_supabase(self):
        with patch("services.exam_paper_processor.supabase_client") as mock:
            mock.table.return_value.insert.return_value.execute = AsyncMock()
            mock.table.return_value.update.return_value.eq.return_value.execute = (
                AsyncMock()
            )
            yield mock

    @pytest.mark.asyncio
    async def test_process_uploaded_paper_success(
        self, processor, mock_hybrid_ai, mock_supabase
    ):
        """Test successful paper processing"""
        # Mock AI responses
        mock_hybrid_ai.generate_response.return_value.content = json.dumps(
            [
                {
                    "question_text": "What is 2+2?",
                    "question_number": 1,
                    "marks": 2,
                    "answer_text": "4",
                    "topic": "Mathematics",
                    "confidence_score": 0.9,
                }
            ]
        )

        # Mock database operations
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "test-id"}
        ]

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Question 1: What is 2+2? (2 marks)")
            test_file_path = f.name

        try:
            result = await processor.process_uploaded_paper(
                file_path=test_file_path,
                user_id="test-user",
                file_name="test.txt",
                file_size=100,
            )

            assert result["success"] is True
            assert "paper_id" in result
            assert result["questions_count"] > 0

        finally:
            os.unlink(test_file_path)

    @pytest.mark.asyncio
    async def test_process_uploaded_paper_failure(
        self, processor, mock_hybrid_ai, mock_supabase
    ):
        """Test paper processing failure"""
        # Mock AI failure
        mock_hybrid_ai.generate_response.side_effect = Exception("AI service error")

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            test_file_path = f.name

        try:
            result = await processor.process_uploaded_paper(
                file_path=test_file_path,
                user_id="test-user",
                file_name="test.txt",
                file_size=100,
            )

            assert result["success"] is False
            assert "error" in result

        finally:
            os.unlink(test_file_path)


class TestOCRService:
    """Test OCR functionality"""

    @pytest.fixture
    def ocr_service(self):
        return OCRService()

    @pytest.mark.asyncio
    async def test_extract_text_from_image(self, ocr_service):
        """Test text extraction from image"""
        # Create a simple test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Create a simple white image
            img = Image.new("RGB", (100, 50), color="white")
            img.save(f.name)
            test_image_path = f.name

        try:
            # Mock Google Vision API
            with patch(
                "services.exam_paper_processor.vision.ImageAnnotatorClient"
            ) as mock_vision:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.full_text_annotation.text = "Extracted text"
                mock_response.error.message = None
                mock_client.text_detection.return_value = mock_response
                mock_vision.return_value = mock_client

                text = await ocr_service.extract_text(test_image_path)
                assert text == "Extracted text"

        finally:
            os.unlink(test_image_path)


class TestPDFProcessor:
    """Test PDF processing functionality"""

    @pytest.fixture
    def pdf_processor(self):
        return PDFProcessor()

    @pytest.mark.asyncio
    async def test_extract_from_pdf(self, pdf_processor):
        """Test PDF text extraction"""
        # This would require a test PDF file
        # For now, test the method exists
        assert hasattr(pdf_processor, "extract_from_pdf")
        assert asyncio.iscoroutinefunction(pdf_processor.extract_from_pdf)


class TestQuestionExtractor:
    """Test AI question extraction"""

    @pytest.fixture
    def question_extractor(self):
        return QuestionExtractor()

    @pytest.mark.asyncio
    async def test_extract_questions(self, question_extractor):
        """Test question extraction from text"""
        with patch("services.exam_paper_processor.get_hybrid_ai_service") as mock_ai:
            ai_service = MagicMock()
            ai_service.generate_response = AsyncMock()
            ai_service.generate_response.return_value.content = json.dumps(
                [
                    {
                        "question_text": "What is the capital of France?",
                        "question_number": 1,
                        "marks": 1,
                        "answer_text": "Paris",
                        "topic": "Geography",
                        "confidence_score": 0.9,
                    }
                ]
            )
            mock_ai.return_value = ai_service

            text_content = "Question 1: What is the capital of France? (1 mark)"
            questions = await question_extractor.extract_questions(text_content)

            assert len(questions) > 0
            assert questions[0]["question_text"] == "What is the capital of France?"

    @pytest.mark.asyncio
    async def test_parse_extraction_response(self, question_extractor):
        """Test parsing of AI extraction response"""
        response_content = json.dumps(
            [
                {
                    "question_text": "Test question",
                    "question_number": 1,
                    "marks": 2,
                    "answer_text": "Test answer",
                    "topic": "Test topic",
                    "confidence_score": 0.8,
                }
            ]
        )

        questions = question_extractor._parse_extraction_response(response_content)

        assert len(questions) == 1
        assert questions[0]["question_text"] == "Test question"
        assert questions[0]["marks"] == 2


class TestSolutionGenerator:
    """Test AI solution generation"""

    @pytest.fixture
    def solution_generator(self):
        return SolutionGenerator()

    @pytest.mark.asyncio
    async def test_enhance_questions(self, solution_generator):
        """Test question enhancement with AI solutions"""
        with patch("services.exam_paper_processor.get_hybrid_ai_service") as mock_ai:
            ai_service = MagicMock()
            ai_service.generate_response = AsyncMock()
            ai_service.generate_response.return_value.content = "Step-by-step solution"
            mock_ai.return_value = ai_service

            questions = [
                {"question_text": "What is 2+2?", "question_number": 1, "marks": 2}
            ]

            enhanced_questions = await solution_generator.enhance_questions(questions)

            assert len(enhanced_questions) == 1
            assert "ai_solution" in enhanced_questions[0]
            assert "ai_hints" in enhanced_questions[0]


class TestUserCollectionsService:
    """Test user collections functionality"""

    @pytest.fixture
    def collections_service(self):
        return get_user_collections_service()

    @pytest.fixture
    def mock_supabase(self):
        with patch("services.user_collections.supabase_client") as mock:
            mock.table.return_value.insert.return_value.execute = AsyncMock()
            mock.table.return_value.select.return_value.eq.return_value.order.return_value.execute = (
                AsyncMock()
            )
            mock.table.return_value.update.return_value.eq.return_value.execute = (
                AsyncMock()
            )
            mock.table.return_value.delete.return_value.eq.return_value.execute = (
                AsyncMock()
            )
            yield mock

    @pytest.mark.asyncio
    async def test_create_collection(self, collections_service, mock_supabase):
        """Test collection creation"""
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "test-collection-id", "name": "Test Collection"}
        ]

        collection = await collections_service.create_collection(
            user_id="test-user",
            name="Test Collection",
            description="Test description",
            is_public=False,
        )

        assert collection["id"] == "test-collection-id"
        assert collection["name"] == "Test Collection"

    @pytest.mark.asyncio
    async def test_get_user_collections(self, collections_service, mock_supabase):
        """Test fetching user collections"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {"id": "col1", "name": "Collection 1"},
            {"id": "col2", "name": "Collection 2"},
        ]

        collections = await collections_service.get_user_collections("test-user")

        assert len(collections) == 2
        assert collections[0]["name"] == "Collection 1"

    @pytest.mark.asyncio
    async def test_add_questions_to_collection(
        self, collections_service, mock_supabase
    ):
        """Test adding questions to collection"""
        success = await collections_service.add_questions_to_collection(
            collection_id="test-collection", question_ids=["q1", "q2"]
        )

        assert success is True


class TestSharingService:
    """Test sharing functionality"""

    @pytest.fixture
    def sharing_service(self):
        return get_sharing_service()

    @pytest.fixture
    def mock_supabase(self):
        with patch("services.user_collections.supabase_client") as mock:
            mock.table.return_value.insert.return_value.execute = AsyncMock()
            mock.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute = (
                AsyncMock()
            )
            yield mock

    @pytest.mark.asyncio
    async def test_create_share_link(self, sharing_service, mock_supabase):
        """Test share link creation"""
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "share-id"}
        ]

        share_data = await sharing_service.create_share_link(
            collection_id="test-collection", user_id="test-user"
        )

        assert "share_id" in share_data
        assert "share_link" in share_data

    @pytest.mark.asyncio
    async def test_get_shared_collection(self, sharing_service, mock_supabase):
        """Test retrieving shared collection"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "share-id",
            "is_active": True,
            "user_question_collections": {
                "id": "collection-id",
                "name": "Shared Collection",
            },
        }

        collection = await sharing_service.get_shared_collection("share-id")

        assert collection["name"] == "Shared Collection"


class TestLegalProtection:
    """Test legal protection functionality"""

    @pytest.fixture
    def legal_protection(self):
        return get_legal_protection()

    @pytest.fixture
    def mock_supabase(self):
        with patch("services.user_collections.supabase_client") as mock:
            mock.table.return_value.insert.return_value.execute = AsyncMock()
            mock.table.return_value.select.return_value.eq.return_value.gte.return_value.execute = (
                AsyncMock()
            )
            yield mock

    @pytest.mark.asyncio
    async def test_log_upload_agreement(self, legal_protection, mock_supabase):
        """Test logging upload agreement"""
        await legal_protection.log_upload_agreement("test-user", "test-file.pdf")

        # Verify the database call was made
        mock_supabase.table.return_value.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_upload_permissions(self, legal_protection, mock_supabase):
        """Test upload permission validation"""
        # Mock no uploads today
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value.count = (
            0
        )

        can_upload = await legal_protection.validate_upload_permissions("test-user")

        assert can_upload is True

        # Mock 5 uploads today (limit reached)
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value.count = (
            5
        )

        can_upload = await legal_protection.validate_upload_permissions("test-user")

        assert can_upload is False


class TestIntegration:
    """Integration tests for the complete system"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test the complete exam paper upload and processing workflow"""
        # This would test the entire workflow from upload to collection creation
        # For now, we'll test that all services can be instantiated
        processor = get_exam_paper_processor()
        collections_service = get_user_collections_service()
        sharing_service = get_sharing_service()
        legal_protection = get_legal_protection()

        assert processor is not None
        assert collections_service is not None
        assert sharing_service is not None
        assert legal_protection is not None

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling throughout the system"""
        processor = get_exam_paper_processor()

        # Test with invalid file path
        result = await processor.process_uploaded_paper(
            file_path="/nonexistent/file.pdf",
            user_id="test-user",
            file_name="test.pdf",
            file_size=100,
        )

        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__])
