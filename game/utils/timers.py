class Cooldown:
    def __init__(self, duration: float = 0.0):
        self.duration = duration
        self.value = 0.0

    def start(self, duration: float | None = None):
        self.value = self.duration if duration is None else duration

    def update(self, dt: float):
        self.value = max(0.0, self.value - dt)

    @property
    def ready(self) -> bool:
        return self.value <= 0.0
