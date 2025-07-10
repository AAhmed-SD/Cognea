"""
AI Study Coach Routes - Core AI features for student productivity and learning
"""

import json
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from models.user import User
from services.ai.context_manager import AdvancedContextManager
from services.ai.openai_service import EnhancedOpenAIService
from services.auth import get_current_user

router = APIRouter(prefix="/api/ai-study-coach", tags=["AI Study Coach"])

# Initialize AI services
openai_service = EnhancedOpenAIService()
context_manager = AdvancedContextManager()


class StudySessionRequest(BaseModel):
    subject: str
    topic: str
    duration_minutes: int = 25
    difficulty_level: str = "medium"  # easy, medium, hard
    learning_style: str = "visual"  # visual, auditory, kinesthetic, reading
    current_knowledge: str = "beginner"  # beginner, intermediate, advanced


class StudyPlanRequest(BaseModel):
    subjects: list[str]
    exam_date: str | None = None
    available_hours_per_day: int = 4
    learning_goals: list[str]


class FlashcardRequest(BaseModel):
    content: str
    subject: str
    difficulty: str = "medium"
    card_type: str = "question_answer"  # question_answer, fill_blank, multiple_choice


class StudySessionResponse(BaseModel):
    session_plan: dict[str, Any]
    study_materials: list[dict[str, Any]]
    practice_questions: list[dict[str, Any]]
    estimated_completion_time: int
    confidence_boost: float


class StudyPlanResponse(BaseModel):
    daily_schedule: list[dict[str, Any]]
    weekly_goals: list[str]
    study_techniques: list[str]
    progress_tracking: dict[str, Any]


# New models for enhanced features
class StudySessionTracking(BaseModel):
    session_id: str
    user_id: str
    subject: str
    topic: str
    start_time: datetime
    end_time: datetime | None = None
    duration_minutes: int
    difficulty_level: str
    learning_style: str
    current_knowledge: str
    progress_percentage: float = 0.0
    confidence_level: float = 0.0
    completed_activities: list[str] = []
    notes: str | None = None
    mood_rating: int | None = None  # 1-10 scale
    energy_level: int | None = None  # 1-10 scale


class StudySessionUpdate(BaseModel):
    progress_percentage: float
    completed_activities: list[str]
    confidence_level: float | None = None
    notes: str | None = None
    mood_rating: int | None = None
    energy_level: int | None = None


class AdaptiveDifficultyRequest(BaseModel):
    session_id: str
    current_performance: float  # 0-100
    time_spent: int  # minutes
    questions_attempted: int
    questions_correct: int
    user_feedback: str | None = None


class StudySessionTemplate(BaseModel):
    name: str
    subject: str
    duration_minutes: int
    difficulty_level: str
    learning_style: str
    activities: list[dict[str, Any]]
    materials_needed: list[str]
    estimated_confidence_boost: float


# In-memory storage for study sessions (in production, use database)
study_sessions = {}
study_templates = {}


@router.post("/create-study-session", response_model=StudySessionResponse)
async def create_study_session(
    request: StudySessionRequest, current_user: User = Depends(get_current_user)
):
    """
    Create a personalized study session based on user preferences and learning style
    """
    try:
        # Build context from user's learning history
        user_context = await context_manager.build_comprehensive_context(
            current_user.id
        )

        # Create study session prompt
        prompt = f"""
        Create a personalized study session for a student with these characteristics:
        - Subject: {request.subject}
        - Topic: {request.topic}
        - Duration: {request.duration_minutes} minutes
        - Difficulty: {request.difficulty_level}
        - Learning Style: {request.learning_style}
        - Current Knowledge: {request.current_knowledge}
        
        User Context: {user_context}
        
        Generate a comprehensive study session that includes:
        1. Session Plan (timeline with activities)
        2. Study Materials (summaries, key concepts, examples)
        3. Practice Questions (with explanations)
        4. Estimated completion time
        5. Confidence boost percentage
        
        Format as JSON with these exact keys: session_plan, study_materials, practice_questions, estimated_completion_time, confidence_boost
        """

        response = await openai_service.generate_response(prompt, temperature=0.7)

        # Parse the response
        try:
            result = json.loads(response)
            return StudySessionResponse(**result)
        except json.JSONDecodeError:
            # Fallback: create structured response
            return StudySessionResponse(
                session_plan={
                    "warm_up": "5 minutes - Review key concepts",
                    "main_study": f"{request.duration_minutes - 10} minutes - Deep dive into {request.topic}",
                    "practice": "5 minutes - Apply knowledge",
                },
                study_materials=[
                    {
                        "type": "summary",
                        "content": f"Key concepts for {request.topic}",
                        "format": (
                            "visual" if request.learning_style == "visual" else "text"
                        ),
                    }
                ],
                practice_questions=[
                    {
                        "question": f"What is the main concept of {request.topic}?",
                        "answer": "Detailed explanation here",
                        "difficulty": request.difficulty_level,
                    }
                ],
                estimated_completion_time=request.duration_minutes,
                confidence_boost=0.15,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create study session: {str(e)}"
        )


