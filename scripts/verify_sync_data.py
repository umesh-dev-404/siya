
import sys
import os
import uuid
import datetime
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sync.sync_manager import get_sync_manager
from sync.sync_queue import OperationType

def main():
    print("Initializing Sync Manager...")
    try:
        sm = get_sync_manager()
    except Exception as e:
        print(f"Failed to init Sync Manager: {e}")
        return

    record_id = str(uuid.uuid4())
    payload = {
        "content": "TEST_MEMORY_ENTRY_FOR_SYNC_VERIFICATION",
        "created_at": datetime.datetime.now().isoformat(),
        "tags": ["test", "verification"],
        "confidence": 1.0,
        "source": "manual_verification_script"
    }

    print(f"Queueing fake memory record {record_id}...")
    try:
        q_id = sm.queue_for_sync(
            item_type=OperationType.INSERT,
            table_name="memory",
            record_id=record_id,
            payload=payload
        )
        print(f"Queued successfully. Queue ID: {q_id}")
    except Exception as e:
        print(f"Failed to queue: {e}")
        return

    print("Checking sync status...")
    status = sm.get_sync_status()
    print(f"Queue Pending: {status['queue']['pending']}")

    print("\nRun 'siya-cli ... call trigger_sync --args \"{\\\"direction\\\": \\\"push\\\"}\"' to push this record.")

if __name__ == "__main__":
    main()
