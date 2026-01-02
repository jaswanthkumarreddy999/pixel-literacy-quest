import random

class Scammer:
    def __init__(self, start_x, start_y):
        self.pos = [start_x, start_y] # [col, row]
        self.name = "Scammer"
        self.color = (200, 50, 50) # Red
    
    def move_randomly(self):
        # Simple AI: Moves 1 step in a random direction
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        
        # Keep inside map bounds (0-9)
        self.pos[0] = max(0, min(9, self.pos[0] + dx))
        self.pos[1] = max(0, min(9, self.pos[1] + dy))