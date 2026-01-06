import pygame
import sys
import asyncio
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLORS
from core.game_manager import GameManager

# --- STATES ---
MENU = "menu"
INPUT_P1 = "input_p1"
INPUT_P2 = "input_p2"
GAMEPLAY = "gameplay"

async def main():
    pygame.init()
    
    # --- WINDOW INITIALIZATION ---
    is_fullscreen = False
    
    # WEB CHECK: Browsers prefer standard windowed modes
    if sys.platform == "emscripten":
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
    game_manager = None 

    # --- TOP RIGHT CONTROL BUTTONS ---
    close_rect = pygame.Rect(SCREEN_WIDTH - 45, 10, 30, 30)
    toggle_rect = pygame.Rect(SCREEN_WIDTH - 85, 10, 30, 30)
    min_rect = pygame.Rect(SCREEN_WIDTH - 125, 10, 30, 30)

    # Menu Buttons
    btn_play_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 300, 200, 50)
    btn_exit_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 380, 200, 50)

    running = True
    while running:
        events = pygame.event.get()
        mouse_pos = pygame.mouse.get_pos()
        hover_ui = False 

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            # --- CUSTOM WINDOW CONTROLS LOGIC ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if close_rect.collidepoint(event.pos):
                    running = False
                elif min_rect.collidepoint(event.pos):
                    pygame.display.iconify()
                elif toggle_rect.collidepoint(event.pos):
                    # Only apply actual Fullscreen flag if NOT on web
                    is_fullscreen = not is_fullscreen
                    if sys.platform != "emscripten":
                        if is_fullscreen:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                        else:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
                    else:
                        # On Web, we let the browser's own Fullscreen button handle it
                        print("Fullscreen toggled - Browser handling scaling")

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11 and sys.platform != "emscripten":
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
                
                if event.key == pygame.K_q and game_state != GAMEPLAY:
                    running = False

            # --- MENU LOGIC ---
            if game_state == MENU:
                if btn_play_rect.collidepoint(mouse_pos) or btn_exit_rect.collidepoint(mouse_pos):
                    hover_ui = True
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_play_rect.collidepoint(event.pos):
                        game_state = INPUT_P1
                        p1_name_input = ""
                    elif btn_exit_rect.collidepoint(event.pos):
                        running = False

            # --- NAME INPUT LOGIC ---
            elif game_state in [INPUT_P1, INPUT_P2]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if game_state == INPUT_P1:
                            p1_name_input = p1_name_input.strip() or "PLAYER 1"
                            game_state = INPUT_P2
                            p2_name_input = ""
                        else:
                            p2_name_input = p2_name_input.strip() or "PLAYER 2"
                            game_manager = GameManager(screen, p1_name_input, p2_name_input)
                            game_state = GAMEPLAY
                    elif event.key == pygame.K_BACKSPACE:
                        if game_state == INPUT_P1: p1_name_input = p1_name_input[:-1]
                        else: p2_name_input = p2_name_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        game_state = MENU
                    else:
                        if event.unicode.isprintable() and len(event.unicode) > 0:
                            if game_state == INPUT_P1 and len(p1_name_input) < 12:
                                p1_name_input += event.unicode
                            elif game_state == INPUT_P2 and len(p2_name_input) < 12:
                                p2_name_input += event.unicode

            # --- GAMEPLAY OVER LOGIC ---
            elif game_state == GAMEPLAY and game_manager and game_manager.winner:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    game_state = MENU
                    game_manager = None

        # --- CURSOR UPDATE ---
        if any(r.collidepoint(mouse_pos) for r in [close_rect, toggle_rect, min_rect]):
            hover_ui = True
        if game_state == GAMEPLAY and game_manager:
            if any(r['rect'].collidepoint(mouse_pos) for r in game_manager.hud.click_regions):
                hover_ui = True
        
        cursor_style = pygame.SYSTEM_CURSOR_HAND if hover_ui else pygame.SYSTEM_CURSOR_ARROW
        pygame.mouse.set_cursor(cursor_style)

        # --- RENDERING ---
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill(COLORS['menu_bg'])

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
            for btn, txt in [(btn_play_rect, "PLAY GAME"), (btn_exit_rect, "EXIT")]:
                col = COLORS['btn_hover'] if btn.collidepoint(mouse_pos) else COLORS['btn_normal']
                pygame.draw.rect(screen, col, btn, border_radius=10)
                pygame.draw.rect(screen, (255, 255, 255), btn, 2, border_radius=10)
                label = font_btn.render(txt, True, (255, 255, 255))
                screen.blit(label, (btn.centerx - label.get_width()//2, btn.centery - label.get_height()//2))

        elif game_state == INPUT_P1:
            draw_input_screen(screen, font_title, font_input, "ENTER PLAYER 1 NAME:", p1_name_input, COLORS['p1_bg'])
        elif game_state == INPUT_P2:
            draw_input_screen(screen, font_title, font_input, "ENTER PLAYER 2 NAME:", p2_name_input, COLORS['p2_bg'])
        elif game_state == GAMEPLAY:
            if game_manager:
                game_manager.handle_input(events)
                game_manager.update()
                game_manager.draw()
                if not game_manager.running:
                    game_state = MENU
                    game_manager = None

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
    pygame.draw.rect(screen, COLORS['input_bg'], input_rect, border_radius=10)
    pygame.draw.rect(screen, accent_col, input_rect, 3, border_radius=10)
    txt_surf = input_font.render(current_text + "|", True, (255, 255, 255))
    screen.blit(txt_surf, (input_rect.centerx - txt_surf.get_width()//2, input_rect.centery - txt_surf.get_height()//2))
    hint = input_font.render("Press ENTER to confirm • ESC to go back", True, COLORS['text_dim'])
    screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 420))

if __name__ == "__main__":
    asyncio.run(main())