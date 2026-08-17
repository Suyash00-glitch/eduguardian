"""
Adaptive Quiz Difficulty Engine for EduGuardian AI.

Provides two-level difficulty adaptation:
1. INITIAL DIFFICULTY:
   - Evaluates topic-specific historical evidence from LearningHistory:
     * Needs practice -> BEGINNER
     * Mastered -> INTERMEDIATE
     * Historical middle-ground -> INTERMEDIATE
     * Fresh / Unknown topic (no history) -> BEGINNER
   - Explicit user requests (e.g. "hard", "easy", "intermediate") override default.
2. WITHIN-QUIZ DIFFICULTY:
   - Evaluates consecutive/recent answers during the active quiz session:
     * Correct -> Gradual level-up (BEGINNER -> INTERMEDIATE -> ADVANCED)
     * Incorrect -> Level-down (ADVANCED -> INTERMEDIATE -> BEGINNER)
     * Incorrect on BEGINNER -> Remain BEGINNER (foundational reinforcement)
     * Correct on ADVANCED -> Remain ADVANCED
"""
from __future__ import annotations

import logging
import re
from typing import Any

from chatbot.backend.schemas.quiz import QuizDifficulty

logger = logging.getLogger(__name__)


def normalize_topic(topic_raw: str | None) -> str:
    """Normalizes topic string for robust cross-turn matching."""
    if not topic_raw:
        return ""
    text = str(topic_raw).strip()
    if not text:
        return ""
    if text.isupper() and len(text) <= 5:
        return text
    words = text.split()
    normalized_words = []
    for w in words:
        if w.upper() in {"DBMS", "SQL", "OS", "OOP", "DSA", "API", "HTML", "CSS", "AI", "ML", "UI", "UX", "REST", "JSON", "JWT"}:
            normalized_words.append(w.upper())
        else:
            normalized_words.append(w.capitalize())
    return " ".join(normalized_words)


def _topic_matches(t1: str, t2: str) -> bool:
    """Case and plural-tolerant topic comparison."""
    n1 = normalize_topic(t1).lower().rstrip("s")
    n2 = normalize_topic(t2).lower().rstrip("s")
    return n1 == n2 or n1 in n2 or n2 in n1


def determine_initial_quiz_difficulty(
    topic: str | None,
    explicit_difficulty: QuizDifficulty | None = None,
    has_explicit_diff: bool = False,
    learning_history: dict[str, Any] | None = None,
) -> QuizDifficulty:
    """
    Determines starting quiz difficulty using explicit request or LearningHistory.

    Rules:
    1. Explicit student request ("hard", "easy", "start with basics") overrides defaults.
    2. Needs-practice topic -> BEGINNER
    3. Mastered topic -> INTERMEDIATE (never automatically starts at ADVANCED)
    4. Historical middle-ground topic -> INTERMEDIATE
    5. Fresh / Unknown topic (no history) -> BEGINNER
    """
    if has_explicit_diff and explicit_difficulty:
        logger.info("AdaptiveQuiz: Explicit difficulty override applied: %s", explicit_difficulty.value)
        return explicit_difficulty

    if not topic or not learning_history or not isinstance(learning_history, dict):
        return QuizDifficulty.BEGINNER

    needs_practice = learning_history.get("needs_practice_topics") or []
    mastered = learning_history.get("mastered_topics") or []
    quiz_mastery = learning_history.get("quiz_mastery") or {}

    # Check needs_practice
    if any(_topic_matches(topic, np) for np in needs_practice):
        logger.info("AdaptiveQuiz: Topic '%s' is in needs_practice -> Initial difficulty: BEGINNER", topic)
        return QuizDifficulty.BEGINNER

    # Check mastered
    if any(_topic_matches(topic, m) for m in mastered):
        logger.info("AdaptiveQuiz: Topic '%s' is in mastered -> Initial difficulty: INTERMEDIATE", topic)
        return QuizDifficulty.INTERMEDIATE

    # Check existing history in quiz_mastery
    if any(_topic_matches(topic, qm_topic) for qm_topic in quiz_mastery.keys()):
        logger.info("AdaptiveQuiz: Topic '%s' has historical record -> Initial difficulty: INTERMEDIATE", topic)
        return QuizDifficulty.INTERMEDIATE

    # Unknown / fresh topic
    logger.info("AdaptiveQuiz: Topic '%s' has no prior history -> Initial difficulty: BEGINNER", topic)
    return QuizDifficulty.BEGINNER


def adapt_quiz_difficulty(
    current_difficulty: QuizDifficulty | str,
    is_correct: bool,
    recent_evaluations: list[bool] | None = None,
) -> QuizDifficulty:
    """
    Adapts quiz question difficulty dynamically based on student's evaluated answer.

    Progression Rules:
    - CORRECT:
      * BEGINNER -> INTERMEDIATE
      * INTERMEDIATE -> ADVANCED
      * ADVANCED -> ADVANCED
    - INCORRECT:
      * ADVANCED -> INTERMEDIATE
      * INTERMEDIATE -> BEGINNER
      * BEGINNER -> BEGINNER (remain foundational, no sub-beginner)
    """
    if isinstance(current_difficulty, QuizDifficulty):
        curr_enum = current_difficulty
    else:
        try:
            curr_enum = QuizDifficulty(str(current_difficulty).lower())
        except ValueError:
            curr_enum = QuizDifficulty.BEGINNER

    if is_correct:
        if curr_enum == QuizDifficulty.BEGINNER:
            return QuizDifficulty.INTERMEDIATE
        elif curr_enum == QuizDifficulty.INTERMEDIATE:
            return QuizDifficulty.ADVANCED
        else:
            return QuizDifficulty.ADVANCED
    else:
        if curr_enum == QuizDifficulty.ADVANCED:
            return QuizDifficulty.INTERMEDIATE
        elif curr_enum == QuizDifficulty.INTERMEDIATE:
            return QuizDifficulty.BEGINNER
        else:
            return QuizDifficulty.BEGINNER
