class PsychologicalProfile:
    def __init__(self):
        self.aggression_score = 0.0
        self.control_score = 0.0
        self.evasion_score = 0.0

    def register_shot(self):
        self.aggression_score += 0.4

    def register_hit_taken(self):
        self.evasion_score -= 0.5

    def register_dash(self):
        self.evasion_score += 0.3

    def register_room_clear(self):
        self.control_score += 0.6

    def final_evaluation(self) -> str:
        if self.control_score > self.aggression_score and self.control_score > self.evasion_score:
            return "SAGE"
        if self.aggression_score >= self.evasion_score:
            return "WARRIOR"
        return "GHOST"
