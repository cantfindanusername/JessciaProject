from dataclasses import dataclass, field
from typing import Tuple, Optional, List, Dict
from datetime import datetime
import uuid


@dataclass
class MemoryEntry:
    goal: str
    plan_id: str
    methods_used: Tuple[str,...]
    skills_used: Tuple[str,...]
    executed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    outcome: Optional[str] = None
    confidence: Optional[float] = None

    def add_feedback(self, *, outcome: str, confidence: float) -> None:
        self.outcome = outcome
        self.confidence = confidence


class MemoryStore:
    def __init__(self):
        self._entries: Dict[str, MemoryEntry] = {}

    def store(self, entry: MemoryEntry) -> None:
        self._entries[entry.memory_id] = entry

    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        return self._entries.get(memory_id, None)

    def search_by_goal(self, goal: str) -> List[MemoryEntry]:
        matches: List[MemoryEntry] = []
        for memory in self._entries.values():
            if goal.lower() in memory.goal.lower():
                matches.append(memory)
        return matches

