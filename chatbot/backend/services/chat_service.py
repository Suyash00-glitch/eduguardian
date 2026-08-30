"""
ChatService — Business Logic and Orchestration Coordinator for Chat API.

Handles:
- Conversation lifecycle (creation, verification, ownership validation)
- Context loading (StudentContext, history, active StudyPlan)
- LangGraph execution and response extraction
- Output persistence and artifact assembly
"""
from __future__ import annotations

from datetime import datetime

import logging
import uuid
from typing import Any
from fastapi import HTTPException, status

from chatbot.backend.db.models import Conversation, Message
from chatbot.backend.db.repositories.conversation import ConversationRepository
from chatbot.backend.db.repositories.student_context import StudentContextRepository
from chatbot.backend.orchestrator.graph import run_graph
from chatbot.backend.orchestrator.state import GraphState
from chatbot.backend.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    MessageRole,
    MessageSchema,
)
from chatbot.backend.schemas.planner import StudyPlan
from chatbot.backend.core.memory import extract_explicit_preference_action

logger = logging.getLogger(__name__)


def _generate_auto_title(text: str) -> str:
    """Generates a clean, readable conversation title from the first message."""
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return "Study Session"
    first_sentence = cleaned.split(".")[0].split("?")[0].split("!")[0].strip()
    if first_sentence and len(first_sentence) <= 45:
        return first_sentence
    if len(cleaned) <= 45:
        return cleaned
    return cleaned[:42].rstrip() + "..."


def _is_student_match(owner_sid: str | None, req_sid: str | None) -> bool:
    """Verifies whether requesting student ID matches the conversation owner, supporting known aliases."""
    if not owner_sid or not req_sid:
        return False
    o = str(owner_sid).strip().lower()
    r = str(req_sid).strip().lower()
    if o == r:
        return True

    # Mohammed Ajmal aliases
    if (o in {"3", "nnm24is127", "nnm24is127@eduguardian.ai"}) and (r in {"3", "nnm24is127", "nnm24is127@eduguardian.ai"}):
        return True
    # Prayag M aliases
    if (o in {"21", "nnm24is172", "9902300115@studentportal.universitysolutions.in"}) and (r in {"21", "nnm24is172", "9902300115@studentportal.universitysolutions.in"}):
        return True
    # Alex Johnson aliases
    if (o in {"1", "1ms21is001", "student@eduguardian.ai"}) and (r in {"1", "1ms21is001", "student@eduguardian.ai"}):
        return True
    return False


def _plan_to_schema(plan: Any) -> StudyPlan | None:
    if plan is None:
        return None
    if isinstance(plan, StudyPlan):
        return plan
    if hasattr(plan, "model_dump"):
        return StudyPlan.model_validate(plan.model_dump())
    if isinstance(plan, dict):
        return StudyPlan.model_validate(plan)
    return None


