import pygame
from config.settings import MAP_LAYOUT, GRID_COLS, GRID_ROWS

class Scammer:
    def __init__(self, start_pos):
        self.pos = list(start_pos)
        self.freeze_timer = 0
        self.intent = "CASH" # "CASH" or "DIGITAL"

    def update_freeze(self):
        """Reduces the freeze timer each turn."""
        if self.freeze_timer > 0:
            self.freeze_timer -= 1

    def move_towards_target(self, players, locations):
        """AI: Chases the targeted player based on intent."""
        if self.freeze_timer > 0:
            return 

        # Decide intent randomly each turn if not frozen
        import random
        if random.random() < 0.5:
            self.intent = "CASH"
        else:
            self.intent = "DIGITAL"

        # Target the appropriate player
        p1, p2 = players[0], players[1]
        
        # Don't target players in the bank
        p1_safe = locations.get(tuple(p1.grid_pos)) == "bank"
        p2_safe = locations.get(tuple(p2.grid_pos)) == "bank"
        
        if p1_safe and p2_safe:
            return # Both safe, do nothing
            
        if self.intent == "CASH":
            if p1_safe: target = p2
            elif p2_safe: target = p1
            else: target = p1 if p1.wallet >= p2.wallet else p2
        else:
            if p1_safe: target = p2
            elif p2_safe: target = p1
            else: target = p1 if p1.bank_balance >= p2.bank_balance else p2
        
        sx, sy = self.pos
        tx, ty = target.grid_pos
        
        # Simple chasing logic
        new_x, new_y = sx, sy
        if sx < tx: new_x += 1
        elif sx > tx: new_x -= 1
        elif sy < ty: new_y += 1
        elif sy > ty: new_y -= 1
        
        # Only move if the tile is walkable (0)
        if 0 <= new_x < GRID_COLS and 0 <= new_y < GRID_ROWS:
            if MAP_LAYOUT[new_y][new_x] == 0:
                self.pos = [new_x, new_y]

    def is_colliding(self, player_pos):
        """Checks if the scammer caught the player."""
        return self.pos == player_pos and self.freeze_timer == 0