@router.post("/start-study-session")
async def start_study_session(
    request: StudySessionRequest, current_user: User = Depends(get_current_user)
):
    """
    Start a new study session with tracking
    """
    try:
        session_id = (
            f"session_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        # Create the study session
        study_session = StudySessionTracking(
            session_id=session_id,
            user_id=current_user.id,
            subject=request.subject,
            topic=request.topic,
            start_time=datetime.now(),
            duration_minutes=request.duration_minutes,
            difficulty_level=request.difficulty_level,
            learning_style=request.learning_style,
            current_knowledge=request.current_knowledge,
        )

        # Store session
        study_sessions[session_id] = study_session.dict()

        # Generate session content
        session_content = await create_study_session(request, current_user)

        return {
            "session_id": session_id,
            "session_data": study_session.dict(),
            "session_content": session_content.dict(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start study session: {str(e)}"
        )


@router.put("/update-study-session/{session_id}")
async def update_study_session(
    session_id: str,
    update: StudySessionUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update study session progress in real-time
    """
    try:
        if session_id not in study_sessions:
            raise HTTPException(status_code=404, detail="Study session not found")

        session = study_sessions[session_id]
        if session["user_id"] != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to update this session"
            )

        # Update session data
        session.update(update.dict(exclude_unset=True))
        study_sessions[session_id] = session

        # Check if session is complete
        if session["progress_percentage"] >= 100:
            session["end_time"] = datetime.now().isoformat()
            session["duration_actual"] = (
                datetime.fromisoformat(session["end_time"])
                - datetime.fromisoformat(session["start_time"])
            ).total_seconds() / 60

        return {"session": session, "message": "Session updated successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update study session: {str(e)}"
        )


@router.post("/adaptive-difficulty/{session_id}")
async def adjust_difficulty(
    session_id: str,
    request: AdaptiveDifficultyRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Adjust difficulty based on real-time performance
    """
    try:
        if session_id not in study_sessions:
            raise HTTPException(status_code=404, detail="Study session not found")

        session = study_sessions[session_id]
        if session["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Calculate performance metrics
        accuracy_rate = request.questions_correct / max(request.questions_attempted, 1)
        time_per_question = request.time_spent / max(request.questions_attempted, 1)

        # Determine difficulty adjustment
        if accuracy_rate > 0.8 and time_per_question < 2:
            # User is performing well - increase difficulty
            new_difficulty = (
                "hard" if session["difficulty_level"] == "medium" else "expert"
            )
            adjustment = "increase"
        elif accuracy_rate < 0.4 or time_per_question > 5:
            # User is struggling - decrease difficulty
            new_difficulty = (
                "easy" if session["difficulty_level"] == "medium" else "medium"
            )
            adjustment = "decrease"
        else:
            # Keep current difficulty
            new_difficulty = session["difficulty_level"]
            adjustment = "maintain"

        # Generate new content with adjusted difficulty
        new_request = StudySessionRequest(
            subject=session["subject"],
            topic=session["topic"],
            duration_minutes=session["duration_minutes"],
            difficulty_level=new_difficulty,
            learning_style=session["learning_style"],
            current_knowledge=session["current_knowledge"],
        )

        new_content = await create_study_session(new_request, current_user)

        return {
            "difficulty_adjustment": adjustment,
            "new_difficulty": new_difficulty,
            "performance_metrics": {
                "accuracy_rate": accuracy_rate,
                "time_per_question": time_per_question,
                "questions_attempted": request.questions_attempted,
            },
            "new_content": new_content.dict(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to adjust difficulty: {str(e)}"
        )


@router.get("/study-analytics/{user_id}")
async def get_study_analytics(
    user_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive study analytics for a user
    """
    try:
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Filter sessions for the user and time period
        cutoff_date = datetime.now() - timedelta(days=days)
        user_sessions = [
            session
            for session in study_sessions.values()
            if session["user_id"] == user_id
            and datetime.fromisoformat(session["start_time"]) >= cutoff_date
        ]

        if not user_sessions:
            return {
                "total_sessions": 0,
                "total_study_time": 0,
                "average_session_length": 0,
                "subjects_studied": [],
                "difficulty_distribution": {},
                "learning_style_preferences": {},
                "progress_trends": [],
                "confidence_trends": [],
                "recommendations": [],
            }

        # Calculate analytics
        total_sessions = len(user_sessions)
        total_study_time = sum(
            session.get("duration_actual", session["duration_minutes"])
            for session in user_sessions
        )
        average_session_length = total_study_time / total_sessions

        # Subject analysis
        subjects_studied = list(set(session["subject"] for session in user_sessions))

        # Difficulty distribution
        difficulty_distribution = {}
        for session in user_sessions:
            difficulty = session["difficulty_level"]
            difficulty_distribution[difficulty] = (
                difficulty_distribution.get(difficulty, 0) + 1
            )

        # Learning style preferences
        learning_style_preferences = {}
        for session in user_sessions:
            style = session["learning_style"]
            learning_style_preferences[style] = (
                learning_style_preferences.get(style, 0) + 1
            )

        # Progress trends (last 7 days)
        progress_trends = []
        confidence_trends = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            day_sessions = [
                session
                for session in user_sessions
                if datetime.fromisoformat(session["start_time"]).date() == date.date()
            ]

            if day_sessions:
                avg_progress = sum(
                    session["progress_percentage"] for session in day_sessions
                ) / len(day_sessions)
                avg_confidence = sum(
                    session.get("confidence_level", 0) for session in day_sessions
                ) / len(day_sessions)
            else:
                avg_progress = 0
                avg_confidence = 0

            progress_trends.append(
                {"date": date.strftime("%Y-%m-%d"), "progress": avg_progress}
            )
            confidence_trends.append(
                {"date": date.strftime("%Y-%m-%d"), "confidence": avg_confidence}
            )

        # Generate AI recommendations
        recommendations = await _generate_study_recommendations(user_sessions)

        return {
            "total_sessions": total_sessions,
            "total_study_time": round(total_study_time, 2),
            "average_session_length": round(average_session_length, 2),
            "subjects_studied": subjects_studied,
            "difficulty_distribution": difficulty_distribution,
            "learning_style_preferences": learning_style_preferences,
            "progress_trends": progress_trends,
            "confidence_trends": confidence_trends,
            "recommendations": recommendations,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get study analytics: {str(e)}"
        )


@router.post("/create-study-template")
async def create_study_template(
    template: StudySessionTemplate, current_user: User = Depends(get_current_user)
):
    """
    Create a reusable study session template
    """
    try:
        template_id = (
            f"template_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        template_data = template.dict()
        template_data["template_id"] = template_id
        template_data["user_id"] = current_user.id
        template_data["created_at"] = datetime.now().isoformat()

        study_templates[template_id] = template_data

        return {
            "template_id": template_id,
            "template": template_data,
            "message": "Study template created successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create study template: {str(e)}"
        )


@router.get("/study-templates/{user_id}")
async def get_study_templates(
    user_id: str, current_user: User = Depends(get_current_user)
):
    """
    Get all study templates for a user
    """
    try:
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        user_templates = [
            template
            for template in study_templates.values()
            if template["user_id"] == user_id
        ]

        return {"templates": user_templates}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get study templates: {str(e)}"
        )


@router.post("/generate-study-plan", response_model=StudyPlanResponse)
async def generate_study_plan(
    request: StudyPlanRequest, current_user: User = Depends(get_current_user)
):
    """
    Generate a comprehensive study plan for multiple subjects
    """
    try:
        # Calculate study days if exam date provided
        study_days = 30  # default
        if request.exam_date:
            exam_date = datetime.strptime(request.exam_date, "%Y-%m-%d")
            study_days = (exam_date - datetime.now()).days

        prompt = f"""
        Create a comprehensive study plan for a student with these requirements:
        - Subjects: {', '.join(request.subjects)}
        - Available hours per day: {request.available_hours_per_day}
        - Study days: {study_days}
        - Learning goals: {', '.join(request.learning_goals)}
        
        Generate a study plan that includes:
        1. Daily schedule (time blocks for each subject)
        2. Weekly goals (specific, measurable objectives)
        3. Study techniques (recommended methods for each subject)
        4. Progress tracking (metrics to measure success)
        
        Format as JSON with these exact keys: daily_schedule, weekly_goals, study_techniques, progress_tracking
        """

        response = await openai_service.generate_response(prompt, temperature=0.7)

        try:
            result = json.loads(response)
            return StudyPlanResponse(**result)
        except json.JSONDecodeError:
            # Fallback response
            return StudyPlanResponse(
                daily_schedule=[
                    {
                        "day": "Monday",
                        "subjects": [
                            {
                                "subject": request.subjects[0],
                                "duration": request.available_hours_per_day // 2,
                            },
                            {
                                "subject": (
                                    request.subjects[1]
                                    if len(request.subjects) > 1
                                    else request.subjects[0]
                                ),
                                "duration": request.available_hours_per_day // 2,
                            },
                        ],
                    }
                ],
                weekly_goals=[
                    f"Complete {subject} review" for subject in request.subjects
                ],
                study_techniques=[
                    "Active recall",
                    "Spaced repetition",
                    "Practice problems",
                ],
                progress_tracking={"daily_quizzes": 0, "concept_mastery": 0.0},
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate study plan: {str(e)}"
        )


@router.post("/generate-flashcards")
async def generate_flashcards(
    request: FlashcardRequest, current_user: User = Depends(get_current_user)
):
    """
    Generate flashcards from content using AI
    """
    try:
        prompt = f"""
        Generate {request.card_type} flashcards from this content:
        
        Content: {request.content}
        Subject: {request.subject}
        Difficulty: {request.difficulty}
        Card Type: {request.card_type}
        
        Create 5-10 flashcards that are:
        - Appropriate for the difficulty level
        - Cover key concepts from the content
        - Include clear explanations
        - Suitable for spaced repetition learning
        
        Format as JSON array with objects containing: question, answer, difficulty, subject, tags
        """

        response = await openai_service.generate_response(prompt, temperature=0.7)

        try:
            flashcards = json.loads(response)
            return {"flashcards": flashcards, "count": len(flashcards)}
        except json.JSONDecodeError:
            # Fallback: create basic flashcards
            return {
                "flashcards": [
                    {
                        "question": f"What is the main topic of {request.subject}?",
                        "answer": "Key concept explanation",
                        "difficulty": request.difficulty,
                        "subject": request.subject,
                        "tags": ["concept", "overview"],
                    }
                ],
                "count": 1,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate flashcards: {str(e)}"
        )


@router.post("/analyze-study-progress")
async def analyze_study_progress(current_user: User = Depends(get_current_user)):
    """
    Analyze user's study progress and provide insights
    """
    try:
        # Get user's study data (this would come from your database)
        user_context = await context_manager.build_comprehensive_context(
            current_user.id
        )

        prompt = f"""
        Analyze this student's study progress and provide insights:
        
        User Context: {user_context}
        
        Provide analysis in JSON format with:
        1. strengths (areas where student excels)
        2. weaknesses (areas needing improvement)
        3. recommendations (specific actions to improve)
        4. study_patterns (observed patterns in study behavior)
        5. predicted_performance (confidence level and predictions)
        
        Be specific and actionable in recommendations.
        """

        response = await openai_service.generate_response(prompt, temperature=0.7)

        try:
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError:
            return {
                "strengths": ["Consistent study habits", "Good time management"],
                "weaknesses": ["Need more practice with complex topics"],
                "recommendations": ["Increase practice time", "Use spaced repetition"],
                "study_patterns": ["Prefers morning study sessions"],
                "predicted_performance": {
                    "confidence": 0.75,
                    "prediction": "Good progress expected",
                },
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze progress: {str(e)}"
        )


@router.post("/create-practice-quiz")
async def create_practice_quiz(
    subject: str = Query(..., description="Subject for the quiz"),
    topic: str = Query(..., description="Specific topic"),
    difficulty: str = Query("medium", description="Quiz difficulty"),
    question_count: int = Query(5, description="Number of questions"),
    current_user: User = Depends(get_current_user),
):
    """
    Create a practice quiz for a specific topic
    """
    try:
        prompt = f"""
        Create a {difficulty} difficulty practice quiz for {subject} - {topic}.
        
        Requirements:
        - {question_count} questions
        - Mix of question types (multiple choice, short answer, true/false)
        - Include explanations for correct answers
        - Progressive difficulty within the quiz
        - Cover key concepts from the topic
        
        Format as JSON with:
        - quiz_title
        - questions (array with question, options, correct_answer, explanation)
        - estimated_time
        - passing_score
        """

        response = await openai_service.generate_response(prompt, temperature=0.7)

        try:
            quiz = json.loads(response)
            return quiz
        except json.JSONDecodeError:
            return {
                "quiz_title": f"{subject} - {topic} Quiz",
                "questions": [
                    {
                        "question": f"What is the main concept of {topic}?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Option A",
                        "explanation": "Detailed explanation here",
                    }
                ],
                "estimated_time": question_count * 2,
                "passing_score": 70,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create quiz: {str(e)}")


@router.post("/get-study-recommendations")
async def get_study_recommendations(current_user: User = Depends(get_current_user)):
    """
    Get personalized study recommendations based on user's learning patterns
    """
    try:
        user_context = await context_manager.build_comprehensive_context(
            current_user.id
        )

        prompt = f"""
        Based on this student's learning context, provide personalized study recommendations:
        
        Context: {user_context}
        
        Provide recommendations in JSON format with:
        1. study_techniques (specific methods to try)
        2. time_management (scheduling suggestions)
        3. focus_areas (subjects/topics to prioritize)
        4. learning_resources (recommended materials)
        5. motivation_tips (ways to stay motivated)
        
        Make recommendations specific and actionable.
        """

        response = await openai_service.generate_response(prompt, temperature=0.7)

        try:
            recommendations = json.loads(response)
            return recommendations
        except json.JSONDecodeError:
            return {
                "study_techniques": [
                    "Pomodoro method",
                    "Active recall",
                    "Spaced repetition",
                ],
                "time_management": [
                    "Study in 25-minute blocks",
                    "Take 5-minute breaks",
                ],
                "focus_areas": ["Prioritize difficult subjects first"],
                "learning_resources": ["Practice problems", "Video tutorials"],
                "motivation_tips": ["Set small daily goals", "Track progress"],
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recommendations: {str(e)}"
        )


async def _generate_study_recommendations(user_sessions: list[dict]) -> list[str]:
    """Generate AI-powered study recommendations based on session data"""
    try:
        if not user_sessions:
            return [
                "Start with short 25-minute study sessions",
                "Focus on one subject at a time",
            ]

        # Analyze patterns
        total_time = sum(
            session.get("duration_actual", session["duration_minutes"])
            for session in user_sessions
        )
        avg_session_length = total_time / len(user_sessions)

        # Generate recommendations based on patterns
        recommendations = []

        if avg_session_length < 20:
            recommendations.append(
                "Consider longer study sessions for better retention"
            )
        elif avg_session_length > 60:
            recommendations.append(
                "Try shorter, more frequent sessions to maintain focus"
            )

        # Subject variety
        subjects = set(session["subject"] for session in user_sessions)
        if len(subjects) < 2:
            recommendations.append("Diversify your study subjects for better learning")

        # Difficulty analysis
        difficulties = [session["difficulty_level"] for session in user_sessions]
        if all(d == "easy" for d in difficulties):
            recommendations.append("Challenge yourself with more difficult topics")
        elif all(d == "hard" for d in difficulties):
            recommendations.append("Include some easier topics to build confidence")

        return recommendations[:5]  # Limit to 5 recommendations

    except Exception:
        return [
            "Continue with your current study routine",
            "Track your progress regularly",
        ]
