from collections import Counter


class MirrorMode:
    """Adapta reflejo usando histórico de acciones de world memory."""

    def infer_style(self, action_buffer: list[str]) -> dict:
        counts = Counter(action_buffer)
        return {
            "aggressive": counts.get("shoot", 0) > counts.get("dash", 0),
            "mobile": counts.get("dash", 0) > 20,
        }
