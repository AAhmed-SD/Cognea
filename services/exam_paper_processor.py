"""
Exam Paper Processing Service
Handles file uploads, OCR/PDF extraction, AI question processing, and database storage.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any
from uuid import uuid4

# Optional PyPDF2 import
try:
    import PyPDF2
    PDF2_AVAILABLE = True
except ImportError:
    PDF2_AVAILABLE = False
    PyPDF2 = None
from google.cloud import vision

from services.ai.hybrid_ai_service import TaskType, get_hybrid_ai_service
from services.supabase import supabase_client

logger = logging.getLogger(__name__)


class ExamPaperProcessor:
    """Main service for processing uploaded exam papers"""

    def __init__(self):
        self.hybrid_ai = get_hybrid_ai_service()
        self.ocr_service = OCRService()
        self.pdf_processor = PDFProcessor()
        self.question_extractor = QuestionExtractor()
        self.solution_generator = SolutionGenerator()

    async def process_uploaded_paper(
        self, file_path: str, user_id: str, file_name: str, file_size: int
    ) -> dict[str, Any]:
        """Process an uploaded exam paper file"""
        try:
            # Step 1: Create database record
            paper_id = await self._create_paper_record(
                user_id, file_name, file_path, file_size
            )

            # Step 2: Extract text from file
            logger.info(f"Extracting text from {file_path}")
            text_content = await self._extract_text_from_file(file_path)

            if not text_content.strip():
                raise Exception("No text content extracted from file")

            # Step 3: Extract questions using AI
            logger.info("Extracting questions using AI")
            questions = await self.question_extractor.extract_questions(text_content)

            # Step 4: Generate AI solutions
            logger.info("Generating AI solutions")
            enhanced_questions = await self.solution_generator.enhance_questions(
                questions
            )

            # Step 5: Store questions in database
            logger.info("Storing questions in database")
            stored_questions = await self._store_questions(enhanced_questions, paper_id)

            # Step 6: Update paper record
            await self._update_paper_status(
                paper_id, "completed", len(stored_questions)
            )

            return {
                "success": True,
                "paper_id": paper_id,
                "questions_count": len(stored_questions),
                "questions": stored_questions[:5],  # Return first 5 for preview
                "processing_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing paper: {str(e)}")
            if "paper_id" in locals():
                await self._update_paper_status(paper_id, "failed")

            return {"success": False, "error": str(e)}

    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or image file"""
        file_extension = file_path.lower().split(".")[-1]

        if file_extension == "pdf":
            return await self.pdf_processor.extract_from_pdf(file_path)
        elif file_extension in ["jpg", "jpeg", "png", "tiff"]:
            return await self.ocr_service.extract_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    async def _create_paper_record(
        self, user_id: str, file_name: str, file_path: str, file_size: int
    ) -> str:
        """Create a new paper record in the database"""
        paper_id = str(uuid4())

        await supabase_client.table("uploaded_papers").insert(
            {
                "id": paper_id,
                "user_id": user_id,
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "processing_status": "processing",
                "upload_date": datetime.now().isoformat(),
            }
        ).execute()

        return paper_id

    async def _store_questions(
        self, questions: list[dict], paper_id: str
    ) -> list[dict]:
        """Store extracted questions in the database"""
        stored_questions = []

        for i, question in enumerate(questions):
            question_id = str(uuid4())

            # Prepare question data
            question_data = {
                "id": question_id,
                "paper_id": paper_id,
                "question_text": question.get("question_text", ""),
                "answer_text": question.get("answer_text", ""),
                "question_number": question.get("question_number", i + 1),
                "marks": question.get("marks", 1),
                "topic": question.get("topic", ""),
                "difficulty": question.get("difficulty", 2),
                "ai_solution": question.get("ai_solution", ""),
                "ai_hints": question.get("ai_hints", ""),
                "confidence_score": question.get("confidence_score", 0.8),
                "needs_review": question.get("needs_review", False),
                "created_at": datetime.now().isoformat(),
            }

            # Insert into database
            result = (
                await supabase_client.table("extracted_questions")
                .insert(question_data)
                .execute()
            )

            if result.data:
                stored_questions.append(question_data)

        return stored_questions

    async def _update_paper_status(
        self, paper_id: str, status: str, questions_count: int = 0
    ):
        """Update the processing status of a paper"""
        update_data = {
            "processing_status": status,
            "extracted_questions_count": questions_count,
        }

        if status == "completed":
            update_data["ai_enhanced"] = True

        await supabase_client.table("uploaded_papers").update(update_data).eq(
            "id", paper_id
        ).execute()


