"""
Task Queue

Implements serial task execution queue.
Enforces LAW 10 — SERIAL EXECUTION: Only one task may execute at a time.

Per DIP Phase 1: Single execution queue, no parallel workers.
"""

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class TaskSource(str, Enum):
    """Source of task request. Per system_schema.json tool_request.source enum."""

    USER_DIRECT = "user_direct"
    """Direct user input (not parsed by AI)."""

    USER_PARSED = "user_parsed"
    """User input parsed by AI intent parser."""

    SCHEDULED = "scheduled"
    """Scheduled event (systemd timer, etc.)."""

    AUTOMATION = "automation"
    """Automation trigger."""


@dataclass
class Task:
    """
    Task representation.

    In Phase 1, this is a skeleton. No actual tool execution yet.
    """

    task_id: UUID
    """Unique task identifier."""

    source: TaskSource
    """Source of the task request."""

    created_at: datetime
    """When the task was created."""

    # Phase 1: Minimal task data
    # In later phases: tool_name, arguments, etc. will be added

    def __post_init__(self) -> None:
        """Validate task data."""
        if self.task_id is None:
            raise ValueError("task_id cannot be None")
        if self.created_at is None:
            raise ValueError("created_at cannot be None")


class TaskQueue:
    """
    Serial task execution queue.

    Enforces LAW 10 — SERIAL EXECUTION:
    - Single execution queue
    - Locking around execution
    - No parallel workers

    Per DIP Phase 1 and LAW 10 enforcement.
    """

    def __init__(self) -> None:
        """Initialize the task queue."""
        self._queue: deque[Task] = deque()
        self._lock = threading.Lock()
        self._current_task: Optional[Task] = None
        self._executing = False

    def enqueue(self, task: Task) -> bool:
        """
        Enqueue a task for execution.

        Args:
            task: Task to enqueue

        Returns:
            True if task was enqueued, False if rejected

        Raises:
            RuntimeError: If queue is in invalid state
        """
        with self._lock:
            # LAW 10: Serial execution - only one task at a time
            if self._executing:
                # Task rejected - another task is executing
                return False

            self._queue.append(task)
            return True

    def dequeue(self) -> Optional[Task]:
        """
        Dequeue the next task for execution.

        Returns:
            Next task to execute, or None if queue is empty

        Raises:
            RuntimeError: If a task is already executing
        """
        with self._lock:
            if self._executing:
                raise RuntimeError(
                    "Cannot dequeue: a task is already executing. "
                    "This violates LAW 10 — SERIAL EXECUTION."
                )

            if not self._queue:
                return None

            task = self._queue.popleft()
            self._current_task = task
            self._executing = True
            return task

    def mark_complete(self) -> None:
        """
        Mark the current task as complete.

        Releases the execution lock, allowing the next task to execute.
        """
        with self._lock:
            if not self._executing:
                raise RuntimeError("No task is currently executing.")

            self._current_task = None
            self._executing = False

    def mark_failed(self) -> None:
        """
        Mark the current task as failed.

        Releases the execution lock, allowing the next task to execute.
        """
        with self._lock:
            if not self._executing:
                raise RuntimeError("No task is currently executing.")

            self._current_task = None
            self._executing = False

    def get_current_task(self) -> Optional[Task]:
        """
        Get the currently executing task.

        Returns:
            Current task, or None if no task is executing
        """
        with self._lock:
            return self._current_task

    def is_executing(self) -> bool:
        """
        Check if a task is currently executing.

        Returns:
            True if a task is executing, False otherwise
        """
        with self._lock:
            return self._executing

    def queue_size(self) -> int:
        """
        Get the number of tasks waiting in the queue.

        Returns:
            Number of queued tasks
        """
        with self._lock:
            return len(self._queue)

    def clear(self) -> None:
        """
        Clear all queued tasks.

        WARNING: Only use this for testing or emergency situations.
        Does not affect the currently executing task.
        """
        with self._lock:
            if self._executing:
                raise RuntimeError(
                    "Cannot clear queue: a task is currently executing. "
                    "Wait for task completion or failure."
                )
            self._queue.clear()
