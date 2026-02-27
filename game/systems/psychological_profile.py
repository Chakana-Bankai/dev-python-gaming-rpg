class PsychologicalProfile:
    def __init__(self):
        self.aggression_score = 0.0
        self.control_score = 0.0
        self.evasion_score = 0.0

        self.shots = 0
        self.dashes = 0
        self.hits_taken = 0
        self.rooms_cleared = 0

    def register_shot(self):
        self.shots += 1
        self.aggression_score += 0.18

    def register_hit_taken(self):
        self.hits_taken += 1
        self.control_score -= 0.1
        self.evasion_score -= 0.25

    def register_dash(self):
        self.dashes += 1
        self.evasion_score += 0.28

    def register_room_clear(self):
        self.rooms_cleared += 1
        self.control_score += 0.65

    def final_evaluation(self) -> str:
        # Evaluación más estable: combina scores + métricas de comportamiento.
        aggression = self.aggression_score + self.shots * 0.02
        control = self.control_score + self.rooms_cleared * 0.12 - self.hits_taken * 0.04
        evasion = self.evasion_score + self.dashes * 0.05 - self.hits_taken * 0.03

        top = max(aggression, control, evasion)
        if top == control:
            return "SAGE"
        if top == aggression:
            return "WARRIOR"
        return "GHOST"
