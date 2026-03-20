import pygame
import asyncio
from core.game_manager import GameManager
from config.settings import AVATAR_COLORS
pygame.init()
screen = pygame.display.set_mode((800, 600))
try:
    p1_avatar = AVATAR_COLORS[0]
    p2_avatar = AVATAR_COLORS[1]
    gm = GameManager(screen, "Jaswanth", "AI Bot", p1_avatar, p2_avatar, True)
    gm.update()
    gm.draw()
    print("AI Flow ok!")
except Exception as e:
    import traceback
    traceback.print_exc()
