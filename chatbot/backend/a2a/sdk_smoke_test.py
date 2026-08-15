"""Smoke test for a2a-sdk API patterns — corrected for a2a-sdk==1.1.2."""
import asyncio
from a2a.types import Message, Part, Role, TaskStatusUpdateEvent, TaskState, TaskStatus
from a2a.server.events import EventQueueLegacy  # EventQueue direct instantiation is deprecated


async def test():
    # Fix 1: Use EventQueueLegacy instead of EventQueue() directly
    eq = EventQueueLegacy()

    msg = Message(role=Role.ROLE_AGENT, parts=[Part(text="hello")])
    await eq.enqueue_event(msg)
    print("EventQueueLegacy.enqueue_event(Message) OK")

    # Fix 2: TaskStatusUpdateEvent has no 'final' field in a2a-sdk==1.1.2
    # Valid fields: task_id, context_id, status, metadata
    status_evt = TaskStatusUpdateEvent(
        task_id="t1",
        context_id="c1",
        status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
        # 'final=True' does NOT exist — removed
    )
    await eq.enqueue_event(status_evt)
    print("EventQueueLegacy.enqueue_event(TaskStatusUpdateEvent) OK")

    print("\nAll SDK smoke tests passed.")


asyncio.run(test())
