from typing import List

class Flashcard:
    # Placeholder for the Flashcard model
    pass

class ReviewEngine:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def get_today_review_plan(self, time_available_mins: int = 30) -> List[Flashcard]:
        """
        Returns a personalized list of flashcards to review today.
        Factors in:
        - What's due
        - What was answered incorrectly before
        - What's tied to an upcoming exam
        - How much time the user has today
        """
        # 1. Get all flashcards + their last review data
        # 2. Score them by importance (due, weak, exam-proximity, confidence)
        # 3. Estimate how many can fit in `time_available_mins`
        # 4. Return sorted review list
        pass

    def update_review_result(self, flashcard_id: str, was_correct: bool):
        """
        Logs a review attempt and updates the spaced repetition logic
        (e.g. ease factor, next due date).
        """
        # Update ReviewPerformance DB row
        # Use SM-2 or similar to compute next interval
        pass

    def get_flashcard_confidence(self, flashcard_id: str) -> float:
        """
        Returns an overall confidence level (0-1) for this flashcard.
        Based on past correctness, ease factor, last review date, etc.
        """
        pass 