import pygame
import random
from config.settings import (
    COLORS, DIGITAL_ONLY, MAP_WIDTH, MAP_HEIGHT, 
    BUILDING_LOCATIONS, ITEM_LOCATIONS, QUIZ_QUESTIONS,
    SCAM_PENALTY_OTP, SCAM_PENALTY_QUIZ, SCAM_PENALTY_FLEE,
    RANDOM_EVENT_INTERVAL, BUDGET_CHALLENGE_INTERVAL,
    SCAM_TIPS, RANDOM_EVENTS, BUDGET_OPTIONS,
    SCORE_WEALTH_DIVIDER, SCORE_HEALTH_MULTIPLIER,
    SCORE_TASK_MULTIPLIER, SCORE_FINISH_BONUS,
    LOAN_REPAY_MULTIPLIER, TILE_SIZE, MONTHLY_INCOME,
    SAVINGS_INTEREST, GRID_COLS, GRID_ROWS, MAP_LAYOUT,
    LOAN_REPAY_TURNS, SCAM_FREEZE_TURNS, SCREEN_WIDTH, SCREEN_HEIGHT,
    MAP_X, MAP_Y
)
from config.assets import loader
from ui.map_view import MapView
from ui.hud import HUD
from entities.player import Player
from entities.npc import Scammer
from logic.economy import BankSystem
from logic.pathfinding import get_bfs_path
import config.audio as audio

