import pygame
from config.settings import *
from config.assets import loader

class HUD:
    def __init__(self, screen):
        self.screen = screen
        try:
            self.font_xl = pygame.font.SysFont("Segoe UI", 32, bold=True)
            self.font_lg = pygame.font.SysFont("Segoe UI", 20, bold=True)
            self.font_md = pygame.font.SysFont("Segoe UI", 16, bold=True)
            self.font_sm = pygame.font.SysFont("Segoe UI", 13) 
        except:
            self.font_xl = pygame.font.Font(None, 40)
            self.font_lg = pygame.font.Font(None, 28)
            self.font_md = pygame.font.Font(None, 22)
            self.font_sm = pygame.font.Font(None, 18)
        
        self.close_btn_rect = None

    def draw(self, p1, p2, turn_idx, message, winner, sel_mode, sel_idx, scam_active=False, scam_type=None, scam_data=None, scam_input="", dice_vals=None):
        border_c = COLORS['positive'] if turn_idx == 0 else COLORS['ui_border']
        self.draw_player_panel(20, 20, p1, border_c, p1.name, COLORS['p1_bg'])
        
        is_p1 = (turn_idx == 0)
        self.draw_checklist(20, 390, p1, is_p1, sel_mode, sel_idx)

        border_c = COLORS['positive'] if turn_idx == 1 else COLORS['ui_border']
        self.draw_player_panel(990, 20, p2, border_c, p2.name, COLORS['p2_bg'])
        
        is_p2 = (turn_idx == 1)
        self.draw_checklist(990, 390, p2, is_p2, sel_mode, sel_idx)

        if not scam_active and not winner:
            self.draw_log_bar(message)
        
        if dice_vals and not winner:
            self.draw_dice(dice_vals)

        if winner:
            self.draw_scorecard(p1, p2, winner)
            
        if scam_active:
            self.draw_scam_window(scam_type, scam_data, scam_input)

    def draw_scorecard(self, p1, p2, finisher):
        # Dim Background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 230))
        self.screen.blit(overlay, (0, 0))

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        s1 = self.calculate_score(p1, finisher)
        s2 = self.calculate_score(p2, finisher)
        
        final_winner = p1 if s1['total'] > s2['total'] else p2
        if s1['total'] == s2['total']: final_winner = None 

        # Title
        self.draw_text("FINAL FINANCIAL REPORT", cx - 180, 50, size=32, color=COLORS['gold'])
        
        # --- ADJUSTED POSITIONS FOR WIDER COLUMNS ---
        # Width is now 300 per column. Gap is 40.
        # Left Panel X: cx - 300 - 20 = cx - 320
        # Right Panel X: cx + 20
        self.draw_score_column(cx - 320, 120, p1, s1, COLORS['p1_bg'])
        self.draw_score_column(cx + 20, 120, p2, s2, COLORS['p2_bg'])

        # Final Verdict
        if final_winner:
            msg = f"WINNER: {final_winner.name}!"
            col = COLORS['gold']
        else:
            msg = "IT'S A DRAW!"
            col = COLORS['white']
            
        pygame.draw.rect(self.screen, (50, 50, 50), (cx - 200, 600, 400, 60), border_radius=10)
        self.draw_text(msg, cx - 100, 615, size=32, color=col)
        self.draw_text("Press Q to Quit", cx - 60, 670, size=16, color=COLORS['text_dim'])

    def draw_score_column(self, x, y, p, s, color):
        w = 300 # INCREASED WIDTH (Was 250)
        h = 450
        pygame.draw.rect(self.screen, (30, 30, 35), (x, y, w, h), border_radius=10)
        pygame.draw.rect(self.screen, color, (x, y, w, h), 2, border_radius=10)
        
        # Header - INCREASED HEIGHT (Was 50)
        header_h = 60
        pygame.draw.rect(self.screen, color, (x, y, w, header_h), border_top_left_radius=8, border_top_right_radius=8)
        
        # Name - Centered vertically in header
        self.draw_text(p.name, x + 20, y + 15, size=24, color=COLORS['black'])
        
        current_y = y + header_h + 20
        gap = 40
        
        self.draw_score_row(x, current_y, "Net Worth", f"Rs. {s['raw_savings']}", f"+{s['savings']}", COLORS['positive'])
        current_y += gap
        self.draw_score_row(x, current_y, "Health", f"{p.health}", f"+{s['health']}", COLORS['active'])
        current_y += gap
        self.draw_score_row(x, current_y, "Happiness", f"{p.happiness}", f"+{s['happy']}", COLORS['gold'])
        current_y += gap
        self.draw_score_row(x, current_y, "Debt", f"Rs. {p.loan}", f"{s['debt']}", COLORS['red'])
        current_y += gap
        self.draw_score_row(x, current_y, "Finisher Bonus", "", f"+{s['bonus']}", COLORS['ui_accent'])
        
        # Total
        pygame.draw.line(self.screen, COLORS['text_dim'], (x+20, current_y + 20), (x+w-20, current_y+20))
        self.draw_text("TOTAL SCORE", x + 20, current_y + 40, size=18, color=COLORS['white'])
        self.draw_text(str(s['total']), x + 180, current_y + 35, size=32, color=color)

    def draw_score_row(self, x, y, label, val, pts, col):
        self.draw_text(label, x + 20, y, size=16, color=COLORS['text_dim'])
        if val:
            self.draw_text(val, x + 130, y+2, size=12, color=COLORS['white'])
        self.draw_text(pts, x + 230, y, size=18, color=col)

    def calculate_score(self, p, finisher):
        savings = p.wallet + p.bank_balance + p.fd_balance
        score_savings = int(savings / 100)
        score_health = int((p.health / 10) * 10)
        score_happy = int((p.happiness / 10) * 5)
        score_debt = int((p.loan / 100) * -2)
        score_bonus = 50 if p == finisher else 0
        
        total = score_savings + score_health + score_happy + score_debt + score_bonus
        
        return {
            "savings": score_savings,
            "health": score_health,
            "happy": score_happy,
            "debt": score_debt,
            "bonus": score_bonus,
            "total": total,
            "raw_savings": savings
        }

    # --- KEEP EXISTING METHODS ---
    def draw_dice(self, dice):
        cx, cy = SCREEN_WIDTH // 2, 80
        size = 50
        gap = 20
        bg_w = (size * 2) + (gap * 3)
        bg_h = size + 40
        s = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 150), (0, 0, bg_w, bg_h), border_radius=15)
        self.screen.blit(s, (cx - bg_w//2, cy - 20))
        self.draw_die_face(cx - size - gap//2, cy, size, dice[0])
        self.draw_die_face(cx + gap//2, cy, size, dice[1])
        total = dice[0] + dice[1]
        self.draw_text(f"MOVES: {total}", cx - 40, cy + size + 5, size=20, color=COLORS['gold'])

    def draw_die_face(self, x, y, size, value):
        pygame.draw.rect(self.screen, COLORS['white'], (x, y, size, size), border_radius=8)
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, size, size), 2, border_radius=8)
        dot_r = 4
        dot_col = COLORS['black']
        mid = size // 2
        q1 = size // 4
        q3 = size * 3 // 4
        dots = []
        if value == 1: dots = [(mid, mid)]
        elif value == 2: dots = [(q1, q1), (q3, q3)]
        elif value == 3: dots = [(q1, q1), (mid, mid), (q3, q3)]
        elif value == 4: dots = [(q1, q1), (q3, q1), (q1, q3), (q3, q3)]
        elif value == 5: dots = [(q1, q1), (q3, q1), (mid, mid), (q1, q3), (q3, q3)]
        elif value == 6: dots = [(q1, q1), (q3, q1), (q1, mid), (q3, mid), (q1, q3), (q3, q3)]
        for dx, dy in dots:
            pygame.draw.circle(self.screen, dot_col, (x + dx, y + dy), dot_r)

    def draw_scam_window(self, scam_type, data, user_input):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) 
        self.screen.blit(overlay, (0, 0))
        w, h = 600, 400
        x = (SCREEN_WIDTH - w) // 2
        y = (SCREEN_HEIGHT - h) // 2
        pygame.draw.rect(self.screen, (30, 30, 35), (x, y, w, h), border_radius=12)
        pygame.draw.rect(self.screen, COLORS['red'], (x, y, w, h), 2, border_radius=12)
        pygame.draw.rect(self.screen, (150, 40, 40), (x, y, w, 50), border_top_left_radius=10, border_top_right_radius=10)
        title = "SECURITY ALERT: VERIFICATION REQUIRED" if scam_type == "OTP" else "INCOMING CALL: BANK ALERT"
        self.draw_text(title, x + 20, y + 12, size=20, color=COLORS['white'])
        close_x = x + w - 40
        close_y = y + 10
        pygame.draw.rect(self.screen, (200, 50, 50), (close_x, close_y, 30, 30), border_radius=5)
        self.draw_text("X", close_x + 9, close_y + 4, size=20, color=COLORS['white'])
        self.close_btn_rect = pygame.Rect(close_x, close_y, 30, 30)
        content_y = y + 80
        if scam_type == "OTP":
            self.draw_text("Unknown Device detected! Enter OTP to verify.", x+30, content_y, size=18, color=COLORS['text_dim'])
            problem = data.get('problem', "Loading...")
            idx = data.get('current_idx', 0) + 1
            self.draw_text(f"Digit #{idx}: Solve this:", x+30, content_y + 40, size=20, color=COLORS['white'])
            self.draw_text(f"{problem}", x+200, content_y + 90, size=40, color=COLORS['gold'])
        elif scam_type == "QUIZ":
            questions = data.get('questions', [])
            q_idx = data.get('current_q_idx', 0)
            if questions and q_idx < len(questions):
                q_item = questions[q_idx]
                question_text = q_item['q']
                options = q_item.get('opts', [])
                self.draw_text(f"Question {q_idx+1}/{len(questions)}:", x+30, content_y, size=18, color=COLORS['text_dim'])
                self.draw_text(question_text, x+30, content_y + 35, size=22, color=COLORS['white'])
                opt_y = content_y + 80
                for opt in options:
                    pygame.draw.rect(self.screen, (50, 50, 60), (x+30, opt_y, w-60, 35), border_radius=5)
                    self.draw_text(f"- {opt}", x+40, opt_y+8, size=18, color=COLORS['ui_accent'])
                    opt_y += 45
        input_y = y + h - 80
        self.draw_text("YOUR ANSWER:", x+30, input_y, size=16, color=COLORS['text_dim'])
        pygame.draw.rect(self.screen, (255, 255, 255), (x+150, input_y-5, 300, 35), border_radius=5)
        self.draw_text(user_input, x+160, input_y+2, size=20, color=COLORS['black'])
        self.draw_text("Press ESC to Cancel (Penalty Applies)", x + w//2 - 120, y + h - 25, size=14, color=COLORS['text_dim'])

    def draw_checklist(self, x, y, p, is_turn, sel_mode, sel_idx):
        w, h = 270, 260
        self.draw_panel_bg(x, y, w, h, COLORS['ui_border'])
        self.draw_text("NEEDS [N]", x+10, y+10, size=14, color=COLORS['white'])
        self.draw_text("WANTS [W]", x+140, y+10, size=14, color=COLORS['white'])
        pygame.draw.line(self.screen, COLORS['ui_border'], (x+10, y+28), (x+w-10, y+28), 1)
        start_y = y + 35
        row_h = 18
        current_y = start_y
        for name in p.completed_needs:
            self.draw_text(f"v {name}", x+10, current_y, size=13, color=COLORS['positive'])
            current_y += row_h
        for i, (name, cost) in enumerate(p.pending_needs):
            col = COLORS['red']
            prefix = "o "
            if is_turn and sel_mode == 'NEEDS' and sel_idx == i:
                col = COLORS['active']
                prefix = "> "
                pygame.draw.rect(self.screen, (50, 50, 60), (x+5, current_y-2, 120, row_h), border_radius=3)
                pygame.draw.rect(self.screen, COLORS['active'], (x+5, current_y-2, 120, row_h), 1, border_radius=3)
            self.draw_text(f"{prefix}{name} Rs. {cost}", x+10, current_y, size=13, color=col)
            current_y += row_h
        current_y = start_y
        for name in p.completed_wants:
            self.draw_text(f"v {name}", x+140, current_y, size=13, color=COLORS['gold'])
            current_y += row_h
        for i, (name, cost, hap) in enumerate(p.pending_wants):
            col = COLORS['ui_accent']
            prefix = "o "
            if is_turn and sel_mode == 'WANTS' and sel_idx == i:
                col = COLORS['active']
                prefix = "> "
                pygame.draw.rect(self.screen, (50, 50, 60), (x+135, current_y-2, 120, row_h), border_radius=3)
                pygame.draw.rect(self.screen, COLORS['active'], (x+135, current_y-2, 120, row_h), 1, border_radius=3)
            self.draw_text(f"{prefix}{name} Rs. {cost}", x+140, current_y, size=13, color=col)
            current_y += row_h

    def draw_player_panel(self, x, y, p, border_col, name, title_bg):
        w, h = 270, 360
        self.draw_panel_bg(x, y, w, h, border_col)
        pygame.draw.rect(self.screen, title_bg, (x, y, w, 40), border_top_left_radius=8, border_top_right_radius=8)
        self.draw_text(f"{name}", x+10, y+8, size=20, color=COLORS['white'])
        self.draw_bar_modern(x+10, y+60, w=120, label="Health", val=p.health, max_val=100, col=COLORS['red'])
        self.draw_bar_modern(x+140, y+60, w=120, label="Happiness", val=p.happiness, max_val=100, col=COLORS['gold'])
        self.draw_inner_box(x+10, y+95, w-20, 95)
        self.draw_text("WALLET", x+20, y+100, size=14, color=COLORS['text_dim'])
        self.draw_text("BANK", x+150, y+100, size=14, color=COLORS['text_dim'])
        self.draw_text(f"Rs. {p.wallet}", x+20, y+120, size=22, color=COLORS['positive'])
        self.draw_text(f"Rs. {p.bank_balance}", x+150, y+120, size=22, color=COLORS['ui_accent'])
        y_status = y + 160
        if p.loan > 0:
            self.draw_text(f"DEBT: -Rs. {p.loan}", x+20, y_status, size=16, color=COLORS['negative'])
        elif p.fd_balance > 0:
             self.draw_text(f"FD: Rs. {p.fd_balance} ({p.fd_timer}t)", x+20, y_status, size=16, color=COLORS['gold'])
        else:
             self.draw_text("No Debt", x+20, y_status, size=16, color=COLORS['text_dim'])
        y_prog = y + 205
        pygame.draw.line(self.screen, COLORS['ui_border'], (x+10, y_prog), (x+w-10, y_prog), 1)
        self.draw_text("PROGRESS SUMMARY", x+10, y_prog+10, size=16, color=COLORS['text_main'])
        n_count = len(p.completed_needs)
        self.draw_progress_row(x+10, y_prog+35, "Needs Paid", n_count, 10, COLORS['p1_bg'])
        w_count = len(p.completed_wants)
        self.draw_progress_row(x+10, y_prog+80, "Wants Bought", w_count, 10, COLORS['gold'])
        self.draw_text("Press N/W to Pay/Buy", x+60, y+335, size=14, color=COLORS['text_dim'])

    def draw_log_bar(self, message):
        h = 50
        y = SCREEN_HEIGHT - h - 10
        w = 800
        x = (SCREEN_WIDTH - w) // 2
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 20, 25, 240), (0, 0, w, h), border_radius=25)
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, COLORS['ui_border'], (x, y, w, h), 2, border_radius=25)
        col = COLORS['text_main']
        if "SCAMMED" in message: col = COLORS['negative']
        if "WINS" in message: col = COLORS['gold']
        txt = self.font_lg.render(message, True, col)
        rect = txt.get_rect(center=(SCREEN_WIDTH // 2, y + h // 2))
        self.screen.blit(txt, rect)

    def draw_panel_bg(self, x, y, w, h, border_col):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill(COLORS['ui_bg']) 
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, border_col, (x, y, w, h), 2, border_radius=8)

    def draw_inner_box(self, x, y, w, h):
        pygame.draw.rect(self.screen, (20, 20, 25, 150), (x, y, w, h), border_radius=5)

    def draw_bar_modern(self, x, y, w, label, val, max_val, col):
        self.draw_text(label, x, y-18, size=14, color=COLORS['text_dim'])
        pygame.draw.rect(self.screen, (50, 50, 60), (x, y, w, 8), border_radius=4)
        safe_val = min(val, max_val)
        fill_w = int((safe_val / max_val) * w)
        if fill_w > 0:
            pygame.draw.rect(self.screen, col, (x, y, fill_w, 8), border_radius=4)

    def draw_progress_row(self, x, y, label, count, max_count, col):
        self.draw_text(label, x, y, size=14, color=COLORS['text_main'])
        self.draw_text(f"{count}/{max_count}", x+200, y, size=14, color=col)
        bx, by = x, y + 20
        block_w, gap = 20, 4
        for i in range(max_count):
            color = col if i < count else (60, 60, 70)
            pygame.draw.rect(self.screen, color, (bx + (i * (block_w + gap)), by, block_w, 10), border_radius=2)

    def draw_text(self, text, x, y, size=18, color=(255, 255, 255)):
        if size >= 32: f = self.font_xl
        elif size >= 20: f = self.font_lg
        elif size >= 16: f = self.font_md
        else: f = self.font_sm
        surf = f.render(str(text), True, color)
        self.screen.blit(surf, (x, y))