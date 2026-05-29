from typing import Dict, List, Tuple

class TaskEncoder:
    """
    Toy encoder: one-hot over task_type + a length feature in [0,1].
    """
    def __init__(self, known_types: Tuple[str, ...] = ("text",)):
        self.known_types = tuple(t.lower() for t in known_types)
        self.output_dim = len(self.known_types) + 1  # +1 for text length feature

    def __call__(self, task: Dict) -> List[float]:
        t = str(task.get("task_type", "")).lower()
        one_hot = [1.0 if t == kt else 0.0 for kt in self.known_types]
        text = str(task.get("text", "") or "")
        length_feat = [min(len(text) / 256.0, 1.0)]
        return one_hot + length_feat
