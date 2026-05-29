from typing import List

class EnvironmentAdapter:
    """
    Week 1 environment: no-ops, collects logs for audit trail.
    """
    def __init__(self):
        self._logs: List[str] = []

    def log(self, message: str) -> None:
        self._logs.append(str(message))

    def get_logs(self) -> List[str]:
        return list(self._logs)
