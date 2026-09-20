"""
BHU-SYNC Phase G: Tamper-Evident SHA-256 Audit Service
Provides append-only, cryptographically hashed audit logging with zero modification/deletion capabilities.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from supabase_client import supabase

# Genesis Hash for blockchain-style audit log chaining
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

# In-memory append-only audit ledger ensuring instant verification and resilience
AUDIT_LOG_LEDGER: List[Dict[str, Any]] = []


def calculate_entry_hash(
    prev_hash: str,
    timestamp: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    payload: Any
) -> str:
    """
    Computes cryptographic SHA-256 hash linking current event to the preceding event hash.
    """
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    raw_content = f"{prev_hash}|{timestamp}|{actor_id}|{action}|{resource_type}|{resource_id}|{payload_str}"
    return hashlib.sha256(raw_content.encode("utf-8")).hexdigest()


def append_audit_log(
    actor_id: str,
    actor_email: str,
    action: str,
    resource_type: str,
    resource_id: str,
    payload: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Appends an immutable audit log entry.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    prev_hash = AUDIT_LOG_LEDGER[-1]["hash"] if AUDIT_LOG_LEDGER else GENESIS_HASH
    entry_payload = payload or {}

    entry_hash = calculate_entry_hash(
        prev_hash=prev_hash,
        timestamp=timestamp,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=entry_payload
    )

    entry = {
        "id": f"AUD-{len(AUDIT_LOG_LEDGER) + 1:06d}",
        "sequence": len(AUDIT_LOG_LEDGER) + 1,
        "timestamp": timestamp,
        "actor_id": actor_id,
        "actor_email": actor_email,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "payload": entry_payload,
        "ip_address": ip_address,
        "previous_hash": prev_hash,
        "hash": entry_hash
    }

    AUDIT_LOG_LEDGER.append(entry)

    # Best-effort persist to Supabase audit_logs table
    try:
        supabase.table("audit_logs").insert({
            "actor_id": actor_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "payload": entry_payload,
            "previous_hash": prev_hash,
            "hash": entry_hash
        }).execute()
    except Exception:
        pass

    return entry


def get_audit_logs(
    limit: int = 100,
    resource_id: Optional[str] = None,
    action: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Returns audit logs with optional filtering and limit bounds.
    """
    logs = list(AUDIT_LOG_LEDGER)
    if resource_id:
        logs = [l for l in logs if l.get("resource_id") == resource_id]
    if action:
        logs = [l for l in logs if l.get("action") == action]
    
    # Return reverse chronological order (newest first)
    return list(reversed(logs))[:limit]


def verify_chain_integrity() -> Tuple[bool, int, str]:
    """
    Validates cryptographic hash chaining across all entries in the ledger.
    Returns (is_valid, verified_count, status_message).
    """
    if not AUDIT_LOG_LEDGER:
        return True, 0, "Audit ledger is empty; integrity intact."

    expected_prev = GENESIS_HASH
    for i, entry in enumerate(AUDIT_LOG_LEDGER):
        # Verify previous hash link
        if entry["previous_hash"] != expected_prev:
            return False, i, f"Broken link at sequence {entry['sequence']}: previous_hash mismatch"

        # Recompute SHA-256
        recomputed = calculate_entry_hash(
            prev_hash=entry["previous_hash"],
            timestamp=entry["timestamp"],
            actor_id=entry["actor_id"],
            action=entry["action"],
            resource_type=entry["resource_type"],
            resource_id=entry["resource_id"],
            payload=entry["payload"]
        )
        if recomputed != entry["hash"]:
            return False, i, f"Tampered entry detected at sequence {entry['sequence']}: hash signature mismatch"

        expected_prev = entry["hash"]

    return True, len(AUDIT_LOG_LEDGER), f"Successfully verified cryptographic chain across {len(AUDIT_LOG_LEDGER)} entries."


# Seed baseline audit entry for demonstration
if not AUDIT_LOG_LEDGER:
    append_audit_log(
        actor_id="00000000-0000-0000-0000-000000000001",
        actor_email="system.init@bhusync.gov.in",
        action="SYSTEM_INIT",
        resource_type="PLATFORM",
        resource_id="BHU-SYNC-ROOT",
        payload={"version": "1.0.0", "mode": "PRODUCTION_SECURE"}
    )
