"""Event helpers that do not depend on persistence or an outbox."""

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _canonical(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite Decimal values cannot be event payloads")
        return {"$decimal": str(value)}
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        raise TypeError("float values are not supported in deterministic event data")
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported event value: {type(value).__name__}")


def deterministic_idempotency_key(
    event_type: str,
    object_ref: Any,
    version: int,
    payload_version: int,
    payload: dict[str, Any],
) -> str:
    """Hash canonical event identity and payload into a reproducible key."""
    canonical = _canonical(
        {
            "event_type": event_type,
            "object_ref": object_ref,
            "version": version,
            "payload_version": payload_version,
            "payload": payload,
        }
    )
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"sha256:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"
