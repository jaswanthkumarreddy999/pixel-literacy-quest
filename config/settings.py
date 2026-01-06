import pygame

# --- SCREEN SETTINGS ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# --- TILE SETTINGS ---
TILE_SIZE = 64
ICON_SIZE = 32

# --- COLORS ---
COLORS = {
    'sky': (135, 206, 235),
    'ui_bg': (30, 35, 45, 240),
    'ui_border': (60, 70, 90),
    'ui_accent': (100, 200, 255),
    'text_main': (240, 240, 240),
    'text_dim': (150, 150, 160),
    'positive': (100, 255, 100),
    'negative': (255, 100, 100),
    'gold': (255, 215, 0),
    'active': (255, 255, 0),
    'p1_bg': (46, 204, 113),
    'p2_bg': (52, 152, 219),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'red': (220, 20, 60),
    'menu_bg': (25, 25, 35),
    'btn_normal': (50, 50, 65),
    'btn_hover': (70, 70, 85),
    'input_bg': (40, 40, 50)
}

# --- ECONOMY RULES ---
STARTING_WALLET = 20000
STARTING_BANK = 1000
MONTHLY_INCOME = 0

# Interest Rates
LOAN_INTEREST = 0.10     
SAVINGS_INTEREST = 0 
FD_INTEREST = 0.15       
FD_LOCK_TURNS = 3 # Default, though we now allow custom turns

# --- NEW: SCAM & DIFFICULTY SETTINGS ---
SCAM_FREEZE_TURNS = 3        # Turns scammer stays quiet after attack
SCAM_PENALTY_OTP = 0.05      # 5% lost for wrong math
SCAM_PENALTY_QUIZ = 0.10     # 10% lost for wrong answer
SCAM_PENALTY_FLEE = 0.10     # 10% lost for pressing ESC
FD_PER_TURN_RATE = 0.05      # 5% profit per turn for Custom FD

# --- GAME CONTENT ---
GAME_NEEDS = [
    ("Fire Accident", 100), 
    ("Groceries", 150), 
    ("Food", 120), 
    ("Medicines", 100), 
    ("fever", 150), 
    ("Heart Attack", 80),
    ("School Fees", 200), 
    ("Clothes", 200), 
    ("water bill", 250), 
    ("Rent", 300)
]

GAME_WANTS = [
    ("Wifi", 50, 3), 
    ("Cinema", 80, 5), 
    ("Dinner", 100, 5),
    ("Headphones", 120, 8), 
    ("Video Game", 150, 10), 
    ("Movie Ticket", 150, 10),
    ("TV", 200, 15), 
    ("Watch", 250, 20), 
    ("Phone", 400, 25), 
    ("Vacation", 500, 40)
]

# --- MAP CONFIGURATION ---
MAP_LAYOUT = [
    [1, 1, 1, 0, 1, 1, 0, 0, 1, 1],
    [1, 1, 1, 0, 1, 1, 0, 0, 0, 1],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 1, 1, 0, 0, 1, 1],
    [1, 1, 0, 0, 1, 1, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 0, 0, 1, 1, 0, 0, 0, 0],
    [1, 1, 0, 0, 1, 1, 0, 1, 0, 1],
]

GRID_ROWS = len(MAP_LAYOUT)
GRID_COLS = len(MAP_LAYOUT[0])
MAP_WIDTH = TILE_SIZE * GRID_COLS
MAP_HEIGHT = TILE_SIZE * GRID_ROWS
MAP_X = (SCREEN_WIDTH - MAP_WIDTH) // 2
MAP_Y = (SCREEN_HEIGHT - MAP_HEIGHT) // 2