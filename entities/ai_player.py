"""
ai_player.py — Simple rule-based AI opponent for single-player mode.
"""
import random
from entities.player import Player
from config.settings import AVATAR_COLORS, ITEM_LOCATIONS


class AIPlayer(Player):
    """
    A rule-based AI that makes decisions automatically.
    Strategy priorities:
      1. Pay off needs first (health risk)
      2. Bank money when wallet is above threshold
      3. Buy wants if happiness is low
      4. Quiz: weighted random (70% correct)
    """
    def __init__(self, id, name, start_pos, avatar_color=None):
        super().__init__(id, name, start_pos, avatar_color=avatar_color)
        self.is_ai = True
        self._action_queue = []
        self._action_timer = 0   # frames between AI actions (for visual pacing)
        self.current_destination = None
        self.current_path = []

    # ------------------------------------------------------------------
    # Called by game_manager when it's the AI's turn to pick a location
    # Returns a location_id string or None (stay)
    # ------------------------------------------------------------------
    def choose_location(self, locations, current_needs, current_wants):
        """Return target location id based on priority."""
        # Check if current destination is still valid and not reached
        if self.current_destination:
            # If we are already at the destination, clear it
            if tuple(self.grid_pos) == tuple(self.current_destination):
                self.current_destination = None
                self.current_path = []
            else:
                return self.current_destination
        
        # Priority 1: go to bank if wallet is fat
        if self.wallet > 500:
            bank_locs = [lid for lid, ltype in locations.items() if ltype == 'bank']
            if bank_locs:
                self.current_destination = random.choice(bank_locs)
                return self.current_destination

        # Priority 2: fulfill a need
        if current_needs:
            need_name = current_needs[0][0]
            target_type = ITEM_LOCATIONS.get(need_name)
            if target_type:
                dest = [lid for lid, ltype in locations.items() if ltype == target_type]
                if dest:
                    self.current_destination = random.choice(dest)
                    return self.current_destination

        # Priority 3: wants if happy < 50
        if self.happiness < 50 and current_wants:
            want_name = current_wants[0][0]
            target_type = ITEM_LOCATIONS.get(want_name)
            if target_type:
                dest = [lid for lid, ltype in locations.items() if ltype == target_type]
                if dest:
                    self.current_destination = random.choice(dest)
                    return self.current_destination

        # Default: random move
        if not self.current_destination and locations:
             self.current_destination = random.choice(list(locations.keys()))
        
        return self.current_destination

    def choose_quiz_answer(self, options, correct_answer):
        """70% chance to pick the correct answer."""
        if random.random() < 0.70:
            return correct_answer
        wrong = [o for o in options if o != correct_answer]
        return random.choice(wrong) if wrong else correct_answer

    def choose_otp_response(self):
        """80% chance to refuse (correct behaviour)."""
        return random.random() < 0.80

    def choose_budget_option(self):
        """Randomly pick a budget strategy, slightly preferring savings."""
        return random.choices([0, 1, 2], weights=[0.50, 0.30, 0.20])[0]