class OCRService:
    """OCR service for extracting text from images"""

    def __init__(self):
        # Initialize Google Vision API client
        try:
            self.vision_client = vision.ImageAnnotatorClient()
            self.use_google_vision = True
        except Exception as e:
            logger.warning(f"Google Vision not available: {e}")
            self.use_google_vision = False

    async def extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        if self.use_google_vision:
            return await self._extract_with_google_vision(image_path)
        else:
            return await self._extract_with_tesseract(image_path)

    async def _extract_with_google_vision(self, image_path: str) -> str:
        """Extract text using Google Vision API"""
        try:
            with open(image_path, "rb") as image_file:
                content = image_file.read()

            image = vision.Image(content=content)
            response = self.vision_client.text_detection(image=image)

            if response.error.message:
                raise Exception(f"Google Vision OCR failed: {response.error.message}")

            return response.full_text_annotation.text

        except Exception as e:
            logger.error(f"Google Vision OCR error: {e}")
            # Fallback to Tesseract
            return await self._extract_with_tesseract(image_path)

    async def _extract_with_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract OCR (fallback)"""
        try:
            import pytesseract
            from PIL import Image

            # Open image
            image = Image.open(image_path)

            # Extract text
            text = pytesseract.image_to_string(image)

            return text

        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            raise Exception(f"OCR extraction failed: {str(e)}")


class PDFProcessor:
    """PDF text extraction service"""

    async def extract_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        if not PDF2_AVAILABLE:
            raise Exception("PyPDF2 is not available. Please install it with: pip install PyPDF2")
        
        try:
            text_content = ""

            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text_content += f"Page {page_num + 1}:\n{page_text}\n\n"

            return text_content

        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise Exception(f"PDF text extraction failed: {str(e)}")


class QuestionExtractor:
    """AI-powered question extraction service"""

    def __init__(self):
        self.hybrid_ai = get_hybrid_ai_service()

    async def extract_questions(self, text_content: str) -> list[dict[str, Any]]:
        """Extract questions from exam paper text using AI"""
        try:
            # Prepare extraction prompt
            extraction_prompt = self._build_extraction_prompt(text_content)

            # Use hybrid AI to extract questions
            response = await self.hybrid_ai.generate_response(
                task_type=TaskType.EXAM_QUESTION,
                prompt=extraction_prompt,
                user_id="system",
            )

            # Parse the response
            questions = self._parse_extraction_response(response.content)

            # Assess difficulty and topics
            enhanced_questions = await self._enhance_questions(questions)

            return enhanced_questions

        except Exception as e:
            logger.error(f"Question extraction error: {e}")
            raise Exception(f"Question extraction failed: {str(e)}")

    def _build_extraction_prompt(self, text_content: str) -> str:
        """Build the AI prompt for question extraction"""
        return f"""
        Extract all questions from this exam paper text. For each question, provide:
        1. Question text (complete and clear)
        2. Question number (if available)
        3. Marks available (if specified)
        4. Answer (if provided in the text)
        5. Topic/subject area (infer from content)
        
        Format your response as a JSON array with this structure:
        [
            {{
                "question_text": "Complete question text here",
                "question_number": 1,
                "marks": 3,
                "answer_text": "Answer if provided",
                "topic": "Inferred topic",
                "confidence_score": 0.9
            }}
        ]
        
        Exam paper text:
        {text_content[:8000]}  # Limit to first 8000 chars to avoid token limits
        
        Return only valid JSON array.
        """

    def _parse_extraction_response(self, response_content: str) -> list[dict[str, Any]]:
        """Parse the AI response into structured questions"""
        try:
            # Clean the response to extract JSON
            json_match = re.search(r"\[.*\]", response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                questions = json.loads(json_str)
            else:
                # Fallback: try to parse the entire response
                questions = json.loads(response_content)

            # Validate and clean questions
            validated_questions = []
            for q in questions:
                if isinstance(q, dict) and "question_text" in q:
                    validated_questions.append(
                        {
                            "question_text": q.get("question_text", "").strip(),
                            "question_number": q.get("question_number", 0),
                            "marks": q.get("marks", 1),
                            "answer_text": q.get("answer_text", "").strip(),
                            "topic": q.get("topic", "").strip(),
                            "confidence_score": q.get("confidence_score", 0.8),
                        }
                    )

            return validated_questions

        except Exception as e:
            logger.error(f"Failed to parse extraction response: {e}")
            # Return empty list if parsing fails
            return []

    async def _enhance_questions(self, questions: list[dict]) -> list[dict]:
        """Enhance questions with difficulty assessment and topic refinement"""
        enhanced_questions = []

        for question in questions:
            try:
                # Assess difficulty
                difficulty = await self._assess_difficulty(question["question_text"])
                question["difficulty"] = difficulty

                # Refine topic if needed
                if not question.get("topic"):
                    topic = await self._infer_topic(question["question_text"])
                    question["topic"] = topic

                # Mark for review if confidence is low
                if question.get("confidence_score", 0) < 0.7:
                    question["needs_review"] = True

                enhanced_questions.append(question)

            except Exception as e:
                logger.error(f"Error enhancing question: {e}")
                # Add question with default values
                question["difficulty"] = 2
                question["needs_review"] = True
                enhanced_questions.append(question)

        return enhanced_questions

    async def _assess_difficulty(self, question_text: str) -> int:
        """Assess question difficulty using AI"""
        try:
            difficulty_prompt = f"""
            Assess the difficulty of this question on a scale of 1-5:
            1 = Very Easy (basic recall)
            2 = Easy (simple application)
            3 = Medium (standard problem solving)
            4 = Hard (complex analysis)
            5 = Very Hard (advanced synthesis)
            
            Question: {question_text}
            
            Return only the number (1-5).
            """

            response = await self.hybrid_ai.generate_response(
                task_type=TaskType.EXAM_QUESTION,
                prompt=difficulty_prompt,
                user_id="system",
            )

            # Extract number from response
            difficulty_match = re.search(r"\b[1-5]\b", response.content)
            if difficulty_match:
                return int(difficulty_match.group(0))
            else:
                return 3  # Default to medium

        except Exception as e:
            logger.error(f"Difficulty assessment failed: {e}")
            return 3  # Default to medium

    async def _infer_topic(self, question_text: str) -> str:
        """Infer topic from question text using AI"""
        try:
            topic_prompt = f"""
            What is the main topic/subject area of this question?
            
            Question: {question_text}
            
            Return only the topic name (e.g., "Algebra", "Biology", "Chemistry").
            """

            response = await self.hybrid_ai.generate_response(
                task_type=TaskType.EXAM_QUESTION, prompt=topic_prompt, user_id="system"
            )

            return response.content.strip()

        except Exception as e:
            logger.error(f"Topic inference failed: {e}")
            return "General"


class SolutionGenerator:
    """AI solution generation service"""

    def __init__(self):
        self.hybrid_ai = get_hybrid_ai_service()

    async def enhance_questions(self, questions: list[dict]) -> list[dict]:
        """Generate AI solutions and hints for questions"""
        enhanced_questions = []

        for question in questions:
            try:
                # Generate AI solution
                ai_solution = await self._generate_solution(question["question_text"])
                question["ai_solution"] = ai_solution

                # Generate AI hints
                ai_hints = await self._generate_hints(question["question_text"])
                question["ai_hints"] = ai_hints

                enhanced_questions.append(question)

            except Exception as e:
                logger.error(f"Error enhancing question with AI: {e}")
                question["ai_solution"] = ""
                question["ai_hints"] = ""
                enhanced_questions.append(question)

        return enhanced_questions

    async def _generate_solution(self, question_text: str) -> str:
        """Generate step-by-step solution for a question"""
        solution_prompt = f"""
        Provide a detailed step-by-step solution for this question:
        
        {question_text}
        
        Include:
        1. Key concepts and formulas needed
        2. Step-by-step working with explanations
        3. Final answer clearly stated
        4. Alternative methods if applicable
        
        Format the solution clearly with numbered steps.
        """

        response = await self.hybrid_ai.generate_response(
            task_type=TaskType.EXAM_QUESTION, prompt=solution_prompt, user_id="system"
        )

        return response.content.strip()

    async def _generate_hints(self, question_text: str) -> str:
        """Generate helpful hints for a question"""
        hints_prompt = f"""
        Generate 2-3 helpful hints for this question:
        
        {question_text}
        
        Hints should:
        1. Guide the student without giving away the answer
        2. Suggest key concepts to consider
        3. Point to relevant formulas or methods
        
        Format as numbered hints.
        """

        response = await self.hybrid_ai.generate_response(
            task_type=TaskType.EXAM_QUESTION, prompt=hints_prompt, user_id="system"
        )

        return response.content.strip()


# Global instance
_exam_paper_processor = None


def get_exam_paper_processor() -> ExamPaperProcessor:
    """Get the global exam paper processor instance"""
    global _exam_paper_processor
    if _exam_paper_processor is None:
        _exam_paper_processor = ExamPaperProcessor()
    return _exam_paper_processor
