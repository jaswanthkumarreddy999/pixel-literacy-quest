import pygame
from config.settings import *
from config.assets import loader

class MapView:
    def __init__(self, screen):
        self.screen = screen
        self.wall_img = None
        self.road_img = None

    def draw(self, walls, players, scammer, locations=None):
        if locations is None: locations = {}

        # 1. Draw Map Tiles (CLEAN - No Grid Lines)
        pass 

        # 2. (REMOVED) Draw Entrance Markers
        # The code that drew the faint border is deleted here.
        # Now the floor will be completely clean.

        # 3. Draw Character Glow (Lighting Effect)
        for p in players:
            pos_tuple = tuple(p.grid_pos)
            if pos_tuple in locations:
                self.draw_halo(p.grid_pos[0], p.grid_pos[1], (255, 255, 200))

        # 4. Draw Players
        for p in players:
            self.draw_entity(p.grid_pos[0], p.grid_pos[1], p.id)

        # 5. Draw Scammer
        self.draw_scammer(scammer.pos[0], scammer.pos[1])

    def draw_halo(self, col, row, color):
        center_x = MAP_X + col * TILE_SIZE + TILE_SIZE // 2
        center_y = MAP_Y + row * TILE_SIZE + TILE_SIZE // 2
        
        radius = TILE_SIZE // 1.2
        s = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
        
        # Soft Gradient Circles
        pygame.draw.circle(s, (*color, 30), (int(radius), int(radius)), int(radius))
        pygame.draw.circle(s, (*color, 60), (int(radius), int(radius)), int(radius * 0.7))
        pygame.draw.circle(s, (*color, 100), (int(radius), int(radius)), int(radius * 0.4))
        
        self.screen.blit(s, (center_x - radius, center_y - radius))

    def draw_entity(self, col, row, pid):
        x = MAP_X + col * TILE_SIZE
        y = MAP_Y + row * TILE_SIZE
        
        if pid == 1: img = loader.get("p1")
        else: img = loader.get("p2")
        
        if img:
            img = pygame.transform.scale(img, (TILE_SIZE-10, TILE_SIZE-10))
            self.screen.blit(img, (x+5, y+5))
        else:
            if pid == 1: color = COLORS['p1_bg']
            else: color = COLORS['p2_bg']
            center = (x + TILE_SIZE//2, y + TILE_SIZE//2)
            pygame.draw.circle(self.screen, color, center, TILE_SIZE//3)
            pygame.draw.circle(self.screen, COLORS['white'], center, TILE_SIZE//3, 2)

    def draw_scammer(self, col, row):
        x = MAP_X + col * TILE_SIZE
        y = MAP_Y + row * TILE_SIZE
        
        img = loader.get("scammer")
        if img:
            img = pygame.transform.scale(img, (TILE_SIZE-10, TILE_SIZE-10))
            self.screen.blit(img, (x+5, y+5))
        else:
            center = (x + TILE_SIZE//2, y + TILE_SIZE//2)
            pygame.draw.circle(self.screen, COLORS['black'], center, TILE_SIZE//3)
            pygame.draw.circle(self.screen, COLORS['red'], center, TILE_SIZE//3, 2)