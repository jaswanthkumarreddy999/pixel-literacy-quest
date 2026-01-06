import pygame
import sys
import platform
import ctypes
from config.settings import *
from config.assets import loader

# --- DPI AWARENESS FIX (Windows Only) ---
if platform.system() == "Windows":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

class HUD:
    def __init__(self, screen):
        self.screen = screen
        
        # --- DYNAMIC ENVIRONMENT SCALING ---
        is_web = sys.platform == "emscripten"
        is_linux = platform.system() == "Linux"
        
        # Using 1.1 for desktop to keep it large, but adjusted font_sm below
        if is_web:
            scale = 0.90
        elif is_linux:
            scale = 1.0
        else:
            scale = 1.1

        try:
            self.font_xl = pygame.font.SysFont("Segoe UI", int(34 * scale), bold=True)
            self.font_lg = pygame.font.SysFont("Segoe UI", int(22 * scale), bold=True)
            self.font_md = pygame.font.SysFont("Segoe UI", int(18 * scale), bold=True)
            # FIX: Slightly smaller base for the checklist items to prevent column overlap
            self.font_sm = pygame.font.SysFont("Segoe UI", int(13 * scale), bold=True) 
        except:
            self.font_xl = pygame.font.Font(None, int(42 * scale))
            self.font_lg = pygame.font.Font(None, int(30 * scale))
            self.font_md = pygame.font.Font(None, int(24 * scale))
            self.font_sm = pygame.font.Font(None, int(18 * scale))
        
        self.close_btn_rect = None

    def draw(self, p1, p2, turn_idx, message, winner, sel_mode, sel_idx, scam_active=False, scam_type=None, scam_data=None, scam_input="", dice_vals=None):
        # Draw Player 1 Panels
        border_c = COLORS['positive'] if turn_idx == 0 else COLORS['ui_border']
        self.draw_player_panel(20, 20, p1, border_c, p1.name, COLORS['p1_bg'])
        self.draw_checklist(20, 390, p1, (turn_idx == 0), sel_mode, sel_idx)

        # Draw Player 2 Panels
        border_c = COLORS['positive'] if turn_idx == 1 else COLORS['ui_border']
        self.draw_player_panel(990, 20, p2, border_c, p2.name, COLORS['p2_bg'])
        self.draw_checklist(990, 390, p2, (turn_idx == 1), sel_mode, sel_idx)

        if not scam_active and not winner:
            self.draw_log_bar(message)
        
        if dice_vals and not winner:
            self.draw_dice(dice_vals)

        if winner:
            self.draw_scorecard(p1, p2, winner)
            
        if scam_active:
            self.draw_scam_window(scam_type, scam_data, scam_input)

    def draw_checklist(self, x, y, p, is_turn, sel_mode, sel_idx):
        w, h = 270, 260
        self.draw_panel_bg(x, y, w, h, COLORS['ui_border'])
        
        # --- FIX: COLUMN COORDINATES ---
        # Separating the X coordinates clearly to prevent overlap
        col1_x = x + 10
        col2_x = x + 140 
        
        self.draw_text("NEEDS [N]", col1_x, y+10, size=15, color=COLORS['white'])
        self.draw_text("WANTS [W]", col2_x, y+10, size=15, color=COLORS['white'])
        pygame.draw.line(self.screen, COLORS['ui_border'], (x+10, y+28), (x+w-10, y+28), 2)
        
        row_h = self.font_sm.get_linesize() + 2
        start_y = y + 38
        max_y = y + h - 10 

        # --- DRAW NEEDS ---
        curr_y = start_y
        for name in p.completed_needs:
            if curr_y + row_h < max_y:
                self.draw_text(f"v {name}", col1_x, curr_y, size=13, color=COLORS['positive'])
                curr_y += row_h
        
        for i, (name, cost) in enumerate(p.pending_needs):
            if curr_y + row_h < max_y:
                col = COLORS['red']
                prefix = "o "
                if is_turn and sel_mode == 'NEEDS' and sel_idx == i:
                    col = COLORS['active']
                    prefix = "> "
                    # Narrow selection box so it doesn't touch the second column
                    pygame.draw.rect(self.screen, (60, 60, 75), (col1_x - 4, curr_y-1, 125, row_h), border_radius=3)
                
                # Using '₹' or removing 'Rs.' helps save horizontal space
                self.draw_text(f"{prefix}{name} ₹{cost}", col1_x, curr_y, size=13, color=col)
                curr_y += row_h

        # --- DRAW WANTS ---
        curr_y = start_y
        for name in p.completed_wants:
            if curr_y + row_h < max_y:
                self.draw_text(f"v {name}", col2_x, curr_y, size=13, color=COLORS['gold'])
                curr_y += row_h
        
        for i, (name, cost, hap) in enumerate(p.pending_wants):
            if curr_y + row_h < max_y:
                col = COLORS['ui_accent']
                prefix = "o "
                if is_turn and sel_mode == 'WANTS' and sel_idx == i:
                    col = COLORS['active']
                    prefix = "> "
                    pygame.draw.rect(self.screen, (60, 60, 75), (col2_x - 4, curr_y-1, 128, row_h), border_radius=3)
                
                self.draw_text(f"{prefix}{name} ₹{cost}", col2_x, curr_y, size=13, color=col)
                curr_y += row_h

    def draw_player_panel(self, x, y, p, border_col, name, title_bg):
        w, h = 270, 360
        self.draw_panel_bg(x, y, w, h, border_col)
        pygame.draw.rect(self.screen, title_bg, (x, y, w, 40), border_top_left_radius=8, border_top_right_radius=8)
        self.draw_text(f"{name}", x+10, y+8, size=22, color=COLORS['white'])
        
        self.draw_bar_modern(x+10, y+60, w=120, label="Health", val=p.health, max_val=100, col=COLORS['red'])
        self.draw_bar_modern(x+140, y+60, w=120, label="Happiness", val=p.happiness, max_val=100, col=COLORS['gold'])
        
        self.draw_inner_box(x+10, y+95, w-20, 95)
        self.draw_text("WALLET", x+20, y+100, size=15, color=COLORS['text_dim'])
        self.draw_text("BANK", x+150, y+100, size=15, color=COLORS['text_dim'])
        self.draw_text(f"Rs. {p.wallet}", x+20, y+120, size=24, color=COLORS['positive'])
        self.draw_text(f"Rs. {p.bank_balance}", x+150, y+120, size=24, color=COLORS['ui_accent'])
        
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
        self.draw_progress_row(x+10, y_prog+35, "Needs Paid", len(p.completed_needs), 10, COLORS['p1_bg'])
        self.draw_progress_row(x+10, y_prog+80, "Wants Bought", len(p.completed_wants), 10, COLORS['gold'])
        self.draw_text("Press N/W to Pay/Buy", x+60, y+335, size=15, color=COLORS['text_dim'])

    def draw_text(self, text, x, y, size=18, color=(255, 255, 255)):
        """FIX: Mapping size logic to match font variables."""
        if size >= 32: f = self.font_xl
        elif size >= 20: f = self.font_lg
        elif size >= 15: f = self.font_md
        else: f = self.font_sm
        
        surf = f.render(str(text), True, color)
        self.screen.blit(surf, (x, y))

    def draw_bar_modern(self, x, y, w, label, val, max_val, col):
        self.draw_text(label, x, y-18, size=14, color=COLORS['text_dim'])
        pygame.draw.rect(self.screen, (50, 50, 60), (x, y, w, 8), border_radius=4)
        fill_w = int((min(val, max_val) / max_val) * w)
        if fill_w > 0: 
            pygame.draw.rect(self.screen, col, (x, y, fill_w, 8), border_radius=4)

    def draw_progress_row(self, x, y, label, count, max_count, col):
        self.draw_text(label, x, y, size=15, color=COLORS['text_main'])
        self.draw_text(f"{count}/{max_count}", x+200, y, size=15, color=col)
        bx, by = x, y + 22
        block_w, gap = 20, 4
        for i in range(max_count):
            color = col if i < count else (60, 60, 70)
            pygame.draw.rect(self.screen, color, (bx + (i * (block_w + gap)), by, block_w, 12), border_radius=2)

    def draw_log_bar(self, message):
        h, w = 60, 850
        y, x = SCREEN_HEIGHT - h - 10, (SCREEN_WIDTH - w) // 2
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 20, 25, 240), (0, 0, w, h), border_radius=30)
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, COLORS['ui_border'], (x, y, w, h), 2, border_radius=30)
        col = COLORS['text_main']
        if "SCAMMED" in message: col = COLORS['negative']
        elif "WINS" in message: col = COLORS['gold']
        txt = self.font_lg.render(message, True, col)
        rect = txt.get_rect(center=(SCREEN_WIDTH // 2, y + h // 2))
        self.screen.blit(txt, rect)

    def draw_panel_bg(self, x, y, w, h, border_col):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill(COLORS['ui_bg']) 
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, border_col, (x, y, w, h), 2, border_radius=10)

    def draw_inner_box(self, x, y, w, h):
        pygame.draw.rect(self.screen, (20, 20, 25, 150), (x, y, w, h), border_radius=8)

    def draw_dice(self, dice):
        cx, cy = SCREEN_WIDTH // 2, 80
        size, gap = 55, 25
        bg_w, bg_h = (size * 2) + (gap * 3), size + 45
        s = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, bg_w, bg_h), border_radius=20)
        self.screen.blit(s, (cx - bg_w//2, cy - 20))
        self.draw_die_face(cx - size - gap//2, cy, size, dice[0])
        self.draw_die_face(cx + gap//2, cy, size, dice[1])
        self.draw_text(f"MOVES: {dice[0] + dice[1]}", cx - 45, cy + size + 8, size=20, color=COLORS['gold'])

    def draw_die_face(self, x, y, size, value):
        pygame.draw.rect(self.screen, COLORS['white'], (x, y, size, size), border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, size, size), 2, border_radius=10)
        dot_r, dot_col = 5, COLORS['black']
        mid, q1, q3 = size // 2, size // 4, size * 3 // 4
        dots = []
        if value == 1: dots = [(mid, mid)]
        elif value == 2: dots = [(q1, q1), (q3, q3)]
        elif value == 3: dots = [(q1, q1), (mid, mid), (q3, q3)]
        elif value == 4: dots = [(q1, q1), (q3, q1), (q1, q3), (q3, q3)]
        elif value == 5: dots = [(q1, q1), (q3, q1), (mid, mid), (q1, q3), (q3, q3)]
        elif value == 6: dots = [(q1, q1), (q3, q1), (q1, mid), (q3, mid), (q1, q3), (q3, q3)]
        for dx, dy in dots: pygame.draw.circle(self.screen, dot_col, (x + dx, y + dy), dot_r)

    def draw_scorecard(self, p1, p2, finisher):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 230))
        self.screen.blit(overlay, (0, 0))
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        s1 = self.calculate_score(p1, finisher)
        s2 = self.calculate_score(p2, finisher)
        final_winner = p1 if s1['total'] > s2['total'] else p2
        if s1['total'] == s2['total']: final_winner = None 
        self.draw_text("FINAL FINANCIAL REPORT", cx - 200, 50, size=32, color=COLORS['gold'])
        self.draw_score_column(cx - 340, 120, p1, s1, COLORS['p1_bg'])
        self.draw_score_column(cx + 40, 120, p2, s2, COLORS['p2_bg'])
        msg = f"WINNER: {final_winner.name}!" if final_winner else "IT'S A DRAW!"
        col = COLORS['gold'] if final_winner else COLORS['white']
        pygame.draw.rect(self.screen, (50, 50, 50), (cx - 220, 600, 440, 70), border_radius=15)
        self.draw_text(msg, cx - 110, 618, size=32, color=col)

    def draw_score_column(self, x, y, p, s, color):
        w, h = 300, 450
        pygame.draw.rect(self.screen, (30, 30, 35), (x, y, w, h), border_radius=15)
        pygame.draw.rect(self.screen, color, (x, y, w, h), 2, border_radius=15)
        header_h = 60
        pygame.draw.rect(self.screen, color, (x, y, w, header_h), border_top_left_radius=12, border_top_right_radius=12)
        self.draw_text(p.name, x + 20, y + 15, size=26, color=COLORS['black'])
        current_y = y + header_h + 20
        gap = 45
        self.draw_score_row(x, current_y, "Net Worth", f"Rs. {s['raw_savings']}", f"+{s['savings']}", COLORS['positive'])
        current_y += gap
        self.draw_score_row(x, current_y, "Health", f"{p.health}", f"+{s['health']}", COLORS['active'])
        current_y += gap
        self.draw_score_row(x, current_y, "Happiness", f"{p.happiness}", f"+{s['happy']}", COLORS['gold'])
        current_y += gap
        self.draw_score_row(x, current_y, "Debt", f"Rs. {p.loan}", f"{s['debt']}", COLORS['red'])
        current_y += gap
        self.draw_score_row(x, current_y, "Finisher Bonus", "", f"+{s['bonus']}", COLORS['ui_accent'])
        pygame.draw.line(self.screen, COLORS['text_dim'], (x+20, current_y + 20), (x+w-20, current_y+20))
        self.draw_text("TOTAL SCORE", x + 20, current_y + 40, size=20, color=COLORS['white'])
        self.draw_text(str(s['total']), x + 180, current_y + 35, size=36, color=color)

    def draw_score_row(self, x, y, label, val, pts, col):
        self.draw_text(label, x + 20, y, size=18, color=COLORS['text_dim'])
        if val:
            self.draw_text(val, x + 130, y+2, size=13, color=COLORS['white'])
        self.draw_text(pts, x + 230, y, size=20, color=col)

    def calculate_score(self, p, finisher):
        savings = p.wallet + p.bank_balance + p.fd_balance
        score_savings = int(savings / 100)
        score_health = int((p.health / 10) * 10)
        score_happy = int((p.happiness / 10) * 5)
        score_debt = int((p.loan / 100) * -2)
        score_bonus = 50 if p == finisher else 0
        total = score_savings + score_health + score_happy + score_debt + score_bonus
        return {"savings": score_savings, "health": score_health, "happy": score_happy, "debt": score_debt, "bonus": score_bonus, "total": total, "raw_savings": savings}

    def draw_scam_window(self, scam_type, data, user_input):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200)) 
        self.screen.blit(overlay, (0, 0))
        w, h = 650, 450
        x, y = (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        pygame.draw.rect(self.screen, (30, 30, 35), (x, y, w, h), border_radius=15)
        pygame.draw.rect(self.screen, COLORS['red'], (x, y, w, h), 2, border_radius=15)
        pygame.draw.rect(self.screen, (150, 40, 40), (x, y, w, 60), border_top_left_radius=13, border_top_right_radius=13)
        title = "SECURITY ALERT: VERIFICATION REQUIRED" if scam_type == "OTP" else "INCOMING CALL: BANK ALERT"
        self.draw_text(title, x + 25, y + 18, size=22, color=COLORS['white'])
        
        close_x, close_y = x + w - 45, y + 15
        pygame.draw.rect(self.screen, (200, 50, 50), (close_x, close_y, 35, 35), border_radius=8)
        self.draw_text("X", close_x + 11, close_y + 5, size=22, color=COLORS['white'])
        self.close_btn_rect = pygame.Rect(close_x, close_y, 35, 35)

        content_y = y + 100
        if scam_type == "OTP":
            self.draw_text("Unknown Device detected! Enter OTP to verify.", x+40, content_y, size=20, color=COLORS['text_dim'])
            problem, idx = data.get('problem', "Loading..."), data.get('current_idx', 0) + 1
            self.draw_text(f"Digit #{idx}: Solve this:", x+40, content_y + 50, size=22, color=COLORS['white'])
            self.draw_text(f"{problem}", x+250, content_y + 110, size=48, color=COLORS['gold'])
        elif scam_type == "QUIZ":
            questions, q_idx = data.get('questions', []), data.get('current_q_idx', 0)
            if questions and q_idx < len(questions):
                q_item = questions[q_idx]
                self.draw_text(f"Question {q_idx+1}/{len(questions)}:", x+40, content_y, size=20, color=COLORS['text_dim'])
                self.draw_text(q_item['q'], x+40, content_y + 40, size=24, color=COLORS['white'])
                opt_y = content_y + 100
                for opt in q_item.get('opts', []):
                    pygame.draw.rect(self.screen, (55, 55, 65), (x+40, opt_y, w-80, 45), border_radius=8)
                    self.draw_text(f"- {opt}", x+55, opt_y+10, size=20, color=COLORS['ui_accent'])
                    opt_y += 55

        input_y = y + h - 100
        self.draw_text("YOUR ANSWER:", x+40, input_y, size=18, color=COLORS['text_dim'])
        pygame.draw.rect(self.screen, (255, 255, 255), (x+180, input_y-5, 300, 45), border_radius=8)
        self.draw_text(user_input, x+195, input_y+5, size=24, color=COLORS['black'])