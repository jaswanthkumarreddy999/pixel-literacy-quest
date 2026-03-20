import pygame
from config.settings import MAP_X, MAP_Y, TILE_SIZE, COLORS, MAP_LAYOUT
from config.assets import loader

class MapView:
    def __init__(self, screen):
        self.screen = screen
        self.wall_img = None
        self.road_img = None

    def draw_to_surface(self, target_surface, walls, players, scammer, locations=None):
        old_screen = self.screen
        self.screen = target_surface
        self.draw(walls, players, scammer, locations)
        self.screen = old_screen

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
            self.draw_entity(p)

        # 5. Draw Scammer
        self.draw_scammer(scammer)

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

    def draw_entity(self, p):
        col, row = p.grid_pos[0], p.grid_pos[1]
        x = MAP_X + col * TILE_SIZE
        y = MAP_Y + row * TILE_SIZE
        
        if p.id == 1: img = loader.get("p1")
        else: img = loader.get("p2")
        
        if img:
            img = pygame.transform.scale(img, (TILE_SIZE-10, TILE_SIZE-10))
            self.screen.blit(img, (x+5, y+5))
        else:
            color = getattr(p, 'avatar_color', COLORS[f'p{p.id}_bg'])
            center = (x + TILE_SIZE//2, y + TILE_SIZE//2)
            pygame.draw.circle(self.screen, color, center, TILE_SIZE//3)
            pygame.draw.circle(self.screen, COLORS['white'], center, TILE_SIZE//3, 2)

    def draw_scammer(self, scammer):
        col, row = scammer.pos[0], scammer.pos[1]
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
            
        # Draw intent bubble
        if hasattr(scammer, 'intent') and scammer.freeze_timer == 0:
            font = pygame.font.SysFont("Arial", 12, bold=True)
            bubble_txt = "CASH" if scammer.intent == "CASH" else "DIGITAL"
            color = COLORS['negative'] if scammer.intent == "CASH" else COLORS['ui_accent']
            
            txt_surf = font.render(bubble_txt, True, COLORS['white'])
            bg_rect = txt_surf.get_rect(center=(x + TILE_SIZE//2, y - 10))
            bg_rect.inflate_ip(6, 4)
            
            pygame.draw.rect(self.screen, color, bg_rect, border_radius=4)
            pygame.draw.rect(self.screen, COLORS['white'], bg_rect, 1, border_radius=4)
            self.screen.blit(txt_surf, txt_surf.get_rect(center=bg_rect.center))