class ChatService:
    """Service layer encapsulating the entire chat turn lifecycle."""

    def __init__(
        self,
        conv_repo: ConversationRepository,
        context_repo: StudentContextRepository,
    ) -> None:
        self._conv_repo = conv_repo
        self._context_repo = context_repo

    async def send_message(
        self,
        student_id: str,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Executes a single chat turn:
        1. Validates user message content.
        2. Resolves or creates conversation thread and checks student ownership.
        3. Loads student academic context and recent message history.
        4. Loads the latest StudyPlan if present for follow-up adjustments.
        5. Runs the LangGraph Orchestrator.
        6. Persists the user and assistant turns to the database.
        7. Returns the final ChatResponse with natural text and optional structured artifacts.
        """
        # 1. Validation
        msg_text = (request.message or "").strip()
        if not msg_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Message cannot be empty.",
            )

        # 2. Resolve Conversation
        auto_title = _generate_auto_title(msg_text)
        if request.conversation_id:
            conversation = await self._conv_repo.get_conversation(request.conversation_id)
            if not conversation:
                conversation = await self._conv_repo.create_conversation(
                    student_id=student_id,
                    title=auto_title,
                )
            elif not _is_student_match(conversation.student_id, student_id):
                logger.warning(
                    "ChatService: Unauthorized access attempt to conversation=%s by student_id=%s (owner=%s)",
                    conversation.id,
                    student_id,
                    conversation.student_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Conversation belongs to another student.",
                )
            if not conversation.title:
                await self._conv_repo.update_title(conversation.id, auto_title)
                conversation.title = auto_title
        else:
            conversation = await self._conv_repo.create_conversation(
                student_id=student_id,
                title=auto_title,
            )

        conversation_id = conversation.id

        # 3. Load Context, History, Latest Plan & Active Teaching State
        student_context = await self._context_repo.get_context(student_id)
        history_messages = await self._conv_repo.get_history(conversation_id, limit=50)
        history_schemas = [self._conv_repo.to_schema(m) for m in history_messages]

        msg_l = msg_text.lower()
        is_plan_inquiry = any(k in msg_l for k in ["study plan", "schedule", "routine", "roadmap", "plan for", "make me a plan", "create a plan", "give me a plan"])

        latest_plan = await self._conv_repo.get_latest_study_plan(conversation_id) if is_plan_inquiry else None
        latest_teaching_state = await self._conv_repo.get_latest_teaching_state(conversation_id)
        latest_quiz_state = await self._conv_repo.get_latest_quiz_state(conversation_id)
        learning_history = await self._conv_repo.get_learning_history(student_id)
        learning_history_dict = learning_history.model_dump(mode="json") if learning_history else None

        # 4. Build Initial LangGraph State & Execute Workflow
        initial_state: GraphState = {
            "student_id": student_id,
            "user_message": msg_text,
            "conversation_id": str(conversation_id),
            "student_context": student_context,
            "conversation_history": history_schemas,
            "teaching_state": latest_teaching_state,
            "quiz_state": latest_quiz_state,
            "learning_history": learning_history_dict,
            "insight_response": None,
            "plan_response": latest_plan,
            "final_response": None,
            "agents_used": [],
            "intent": "general_support",
            "response_mode": None,       # populated by request_processor
            "conversational_name": None, # populated by request_processor
            "user_facts": None,          # populated by request_processor
            "processed_request": None,   # populated by request_processor
            "constraints": None,         # populated by request_processor
        }

        try:
            result_state = await run_graph(initial_state)
        except Exception as exc:
            logger.error("ChatService: LangGraph execution failed (%s)", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="I'm having trouble processing that right now. Please try again.",
            )

        # 5. Extract Output
        coach_response = result_state.get("final_response")
        if not coach_response:
            logger.error("ChatService: Orchestrator completed without final_response")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="I'm having trouble generating a response right now. Please try again.",
            )

        response_text = coach_response.response_text
        plan_response = result_state.get("plan_response")
        agents_used = result_state.get("agents_used", [])
        new_plan_generated = "study_planner" in agents_used or bool(coach_response and coach_response.has_study_plan)

        # 6. Persist Messages & Structured Artifacts
        structured_payload: dict[str, Any] | None = None
        if plan_response and new_plan_generated:
            structured_payload = plan_response.model_dump(mode="json")
            structured_payload["type"] = "study_plan"
        if coach_response and coach_response.teaching_state:
            if structured_payload is None:
                structured_payload = {}
            structured_payload["teaching_state"] = coach_response.teaching_state
        elif result_state.get("teaching_state"):
            t_st = result_state.get("teaching_state")
            if t_st is not None:
                if structured_payload is None:
                    structured_payload = {}
                structured_payload["teaching_state"] = t_st.model_dump(mode="json") if hasattr(t_st, "model_dump") else t_st

        if coach_response and coach_response.quiz_state:
            if structured_payload is None:
                structured_payload = {}
            structured_payload["quiz_state"] = coach_response.quiz_state
            structured_payload["type"] = "quiz_session"
        elif result_state.get("quiz_state"):
            q_st = result_state.get("quiz_state")
            if q_st is not None:
                if structured_payload is None:
                    structured_payload = {}
                structured_payload["quiz_state"] = q_st.model_dump(mode="json") if hasattr(q_st, "model_dump") else q_st
                structured_payload["type"] = "quiz_session"

        pref_action = extract_explicit_preference_action(msg_text)
        if pref_action:
            if structured_payload is None:
                structured_payload = {}
            structured_payload["preference_action"] = pref_action
            if "type" not in structured_payload:
                structured_payload["type"] = "learning_preference"

        await self._conv_repo.save_user_message(conversation_id, msg_text)
        assistant_msg = await self._conv_repo.save_assistant_message(
            conversation_id=conversation_id,
            content=response_text,
            structured_data=structured_payload,
            agents_used=agents_used,
        )

        # 7. Build Response (strictly sanitize correct_answer so it never leaks)
        study_plan_schema = _plan_to_schema(plan_response) if new_plan_generated else None
        if study_plan_schema:
            try:
                import urllib.request
                sync_url = "http://edu-backend:5000/api/recovery/ai-sync"
                req_data = json.dumps(study_plan_schema.model_dump(mode="json")).encode("utf-8")
                req = urllib.request.Request(
                    sync_url,
                    data=req_data,
                    headers={"Content-Type": "application/json", "X-Internal-Student-Id": str(student_id)}
                )
                urllib.request.urlopen(req, timeout=1.5)
            except Exception as e:
                logger.debug("Background edu-backend sync: %s", e)

        teaching_state_data = structured_payload.get("teaching_state") if structured_payload else None
        raw_quiz_data = structured_payload.get("quiz_state") if structured_payload else None
        quiz_state_data = dict(raw_quiz_data) if isinstance(raw_quiz_data, dict) else None
        if quiz_state_data:
            quiz_state_data.pop("current_correct_answer", None)

        return ChatResponse(
            conversation_id=conversation_id,
            message=MessageSchema(
                id=assistant_msg.id,
                role=MessageRole.ASSISTANT,
                content=response_text,
                created_at=assistant_msg.created_at,
            ),
            study_plan=study_plan_schema,
            teaching_state=teaching_state_data,
            quiz_state=quiz_state_data,
            agents_used=agents_used,
        )

    async def send_message_stream(
        self,
        student_id: str,
        request: ChatRequest,
    ):
        """
        Executes a chat turn and yields Server-Sent Events (SSE) token chunks progressively.
        """
        import asyncio
        import json
        import re
        from chatbot.backend.db.session import AsyncSessionLocal
        from chatbot.backend.db.repositories.conversation import ConversationRepository

        msg_text = (request.message or "").strip()
        if not msg_text:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Message cannot be empty.'})}\n\n"
            return

        async with AsyncSessionLocal() as session:
            conv_repo = ConversationRepository(session)
            try:
                # 1. Resolve Conversation
                auto_title = _generate_auto_title(msg_text)
                if request.conversation_id:
                    conversation = await conv_repo.get_conversation(request.conversation_id)
                    if not conversation:
                        conversation = await conv_repo.create_conversation(
                            student_id=student_id,
                            title=auto_title,
                        )
                    elif not _is_student_match(conversation.student_id, student_id):
                        logger.warning(
                            "ChatService stream: Unauthorized access attempt to conversation=%s by student_id=%s (owner=%s)",
                            conversation.id,
                            student_id,
                            conversation.student_id,
                        )
                        yield f"data: {json.dumps({'type': 'error', 'message': 'Access denied: Conversation belongs to another student.'})}\n\n"
                        return
                    if not conversation.title:
                        await conv_repo.update_title(conversation.id, auto_title)
                        conversation.title = auto_title
                else:
                    conversation = await conv_repo.create_conversation(
                        student_id=student_id,
                        title=auto_title,
                    )

                conversation_id = conversation.id
                # 2. Load Context, History, Latest Plan & Active Teaching State
                student_context = await self._context_repo.get_context(student_id)
                history_messages = await conv_repo.get_history(conversation_id, limit=50)
                history_schemas = [conv_repo.to_schema(m) for m in history_messages]

                msg_l = msg_text.lower()
                is_plan_inquiry = any(k in msg_l for k in ["study plan", "schedule", "routine", "roadmap", "plan for", "make me a plan", "create a plan", "give me a plan"])

                latest_plan = await conv_repo.get_latest_study_plan(conversation_id) if is_plan_inquiry else None
                latest_teaching_state = await conv_repo.get_latest_teaching_state(conversation_id)
                latest_quiz_state = await conv_repo.get_latest_quiz_state(conversation_id)
                learning_history = await conv_repo.get_learning_history(student_id)
                learning_history_dict = learning_history.model_dump(mode="json") if learning_history else None

                # 3. Construct State & Execute Graph
                initial_state: GraphState = {
                    "student_id": student_id,
                    "user_message": msg_text,
                    "conversation_id": str(conversation_id),
                    "student_context": student_context,
                    "conversation_history": history_schemas,
                    "teaching_state": latest_teaching_state,
                    "quiz_state": latest_quiz_state,
                    "learning_history": learning_history_dict,
                    "insight_response": None,
                    "plan_response": latest_plan,
                    "final_response": None,
                    "agents_used": [],
                    "intent": "general_support",
                    "response_mode": None,
                    "conversational_name": None,
                    "user_facts": None,
                    "processed_request": None,
                    "constraints": None,
                }

                from chatbot.backend.orchestrator.graph import run_graph_with_events
                result_state = None
                async for kind, payload in run_graph_with_events(initial_state):
                    if kind == "status":
                        yield f"data: {json.dumps(payload)}\n\n"
                    elif kind == "final_state":
                        result_state = payload

                if not result_state:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'I had trouble processing that. Please try again.'})}\n\n"
                    return

                coach_response = result_state.get("final_response")
                response_text = coach_response.response_text if coach_response else "I am here to help with your academic questions."
                plan_response = result_state.get("plan_response")
                agents_used = result_state.get("agents_used", [])
                new_plan_generated = "study_planner" in agents_used or bool(coach_response and coach_response.has_study_plan)

                # 4. Persist turns in PostgreSQL & commit
                structured_payload: dict[str, Any] | None = None
                if plan_response and new_plan_generated:
                    structured_payload = plan_response.model_dump(mode="json")
                    structured_payload["type"] = "study_plan"
                if coach_response and coach_response.teaching_state:
                    if structured_payload is None:
                        structured_payload = {}
                    structured_payload["teaching_state"] = coach_response.teaching_state
                elif result_state.get("teaching_state"):
                    t_st = result_state.get("teaching_state")
                    if t_st is not None:
                        if structured_payload is None:
                            structured_payload = {}
                        structured_payload["teaching_state"] = t_st.model_dump(mode="json") if hasattr(t_st, "model_dump") else t_st

                if coach_response and coach_response.quiz_state:
                    if structured_payload is None:
                        structured_payload = {}
                    structured_payload["quiz_state"] = coach_response.quiz_state
                    structured_payload["type"] = "quiz_session"
                elif result_state.get("quiz_state"):
                    q_st = result_state.get("quiz_state")
                    if q_st is not None:
                        if structured_payload is None:
                            structured_payload = {}
                        structured_payload["quiz_state"] = q_st.model_dump(mode="json") if hasattr(q_st, "model_dump") else q_st
                        structured_payload["type"] = "quiz_session"

                pref_action = extract_explicit_preference_action(msg_text)
                if pref_action:
                    if structured_payload is None:
                        structured_payload = {}
                    structured_payload["preference_action"] = pref_action
                    if "type" not in structured_payload:
                        structured_payload["type"] = "learning_preference"

                await conv_repo.save_user_message(conversation_id, msg_text)
                assistant_msg = await conv_repo.save_assistant_message(
                    conversation_id=conversation_id,
                    content=response_text,
                    structured_data=structured_payload,
                    agents_used=agents_used,
                )
                await session.commit()

                study_plan_schema = _plan_to_schema(plan_response) if new_plan_generated else None
                if study_plan_schema:
                    try:
                        import urllib.request
                        sync_url = "http://edu-backend:5000/api/recovery/ai-sync"
                        req_data = json.dumps(study_plan_schema.model_dump(mode="json")).encode("utf-8")
                        req = urllib.request.Request(
                            sync_url,
                            data=req_data,
                            headers={"Content-Type": "application/json", "X-Internal-Student-Id": str(student_id)}
                        )
                        urllib.request.urlopen(req, timeout=1.5)
                    except Exception as e:
                        logger.debug("Background edu-backend sync in stream: %s", e)

                teaching_state_data = structured_payload.get("teaching_state") if structured_payload else None
                raw_quiz_data = structured_payload.get("quiz_state") if structured_payload else None
                quiz_state_data = dict(raw_quiz_data) if isinstance(raw_quiz_data, dict) else None
                if quiz_state_data:
                    quiz_state_data.pop("current_correct_answer", None)

                # 5. Yield progressive tokens
                words = re.findall(r"\S+|\s+", response_text)
                for w in words:
                    yield f"data: {json.dumps({'type': 'chunk', 'text': w})}\n\n"
                    await asyncio.sleep(0.012)

                # 6. Yield metadata and done
                created_at_iso = assistant_msg.created_at.isoformat() if hasattr(assistant_msg, "created_at") and assistant_msg.created_at else datetime.utcnow().isoformat() + "Z"
                meta_event = {
                    "type": "meta",
                    "conversation_id": str(conversation_id),
                    "message_id": str(assistant_msg.id),
                    "created_at": created_at_iso,
                    "study_plan": study_plan_schema.model_dump(mode="json") if study_plan_schema else None,
                    "teaching_state": teaching_state_data,
                    "quiz_state": quiz_state_data,
                    "agents_used": agents_used,
                }
                yield f"data: {json.dumps(meta_event)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                await session.rollback()
                logger.error("ChatService stream: Error occurred during streaming (%s)", e, exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': 'An unexpected error occurred. Please try again.'})}\n\n"


    async def get_history(
        self,
        student_id: str,
        conversation_id: uuid.UUID,
        limit: int = 50,
    ) -> ConversationHistoryResponse:
        """Fetches chronological message history for a conversation after verifying ownership."""
        conversation = await self._conv_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' was not found.",
            )
        if not _is_student_match(conversation.student_id, student_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation thread.",
            )

        messages = await self._conv_repo.get_history(conversation_id, limit=limit)
        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=[self._conv_repo.to_schema(m) for m in messages],
            created_at=conversation.created_at,
        )

    async def list_conversations(self, student_id: str) -> list[dict[str, Any]]:
        """Returns metadata for all conversations owned by the student."""
        convs = await self._conv_repo.list_conversations(student_id)
        return [
            {
                "conversation_id": str(c.id),
                "student_id": c.student_id,
                "title": c.title,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in convs
        ]

    async def delete_conversation(self, student_id: str, conversation_id: uuid.UUID) -> dict[str, Any]:
        """Deletes a conversation thread owned by the student."""
        success = await self._conv_repo.delete_conversation(conversation_id, student_id=student_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found or access denied.",
            )
        return {"status": "deleted", "conversation_id": str(conversation_id)}

    async def rename_conversation(
        self,
        student_id: str,
        conversation_id: uuid.UUID,
        new_title: str,
    ) -> dict[str, Any]:
        """Renames a conversation title after verifying student ownership."""
        conversation = await self._conv_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' was not found.",
            )
        if not _is_student_match(conversation.student_id, student_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation thread.",
            )
        title = new_title.strip()[:80] or "Study Session"
        await self._conv_repo.update_title(conversation_id, title)
        return {"status": "renamed", "conversation_id": str(conversation_id), "title": title}
