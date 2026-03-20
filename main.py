import pygame
import sys
import asyncio
import platform
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLORS, 
    AVATAR_COLORS, AVATAR_NAMES
)
from core.game_manager import GameManager
import config.audio as audio

# --- STATES ---
MENU = "menu"
INPUT_P1 = "input_p1"
AVATAR_P1 = "avatar_p1"
INPUT_P2 = "input_p2"
AVATAR_P2 = "avatar_p2"
GAMEPLAY = "gameplay"

async def main():
    pygame.init()
    
    # --- WINDOW INITIALIZATION ---
    is_fullscreen = False
    IS_WEB = sys.platform == "emscripten"
    
    if IS_WEB:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    else:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)

    pygame.display.set_caption("Pixel Literacy Quest")
    clock = pygame.time.Clock()

    # --- ASSETS ---
    bg_image = None
    try:
        raw_bg = pygame.image.load("assets/images/background.jpg").convert()
        bg_image = pygame.transform.scale(raw_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except:
        pass

    font_title = pygame.font.Font(None, 60)
    font_btn = pygame.font.Font(None, 40)
    font_input = pygame.font.Font(None, 50)

    # State Variables
    game_state = MENU
    p1_name_input = ""
    p2_name_input = ""
    p1_avatar = COLORS['p1_bg']
    p2_avatar = COLORS['p2_bg']
    avatar_idx = 0
    play_vs_ai = False
    game_manager = None 

    # UI Rects
    close_rect = pygame.Rect(SCREEN_WIDTH - 45, 10, 30, 30)
    toggle_rect = pygame.Rect(SCREEN_WIDTH - 85, 10, 30, 30)
    min_rect = pygame.Rect(SCREEN_WIDTH - 125, 10, 30, 30)
    btn_play_rect = pygame.Rect(SCREEN_WIDTH//2 - 220, 300, 200, 50)
    btn_ai_rect = pygame.Rect(SCREEN_WIDTH//2 + 20, 300, 200, 50)
    btn_exit_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 380, 200, 50)

    running = True
    while running:
        events = pygame.event.get()
        mouse_pos = pygame.mouse.get_pos()
        hover_ui = False 

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            # --- HIDDEN Q KEY LOGIC ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    if game_state == MENU:
                        running = False  
                    else:
                        game_state = MENU  
                        game_manager = None

            # --- WINDOW CONTROLS LOGIC ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if close_rect.collidepoint(event.pos):
                    running = False
                elif min_rect.collidepoint(event.pos) and not IS_WEB:
                    pygame.display.iconify()
                elif toggle_rect.collidepoint(event.pos):
                    # Standard Pygame fullscreen toggle
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)

            # --- INPUT HANDLING ---
            if game_state in [INPUT_P1, INPUT_P2]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if game_state == INPUT_P1 and p1_name_input.strip():
                            game_state = AVATAR_P1
                            avatar_idx = 0
                        elif game_state == INPUT_P2 and p2_name_input.strip():
                            game_state = AVATAR_P2
                            avatar_idx = 0
                    elif event.key == pygame.K_BACKSPACE:
                        if game_state == INPUT_P1: p1_name_input = p1_name_input[:-1]
                        else: p2_name_input = p2_name_input[:-1]
                    elif event.unicode.isprintable() and len(event.unicode) > 0:
                        # Ensure 'q' doesn't get typed as it's our escape key
                        if event.key != pygame.K_q:
                            if game_state == INPUT_P1 and len(p1_name_input) < 12:
                                p1_name_input += event.unicode
                            elif game_state == INPUT_P2 and len(p2_name_input) < 12:
                                p2_name_input += event.unicode
                                
            # --- AVATAR SELECTION LOGIC ---
            elif game_state in [AVATAR_P1, AVATAR_P2]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        avatar_idx = (avatar_idx - 1) % len(AVATAR_COLORS)
                        audio.play('click')
                    elif event.key == pygame.K_RIGHT:
                        avatar_idx = (avatar_idx + 1) % len(AVATAR_COLORS)
                        audio.play('click')
                    elif event.key == pygame.K_RETURN:
                        audio.play('click')
                        if game_state == AVATAR_P1:
                            p1_avatar = AVATAR_COLORS[avatar_idx]
                            if play_vs_ai:
                                p2_name_input = "AI Bot"
                                p2_avatar = AVATAR_COLORS[(avatar_idx + 1) % len(AVATAR_COLORS)]
                                game_manager = GameManager(screen, p1_name_input.strip(), p2_name_input, 
                                                           p1_avatar, p2_avatar, True)
                                game_state = GAMEPLAY
                            else:
                                game_state = INPUT_P2
                        else:
                            p2_avatar = AVATAR_COLORS[avatar_idx]
                            game_manager = GameManager(screen, p1_name_input.strip(), p2_name_input.strip(),
                                                       p1_avatar, p2_avatar, False)
                            game_state = GAMEPLAY

            # --- GAMEPLAY RESTART LOGIC ---
            elif game_state == GAMEPLAY and game_manager and game_manager.winner:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    game_state = MENU
                    game_manager = None

            # --- MENU BUTTONS ---
            elif game_state == MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_play_rect.collidepoint(event.pos):
                        play_vs_ai = False
                        game_state = INPUT_P1
                        p1_name_input = ""
                        p2_name_input = ""
                        audio.play('click')
                    elif btn_ai_rect.collidepoint(event.pos):
                        play_vs_ai = True
                        game_state = INPUT_P1
                        p1_name_input = ""
                        audio.play('click')
                    elif btn_exit_rect.collidepoint(event.pos):
                        running = False

        # --- RENDERING ---
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill(COLORS.get('menu_bg', (30, 30, 30)))

        # --- DRAW CUSTOM WINDOW CONTROLS ---
        for r, icon in [(min_rect, "min"), (toggle_rect, "square"), (close_rect, "x")]:
            col = (200, 50, 50) if icon == "x" and r.collidepoint(mouse_pos) else (80, 80, 80) if r.collidepoint(mouse_pos) else (40, 40, 40)
            pygame.draw.rect(screen, col, r, border_radius=5)
            
            if icon == "min":
                pygame.draw.line(screen, (255, 255, 255), (r.x + 8, r.centery + 5), (r.right - 8, r.centery + 5), 2)
            elif icon == "square":
                pygame.draw.rect(screen, (255, 255, 255), (r.x + 8, r.y + 8, 14, 14), 2)
            elif icon == "x":
                pygame.draw.line(screen, (255, 255, 255), (r.x + 9, r.y + 9), (r.right - 9, r.bottom - 9), 2)
                pygame.draw.line(screen, (255, 255, 255), (r.right - 9, r.y + 9), (r.x + 9, r.bottom - 9), 2)

        if game_state == MENU:
            title_surf = font_title.render("PIXEL LITERACY QUEST", True, (255, 255, 255))
            screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 150))
            
            for btn, txt in [(btn_play_rect, "1P vs 2P"), (btn_ai_rect, "1P vs AI"), (btn_exit_rect, "EXIT")]:
                c = COLORS['btn_hover'] if btn.collidepoint(mouse_pos) else COLORS['btn_normal']
                pygame.draw.rect(screen, c, btn, border_radius=10)
                pygame.draw.rect(screen, COLORS['ui_border'], btn, 2, border_radius=10)
                lbl = font_btn.render(txt, True, (255, 255, 255))
                screen.blit(lbl, (btn.centerx - lbl.get_width()//2, btn.centery - lbl.get_height()//2))
        
        elif game_state in [INPUT_P1, INPUT_P2]:
            prompt = "ENTER PLAYER 1 NAME:" if game_state == INPUT_P1 else "ENTER PLAYER 2 NAME:"
            text = p1_name_input if game_state == INPUT_P1 else p2_name_input
            draw_input_screen(screen, font_title, font_input, prompt, text, COLORS['p1_bg' if game_state == INPUT_P1 else 'p2_bg'])

        elif game_state in [AVATAR_P1, AVATAR_P2]:
            prompt = f"{p1_name_input}, CHOOSE AVATAR:" if game_state == AVATAR_P1 else f"{p2_name_input}, CHOOSE AVATAR:"
            draw_avatar_screen(screen, font_title, font_input, prompt, avatar_idx)
        
        elif game_state == GAMEPLAY and game_manager:
            if not game_manager.winner:
                game_manager.handle_input(events)
            
            game_manager.update()
            game_manager.draw()

            # Winner screen is fully rendered by HUD's draw_scorecard

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

def draw_input_screen(screen, title_font, input_font, prompt, current_text, accent_col):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0,0))
    prompt_surf = title_font.render(prompt, True, (255, 255, 255))
    screen.blit(prompt_surf, (SCREEN_WIDTH//2 - prompt_surf.get_width()//2, 200))
    input_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 300, 400, 60)
    pygame.draw.rect(screen, (50, 50, 50), input_rect, border_radius=10)
    pygame.draw.rect(screen, accent_col, input_rect, 3, border_radius=10)
    cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
    txt_surf = input_font.render(current_text + cursor, True, (255, 255, 255))
    screen.blit(txt_surf, (input_rect.centerx - txt_surf.get_width()//2, input_rect.centery - txt_surf.get_height()//2))

def draw_avatar_screen(screen, title_font, input_font, prompt, current_idx):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0,0))
    
    prompt_surf = title_font.render(prompt, True, (255, 255, 255))
    screen.blit(prompt_surf, (SCREEN_WIDTH//2 - prompt_surf.get_width()//2, 150))
    
    # Draw avatar choices
    num_avatars = len(AVATAR_COLORS)
    spacing = 150
    start_x = SCREEN_WIDTH//2 - (spacing * (num_avatars-1))//2
    cy = 350
    
    for i, color in enumerate(AVATAR_COLORS):
        name = AVATAR_NAMES[i]
        cx = start_x + i * spacing
        is_sel = (i == current_idx)
        
        radius = 50 if is_sel else 40
        pygame.draw.circle(screen, color, (cx, cy), radius)
        pygame.draw.circle(screen, COLORS['white'] if is_sel else (80,80,80), (cx, cy), radius, 4 if is_sel else 2)
        
        if is_sel:
            name_surf = input_font.render(name, True, color)
            screen.blit(name_surf, (cx - name_surf.get_width()//2, cy + 70))
            
    help_surf = pygame.font.Font(None, 30).render("Use LEFT/RIGHT arrows, press ENTER to confirm", True, (150, 150, 150))
    screen.blit(help_surf, (SCREEN_WIDTH//2 - help_surf.get_width()//2, 500))

if __name__ == "__main__":
    asyncio.run(main())