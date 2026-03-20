import pygame
import sys
import platform
import ctypes
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, DIGITAL_ONLY, BUDGET_OPTIONS,
    MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, GRID_COLS, GRID_ROWS,
    MAP_X, MAP_Y, ICON_SIZE, MONTHLY_INCOME
)
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
            self.font_sm = pygame.font.SysFont("Segoe UI", int(13 * scale), bold=True) 
        except:
            self.font_xl = pygame.font.Font(None, int(42 * scale))
            self.font_lg = pygame.font.Font(None, int(30 * scale))
            self.font_md = pygame.font.Font(None, int(24 * scale))
            self.font_sm = pygame.font.Font(None, int(18 * scale))
        
        # Interactive Hitboxes
        self.click_regions = [] 
        self.close_btn_rect = None

    def draw(self, p1, p2, turn_idx, logs, winner, sel_mode, sel_idx, scam_active=False, scam_type=None, scam_data=None, scam_input="", dice_vals=None, popup_active=False, popup_message="", scam_failed=False, scam_explanation="", game_manager=None):
        self.click_regions = [] # Reset click map every frame
        
        # Draw Player 1 Panels
        border_c = COLORS['positive'] if turn_idx == 0 else COLORS['ui_border']
        self.draw_player_panel(20, 20, p1, border_c, p1.name, COLORS['p1_bg'])
        self.draw_checklist(20, 390, p1, (turn_idx == 0), sel_mode, sel_idx)

        # Draw Player 2 Panels
        border_c = COLORS['positive'] if turn_idx == 1 else COLORS['ui_border']
        self.draw_player_panel(990, 20, p2, border_c, p2.name, COLORS['p2_bg'])
        self.draw_checklist(990, 390, p2, (turn_idx == 1), sel_mode, sel_idx)

        if not scam_active and not winner and not popup_active:
            self.draw_log_bar(logs)
            
        if popup_active:
            self.draw_knowledge_popup(popup_message)
        
        if dice_vals and not winner:
            self.draw_dice(dice_vals)

        if winner:
            self.draw_scorecard(p1, p2, winner)
            
        if scam_active:
            self.draw_scam_window(scam_type, scam_data, scam_input, scam_failed, scam_explanation)

        if game_manager:
            if getattr(game_manager, 'in_bank', False) and getattr(game_manager, 'bank_mode', "MENU") == "MENU":
                self.draw_bank_menu(game_manager.get_current_player(), game_manager)
                
            if getattr(game_manager, 'budget_active', False):
                self.draw_budget_window(game_manager.budget_player)
                
            if getattr(game_manager, 'popup_active', False):
                self.draw_knowledge_popup(game_manager.popup_message)
            
            if getattr(game_manager, 'tip_active', False):
                self.draw_tip_card(game_manager.tip_title, game_manager.tip_text)
                
            # Draw Floating Texts
            for ft in getattr(game_manager, 'float_texts', []):
                # txt_col = list(ft['color']) + [int(ft['alpha'])] # This line is not needed for render
                font_surf = self.font_md.render(ft['text'], True, ft['color'])
                font_surf.set_alpha(ft['alpha'])
                self.screen.blit(font_surf, (ft['x'], ft['y']))

    def draw_checklist(self, x, y, p, is_turn, sel_mode, sel_idx):
        w, h = 270, 260
        self.draw_panel_bg(x, y, w, h, COLORS['ui_border'])
        
        col1_x = x + 10
        col2_x = x + 140 
        
        self.draw_text("NEEDS [N]", col1_x, y+10, size=15, color=COLORS['white'])
        self.draw_text("WANTS [W]", col2_x, y+10, size=15, color=COLORS['white'])
        pygame.draw.line(self.screen, COLORS['ui_border'], (x+10, y+28), (x+w-10, y+28), 2)
        
        row_h = self.font_sm.get_linesize() + 2
        start_y = y + 38
        max_y = y + h - 10 
        m_pos = pygame.mouse.get_pos()

        # --- DRAW NEEDS ---
        curr_y = start_y
        for name in p.completed_needs:
            if curr_y + row_h < max_y:
                self.draw_text(f"v {name}", col1_x, curr_y, size=13, color=COLORS['positive'])
                curr_y += row_h
        
        for i, (name, cost) in enumerate(p.pending_needs):
            if curr_y + row_h < max_y:
                rect = pygame.Rect(col1_x - 4, curr_y - 1, 125, row_h)
                is_hovered = rect.collidepoint(m_pos)
                
                # Logic: Is this specific item selected or hovered?
                is_selected = (is_turn and sel_mode == 'NEEDS' and sel_idx == i)
                
                if is_turn:
                    self.click_regions.append({'rect': rect, 'type': 'SEL', 'mode': 'NEEDS', 'idx': i})
                
                if is_selected:
                    pygame.draw.rect(self.screen, (60, 60, 75), rect, border_radius=3)
                    col = COLORS['active']
                elif is_hovered and is_turn:
                    pygame.draw.rect(self.screen, (45, 45, 55), rect, border_radius=3)
                    col = COLORS['white']
                else:
                    col = COLORS['red']

                prefix = "[D] " if name in DIGITAL_ONLY else ""
                self.draw_text(f"o {prefix}{name} ₹{cost}", col1_x, curr_y, size=12, color=col)
                curr_y += row_h

        # --- DRAW WANTS ---
        curr_y = start_y
        for name in p.completed_wants:
            if curr_y + row_h < max_y:
                self.draw_text(f"v {name}", col2_x, curr_y, size=13, color=COLORS['gold'])
                curr_y += row_h
        
        for i, (name, cost, hap) in enumerate(p.pending_wants):
            if curr_y + row_h < max_y:
                rect = pygame.Rect(col2_x - 4, curr_y - 1, 128, row_h)
                is_hovered = rect.collidepoint(m_pos)
                is_selected = (is_turn and sel_mode == 'WANTS' and sel_idx == i)

                if is_turn:
                    self.click_regions.append({'rect': rect, 'type': 'SEL', 'mode': 'WANTS', 'idx': i})

                if is_selected:
                    pygame.draw.rect(self.screen, (60, 60, 75), rect, border_radius=3)
                    col = COLORS['active']
                elif is_hovered and is_turn:
                    pygame.draw.rect(self.screen, (45, 45, 55), rect, border_radius=3)
                    col = COLORS['white']
                else:
                    col = COLORS['ui_accent']
                
                prefix = "[D] " if name in DIGITAL_ONLY else ""
                self.draw_text(f"o {prefix}{name} ₹{cost}", col2_x, curr_y, size=12, color=col)
                curr_y += row_h

    def draw_dice(self, dice):
        cx, cy = SCREEN_WIDTH // 2, 80
        size = 55
        # Hitbox for clicking dice
        dice_rect = pygame.Rect(cx - 75, cy - 25, 150, 110)
        self.click_regions.append({'rect': dice_rect, 'type': 'DICE'})
        
        is_hover = dice_rect.collidepoint(pygame.mouse.get_pos())
        bg_col = (40, 40, 50, 200) if is_hover else (0, 0, 0, 180)

        s = pygame.Surface((150, 110), pygame.SRCALPHA)
        pygame.draw.rect(s, bg_col, (0, 0, 150, 110), border_radius=20)
        self.screen.blit(s, (cx - 75, cy - 25))
        
        self.draw_die_face(cx - 60, cy, size, dice[0])
        self.draw_die_face(cx + 5, cy, size, dice[1])
        self.draw_text("CLICK TO ROLL", cx - 45, cy + 68, size=14, color=COLORS['gold'])

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
        self.draw_progress_row(x+10, y_prog+35, "Needs Paid", len(p.completed_needs), 10, COLORS['p1_bg'])
        self.draw_progress_row(x+10, y_prog+80, "Wants Bought", len(p.completed_wants), 10, COLORS['gold'])

    def draw_text(self, text, x, y, size=18, color=(255, 255, 255)):
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

    def draw_log_bar(self, logs):
        h, w = 90, 850
        y, x = SCREEN_HEIGHT - h - 10, (SCREEN_WIDTH - w) // 2
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        # Glassmorphic: Lower alpha (140) and draw border on the same surface
        pygame.draw.rect(s, (20, 20, 25, 140), (0, 0, w, h), border_radius=30)
        pygame.draw.rect(s, (100, 100, 120, 180), (0, 0, w, h), 2, border_radius=30)
        self.screen.blit(s, (x, y))
        
        if not isinstance(logs, list): logs = [logs]
            
        start_y = y + 15
        for i, msg in enumerate(logs[-3:]):
            col = COLORS['text_dim'] if i < len(logs[-3:]) - 1 else COLORS['text_main']
            if "SCAMMED" in msg or "LOAN DUE" in msg or "Lost" in msg or "PICKPOCKET" in msg: col = COLORS['negative']
            elif "WINS" in msg or "Paid" in msg or "Bought" in msg: col = COLORS['gold']
            
            txt = self.font_md.render(msg, True, col)
            rect = txt.get_rect(center=(SCREEN_WIDTH // 2, start_y + (i * 25)))
            self.screen.blit(txt, rect)

    def draw_knowledge_popup(self, message):
        w, h = 600, 200
        x, y = (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150)) 
        self.screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(self.screen, (30, 40, 60), (x, y, w, h), border_radius=15)
        pygame.draw.rect(self.screen, COLORS['gold'], (x, y, w, h), 3, border_radius=15)
        
        title = self.font_lg.render("DID YOU KNOW?", True, COLORS['gold'])
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, y + 40)))
        
        parts = message.split("! ")
        for i, part in enumerate(parts):
            txt = part + ("!" if i < len(parts)-1 else "")
            rendered = self.font_md.render(txt, True, COLORS['white'])
            self.screen.blit(rendered, rendered.get_rect(center=(SCREEN_WIDTH // 2, y + 90 + (i * 30))))

    def draw_panel_bg(self, x, y, w, h, border_col):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill(COLORS['ui_bg']) 
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, border_col, (x, y, w, h), 2, border_radius=10)

    def draw_inner_box(self, x, y, w, h):
        pygame.draw.rect(self.screen, (20, 20, 25, 150), (x, y, w, h), border_radius=8)

    def draw_scam_window(self, scam_type, data, user_input, failed=False, explanation=""):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200)) 
        self.screen.blit(overlay, (0, 0))
        w, h = 650, 450
        x, y = (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        pygame.draw.rect(self.screen, (30, 30, 35), (x, y, w, h), border_radius=15)
        pygame.draw.rect(self.screen, COLORS['red'], (x, y, w, h), 2, border_radius=15)
        pygame.draw.rect(self.screen, (150, 40, 40), (x, y, w, 60), border_top_left_radius=13, border_top_right_radius=13)
        title = "SECURITY ALERT" if scam_type == "OTP" else "INCOMING CALL"
        self.draw_text(title, x + 25, y + 18, size=22, color=COLORS['white'])
        
        close_x, close_y = x + w - 45, y + 15
        pygame.draw.rect(self.screen, (200, 50, 50), (close_x, close_y, 35, 35), border_radius=8)
        self.draw_text("X", close_x + 11, close_y + 5, size=22, color=COLORS['white'])
        self.close_btn_rect = pygame.Rect(close_x, close_y, 35, 35)

        content_y = y + 100
        
        if failed:
            self.draw_text("SCAMMED!", x+250, content_y, size=32, color=COLORS['negative'])
            
            # wrap explanation if it's too long
            words = explanation.split(' ')
            lines = []
            curr_line = ""
            for word in words:
                if len(curr_line) + len(word) < 40:
                    curr_line += word + " "
                else:
                    lines.append(curr_line)
                    curr_line = word + " "
            lines.append(curr_line)
            
            for i, line in enumerate(lines):
                 self.draw_text(line, x+40, content_y + 60 + (i*30), size=24, color=COLORS['white'])
                 
            self.draw_text("Press ENTER to continue", x+200, y + h - 50, size=20, color=COLORS['gold'])
            return

        if scam_type == "OTP":
            self.draw_text("Verify transaction. Solve:", x+40, content_y, size=20, color=COLORS['text_dim'])
            problem = data.get('problem', "...")
            self.draw_text(f"{problem}", x+250, content_y + 110, size=48, color=COLORS['gold'])
        elif scam_type == "QUIZ":
            questions = data.get('questions', [])
            q_idx = data.get('q_idx', 0)
            if questions and q_idx < len(questions):
                q_item = questions[q_idx]
                # Question counter
                self.draw_text(f"Q {q_idx + 1} / 3", x + w - 100, content_y, size=18, color=COLORS['text_dim'])
                self.draw_text(q_item['q'], x+40, content_y + 20, size=24, color=COLORS['white'])
                # Draw A/B/C/D labelled options
                opt_y = content_y + 70
                labels = ["A", "B", "C", "D"]
                label_colors = [
                    (120, 220, 120),   # A - green
                    (100, 180, 255),   # B - blue
                    (255, 200, 80),    # C - yellow
                    (255, 120, 120),   # D - red
                ]
                if 'opts' in q_item:
                    for i, opt in enumerate(q_item['opts']):
                        lbl = labels[i] if i < len(labels) else str(i + 1)
                        lbl_col = label_colors[i] if i < len(label_colors) else COLORS['ui_accent']
                        # Draw label badge
                        badge_rect = pygame.Rect(x + 50, opt_y + (i * 42) - 2, 30, 28)
                        pygame.draw.rect(self.screen, lbl_col, badge_rect, border_radius=6)
                        self.draw_text(lbl, x + 57, opt_y + (i * 42), size=18, color=COLORS['black'])
                        # Draw option text
                        self.draw_text(f"{opt}", x + 95, opt_y + (i * 42), size=20, color=COLORS['ui_accent'])
                self.draw_text("Type A / B / C / D and press ENTER", x + 40, y + h - 140, size=16, color=COLORS['text_dim'])

        input_y = y + h - 100
        hint = "Your answer (A/B/C/D):" if scam_type == "QUIZ" else "Your answer:"
        self.draw_text(hint, x + 40, input_y - 28, size=15, color=COLORS['text_dim'])
        pygame.draw.rect(self.screen, (255, 255, 255), (x+180, input_y-5, 300, 45), border_radius=8)
        self.draw_text(user_input.upper(), x+195, input_y+5, size=24, color=COLORS['black'])

    def draw_scorecard(self, p1, p2, finisher):
        s1 = self.calculate_score(p1, finisher)
        s2 = self.calculate_score(p2, finisher)
        cx = SCREEN_WIDTH // 2
        is_draw = s1['total'] == s2['total']
        winner = p1 if s1['total'] >= s2['total'] else p2
        loser  = p2 if winner == p1 else p1
        ws     = s1 if winner == p1 else s2
        ls     = s2 if winner == p1 else s1
        w_accent = COLORS['p1_bg'] if winner == p1 else COLORS['p2_bg']
        l_accent = COLORS['p2_bg'] if winner == p1 else COLORS['p1_bg']

        # ── BACKGROUND ──────────────────────────────────────────────
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        bg.fill((6, 8, 18, 252))
        self.screen.blit(bg, (0, 0))

        # Subtle diagonal grid lines for depth
        for i in range(0, SCREEN_WIDTH + SCREEN_HEIGHT, 60):
            pygame.draw.line(self.screen, (18, 20, 30), (i, 0), (i - SCREEN_HEIGHT, SCREEN_HEIGHT), 1)

        # ── HERO BANNER (top zone) ───────────────────────────────────
        hero_h = 140
        pygame.draw.rect(self.screen, (10, 10, 20), (0, 0, SCREEN_WIDTH, hero_h))
        # Gold accent side bars (Premium feel)
        pygame.draw.rect(self.screen, COLORS['gold'], (0, 0, 8, hero_h))
        pygame.draw.rect(self.screen, COLORS['gold'], (SCREEN_WIDTH - 8, 0, 8, hero_h))
        pygame.draw.line(self.screen, COLORS['gold'], (0, hero_h), (SCREEN_WIDTH, hero_h), 3)

        if is_draw:
            title = self.font_xl.render("DRAW  —  WELL PLAYED!", True, COLORS['ui_accent'])
            sub   = self.font_md.render("Both players performed equally well", True, COLORS['text_dim'])
        else:
            title = self.font_xl.render(f"WINNER  —  {winner.name.upper()}", True, COLORS['gold'])
            sub   = self.font_md.render("Financial Literacy Champion", True, COLORS['text_dim'])

        self.screen.blit(title, title.get_rect(center=(cx, 60)))
        self.screen.blit(sub,   sub.get_rect(center=(cx, 105)))

        # ── PLAYER SCORE CARDS ───────────────────────────────────────
        card_y  = hero_h + 35
        card_w  = 340
        card_h  = 430
        gap     = 50
        
        # Centering both cards
        total_w = (card_w * 2) + gap
        start_x = (SCREEN_WIDTH - total_w) // 2
        
        self._draw_score_card(start_x, card_y, card_w, card_h, winner, ws, w_accent, is_winner=not is_draw)
        self._draw_score_card(start_x + card_w + gap, card_y, card_w, card_h, loser, ls, l_accent, is_winner=False)

        # ── FOOTER ───────────────────────────────────────────────────
        footer = self.font_md.render("Press  ENTER  to return to Menu", True, COLORS['gold'])
        self.screen.blit(footer, footer.get_rect(center=(cx, SCREEN_HEIGHT - 40)))

    def _draw_score_card(self, x, y, w, h, p, s, accent, is_winner=False):
        # Card background with glassmorphism effect
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((14, 16, 26, 248))
        self.screen.blit(surf, (x, y))

        border_col = COLORS['gold'] if is_winner else accent
        pygame.draw.rect(self.screen, border_col, (x, y, w, h), 4 if is_winner else 2, border_radius=16)

        # Header strip
        hdr_h = 50
        hdr_col = (60, 45, 0) if is_winner else (accent[0]//5, accent[1]//5, accent[2]//5)
        pygame.draw.rect(self.screen, hdr_col, (x, y, w, hdr_h), border_top_left_radius=14, border_top_right_radius=14)

        if is_winner:
            lbl = self.font_lg.render("🏆 WINNER 🏆", True, COLORS['gold'])
            self.screen.blit(lbl, lbl.get_rect(center=(x + w // 2, y + 25)))
            name_y = y + 65
        else:
            name_y = y + 15

        name_s = self.font_xl.render(p.name, True, border_col)
        self.screen.blit(name_s, name_s.get_rect(center=(x + w // 2, name_y + 15)))

        # Stats list
        stats = [
            ("Wealth Savvy",  f"Rs. {s['raw_savings']}", f"+{s['savings']} Pts", COLORS['positive']),
            ("Health Care",   f"{p.health}/100",          f"+{s['health']} Pts",  COLORS['active']),
            ("Happiness",     f"{p.happiness}/100",       f"+{s['happy']} Pts",   COLORS['gold']),
            ("Debt Control",  f"Rs. {p.loan}",            f"{s['debt']} Pts",    COLORS['negative']),
        ]
        
        ry = name_y + 60
        row_h = 62
        for lbl, val, pts, str_col in stats:
            pygame.draw.line(self.screen, (40, 45, 60), (x + 20, ry), (x + w - 20, ry), 1)
            
            l_s = self.font_sm.render(lbl, True, COLORS['text_dim'])
            v_s = self.font_md.render(val, True, COLORS['white'])
            p_s = self.font_md.render(pts, True, str_col)
            
            self.screen.blit(l_s, (x + 25, ry + 8))
            self.screen.blit(v_s, (x + 25, ry + 28))
            self.screen.blit(p_s, p_s.get_rect(right=x + w - 25, y=ry + 28))
            ry += row_h

        # Big total score at bottom
        footer_y = y + h - 75
        pygame.draw.rect(self.screen, (25, 28, 45), (x + 15, footer_y, w - 30, 60), border_radius=12)
        pygame.draw.rect(self.screen, border_col, (x + 15, footer_y, w - 30, 60), 2, border_radius=12)
        
        tot_lbl = self.font_sm.render("TOTAL SCORE", True, COLORS['text_dim'])
        tot_val = self.font_xl.render(str(s['total']), True, border_col)
        
        self.screen.blit(tot_lbl, (x + 25, footer_y + 12))
        self.screen.blit(tot_val, tot_val.get_rect(right=x + w - 25, centery=footer_y + 30))

        # --- Badges Area ---
        badges = self._compute_badges(p)
        if badges:
            badge_y = footer_y - 35
            bx = x + 20
            for b_name, b_col in badges:
                tw, th = self.font_sm.size(b_name)
                bw = tw + 16
                pygame.draw.rect(self.screen, b_col, (bx, badge_y, bw, 22), border_radius=11)
                b_surf = self.font_sm.render(b_name, True, (0,0,0))
                self.screen.blit(b_surf, b_surf.get_rect(center=(bx + bw//2, badge_y + 11)))
                bx += bw + 8

    def calculate_score(self, p, finisher):
        savings = p.wallet + p.bank_balance + p.fd_balance
        score_savings = int(savings / 100)
        score_health = int(p.health)
        score_happy = int(p.happiness)
        score_debt = int(p.loan / -50)
        score_bonus = 100 if p == finisher else 0
        total = score_savings + score_health + score_happy + score_debt + score_bonus
        return {"savings": score_savings, "health": score_health, "happy": score_happy, "debt": score_debt, "total": total, "raw_savings": savings}

    def _compute_badges(self, player):
        badges = []
        if player.bank_balance >= 3000:
            badges.append(("Smart Saver", COLORS['positive']))
        if getattr(player, 'loan', 0) == 0:
            badges.append(("Debt-Free", COLORS['ui_accent']))
        if len(player.completed_needs) >= 8:
            badges.append(("Responsible", (155, 89, 182))) 
        if player.health == 100:
            badges.append(("Healthy Resident", COLORS['active']))
        if player.happiness >= 80:
            badges.append(("Joyful Citizen", COLORS['gold']))
        return badges[:3]

    def draw_bank_menu(self, player, game_manager):
        w, h = 500, 360
        x, y = (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(self.screen, (30, 40, 60), (x, y, w, h), border_radius=15)
        pygame.draw.rect(self.screen, COLORS['ui_accent'], (x, y, w, h), 3, border_radius=15)
        
        title = self.font_lg.render("BANK OF PIXEL", True, COLORS['ui_accent'])
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, y + 35)))
        
        self.draw_text(f"Wallet: Rs. {player.wallet}", x + 40, y + 80, size=18, color=COLORS['white'])
        self.draw_text(f"Bank: Rs. {player.bank_balance}", x + 260, y + 80, size=18, color=COLORS['white'])
        
        options = [
            ("1. Deposit Cash (Increases Bank)", 130),
            ("2. Withdraw Cash (Increases Wallet)", 180),
            ("3. Create Fixed Deposit (FD)", 230),
            ("4. Repay Loan", 280),
        ]
        
        for text, opt_y in options:
            btn_rect = pygame.Rect(x + 40, y + opt_y, w - 80, 40)
            pygame.draw.rect(self.screen, (45, 50, 70), btn_rect, border_radius=8)
            self.draw_text(text, x + 60, y + opt_y + 8, size=18, color=COLORS['white'])

        self.draw_text("Press ESC to Close", x + 160, y + h - 35, size=16, color=COLORS['text_dim'])

    def draw_budget_window(self, player):
        w, h = 600, 450
        x, y = (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(self.screen, (35, 35, 45), (x, y, w, h), border_radius=20)
        pygame.draw.rect(self.screen, COLORS['gold'], (x, y, w, h), 3, border_radius=20)
        
        title = self.font_xl.render("MONTHLY BUDGET CHALLENGE", True, COLORS['gold'])
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, y + 50)))
        
        self.draw_text("You have Rs. 500. How will you split it?", x + 140, y + 100, size=18, color=COLORS['white'])
        
        for i, opt in enumerate(BUDGET_OPTIONS):
            oy = y + 150 + (i * 90)
            rect = pygame.Rect(x + 50, oy, w - 100, 75)
            pygame.draw.rect(self.screen, (50, 50, 65), rect, border_radius=12)
            
            self.draw_text(f"[{i+1}] {opt['label']}", x + 70, oy + 15, size=22, color=COLORS['active'])
            self.draw_text(opt['desc'], x + 70, oy + 45, size=16, color=COLORS['text_dim'])

    def draw_tip_card(self, title, text):
        w, h = 550, 400
        x, y = (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(self.screen, (40, 45, 60), (x, y, w, h), border_radius=20)
        pygame.draw.rect(self.screen, COLORS['active'], (x, y, w, h), 3, border_radius=20)
        
        # Header
        pygame.draw.rect(self.screen, (50, 60, 80), (x, y, w, 50), border_top_left_radius=18, border_top_right_radius=18)
        self.draw_text(title, x + 25, y + 12, size=22, color=COLORS['gold'])
        
        # Body
        lines = text.split('\n')
        curr_y = y + 80
        for line in lines:
            self.draw_text(line, x + 30, curr_y, size=20, color=COLORS['white'])
            curr_y += 30
            
        self.draw_text("Press ENTER to continue", x + 160, y + h - 50, size=18, color=COLORS['gold'])