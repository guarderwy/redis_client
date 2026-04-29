from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class KeyInfo:
    key: str
    key_type: str
    ttl: int = -1
    size: Optional[int] = None
    encoding: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "key_type": self.key_type,
            "ttl": self.ttl,
            "size": self.size,
            "encoding": self.encoding,
        }


@dataclass
class KeyValue:
    key: str
    key_type: str
    value: Any
    ttl: int = -1

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "key_type": self.key_type,
            "value": self.value,
            "ttl": self.ttl,
        }


@dataclass
class CommandHistory:
    command: str
    result: Any
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "result": str(self.result) if self.result is not None else None,
            "timestamp": self.timestamp,
            "success": self.success,
            "duration_ms": self.duration_ms,
        }
