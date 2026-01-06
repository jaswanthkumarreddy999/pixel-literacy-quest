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
    
    # --- FIX FOR WEB RENDERER ERROR ---
    if sys.platform == "emscripten":
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    else:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.FULLSCREEN)

    pygame.display.set_caption("Pixel Literacy Quest")
    clock = pygame.time.Clock()

    # --- LOAD BACKGROUND IMAGE ---
    bg_image = None
    try:
        raw_bg = pygame.image.load("assets/images/background.jpg")
        bg_image = pygame.transform.scale(raw_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception as e:
        print(f"Menu Background Warning: {e}")

    # --- FONTS ---
    font_title = pygame.font.Font(None, 60)
    font_btn = pygame.font.Font(None, 40)
    font_input = pygame.font.Font(None, 50)

    # Game Variables
    game_state = MENU
    p1_name_input = ""
    p2_name_input = ""
    game_manager = None 

    # Buttons
    btn_play_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 300, 200, 50)
    btn_exit_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 380, 200, 50)

    running = True
    while running:
        # --- 1. CAPTURE EVENTS ---
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                 if game_state == MENU or game_state == GAMEPLAY:
                     running = False

            # --- STATE INPUT ---
            if game_state == MENU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_play_rect.collidepoint(event.pos):
                        game_state = INPUT_P1
                    elif btn_exit_rect.collidepoint(event.pos):
                        running = False

            elif game_state in [INPUT_P1, INPUT_P2]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if game_state == INPUT_P1:
                            if not p1_name_input.strip(): p1_name_input = "Player 1"
                            game_state = INPUT_P2
                        elif game_state == INPUT_P2:
                            if not p2_name_input.strip(): p2_name_input = "Player 2"
                            game_manager = GameManager(screen, p1_name_input, p2_name_input)
                            game_state = GAMEPLAY
                    elif event.key == pygame.K_BACKSPACE:
                        if game_state == INPUT_P1: p1_name_input = p1_name_input[:-1]
                        else: p2_name_input = p2_name_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        game_state = MENU
                        p1_name_input = ""
                        p2_name_input = ""
                    else:
                        if len(event.unicode) > 0 and event.unicode.isprintable():
                            if game_state == INPUT_P1 and len(p1_name_input) < 12:
                                p1_name_input += event.unicode
                            elif game_state == INPUT_P2 and len(p2_name_input) < 12:
                                p2_name_input += event.unicode

            # --- RESTART LOGIC (DETECT ENTER AFTER GAME OVER) ---
            elif game_state == GAMEPLAY and game_manager and game_manager.winner:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    # Reset all variables to go back to the start
                    game_state = MENU
                    p1_name_input = ""
                    p2_name_input = ""
                    game_manager = None

        # --- DRAWING ---
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill(COLORS['menu_bg'])

        mouse_pos = pygame.mouse.get_pos()

        if game_state == MENU:
            title_surf = font_title.render("PIXEL LITERACY QUEST", True, COLORS['white'])
            screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 150))

            # Play Button
            col = COLORS['btn_hover'] if btn_play_rect.collidepoint(mouse_pos) else COLORS['btn_normal']
            pygame.draw.rect(screen, col, btn_play_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS['white'], btn_play_rect, 2, border_radius=10)
            play_txt = font_btn.render("PLAY GAME", True, COLORS['white'])
            screen.blit(play_txt, (btn_play_rect.centerx - play_txt.get_width()//2, btn_play_rect.centery - play_txt.get_height()//2))

            # Exit Button
            col = COLORS['btn_hover'] if btn_exit_rect.collidepoint(mouse_pos) else COLORS['btn_normal']
            pygame.draw.rect(screen, col, btn_exit_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS['white'], btn_exit_rect, 2, border_radius=10)
            exit_txt = font_btn.render("EXIT", True, COLORS['white'])
            screen.blit(exit_txt, (btn_exit_rect.centerx - exit_txt.get_width()//2, btn_exit_rect.centery - exit_txt.get_height()//2))

        elif game_state == INPUT_P1:
            draw_input_screen(screen, font_title, font_input, "ENTER PLAYER 1 NAME:", p1_name_input, COLORS['p1_bg'])

        elif game_state == INPUT_P2:
            draw_input_screen(screen, font_title, font_input, "ENTER PLAYER 2 NAME:", p2_name_input, COLORS['p2_bg'])

        elif game_state == GAMEPLAY:
            if game_manager and game_manager.running:
                game_manager.handle_input(events)
                game_manager.update()
                game_manager.draw()
            else:
                # Fallback if GameManager stops running internally
                game_state = MENU
                game_manager = None

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

def draw_input_screen(screen, title_font, input_font, prompt, current_text, accent_col):
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, 150))
    screen.blit(s, (0,0))

    prompt_surf = title_font.render(prompt, True, COLORS['white'])
    screen.blit(prompt_surf, (SCREEN_WIDTH//2 - prompt_surf.get_width()//2, 200))
    
    input_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 300, 300, 60)
    pygame.draw.rect(screen, COLORS['input_bg'], input_rect, border_radius=10)
    pygame.draw.rect(screen, accent_col, input_rect, 3, border_radius=10)
    
    txt_surf = input_font.render(current_text, True, COLORS['white'])
    screen.blit(txt_surf, (input_rect.centerx - txt_surf.get_width()//2, input_rect.centery - txt_surf.get_height()//2))
    
    hint = input_font.render("Press ENTER to confirm", True, COLORS['text_dim'])
    screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 400))

if __name__ == "__main__":
    asyncio.run(main())