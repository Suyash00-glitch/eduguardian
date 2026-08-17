"""
Phase 7 Live End-to-End Verification Script  (DEV TOOL — not a pytest test).

Requires all Docker services to be running:
    docker compose up --build

Then run from the repo root:
    python scripts/live_phase7_test.py

This script makes real HTTP calls to the gateway and validates the full
Adaptive Teach Me conversation flow (Levels 0→4 escalation + topic reset).
It is superseded for CI purposes by tests_phase7_regression.py, but remains
useful for interactive manual verification during development.
"""
import asyncio
import httpx
from chatbot.backend.db.session import get_async_session
from chatbot.backend.db.repositories.conversation import ConversationRepository

async def run_live_phase_7_teach_me():
    print("=" * 80)
    print("STARTING LIVE PHASE 7 ADAPTIVE TEACH ME CONVERSATION")
    print("=" * 80)

    client = httpx.Client(timeout=90.0)
    student_id = "student_p7_demo"

    # Cleanup prior conversations
    async with get_async_session() as session:
        conv_repo = ConversationRepository(session)
        for c in await conv_repo.list_conversations(student_id):
            await conv_repo.delete_conversation(c.id)
        await session.commit()

    # TURN 1: User: 'Teach me recursion.'
    print("\n[TURN 1] User: \"Teach me recursion.\"")
    r1 = client.post("http://localhost:8000/api/chat", json={"student_id": student_id, "message": "Teach me recursion."})
    assert r1.status_code == 200
    t1 = r1.json().get("teaching_state")
    reply1 = r1.json().get("message", {}).get("content")
    conv_id = r1.json().get("conversation_id")
    print(f"  Assistant (Level {t1.get('support_level')} - {t1.get('support_strategy')}):\n{reply1}\n")
    assert t1.get("support_level") == 0
    assert t1.get("support_strategy") == "normal"

    # TURN 2: User: "I don't understand."
    print("\n[TURN 2] User: \"I don't understand.\"")
    r2 = client.post("http://localhost:8000/api/chat", json={"student_id": student_id, "conversation_id": conv_id, "message": "I don't understand."})
    assert r2.status_code == 200
    t2 = r2.json().get("teaching_state")
    reply2 = r2.json().get("message", {}).get("content")
    print(f"  Assistant (Level {t2.get('support_level')} - {t2.get('support_strategy')}):\n{reply2}\n")
    assert t2.get("support_level") == 1
    assert t2.get("support_strategy") == "simpler_with_example"

    # TURN 3: User: 'Explain again.'
    print("\n[TURN 3] User: \"Explain again.\"")
    r3 = client.post("http://localhost:8000/api/chat", json={"student_id": student_id, "conversation_id": conv_id, "message": "Explain again."})
    assert r3.status_code == 200
    t3 = r3.json().get("teaching_state")
    reply3 = r3.json().get("message", {}).get("content")
    print(f"  Assistant (Level {t3.get('support_level')} - {t3.get('support_strategy')}):\n{reply3}\n")
    assert t3.get("support_level") == 2
    assert t3.get("support_strategy") == "real_world_analogy"

    # TURN 4: User: "Still don't understand."
    print("\n[TURN 4] User: \"Still don't understand.\"")
    r4 = client.post("http://localhost:8000/api/chat", json={"student_id": student_id, "conversation_id": conv_id, "message": "Still don't understand."})
    assert r4.status_code == 200
    t4 = r4.json().get("teaching_state")
    reply4 = r4.json().get("message", {}).get("content")
    print(f"  Assistant (Level {t4.get('support_level')} - {t4.get('support_strategy')}):\n{reply4}\n")
    assert t4.get("support_level") == 3
    assert t4.get("support_strategy") == "step_by_step_breakdown"

    # TURN 5: User: 'Explain again.'
    print("\n[TURN 5] User: \"Explain again.\"")
    r5 = client.post("http://localhost:8000/api/chat", json={"student_id": student_id, "conversation_id": conv_id, "message": "Explain again."})
    assert r5.status_code == 200
    t5 = r5.json().get("teaching_state")
    reply5 = r5.json().get("message", {}).get("content")
    print(f"  Assistant (Level {t5.get('support_level')} - {t5.get('support_strategy')}):\n{reply5}\n")
    assert t5.get("support_level") == 4
    assert t5.get("support_strategy") == "interactive_micro_teaching"


    # Cleanup
    async with get_async_session() as session:
        conv_repo = ConversationRepository(session)
        for c in await conv_repo.list_conversations(student_id):
            await conv_repo.delete_conversation(c.id)
        await session.commit()

    print("=" * 80)
    print("ALL 5 LIVE TEACH ME PROGRESSION TURNS COMPLETED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_live_phase_7_teach_me())
