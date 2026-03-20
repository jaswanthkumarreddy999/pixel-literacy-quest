import pygame
pygame.init()
pygame.display.set_mode((800, 600))
from core.game_manager import GameManager
try:
    gm = GameManager(pygame.display.get_surface(), "P1", "AI Bot", None, None, True)
    print("GameManager initialized successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()