class GameManager:
    def __init__(self, screen, p1_name, p2_name, p1_avatar=None, p2_avatar=None, p2_is_ai=False):
        self.screen = screen
        self.running = True
        self.font_md = pygame.font.Font(None, 24)
        self.font_lg = pygame.font.Font(None, 36)
        
        # --- UI & ASSETS ---
        self.bg_image = loader.get("map")
        if self.bg_image:
            self.bg_image = pygame.transform.scale(self.bg_image, (MAP_WIDTH, MAP_HEIGHT))
        
        self.map_view = MapView(screen)
        self.hud = HUD(screen)
        
        # --- ENTITIES ---
        p1_n = p1_name[:12].upper() if p1_name else "PLAYER 1"
        p2_n = p2_name[:12].upper() if p2_name else "PLAYER 2"
        
        from entities.ai_player import AIPlayer
        p1_obj = Player(1, p1_n, (5, 6), p1_avatar)
        p2_obj = AIPlayer(2, p2_n, (5, 3), p2_avatar) if p2_is_ai else Player(2, p2_n, (5, 3), p2_avatar)
        self.players = [p1_obj, p2_obj]
        self.turn_index = 0
        self.scammer = Scammer([0, 3])
        
        # --- GAME STATE ---
        self.message = "Welcome! Press ENTER to Start."
        self.turn_phase = "START" 
        self.winner = None
        self.finisher = None # Tracks who hit 20/20 first
        self.selection_mode = None
        self.selection_index = 0
        self.last_clicked_id = None
        
        # --- KNOWLEDGE, LOGS, JUICE ---
        self.logs = []
        self.popup_active = False
        self.popup_message = ""
        self.popup_timer = 0
        self.particles = []
        self.scam_flash_timer = 0
        self.screen_shake_timer = 0
        
        # --- BANK & SCAM UI STATE ---
        self.in_bank = False
        self.bank_mode = "MENU"
        self.input_text = ""
        self.temp_fd_amount = 0
        self.scam_active = False
        self.scam_type = None
        self.scam_data = {}
        self.scam_input = ""
        self.scam_failed = False
        self.scam_explanation = ""

        # --- DICE & MOVEMENT ---
        self.dice_vals = [1, 1]
        self.moves_left = 0
        self.dice_rolled = False
        self.dice_visible = False

        # --- DATA ---
        self.locations = BUILDING_LOCATIONS
        self.item_locations = ITEM_LOCATIONS
        self.quiz_questions = QUIZ_QUESTIONS
        self.last_click_time = 0

        # --- FEATURE: Tip Cards (#12) ---
        self.tip_active = False
        self.tip_title = ""
        self.tip_text = ""

        # --- FEATURE: Floating Notifications (#10) ---
        self.float_texts = []   # [{text, x, y, color, alpha, vy, life}]

        # --- FEATURE: Random Events (#2) ---
        self.turn_counter = 0
        self.pending_event = None

        # --- FEATURE: Budget Challenge (#4) ---
        self.budget_active = False
        self.budget_player = None

        # --- AUDIO ---
        audio.init()
        
        self.start_new_turn()

    @property
    def message(self):
        return self.logs[-1] if self.logs else ""
        
    @message.setter
    def message(self, value):
        if not hasattr(self, 'logs'): self.logs = []
        self.logs.append(value)
        if len(self.logs) > 4: self.logs.pop(0)

    def trigger_knowledge_popup(self, msg, duration_frames=180):
        p = self.get_current_player()
        if msg not in p.seen_popups:
            self.popup_active = True
            self.popup_message = msg
            self.popup_timer = duration_frames
            p.seen_popups.add(msg)

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

        # LOAN REPAYMENT LOGIC (Penalty)
        if p.loan > 0:
            if p.loan_timer > 0:
                p.loan_timer -= 1
                if p.loan_timer == 0:
                    penalty = int(p.loan * LOAN_REPAY_MULTIPLIER)
                    p.wallet -= penalty
                    p.loan = 0
                    self.message = f"LOAN DUE! Deducted ₹{penalty} (100% Interest!)"
                    self.trigger_knowledge_popup("Debt traps! High compound interest can destroy your finances.")

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

        self.turn_counter += 1
        
        # --- FEATURE: Mini-Budget Challenge (#4) ---
        if self.turn_counter % BUDGET_CHALLENGE_INTERVAL == 0 and not p.is_ai:
            self.budget_active = True
            self.budget_player = p
            audio.play('budget')
            # Wait for budget choice before actual turn starts
            self.turn_phase = "WAIT_BUDGET"
            return

        # --- FEATURE: Random Events (#2) ---
        if self.turn_counter % RANDOM_EVENT_INTERVAL == 0 and not self.budget_active:
            self.pending_event = random.choice(RANDOM_EVENTS)
            self.popup_active = True
            self.popup_timer = 180
            
            p.seen_popups.add(self.pending_event["name"])
            self.popup_message = f"EVENT: {self.pending_event['name']}\n{self.pending_event['desc']}"
            
            amt = self.pending_event["amount"]
            if self.pending_event["type"] == "wallet":
                p.wallet = max(0, p.wallet + amt)
            else:
                p.bank_balance = max(0, p.bank_balance + amt)
                
            if amt > 0:
                audio.play('event_good')
                self.spawn_float(f"+Rs.{amt}", p.grid_pos[0]*TILE_SIZE, p.grid_pos[1]*TILE_SIZE, COLORS['positive'])
            else:
                audio.play('event_bad')
                self.spawn_float(f"-Rs.{abs(amt)}", p.grid_pos[0]*TILE_SIZE, p.grid_pos[1]*TILE_SIZE, COLORS['negative'])
            
            self.logs.append(f"EVENT: {self.pending_event['name']} ({'+' if amt>0 else ''}{amt})")

        p.wallet += MONTHLY_INCOME
        self.spawn_float(f"+Rs.{MONTHLY_INCOME} Income", p.grid_pos[0]*TILE_SIZE, p.grid_pos[1]*TILE_SIZE - 20, COLORS['gold'])
        audio.play('income')
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
        self.scam_failed = False
        self.scam_explanation = ""
        self.dice_rolled = False
        self.moves_left = 0
        self.selection_mode = None
        self.message = f"{hp_msg}Turn: {p.name}. SPACE to ROLL!"
        
        # --- FEATURE: AI Turn (#16) ---
        if p.is_ai:
            p._action_timer = 20  # Delay before AI rolls dice

    def spawn_float(self, text, x, y, color):
        """Feature 10: Floating Text."""
        self.float_texts.append({
            "text": str(text), "x": x + random.randint(0, 30), "y": y,
            "color": color, "alpha": 255, "vy": -1.5, "life": 60
        })
    def apply_budget_choice(self, choice_index):
        p = self.get_current_player()
        if choice_index < 0 or choice_index >= len(BUDGET_OPTIONS): return
        opt = BUDGET_OPTIONS[choice_index]
        p.bank_balance += opt['bank']
        p.wallet += opt['wallet']
        p.health = min(100, p.health + opt['health'])
        p.happiness = min(100, p.happiness + opt['happy'])
        self.spawn_float(f"Budget: {opt['label']}", p.grid_pos[0]*TILE_SIZE, p.grid_pos[1]*TILE_SIZE, COLORS['positive'])
        audio.play('coin')
        self.budget_active = False
        self.turn_phase = "ACTION"

    def handle_input(self, events):
        # Ignore input if AI is playing
        p = self.get_current_player()
        is_ai = getattr(p, 'is_ai', False)
        
        if is_ai and not self.winner:
            # Special case: allow AI to process specific internal calls via FakeEvent
            # But normally we return
            return

        if self.tip_active:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.tip_active = False
                    audio.play('click')
            return

        if self.popup_active:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    self.popup_active = False
                    audio.play('click')
            return

        if self.budget_active:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: self.apply_budget_choice(0)
                    elif event.key == pygame.K_2: self.apply_budget_choice(1)
                    elif event.key == pygame.K_3: self.apply_budget_choice(2)
            return
            
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
                    continue 
                
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
                self.message = "Bank: 1:Dep, 2:With, 3:FD, 4:Redeem, 5:Repay"
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
                if region.get('type') == 'DICE':
                    if self.turn_phase == "ACTION" and not self.dice_rolled:
                        self.roll_dice_animation()
                    return
                    
                p = self.get_current_player()
                cid = f"{region.get('mode')}_{region.get('idx')}"
                if is_double and self.last_clicked_id == cid:
                    lst = p.pending_needs if region.get('mode') == 'NEEDS' else p.pending_wants
                    if region.get('idx') < len(lst):
                        item = lst[region['idx']]
                        if region.get('mode') == 'NEEDS': self.pay_specific_need(item)
                        else: self.buy_specific_want(item)
                else:
                    self.selection_mode = region.get('mode')
                    self.selection_index = region.get('idx')
                self.last_click_time, self.last_clicked_id = t, cid
                return

    def handle_movement_input(self, event):
        if not self.dice_rolled: return
        if self.moves_left > 0:
            d = {pygame.K_LEFT: (-1,0), pygame.K_RIGHT: (1,0), pygame.K_UP: (0,-1), pygame.K_DOWN: (0,1)}
            if event.key in d:
                dx, dy = d[event.key]
                self.move_player(dx, dy)
                if not self.scam_active:
                    self.scammer.move_towards_target(self.players, self.locations)
                    # Don't trigger scam if player is in the bank
                    p = self.get_current_player()
                    is_safe = self.locations.get(tuple(p.grid_pos)) == "bank"
                    
                    if not is_safe and self.scammer.is_colliding(p.grid_pos):
                        self.trigger_scam_event()
                        self.moves_left = 0
                        self.dice_visible = False
        else: self.message = "Press ENTER to end turn."

    def move_player(self, dx, dy):
        p = self.get_current_player()
        nx, ny = p.grid_pos[0] + dx, p.grid_pos[1] + dy
        if 0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS and MAP_LAYOUT[ny][nx] == 0:
            p.grid_pos = [nx, ny]
            self.moves_left -= 1
            self.dice_visible = False
            
            is_safe = self.locations.get(tuple(p.grid_pos)) == "bank"
            if not is_safe and self.scammer.is_colliding(p.grid_pos): 
                self.trigger_scam_event()
                return
            loc = self.locations.get(tuple(p.grid_pos))
            self.message = f"At {loc.title()}." if loc else f"Moves: {self.moves_left}"

    def pay_specific_need(self, item):
        p = self.get_current_player()
        name, cost = item
        if self.locations.get(tuple(p.grid_pos)) != self.item_locations.get(name):
            self.message = f"Go to {self.item_locations.get(name)}!"
            return

        is_digital = name in DIGITAL_ONLY
        paid = False

        if not is_digital and p.wallet >= cost:
            p.wallet -= cost
            paid = True
            self.message = f"Paid {name} using Cash!"
        elif p.bank_balance >= cost:
            p.bank_balance -= cost
            paid = True
            self.message = f"Paid {name} using Bank Balance!"
        elif p.fd_balance >= cost:
            # Break FD to avoid toxic loan
            p.bank_balance += p.fd_balance - cost 
            p.fd_balance = 0
            p.fd_timer = 0
            paid = True
            self.message = f"Broke FD to pay {name} (Saved from toxic loan!)"
            self.trigger_knowledge_popup("Emergency Fund (FD) saves you from toxic loans!")
        else:
            # Fast Loan
            p.loan += cost
            p.loan_timer = LOAN_REPAY_TURNS
            paid = True
            self.message = f"Forced to take FAST LOAN of ₹{cost} for {name}!"
            self.trigger_knowledge_popup("Fast Loans charge high interest! Repay in 3 turns or face penalty.")
            self.scam_active = False # Reset UI just in case

        if paid:
            p.pending_needs.remove(item)
            p.completed_needs.append(name)

    def buy_specific_want(self, item):
        p = self.get_current_player()
        name, cost, happy = item
        if self.locations.get(tuple(p.grid_pos)) != self.item_locations.get(name):
            self.message = f"Go to {self.item_locations.get(name)}!"
            return
            
        is_digital = name in DIGITAL_ONLY
        
        if not is_digital and p.wallet >= cost:
            p.wallet -= cost; p.happiness += happy
            p.pending_wants.remove(item); p.completed_wants.append(name)
            self.message = f"Bought {name} with Cash!"
        elif is_digital and p.bank_balance >= cost:
            p.bank_balance -= cost; p.happiness += happy
            p.pending_wants.remove(item); p.completed_wants.append(name)
            self.message = f"Bought {name} with Digital Payment!"
        elif is_digital and p.wallet >= cost:
            self.message = f"{name} requires Digital Payment! Deposit cash at Bank."
        else:
            self.message = "Need more money to buy this want!"

    def handle_bank_input(self, event):
        p = self.get_current_player()
        if self.bank_mode == "MENU":
            if event.key == pygame.K_1: self.bank_mode, self.input_text = "DEPOSIT", ""
            elif event.key == pygame.K_2: self.bank_mode, self.input_text = "WITHDRAW", ""
            elif event.key == pygame.K_3: self.bank_mode, self.input_text = "FD_AMT", ""
            elif event.key == pygame.K_4: 
                _, m = BankSystem.redeem_fd(p)
                self.message, self.bank_mode = m, "MENU"
            elif event.key == pygame.K_5: self.bank_mode, self.input_text = "REPAY", ""
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
                elif self.bank_mode == "REPAY":
                    success, m = BankSystem.repay_loan(p, val)
                    self.message, self.bank_mode = m, "MENU"
                    if success and "FULLY PAID OFF" in m:
                        self.trigger_loan_paid_juice()
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
        p = self.get_current_player()
        
        # Decide scam type based on scammer's intent
        if self.scammer.intent == "CASH":
            if p.wallet > 0:
                self.scam_type = "PICKPOCKET"
                self.scam_data = {}
                self.scam_active = False
                loss = int(p.wallet * 0.2)
                p.wallet -= loss
                self.message = f"PICKPOCKET! Lost ₹{loss} cash."
                self.trigger_knowledge_popup("Physical cash can be stolen! Keeping money in a bank is safer.")
                self.end_scam()
            else:
                self.scam_active = False
                self.message = "Scammer tried to pickpocket you, but you have no cash! Safe!"
                self.trigger_knowledge_popup("Good job! Keeping cash safely in the bank protects you from pickpockets.")
                self.end_scam()
        elif self.scammer.intent == "DIGITAL":
            r = random.random()
            if r < 0.5:
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
        if self.scam_failed:
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.end_scam()
            return
            
        if event.key == pygame.K_ESCAPE: self.apply_scam_penalty(SCAM_PENALTY_FLEE); self.end_scam()
        elif event.key == pygame.K_RETURN:
            if self.scam_type == "OTP":
                target = self.scam_data['digits'][self.scam_data['idx']]
                if self.scam_input == str(target):
                    self.scam_data['idx'] += 1
                    if self.scam_data['idx'] >= 4: self.end_scam()
                    else: self.generate_otp_problem(); self.scam_input = ""
                else: 
                    self.scam_failed = True
                    self.scam_explanation = f"Wrong! The correct answer was {target}. Always verify transactions!"
                    self.apply_scam_penalty(SCAM_PENALTY_OTP)
            elif self.scam_type == "QUIZ":
                q = self.scam_data['questions'][self.scam_data['q_idx']]
                # Map A/B/C/D letter to the corresponding option text
                letter_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
                typed = self.scam_input.strip().lower()
                opts = q.get('opts', [])
                if typed in letter_map and letter_map[typed] < len(opts):
                    selected_answer = opts[letter_map[typed]]
                else:
                    selected_answer = typed  # fallback: compare directly
                if selected_answer.lower() == q['a'].lower():
                    self.scam_data['q_idx'] += 1; self.scam_input = ""
                    if self.scam_data['q_idx'] >= 3: self.end_scam()
                else:
                    self.scam_failed = True
                    # Find the correct letter label for the explanation
                    correct_letter = "?"
                    for letter, idx in letter_map.items():
                        if idx < len(opts) and opts[idx].lower() == q['a'].lower():
                            correct_letter = letter.upper()
                            break
                    self.scam_explanation = f"Wrong! Correct: {correct_letter}) {q['a']}. {q.get('exp', '')}"
                    self.apply_scam_penalty(SCAM_PENALTY_QUIZ)
                    audio.play('wrong')
        elif event.key == pygame.K_BACKSPACE: self.scam_input = self.scam_input[:-1]
        else: self.scam_input += event.unicode

    def apply_scam_penalty(self, pct):
        p = self.get_current_player()
        loss = int(max(p.bank_balance, p.wallet) * pct)
        if p.bank_balance >= loss:
            p.bank_balance -= loss
            self.message = f"CYBER SCAM! Lost ₹{loss} from Bank!"
        else:
            p.wallet -= loss
            self.message = f"CYBER SCAM! Lost ₹{loss} from Wallet!"
            
        self.spawn_float(f"-Rs.{loss}", p.grid_pos[0]*TILE_SIZE, p.grid_pos[1]*TILE_SIZE, COLORS['negative'])
        self.scam_flash_timer = 20
        self.screen_shake_timer = 15

    def end_scam(self):
        self.scam_active = False
        self.scam_failed = False
        self.scammer.freeze_timer = SCAM_FREEZE_TURNS
        
        # --- FEATURE: Tip Cards (#12) ---
        if self.scam_type in SCAM_TIPS:
            title, text = SCAM_TIPS[self.scam_type]
            self.tip_active = True
            self.tip_title = title
            self.tip_text = text

    def trigger_loan_paid_juice(self):
        # Spawn massive green particles
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        for _ in range(100):
            self.particles.append([
                [cx, cy], 
                [random.uniform(-10, 10), random.uniform(-10, 10)], 
                random.randint(5, 12)
            ])

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
        # --- SCREEN SHAKE ---
        shake_x, shake_y = 0, 0
        if self.screen_shake_timer > 0:
            shake_x = random.randint(-4, 4)
            shake_y = random.randint(-4, 4)

        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.fill(COLORS['menu_bg']) 
        if self.bg_image: surface.blit(self.bg_image, (MAP_X, MAP_Y))
        self.map_view.draw_to_surface(surface, [], self.players, self.scammer, self.locations)
        
        if self.in_bank and self.bank_mode != "MENU":
            # Dark blurred overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            
            # Premium Dialog Box
            bw, bh = 500, 150
            bx, by = (SCREEN_WIDTH - bw) // 2, (SCREEN_HEIGHT - bh) // 2
            pygame.draw.rect(surface, (30, 40, 60), (bx, by, bw, bh), border_radius=15)
            pygame.draw.rect(surface, COLORS['ui_accent'], (bx, by, bw, bh), 3, border_radius=15)
            
            # Label
            lbl_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
            lbl_surf = lbl_font.render(f"ENTER {self.bank_mode} AMOUNT:", True, COLORS['ui_accent'])
            surface.blit(lbl_surf, (bx + (bw - lbl_surf.get_width())//2, by + 25))
            
            # Input Field
            input_w, input_h = 350, 50
            ix, iy = bx + (bw - input_w)//2, by + 70
            pygame.draw.rect(surface, (20, 25, 35), (ix, iy, input_w, input_h), border_radius=8)
            pygame.draw.rect(surface, (60, 70, 90), (ix, iy, input_w, input_h), 2, border_radius=8)
            
            # Input Text
            val_font = pygame.font.SysFont("Consolas", 32, bold=True)
            txt = self.input_text + ("|" if (pygame.time.get_ticks() // 500) % 2 == 0 else "")
            txt_surf = val_font.render(txt, True, COLORS['white'])
            surface.blit(txt_surf, (ix + 20, iy + (input_h - txt_surf.get_height())//2))
            
            # Instructions
            hint_font = pygame.font.SysFont("Segoe UI", 14)
            hint_surf = hint_font.render("Press ENTER to confirm, ESC to cancel", True, COLORS['text_dim'])
            surface.blit(hint_surf, (bx + (bw - hint_surf.get_width())//2, by + bh - 25))
            
        dice = self.dice_vals if self.dice_visible else None
        
        # We need HUD to draw to the shaking surface too.  We temporarily pass surface instead of self.screen.
        old_screen = self.hud.screen
        self.hud.screen = surface
        self.hud.draw(self.players[0], self.players[1], self.turn_index, self.logs, self.winner, 
                      self.selection_mode, self.selection_index, self.scam_active, self.scam_type, 
                      self.scam_data, self.scam_input, dice, self.popup_active, self.popup_message,
                      self.scam_failed, self.scam_explanation, self)
        self.hud.screen = old_screen
        
        # Draw Particles
        for p in self.particles:
            pygame.draw.circle(surface, COLORS['positive'], (int(p[0][0]), int(p[0][1])), int(p[2]))


        # Winner screen is fully handled by HUD's draw_scorecard

        # Apply red flash
        if self.scam_flash_timer > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = min(255, self.scam_flash_timer * 12)
            overlay.fill((255, 0, 0, alpha))
            surface.blit(overlay, (0, 0))

        # Final blit to actual screen
        self.screen.blit(surface, (shake_x, shake_y))

    def update(self):
        # Always update floating texts even during popups
        for ft in self.float_texts[:]:
            ft['y'] += ft['vy']
            ft['alpha'] = max(0, ft['alpha'] - 4)
            ft['life'] -= 1
            if ft['life'] <= 0:
                self.float_texts.remove(ft)

        # AI Update Step
        cp = self.get_current_player()
        if getattr(cp, 'is_ai', False) and not self.winner:
            self._update_ai(cp)

        if self.popup_active:
            if self.popup_timer > 0:
                self.popup_timer -= 1
            else:
                self.popup_active = False

        if self.tip_active or self.budget_active:
            return

        if self.scam_flash_timer > 0:
            self.scam_flash_timer -= 1
        if self.screen_shake_timer > 0:
            self.screen_shake_timer -= 1
            
        new_particles = []
        for p in self.particles:
            p[0][0] += p[1][0]
            p[0][1] += p[1][1]
            p[2] -= 0.2 # shrink radius
            p[1][1] += 0.5 # gravity
            if p[2] > 0:
                new_particles.append(p)
        self.particles = new_particles

    def _update_ai(self, cp):
        """Feature 16: Automated AI logic."""
        class FakeEvent:
            def __init__(self, key): self.key = key

        if cp._action_timer > 0:
            cp._action_timer -= 1
            return

        # 1. Handle UI Blockers (Tips, Budget, Failed Scams)
        if self.tip_active:
            self.tip_active = False
            cp._action_timer = 40
            return
            
        if self.popup_active:
            self.popup_active = False
            cp._action_timer = 40
            return

        if self.scam_failed:
            self.end_scam()
            cp._action_timer = 60
            return

        if self.budget_active:
            choice = cp.choose_budget_option()
            self.apply_budget_choice(choice)
            cp._action_timer = 60
            return

        # 2. Handle Active Scam Mini-games
        if self.scam_active:
            if self.scam_type == "OTP":
                target = self.scam_data['digits'][self.scam_data['idx']]
                # 80% chance to 'get it right' vs scam defense
                if random.random() < 0.8:
                    self.scam_input = str(target)
                else:
                    self.scam_input = str(random.randint(1,9))
                
                self.handle_scam_input(FakeEvent(pygame.K_RETURN))
                cp._action_timer = 40
            elif self.scam_type == "QUIZ":
                q = self.scam_data['questions'][self.scam_data['q_idx']]
                ans = cp.choose_quiz_answer(q['opts'], q['a'])
                # Find letter for chosen answer
                letter = 'a'
                for l, idx in {'a':0, 'b':1, 'c':2, 'd':3}.items():
                    if idx < len(q['opts']) and q['opts'][idx] == ans:
                        letter = l
                        break
                self.scam_input = letter
                self.handle_scam_input(FakeEvent(pygame.K_RETURN))
                cp._action_timer = 50
            return

        # 3. Standard Turn Logic
        if not self.dice_rolled:
            self.roll_dice_animation()
            cp._action_timer = 60
            return
        if self.moves_left > 0:
            # AI logic for movement
            target_lid = cp.choose_location(self.locations, cp.pending_needs, cp.pending_wants)
            
            if target_lid:
                # If path is empty, calculate a new BFS path to the destination
                if not cp.current_path or cp.current_path[-1] != tuple(target_lid):
                    cp.current_path = get_bfs_path(cp.grid_pos, target_lid, MAP_LAYOUT)
                
                if cp.current_path:
                    # Get next tile and determine direction
                    next_tile = cp.current_path.pop(0)
                    tx, ty = next_tile
                    sx, sy = cp.grid_pos
                    dx, dy = tx - sx, ty - sy
                    
                    if dx == 1: move_key = pygame.K_RIGHT
                    elif dx == -1: move_key = pygame.K_LEFT
                    elif dy == 1: move_key = pygame.K_DOWN
                    elif dy == -1: move_key = pygame.K_UP
                    else:
                        # Should not happen with BFS unless already there
                        self.moves_left = 0
                        return

                    self.handle_movement_input(FakeEvent(move_key))
                    cp._action_timer = 15 # delay between steps
                else:
                    # No path found or already at destination
                    self.moves_left = 0
                    cp.current_destination = None
            else:
                self.moves_left = 0
            return

        # Phase 3: Interaction & End Turn
        if (self.turn_phase == "ACTION" or self.turn_phase == "WAIT_BUDGET") and self.dice_rolled and self.moves_left == 0:
            # Check if AI can fulfill any needs/wants on current spot
            pos = tuple(cp.grid_pos)
            loc_type = self.locations.get(pos)
            
            # Auto-pay needs if at correct location (Needs always processed via loan if needed)
            for need in cp.pending_needs[:]:
                if ITEM_LOCATIONS.get(need[0]) == loc_type:
                    self.pay_specific_need(need)
                    cp._action_timer = 30
                    return
            
            # Auto-buy wants if at correct location AND affordable
            for want in cp.pending_wants[:]:
                name, cost, _ = want
                if ITEM_LOCATIONS.get(name) == loc_type:
                    is_digital = name in DIGITAL_ONLY
                    can_afford = (cp.bank_balance >= cost) if is_digital else (cp.wallet >= cost)
                    if can_afford:
                        self.buy_specific_want(want)
                        cp._action_timer = 30
                        return
                    else:
                        break # Cannot afford right now, don't loop
            
            # If at bank, check if should deposit
            if loc_type == "bank" and cp.wallet > 500:
                # Simple AI deposit all
                amt = cp.wallet - 100
                cp.wallet -= amt
                cp.bank_balance += amt
                self.spawn_float(f"AI Saved Rs.{amt}", cp.grid_pos[0]*TILE_SIZE, cp.grid_pos[1]*TILE_SIZE, (255,255,0))
                audio.play('coin')
                cp._action_timer = 30
                return

            # End turn
            self.turn_phase = "END"
            self.end_turn()
            cp._action_timer = 40