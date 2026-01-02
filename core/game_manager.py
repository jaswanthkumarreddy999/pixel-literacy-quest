import pygame
import random
import time
from config.settings import *
from config.assets import loader
from ui.map_view import MapView
from ui.hud import HUD

class Player:
    def __init__(self, id, name, start_pos):
        self.id = id
        self.name = name
        self.grid_pos = list(start_pos)
        self.wallet = STARTING_WALLET       
        self.bank_balance = STARTING_BANK   
        self.loan = 0
        self.fd_balance = 0
        self.fd_timer = 0
        self.fd_rate = 0.0
        self.inventory = [] 
        self.health = 100       
        self.happiness = 0
        self.next_need_index = 0
        self.next_want_index = 0
        self.pending_needs = [] 
        self.pending_wants = []
        self.completed_needs = []
        self.completed_wants = []
        self.game_needs = list(GAME_NEEDS)
        self.game_wants = list(GAME_WANTS)
        random.shuffle(self.game_needs)
        random.shuffle(self.game_wants)

class GameManager:
    def __init__(self, screen, p1_name, p2_name):
        self.screen = screen
        self.running = True
        
        self.bg_image = loader.get("map")
        if self.bg_image:
            self.bg_image = pygame.transform.scale(self.bg_image, (MAP_WIDTH, MAP_HEIGHT))
        else:
            self.bg_image = None
        
        self.map_view = MapView(screen)
        self.hud = HUD(screen)
        
        p1_n = p1_name[:12].upper() if p1_name else "PLAYER 1"
        p2_n = p2_name[:12].upper() if p2_name else "PLAYER 2"
        
        self.players = [Player(1, p1_n, (5, 6)), Player(2, p2_n, (5, 3))]
        self.turn_index = 0
        
        self.scammer_pos = [0, 3]
        self.scammer_freeze_timer = 0
        
        self.message = "Welcome! Press ENTER to Start."
        self.turn_phase = "START" 
        self.winner = None
        self.selection_mode = None
        self.selection_index = 0
        
        # --- BANK VARIABLES ---
        self.in_bank = False
        self.bank_mode = "MENU"
        self.input_text = ""
        self.temp_fd_amount = 0

        # --- SCAM VARIABLES ---
        self.scam_active = False
        self.scam_type = None
        self.scam_data = {}
        self.scam_input = ""

        # --- DICE VARIABLES ---
        self.dice_vals = [1, 1]
        self.moves_left = 0
        self.dice_rolled = False
        self.dice_visible = False 

        self.locations = {
            (4, 6): "bank", (5, 6): "bank",         
            (2, 9): "store",        
            (8, 6): "hospital", (9, 6): "hospital",      
            (0, 6): "fire_station", (1, 6): "fire_station", 
            (1, 3): "apartment", (2, 3): "apartment",    
            (4, 2): "school", (5, 2): "school"  
        }

        self.item_locations = {
            "Fire Accident": "fire_station", "Groceries": "store", "Food": "store",
            "Medicines": "hospital", "fever": "hospital", "Heart Attack": "hospital",
            "School Fees": "school", "Clothes": "store", "House Repairs": "apartment",
            "Rent": "apartment", "Wifi": "bank", "Cinema": "store",
            "Fancy Dinner": "store", "Headphones": "store", "Video Game": "store",
            "Concert Tickets": "store", "TV": "store", "Smart Watch": "store",
            "New Phone": "store", "School Vacation ": "bank" 
        }

        self.quiz_questions = [
            {"q": "OTP valid for how long?", "a": "10 min", "opts": ["10 min", "1 hour", "Forever"]},
            {"q": "Share PIN with?", "a": "No One", "opts": ["Bank", "No One", "Friends"]},
            {"q": "Green lock on URL means?", "a": "Secure", "opts": ["Secure", "Hacked", "Open"]},
            {"q": "Full form of ATM?", "a": "Automated Teller", "opts": ["Any Time Money", "Automated Teller", "All Time Money"]},
            {"q": "CVV is on which side?", "a": "Back", "opts": ["Front", "Back", "Chip"]},
        ]
        
        self.start_new_turn()

    def start_new_turn(self):
        p = self.get_current_player()
        
        # --- 1. HEALTH PENALTY (New) ---
        # Count pending needs BEFORE adding new ones
        unpaid_count = len(p.pending_needs)
        health_penalty_msg = ""
        
        if unpaid_count > 0:
            p.health -= unpaid_count
            health_penalty_msg = f"Lost {unpaid_count} HP (Unpaid Bills)! "
            
        # --- 2. GAME OVER CHECK ---
        if p.health <= 0:
            p.health = 0
            # Opponent wins
            opponent_idx = 1 if self.turn_index == 0 else 0
            self.winner = self.players[opponent_idx]
            self.message = f"{p.name} Health 0! {self.winner.name} WINS!"
            # Stop here, do not give income
            return

        # --- 3. INCOME & INTEREST ---
        p.wallet += MONTHLY_INCOME
        if p.bank_balance > 0: p.bank_balance += int(p.bank_balance * SAVINGS_INTEREST)
        if p.loan > 0: p.loan += int(p.loan * LOAN_INTEREST)
        
        if p.fd_timer > 0:
            p.fd_timer -= 1
            if p.fd_timer == 0:
                interest = int(p.fd_balance * p.fd_rate)
                total = p.fd_balance + interest
                p.bank_balance += total
                p.fd_balance = 0
                p.fd_rate = 0.0
                self.message = f"FD Matured! Got Rs. {total}."
        
        if self.scammer_freeze_timer > 0:
            self.scammer_freeze_timer -= 1
        
        # --- 4. NEW BILLS ---
        new_items_msg = ""
        if p.next_need_index < len(p.game_needs):
            p.pending_needs.append(p.game_needs[p.next_need_index])
            p.next_need_index += 1
            new_items_msg += "Bill Added. "
        if p.next_want_index < len(p.game_wants):
            p.pending_wants.append(p.game_wants[p.next_want_index])
            p.next_want_index += 1
            new_items_msg += "Item Added."
        
        self.turn_phase = "ACTION"
        self.selection_mode = None
        self.in_bank = False 
        self.scam_active = False
        
        self.dice_rolled = False
        self.dice_visible = False
        self.moves_left = 0
        self.dice_vals = [1, 1]
        
        # Add the health msg to the main message
        self.message = f"{health_penalty_msg}Income Received. Press SPACE to ROLL!"

    def handle_input(self, events):
        for event in events:
            if self.scam_active and event.type == pygame.MOUSEBUTTONDOWN:
                if self.hud.close_btn_rect and self.hud.close_btn_rect.collidepoint(event.pos):
                    self.message = "Panic! You hung up but lost money."
                    self.apply_scam_penalty(0.10)
                    self.end_scam()
                    return

            if event.type == pygame.KEYDOWN:
                if self.scam_active:
                    self.handle_scam_input(event)
                    return 
                
                if self.turn_phase == "ACTION" and not self.dice_rolled and not self.in_bank and not self.selection_mode:
                    if event.key == pygame.K_SPACE:
                        self.roll_dice_animation()
                        return 
                
                if event.key == pygame.K_q and self.selection_mode is None and not self.in_bank: 
                    self.running = False
                if self.winner: return
                
                if self.turn_phase == "ACTION":
                    if self.in_bank:
                        self.handle_bank_input(event)
                    elif self.selection_mode: 
                        self.handle_selection_input(event)
                    else: 
                        self.handle_movement_input(event)
                        
                elif self.turn_phase == "END":
                    if event.key == pygame.K_RETURN: self.end_turn()

    def roll_dice_animation(self):
        self.dice_visible = True
        for _ in range(10):
            d1 = random.randint(1, 6)
            d2 = random.randint(1, 6)
            self.dice_vals = [d1, d2]
            self.draw()
            pygame.display.flip()
            pygame.time.delay(50) 
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self.dice_vals = [d1, d2]
        self.moves_left = d1 + d2
        self.dice_rolled = True
        self.message = f"Rolled {d1+d2}! Moves Left: {self.moves_left}"

    def trigger_scam_event(self):
        self.scam_active = True
        self.scam_input = ""
        
        if random.random() < 0.5:
            self.scam_type = "OTP"
            self.scam_data['digits'] = [random.randint(1, 9) for _ in range(4)]
            self.scam_data['current_idx'] = 0
            self.generate_otp_problem()
        else:
            self.scam_type = "QUIZ"
            self.scam_data['questions'] = random.sample(self.quiz_questions, 3) 
            self.scam_data['current_q_idx'] = 0
            self.load_next_quiz_question()

    def generate_otp_problem(self):
        target = self.scam_data['digits'][self.scam_data['current_idx']]
        op = random.choice(['+', '-'])
        if op == '+':
            a = random.randint(0, target)
            b = target - a
            self.scam_data['problem'] = f"{a} + {b} = ?"
        else:
            a = random.randint(target, 18)
            b = a - target
            self.scam_data['problem'] = f"{a} - {b} = ?"
        
    def load_next_quiz_question(self):
        if self.scam_data['current_q_idx'] < len(self.scam_data['questions']):
            pass 
        else:
            self.end_scam()

    def handle_scam_input(self, event):
        if event.key == pygame.K_ESCAPE:
            self.message = "Panic! You cancelled verification."
            self.apply_scam_penalty(0.10)
            self.end_scam()
            return

        if event.key == pygame.K_RETURN:
            if self.scam_type == "OTP":
                target = self.scam_data['digits'][self.scam_data['current_idx']]
                if self.scam_input.isdigit() and int(self.scam_input) == target:
                    self.scam_data['current_idx'] += 1
                    if self.scam_data['current_idx'] >= 4:
                        self.message = "OTP Verified! Money Saved."
                        self.end_scam()
                    else:
                        self.generate_otp_problem()
                        self.scam_input = ""
                else:
                    self.apply_scam_penalty(0.05)
                    self.end_scam()
            elif self.scam_type == "QUIZ":
                q_data = self.scam_data['questions'][self.scam_data['current_q_idx']]
                correct_ans = q_data['a'].lower()
                user_ans = self.scam_input.lower()
                if correct_ans in user_ans:
                    self.message = "Correct!"
                else:
                    self.message = "Wrong! Penalty applied."
                    self.apply_scam_penalty(0.10) 
                self.scam_data['current_q_idx'] += 1
                self.scam_input = ""
                if self.scam_data['current_q_idx'] >= len(self.scam_data['questions']):
                    self.end_scam()
                else:
                    self.load_next_quiz_question()
        elif event.key == pygame.K_BACKSPACE:
            self.scam_input = self.scam_input[:-1]
        else:
            self.scam_input += event.unicode

    def apply_scam_penalty(self, percent):
        p = self.get_current_player()
        loss = int(p.wallet * percent)
        p.wallet -= loss
        self.message = f"SCAMMED! Lost Rs. {loss}!"

    def end_scam(self):
        self.scam_active = False
        self.scammer_freeze_timer = 3 

    def handle_bank_input(self, event):
        p = self.get_current_player()
        if self.bank_mode == "MENU":
            if event.key == pygame.K_1:
                self.bank_mode = "DEPOSIT"
                self.input_text = ""
                self.message = "DEPOSIT: Type amount > "
            elif event.key == pygame.K_2:
                self.bank_mode = "WITHDRAW"
                self.input_text = ""
                self.message = "WITHDRAW: Type amount > "
            elif event.key == pygame.K_3:
                self.bank_mode = "FD_AMOUNT"
                self.input_text = ""
                self.message = "NEW FD: Enter Amount > "
            elif event.key == pygame.K_4:
                if p.fd_balance > 0:
                    p.bank_balance += p.fd_balance
                    p.fd_balance = 0
                    p.fd_timer = 0
                    p.fd_rate = 0.0
                    self.message = "FD Redeemed! Principal returned."
                else: self.message = "No Active FD."
            elif event.key == pygame.K_ESCAPE:
                self.in_bank = False
                self.message = "Exited Bank. Press ENTER."
        else:
            if event.key == pygame.K_ESCAPE:
                self.bank_mode = "MENU"
                self.message = "1:Dep 2:Wdr 3:New FD 4:Redeem"
                return
            if event.key == pygame.K_RETURN:
                if self.input_text.isdigit():
                    val = int(self.input_text)
                    if self.bank_mode == "FD_AMOUNT":
                        if val > 0:
                            self.temp_fd_amount = val
                            self.bank_mode = "FD_TURNS"
                            self.input_text = ""
                            self.message = f"FD Rs.{val}: Enter Duration (Turns) > "
                            return
                        else: self.message = "Amount > 0."
                    elif self.bank_mode == "FD_TURNS":
                        if val > 0:
                            self.process_custom_fd(p, self.temp_fd_amount, val)
                            self.bank_mode = "MENU"
                        else: self.message = "Turns > 0."
                    else:
                        if val > 0: self.process_bank_transaction(p, val)
                        else: self.message = "Invalid Amount."
                        self.bank_mode = "MENU"
                else: self.message = "Numbers only."
                return
            if event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
            else:
                if event.unicode.isdigit(): self.input_text += event.unicode
            if self.bank_mode == "FD_TURNS": self.message = f"Duration > {self.input_text}"
            else: self.message = f"{self.bank_mode}: Type amount > {self.input_text}"

    def process_bank_transaction(self, p, amount):
        if self.bank_mode == "DEPOSIT":
            if p.wallet >= amount:
                p.wallet -= amount
                p.bank_balance += amount
                self.message = f"Deposited Rs. {amount}."
            else: self.message = "Not enough cash!"
        elif self.bank_mode == "WITHDRAW":
            if p.bank_balance >= amount:
                p.bank_balance -= amount
                p.wallet += amount
                self.message = f"Withdrew Rs. {amount}."
            else: self.message = "Not enough money!"

    def process_custom_fd(self, p, amount, turns):
        if p.fd_balance > 0:
            self.message = "You already have an FD!"
            return
        if p.bank_balance >= amount:
            p.bank_balance -= amount
            p.fd_balance = amount
            p.fd_timer = turns
            p.fd_rate = 0.05 * turns 
            percent = int(p.fd_rate * 100)
            self.message = f"FD Created: Rs.{amount}, {turns} turns @ {percent}%."
        else: self.message = "Not enough bank balance!"

    def handle_movement_input(self, event):
        if not self.dice_rolled:
            self.message = "Press SPACE to Roll Dice first!"
            return
        if self.moves_left <= 0 and event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
            self.message = "No moves left! Press ENTER to End Turn."
            return

        if event.key == pygame.K_n:
            if self.get_current_player().pending_needs:
                self.selection_mode = 'NEEDS'
                self.selection_index = 0
                self.message = "Select Bill (UP/DOWN). ENTER to Pay."
            else: self.message = "No pending bills!"
        elif event.key == pygame.K_w:
            if self.get_current_player().pending_wants:
                self.selection_mode = 'WANTS'
                self.selection_index = 0
                self.message = "Select Item (UP/DOWN). ENTER to Buy."
            else: self.message = "No wants available!"

        dx, dy = 0, 0
        if event.key == pygame.K_LEFT: dx = -1
        elif event.key == pygame.K_RIGHT: dx = 1
        elif event.key == pygame.K_UP: dy = -1
        elif event.key == pygame.K_DOWN: dy = 1
        
        if dx != 0 or dy != 0:
            self.move_player(dx, dy)
            self.move_scammer_ai()
        
        if event.key == pygame.K_e: self.interact_with_building()
        if event.key == pygame.K_RETURN:
            if not self.in_bank: self.finish_turn_action()

    def handle_selection_input(self, event):
        p = self.get_current_player()
        current_list = p.pending_needs if self.selection_mode == 'NEEDS' else p.pending_wants
        if not current_list:
            self.selection_mode = None
            return
        if event.key == pygame.K_UP: self.selection_index = max(0, self.selection_index - 1)
        elif event.key == pygame.K_DOWN: self.selection_index = min(len(current_list) - 1, self.selection_index + 1)
        elif event.key == pygame.K_ESCAPE:
            self.selection_mode = None
            self.message = "Cancelled selection."
        elif event.key == pygame.K_RETURN:
            item = current_list[self.selection_index]
            if self.selection_mode == 'NEEDS': self.pay_specific_need(item)
            else: self.buy_specific_want(item)
            self.selection_mode = None

    def check_location_requirement(self, item_name, player_pos):
        required_type = self.item_locations.get(item_name, "bank") 
        current_type = self.locations.get(tuple(player_pos))
        if current_type == required_type: return True, ""
        else: return False, f"Go to {required_type.upper().replace('_', ' ')}!"

    def pay_specific_need(self, item):
        p = self.get_current_player()
        name, cost = item
        valid_loc, msg = self.check_location_requirement(name, p.grid_pos)
        if not valid_loc:
            self.message = msg
            return
        if p.wallet >= cost:
            p.wallet -= cost
            self.message = f"Paid {name} (Cash)."
            p.pending_needs.remove(item)
            p.completed_needs.append(name)
            self.check_win_condition(p)
        elif p.bank_balance >= cost:
            p.bank_balance -= cost
            self.message = f"Paid {name} (Bank)."
            p.pending_needs.remove(item)
            p.completed_needs.append(name)
            self.check_win_condition(p)
        else: self.message = f"Not enough funds for {name}!"

    def buy_specific_want(self, item):
        p = self.get_current_player()
        name, cost, happiness = item
        valid_loc, msg = self.check_location_requirement(name, p.grid_pos)
        if not valid_loc:
            self.message = msg
            return
        if p.wallet >= cost:
            p.wallet -= cost
            p.happiness += happiness
            self.message = f"Bought {name}!"
            p.pending_wants.remove(item)
            p.completed_wants.append(name)
            self.check_win_condition(p)
        else: self.message = f"Need Cash (${cost}) for {name}!"

    def move_player(self, dx, dy):
        if self.moves_left <= 0:
            return
        p = self.get_current_player()
        nx, ny = p.grid_pos[0] + dx, p.grid_pos[1] + dy
        if 0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS:
            if MAP_LAYOUT[ny][nx] == 0:
                p.grid_pos = [nx, ny]
                self.moves_left -= 1
                self.dice_visible = False 
                self.message = f"Moves Left: {self.moves_left}"
        if p.grid_pos == self.scammer_pos and not self.scam_active and self.scammer_freeze_timer == 0:
            self.trigger_scam_event()

    def move_scammer_ai(self):
        if self.scammer_freeze_timer > 0:
            return 
        p1 = self.players[0]
        p2 = self.players[1]
        target = p1 if p1.wallet >= p2.wallet else p2
        sx, sy = self.scammer_pos
        tx, ty = target.grid_pos
        if sx < tx: sx += 1
        elif sx > tx: sx -= 1
        if sx == tx:
            if sy < ty: sy += 1
            elif sy > ty: sy -= 1
        if MAP_LAYOUT[sy][sx] == 0:
            self.scammer_pos = [sx, sy]
        p = self.get_current_player()
        if p.grid_pos == self.scammer_pos:
            self.trigger_scam_event()

    def interact_with_building(self):
        p = self.get_current_player()
        loc = self.locations.get(tuple(p.grid_pos))
        if loc:
            name = loc.replace("_", " ").title()
            if loc == "hospital":
                 if p.wallet >= 100:
                    p.wallet -= 100
                    p.health = min(100, p.health + 20)
                    self.message = "Health Restored!"
            elif loc == "bank":
                self.in_bank = True
                self.bank_mode = "MENU"
                self.input_text = ""
                self.message = "1:Deposit 2:Withdraw 3:New FD 4:Redeem"
            else: self.message = f"At {name}."
        else: self.message = "Nothing here."

    def finish_turn_action(self):
        self.turn_phase = "END"
        self.message = "Turn Done. Press ENTER for Next Player."

    def check_win_condition(self, p):
        # Trigger end game when the list is complete
        if len(p.completed_needs) >= 10 and len(p.completed_wants) >= 10:
            self.winner = p # This player "finished" first, but HUD calculates score
            self.message = "Calculating Scores..."

    def end_turn(self):
        if self.winner: return
        self.turn_index = (self.turn_index + 1) % len(self.players)
        self.start_new_turn()

    def get_current_player(self):
        return self.players[self.turn_index]
        
    def draw(self):
        self.screen.fill(COLORS['menu_bg']) 
        if self.bg_image: 
            self.screen.blit(self.bg_image, (MAP_X, MAP_Y))
            
        class ScammerObj:
            def __init__(self, pos): self.pos = pos
        self.map_view.draw([], self.players, ScammerObj(self.scammer_pos), self.locations)
        dice_to_draw = self.dice_vals if self.dice_visible else None
        self.hud.draw(self.players[0], self.players[1], self.turn_index, self.message, self.winner, self.selection_mode, self.selection_index, self.scam_active, self.scam_type, self.scam_data, self.scam_input, dice_to_draw)
    
    def update(self): pass