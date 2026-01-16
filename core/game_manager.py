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
        self.finisher = None # Tracks who hit 20/20 first
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

        # --- DATA ---
        self.locations = BUILDING_LOCATIONS
        self.item_locations = ITEM_LOCATIONS
        self.quiz_questions = QUIZ_QUESTIONS
        
        self.start_new_turn()

    def get_current_player(self):
        return self.players[self.turn_index]

    def calculate_score(self, player):
        """Calculates score using strategic weights from settings."""
        wealth = player.wallet + player.bank_balance + player.fd_balance
        tasks = len(player.completed_needs) + len(player.completed_wants)
        
        score = (wealth / SCORE_WEALTH_DIVIDER) + \
                (player.health * SCORE_HEALTH_MULTIPLIER) + \
                (tasks * SCORE_TASK_MULTIPLIER)
        
        # Add completion bonus if this player was the one who finished first
        if self.finisher == player:
            score += SCORE_FINISH_BONUS
            
        return int(score)

    def check_win(self, p):
        """Triggered when a player completes all 20 tasks."""
        if len(p.completed_needs) >= 10 and len(p.completed_wants) >= 10:
            self.finisher = p # Award the bonus to this player
            
            # Compare final scores to decide actual winner
            s1 = self.calculate_score(self.players[0])
            s2 = self.calculate_score(self.players[1])
            
            if s1 > s2:
                self.winner = self.players[0]
            elif s2 > s1:
                self.winner = self.players[1]
            else:
                self.winner = p # Tie-breaker
            
            self.message = f"GAME OVER! {p.name} FINISHED!"

    def start_new_turn(self):
        p = self.get_current_player()
        self.scammer.update_freeze()

        # HP Penalty for unpaid needs
        unpaid_count = len(p.pending_needs)
        hp_msg = ""
        if unpaid_count > 0:
            p.health -= unpaid_count
            hp_msg = f"Lost {unpaid_count} HP! "
        
        if p.health <= 0:
            p.health = 0
            self.winner = self.players[(self.turn_index + 1) % 2]
            return

        p.wallet += MONTHLY_INCOME
        if p.bank_balance > 0: 
            p.bank_balance += int(p.bank_balance * SAVINGS_INTEREST)
        
        if p.next_need_index < len(p.game_needs):
            p.pending_needs.append(p.game_needs[p.next_need_index])
            p.next_need_index += 1
        if p.next_want_index < len(p.game_wants):
            p.pending_wants.append(p.game_wants[p.next_want_index])
            p.next_want_index += 1
        
        self.turn_phase = "ACTION"
        self.in_bank = False
        self.scam_active = False
        self.dice_rolled = False
        self.moves_left = 0
        self.selection_mode = None
        self.message = f"{hp_msg}Turn: {p.name}. SPACE to ROLL!"

    def handle_input(self, events):
        for event in events:
            if self.winner:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.running = False 
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_click(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.in_bank = False
                    self.selection_mode = None
                    if self.scam_active: self.end_scam()
                    return

                if self.scam_active:
                    self.handle_scam_input(event)
                    return 
                
                if self.turn_phase == "ACTION":
                    if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                        if self.in_bank: self.in_bank = False
                        self.handle_movement_input(event)
                    elif event.key == pygame.K_e:
                        self.toggle_bank()
                    elif self.in_bank:
                        self.handle_bank_input(event)
                    elif not self.dice_rolled and event.key == pygame.K_SPACE:
                        self.roll_dice_animation()
                    elif event.key == pygame.K_RETURN:
                        self.turn_phase = "END"
                        self.message = "Turn Finished. Press ENTER."
                        
                elif self.turn_phase == "END" and event.key == pygame.K_RETURN:
                    self.end_turn()

    def end_turn(self):
        p = self.get_current_player()
        self.check_win(p)

        if p.fd_balance > 0 and p.fd_timer > 0:
            p.fd_timer -= 1
            if p.fd_timer == 0: self.message = f"FD MATURED for {p.name}!"

        self.in_bank = False
        self.selection_mode = None
        
        if not self.winner:
            self.turn_index = (self.turn_index + 1) % 2
            self.start_new_turn()

    def toggle_bank(self):
        p = self.get_current_player()
        if self.locations.get(tuple(p.grid_pos)) == "bank":
            if not self.in_bank:
                self.in_bank, self.bank_mode = True, "MENU"
                self.message = "Bank: 1:Dep, 2:With, 3:FD, 4:Redeem"
            else:
                self.in_bank = False
                self.message = "Exited Bank."
        else: self.message = "Go to the Bank tile!"

    def handle_mouse_click(self, pos):
        if self.winner or self.scam_active or self.in_bank: return
        t = pygame.time.get_ticks()
        is_double = (t - self.last_click_time) < 500
        for region in self.hud.click_regions:
            if region['rect'].collidepoint(pos):
                p = self.get_current_player()
                cid = f"{region['mode']}_{region['idx']}"
                if is_double and self.last_clicked_id == cid:
                    lst = p.pending_needs if region['mode'] == 'NEEDS' else p.pending_wants
                    if region['idx'] < len(lst):
                        item = lst[region['idx']]
                        if region['mode'] == 'NEEDS': self.pay_specific_need(item)
                        else: self.buy_specific_want(item)
                else:
                    self.selection_mode = region['mode']
                    self.selection_index = region['idx']
                self.last_click_time, self.last_clicked_id = t, cid

    def handle_movement_input(self, event):
        if not self.dice_rolled: return
        if self.moves_left > 0:
            d = {pygame.K_LEFT: (-1,0), pygame.K_RIGHT: (1,0), pygame.K_UP: (0,-1), pygame.K_DOWN: (0,1)}
            if event.key in d:
                dx, dy = d[event.key]
                self.move_player(dx, dy)
                self.scammer.move_towards_target(self.players)
        else: self.message = "Press ENTER to end turn."

    def move_player(self, dx, dy):
        p = self.get_current_player()
        nx, ny = p.grid_pos[0] + dx, p.grid_pos[1] + dy
        if 0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS and MAP_LAYOUT[ny][nx] == 0:
            p.grid_pos = [nx, ny]
            self.moves_left -= 1
            self.dice_visible = False
            if self.scammer.is_colliding(p.grid_pos): 
                self.trigger_scam_event()
                return
            loc = self.locations.get(tuple(p.grid_pos))
            self.message = f"At {loc.title()}." if loc else f"Moves: {self.moves_left}"

    def pay_specific_need(self, item):
        p = self.get_current_player()
        name, cost = item
        if self.locations.get(tuple(p.grid_pos)) == self.item_locations.get(name):
            if p.wallet >= cost:
                p.wallet -= cost
                p.pending_needs.remove(item); p.completed_needs.append(name)
                self.message = f"Paid {name}!"
            elif p.bank_balance >= cost:
                p.bank_balance -= cost
                p.pending_needs.remove(item); p.completed_needs.append(name)
                self.message = f"Paid {name} (Bank)!"
            else: self.message = "Not enough money!"
        else: self.message = f"Go to {self.item_locations.get(name)}!"

    def buy_specific_want(self, item):
        p = self.get_current_player()
        name, cost, happy = item
        if self.locations.get(tuple(p.grid_pos)) == self.item_locations.get(name):
            if p.wallet >= cost:
                p.wallet -= cost; p.happiness += happy
                p.pending_wants.remove(item); p.completed_wants.append(name)
                self.message = f"Bought {name}!"
            else: self.message = "Need cash!"
        else: self.message = f"Go to {self.item_locations.get(name)}!"

    def handle_bank_input(self, event):
        p = self.get_current_player()
        if self.bank_mode == "MENU":
            if event.key == pygame.K_1: self.bank_mode, self.input_text = "DEPOSIT", ""
            elif event.key == pygame.K_2: self.bank_mode, self.input_text = "WITHDRAW", ""
            elif event.key == pygame.K_3: self.bank_mode, self.input_text = "FD_AMT", ""
            elif event.key == pygame.K_4: 
                _, m = BankSystem.redeem_fd(p)
                self.message, self.bank_mode = m, "MENU"
        else:
            if event.key == pygame.K_RETURN and self.input_text.isdigit():
                val = int(self.input_text)
                if self.bank_mode == "FD_AMT": self.temp_fd_amount, self.bank_mode, self.input_text = val, "FD_TURNS", ""
                elif self.bank_mode == "FD_TURNS": 
                    _, m = BankSystem.create_fd(p, self.temp_fd_amount, val)
                    self.message, self.bank_mode = m, "MENU"
                elif self.bank_mode == "DEPOSIT": 
                    _, m = BankSystem.deposit(p, val)
                    self.message, self.bank_mode = m, "MENU"
                elif self.bank_mode == "WITHDRAW": 
                    _, m = BankSystem.withdraw(p, val)
                    self.message, self.bank_mode = m, "MENU"
            elif event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
            elif event.unicode.isdigit(): self.input_text += event.unicode

    def roll_dice_animation(self):
        self.dice_visible = True
        for _ in range(6):
            self.dice_vals = [random.randint(1, 6), random.randint(1, 6)]
            self.draw(); pygame.display.flip(); pygame.time.delay(80) 
        self.moves_left, self.dice_rolled = sum(self.dice_vals), True

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
        if event.key == pygame.K_ESCAPE: self.apply_scam_penalty(SCAM_PENALTY_FLEE); self.end_scam()
        elif event.key == pygame.K_RETURN:
            if self.scam_type == "OTP":
                if self.scam_input == str(self.scam_data['digits'][self.scam_data['idx']]):
                    self.scam_data['idx'] += 1
                    if self.scam_data['idx'] >= 4: self.end_scam()
                    else: self.generate_otp_problem(); self.scam_input = ""
                else: self.apply_scam_penalty(SCAM_PENALTY_OTP); self.end_scam()
            elif self.scam_type == "QUIZ":
                q = self.scam_data['questions'][self.scam_data['q_idx']]
                if self.scam_input.strip().lower() == q['a'].lower():
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

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(245); overlay.fill((10, 15, 25))
        self.screen.blit(overlay, (0, 0))

        font_l = pygame.font.SysFont("Arial", 60, bold=True)
        font_s = pygame.font.SysFont("Arial", 28)

        # Champion Banner
        title = font_l.render(f"CHAMPION: {self.winner.name}", True, (255, 215, 0))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 100)))

        # Score Breakdown Table
        stats = [
            ("TOTAL WEALTH", f"Rs {self.players[0].wallet + self.players[0].bank_balance}", f"Rs {self.players[1].wallet + self.players[1].bank_balance}"),
            ("TASKS (150pt ea)", f"{len(self.players[0].completed_needs)+len(self.players[0].completed_wants)}/20", f"{len(self.players[1].completed_needs)+len(self.players[1].completed_wants)}/20"),
            ("SURVIVAL (HP)", f"{self.players[0].health} HP", f"{self.players[1].health} HP"),
            ("FINISH BONUS", f"+{SCORE_FINISH_BONUS if self.finisher == self.players[0] else 0}", f"+{SCORE_FINISH_BONUS if self.finisher == self.players[1] else 0}"),
            ("FINAL SCORE", str(self.calculate_score(self.players[0])), str(self.calculate_score(self.players[1])))
        ]

        y_off = 220
        self.screen.blit(font_s.render(self.players[0].name, True, (255,100,100)), (450, y_off))
        self.screen.blit(font_s.render(self.players[1].name, True, (100,100,255)), (750, y_off))

        for idx, (label, p1, p2) in enumerate(stats):
            y = y_off + 60 + (idx * 50)
            color = (0, 255, 120) if "FINAL" in label else (200, 200, 200)
            self.screen.blit(font_s.render(label, True, (150, 150, 150)), (150, y))
            self.screen.blit(font_s.render(p1, True, color), (450, y))
            self.screen.blit(font_s.render(p2, True, color), (750, y))

        msg = font_s.render("Press ENTER to return to Main Menu", True, (255, 255, 0))
        self.screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80)))

    def draw(self):
        self.screen.fill(COLORS['menu_bg']) 
        if self.bg_image: self.screen.blit(self.bg_image, (MAP_X, MAP_Y))
        self.map_view.draw([], self.players, self.scammer, self.locations)
        
        if self.in_bank and self.bank_mode != "MENU":
            overlay = pygame.Surface((500, 100))
            overlay.set_alpha(200); overlay.fill((0, 0, 0))
            rect = overlay.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(overlay, rect)
            font = pygame.font.SysFont("Arial", 28, bold=True)
            txt = font.render(f"{self.bank_mode}: {self.input_text}_", True, (255, 255, 0))
            self.screen.blit(txt, txt.get_rect(center=rect.center))
            
        dice = self.dice_vals if self.dice_visible else None
        self.hud.draw(self.players[0], self.players[1], self.turn_index, self.message, self.winner, 
                      self.selection_mode, self.selection_index, self.scam_active, self.scam_type, 
                      self.scam_data, self.scam_input, dice)

        if self.winner: self.draw_game_over()

    def update(self): pass