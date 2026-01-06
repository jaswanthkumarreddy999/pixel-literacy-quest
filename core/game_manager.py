import pygame
import random
from config.settings import *
from config.assets import loader
from ui.map_view import MapView
from ui.hud import HUD
from entities.player import Player
from entities.npc import Scammer
from logic.economy import BankSystem

class GameManager:
    def __init__(self, screen, p1_name, p2_name):
        self.screen = screen
        self.running = True
        
        # --- UI & ASSETS ---
        self.bg_image = loader.get("map")
        if self.bg_image:
            self.bg_image = pygame.transform.scale(self.bg_image, (MAP_WIDTH, MAP_HEIGHT))
        
        self.map_view = MapView(screen)
        self.hud = HUD(screen)
        
        # --- ENTITIES ---
        p1_n = p1_name[:12].upper() if p1_name else "PLAYER 1"
        p2_n = p2_name[:12].upper() if p2_name else "PLAYER 2"
        self.players = [Player(1, p1_n, (5, 6)), Player(2, p2_n, (5, 3))]
        self.turn_index = 0
        self.scammer = Scammer([0, 3])
        
        # --- GAME STATE ---
        self.message = "Welcome! Press ENTER to Start."
        self.turn_phase = "START" 
        self.winner = None
        self.selection_mode = None
        self.selection_index = 0
        self.last_click_time = 0
        self.last_clicked_id = None

        # --- BANK & SCAM UI STATE ---
        self.in_bank = False
        self.bank_mode = "MENU"
        self.input_text = ""
        self.temp_fd_amount = 0
        self.scam_active = False
        self.scam_type = None
        self.scam_data = {}
        self.scam_input = ""

        # --- DICE & MOVEMENT ---
        self.dice_vals = [1, 1]
        self.moves_left = 0
        self.dice_rolled = False
        self.dice_visible = False 

        # --- CONFIG DATA ---
        self.locations = BUILDING_LOCATIONS
        self.item_locations = ITEM_LOCATIONS
        self.quiz_questions = QUIZ_QUESTIONS
        
        self.start_new_turn()

    def get_current_player(self):
        return self.players[self.turn_index]

    def start_new_turn(self):
        p = self.get_current_player()
        self.scammer.update_freeze()

        # Health Penalties
        unpaid_count = len(p.pending_needs)
        hp_msg = ""
        if unpaid_count > 0:
            p.health -= unpaid_count
            hp_msg = f"Lost {unpaid_count} HP! "
            
        if p.health <= 0:
            p.health = 0
            self.winner = self.players[(self.turn_index + 1) % 2]
            return

        # Passive Income & Savings
        p.wallet += MONTHLY_INCOME
        if p.bank_balance > 0: 
            p.bank_balance += int(p.bank_balance * SAVINGS_INTEREST)
        
        # FD Check
        if p.fd_timer > 0:
            p.fd_timer -= 1
            if p.fd_timer == 0:
                interest = int(p.fd_balance * p.fd_rate)
                p.bank_balance += (p.fd_balance + interest)
                p.fd_balance = 0
                self.message = f"FD Matured! Gained Rs. {interest} interest."

        # New Tasks
        if p.next_need_index < len(p.game_needs):
            p.pending_needs.append(p.game_needs[p.next_need_index])
            p.next_need_index += 1
        if p.next_want_index < len(p.game_wants):
            p.pending_wants.append(p.game_wants[p.next_want_index])
            p.next_want_index += 1
        
        # Reset Phase
        self.turn_phase, self.in_bank, self.scam_active = "ACTION", False, False
        self.dice_rolled, self.moves_left = False, 0
        self.message = f"{hp_msg}Turn: {p.name}. SPACE to ROLL!"

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_click(event.pos)

            if event.type == pygame.KEYDOWN:
                if self.scam_active:
                    self.handle_scam_input(event)
                    return 
                if self.winner: return
                
                if self.turn_phase == "ACTION":
                    if self.in_bank: self.handle_bank_input(event)
                    elif self.selection_mode: self.handle_selection_input(event)
                    elif not self.dice_rolled and event.key == pygame.K_SPACE:
                        self.roll_dice_animation()
                    else: self.handle_movement_input(event)
                elif self.turn_phase == "END" and event.key == pygame.K_RETURN:
                    self.end_turn()

    # --- DICE ---
    def roll_dice_animation(self):
        self.dice_visible = True
        for _ in range(6):
            self.dice_vals = [random.randint(1, 6), random.randint(1, 6)]
            self.draw(); pygame.display.flip(); pygame.time.delay(80) 
        self.moves_left, self.dice_rolled = sum(self.dice_vals), True
        self.message = f"Rolled {self.moves_left}! Use Arrows to Move."

    # --- MOUSE ---
    def handle_mouse_click(self, pos):
        if self.winner: return
        t = pygame.time.get_ticks()
        is_double = (t - self.last_click_time) < 500

        if self.scam_active and self.hud.close_btn_rect and self.hud.close_btn_rect.collidepoint(pos):
            self.apply_scam_penalty(SCAM_PENALTY_FLEE); self.end_scam(); return

        for region in self.hud.click_regions:
            if region['rect'].collidepoint(pos):
                if region['type'] == 'DICE' and not self.dice_rolled and not self.in_bank:
                    self.roll_dice_animation()
                elif region['type'] == 'SEL' and self.turn_phase == "ACTION":
                    p = self.get_current_player()
                    cid = f"{region['mode']}_{region['idx']}"
                    if is_double and self.last_clicked_id == cid:
                        lst = p.pending_needs if region['mode'] == 'NEEDS' else p.pending_wants
                        if region['idx'] < len(lst):
                            item = lst[region['idx']]
                            if region['mode'] == 'NEEDS': self.pay_specific_need(item)
                            else: self.buy_specific_want(item)
                            self.selection_mode = None
                    else:
                        self.selection_mode, self.selection_index = region['mode'], region['idx']
                    self.last_click_time, self.last_clicked_id = t, cid
                return

    # --- BANK (Uses Economy.py) ---
    def handle_bank_input(self, event):
        p = self.get_current_player()
        if self.bank_mode == "MENU":
            if event.key == pygame.K_1: self.bank_mode, self.input_text, self.message = "DEPOSIT", "", "Amount >"
            elif event.key == pygame.K_2: self.bank_mode, self.input_text, self.message = "WITHDRAW", "", "Amount >"
            elif event.key == pygame.K_3: self.bank_mode, self.input_text, self.message = "FD_AMT", "", "FD Principal >"
            elif event.key == pygame.K_4:
                _, self.message = BankSystem.redeem_fd(p)
            elif event.key == pygame.K_ESCAPE: self.in_bank = False
        else:
            if event.key == pygame.K_ESCAPE: self.bank_mode = "MENU"
            elif event.key == pygame.K_RETURN and self.input_text.isdigit():
                val = int(self.input_text)
                if self.bank_mode == "FD_AMT":
                    self.temp_fd_amount, self.bank_mode, self.input_text, self.message = val, "FD_TURNS", "", "Duration >"
                elif self.bank_mode == "FD_TURNS":
                    _, self.message = BankSystem.create_fd(p, self.temp_fd_amount, val)
                    self.bank_mode = "MENU"
                elif self.bank_mode == "DEPOSIT":
                    _, self.message = BankSystem.deposit(p, val); self.bank_mode = "MENU"
                elif self.bank_mode == "WITHDRAW":
                    _, self.message = BankSystem.withdraw(p, val); self.bank_mode = "MENU"
            elif event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
            elif event.unicode.isdigit(): self.input_text += event.unicode

    # --- SCAM ---
    def trigger_scam_event(self):
        self.scam_active, self.scam_input = True, ""
        if random.random() < 0.5:
            self.scam_type = "OTP"
            self.scam_data = {'digits': [random.randint(1,9) for _ in range(4)], 'idx': 0}
            self.generate_otp_problem()
        else:
            self.scam_type = "QUIZ"
            self.scam_data = {'questions': random.sample(self.quiz_questions, 3), 'q_idx': 0}

    def generate_otp_problem(self):
        target = self.scam_data['digits'][self.scam_data['idx']]
        a = random.randint(0, target)
        self.scam_data['problem'] = f"{a} + {target - a} = ?"
        
    def handle_scam_input(self, event):
        if event.key == pygame.K_ESCAPE:
            self.apply_scam_penalty(SCAM_PENALTY_FLEE); self.end_scam()
        elif event.key == pygame.K_RETURN:
            if self.scam_type == "OTP":
                if self.scam_input == str(self.scam_data['digits'][self.scam_data['idx']]):
                    self.scam_data['idx'] += 1
                    if self.scam_data['idx'] >= 4: self.end_scam()
                    else: self.generate_otp_problem(); self.scam_input = ""
                else: self.apply_scam_penalty(SCAM_PENALTY_OTP); self.end_scam()
            elif self.scam_type == "QUIZ":
                q = self.scam_data['questions'][self.scam_data['q_idx']]
                if q['a'].lower() in self.scam_input.lower():
                    self.scam_data['q_idx'] += 1; self.scam_input = ""
                    if self.scam_data['q_idx'] >= 3: self.end_scam()
                else: self.apply_scam_penalty(SCAM_PENALTY_QUIZ); self.end_scam()
        elif event.key == pygame.K_BACKSPACE: self.scam_input = self.scam_input[:-1]
        else: self.scam_input += event.unicode

    def apply_scam_penalty(self, pct):
        p = self.get_current_player()
        loss = int(p.wallet * pct)
        p.wallet -= loss; self.message = f"SCAMMED! Lost Rs. {loss}!"

    def end_scam(self):
        self.scam_active = False; self.scammer.freeze_timer = SCAM_FREEZE_TURNS

    # --- MOVEMENT ---
    def handle_movement_input(self, event):
        if not self.dice_rolled: return
        d = {pygame.K_LEFT: (-1,0), pygame.K_RIGHT: (1,0), pygame.K_UP: (0,-1), pygame.K_DOWN: (0,1)}
        if event.key in d:
            dx, dy = d[event.key]
            self.move_player(dx, dy)
            self.scammer.move_towards_target(self.players)
            if self.scammer.is_colliding(self.get_current_player().grid_pos): self.trigger_scam_event()
        
        if event.key == pygame.K_e: self.interact_with_building()
        if event.key == pygame.K_RETURN and not self.in_bank: self.turn_phase = "END"; self.message = "Turn Over. ENTER."

    def move_player(self, dx, dy):
        if self.moves_left <= 0: return
        p = self.get_current_player()
        nx, ny = p.grid_pos[0] + dx, p.grid_pos[1] + dy
        if 0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS and MAP_LAYOUT[ny][nx] == 0:
            p.grid_pos = [nx, ny]; self.moves_left -= 1; self.dice_visible = False
            if self.scammer.is_colliding(p.grid_pos): self.trigger_scam_event()

    def interact_with_building(self):
        p = self.get_current_player()
        loc = self.locations.get(tuple(p.grid_pos))
        if loc == "hospital" and p.wallet >= 100:
            p.wallet -= 100; p.health = min(100, p.health + 20); self.message = "Health Restored!"
        elif loc == "bank": self.in_bank, self.bank_mode = True, "MENU"

    # --- TASKS ---
    def handle_selection_input(self, event):
        p = self.get_current_player()
        lst = p.pending_needs if self.selection_mode == 'NEEDS' else p.pending_wants
        if not lst: self.selection_mode = None; return
        if event.key == pygame.K_UP: self.selection_index = max(0, self.selection_index - 1)
        elif event.key == pygame.K_DOWN: self.selection_index = min(len(lst)-1, self.selection_index + 1)
        elif event.key == pygame.K_ESCAPE: self.selection_mode = None
        elif event.key == pygame.K_RETURN:
            item = lst[self.selection_index]
            if self.selection_mode == 'NEEDS': self.pay_specific_need(item)
            else: self.buy_specific_want(item)
            self.selection_mode = None

    def pay_specific_need(self, item):
        p = self.get_current_player()
        name, cost = item
        if self.locations.get(tuple(p.grid_pos)) == self.item_locations.get(name):
            if p.wallet >= cost: p.wallet -= cost; p.pending_needs.remove(item); p.completed_needs.append(name)
            elif p.bank_balance >= cost: p.bank_balance -= cost; p.pending_needs.remove(item); p.completed_needs.append(name)
            self.check_win(p)

    def buy_specific_want(self, item):
        p = self.get_current_player()
        name, cost, happy = item
        if self.locations.get(tuple(p.grid_pos)) == self.item_locations.get(name) and p.wallet >= cost:
            p.wallet -= cost; p.happiness += happy; p.pending_wants.remove(item); p.completed_wants.append(name)
            self.check_win(p)

    def check_win(self, p):
        if len(p.completed_needs) >= 10 and len(p.completed_wants) >= 10: self.winner = p

    def end_turn(self):
        self.turn_index = (self.turn_index + 1) % 2; self.start_new_turn()

    # --- DRAW ---
    def draw(self):
        self.screen.fill(COLORS['menu_bg']) 
        if self.bg_image: self.screen.blit(self.bg_image, (MAP_X, MAP_Y))
        self.map_view.draw([], self.players, self.scammer, self.locations)
        dice = self.dice_vals if self.dice_visible else None
        self.hud.draw(self.players[0], self.players[1], self.turn_index, self.message, self.winner, 
                      self.selection_mode, self.selection_index, self.scam_active, self.scam_type, 
                      self.scam_data, self.scam_input, dice)
    
    def update(self): pass