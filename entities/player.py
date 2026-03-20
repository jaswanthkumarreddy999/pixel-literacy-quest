import pygame
import random
from config.settings import COLORS, STARTING_WALLET, STARTING_BANK, GAME_NEEDS, GAME_WANTS

class Player:
    def __init__(self, id, name, start_pos, avatar_color=None):
        self.id = id
        self.name = name
        self.grid_pos = list(start_pos)
        self.avatar_color = avatar_color or COLORS['p1_bg']
        self.is_ai = False

        
        # Financial & Game Stats
        self.wallet = STARTING_WALLET       
        self.bank_balance = STARTING_BANK   
        self.loan = 0
        self.loan_timer = 0
        self.fd_balance = 0
        self.fd_timer = 0
        self.fd_rate = 0.0
        
        # Status
        self.health = 100       
        self.happiness = 0
        self.inventory = [] 
        self.seen_popups = set()
        
        # Task Management
        self.next_need_index = 0
        self.next_want_index = 0
        self.pending_needs = [] 
        self.pending_wants = []
        self.completed_needs = []
        self.completed_wants = []
        
        # Shuffle game items for this specific player
        self.game_needs = list(GAME_NEEDS)
        self.game_wants = list(GAME_WANTS)
        random.shuffle(self.game_needs)
        random.shuffle(self.game_wants)

    def get_total_wealth(self):
        """Helper method to calculate player worth."""
        return self.wallet + self.bank_balance + self.fd_balance - self.loan