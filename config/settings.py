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
STARTING_WALLET = 1000
STARTING_BANK = 2000
MONTHLY_INCOME = 100

LOAN_INTEREST = 0.10     
LOAN_REPAY_TURNS = 3
LOAN_REPAY_MULTIPLIER = 2.0
SAVINGS_INTEREST = 0 
FD_INTEREST = 0.15       
FD_LOCK_TURNS = 3 
FD_PER_TURN_RATE = 0.05      

# --- DIGITAL PAYMENTS ---
DIGITAL_ONLY = ["Rent", "water bill", "Wifi"]

# --- SCAM & DIFFICULTY SETTINGS ---
SCAM_FREEZE_TURNS = 3        
SCAM_PENALTY_OTP = 0.05      
SCAM_PENALTY_QUIZ = 0.10     
SCAM_PENALTY_FLEE = 0.10     

# --- GAME CONTENT ---
GAME_NEEDS = [
    ("Fire Accident", 100), ("Groceries", 150), ("Food", 120), 
    ("Medicines", 100), ("fever", 150), ("Heart Attack", 80),
    ("School Fees", 200), ("Clothes", 200), ("water bill", 250), ("Rent", 300)
]

GAME_WANTS = [
    ("Wifi", 50, 3), ("Cinema", 80, 5), ("Dinner", 100, 5),
    ("Headphones", 120, 8), ("Video Game", 150, 10), ("Movie Ticket", 150, 10),
    ("TV", 200, 15), ("Watch", 250, 20), ("Phone", 400, 25), ("Vacation", 500, 40)
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

# --- BUILDING & ITEM MAPPING ---
BUILDING_LOCATIONS = {
    (4, 6): "bank", (5, 6): "bank",         
    (2, 9): "store",        
    (8, 6): "hospital", (9, 6): "hospital",      
    (0, 6): "fire_station", (1, 6): "fire_station", 
    (1, 3): "apartment", (2, 3): "apartment",    
    (4, 2): "school", (5, 2): "school"  
}

ITEM_LOCATIONS = {
    "Fire Accident": "fire_station", "Groceries": "store", "Food": "store",
    "Medicines": "hospital", "fever": "hospital", "Heart Attack": "hospital",
    "School Fees": "school", "Clothes": "store", "water bill": "apartment",
    "Rent": "apartment", "Wifi": "apartment", "Cinema": "apartment",
    "Dinner": "store", "Headphones": "store", "Video Game": "store",
    "Movie Ticket": "store", "TV": "store", "Watch": "store",
    "Phone": "store", "Vacation": "school" 
}

QUIZ_QUESTIONS = [
    {"q": "OTP valid for how long?", "a": "10 min", "opts": ["10 min", "1 hour", "Forever"], "exp": "OTPs usually expire in 10 minutes!"},
    {"q": "Share PIN with?", "a": "No One", "opts": ["Bank", "No One", "Friends"], "exp": "Never share your PIN, not even with the bank!"},
    {"q": "Green lock on URL means?", "a": "Secure", "opts": ["Secure", "Hacked", "Open"], "exp": "A green lock means the website is secure (HTTPS)."},
    {"q": "Full form of ATM?", "a": "Automated Teller", "opts": ["Any Time Money", "Automated Teller", "All Time Money"], "exp": "ATM means Automated Teller Machine."},
    {"q": "CVV is on which side?", "a": "Back", "opts": ["Front", "Back", "Chip"], "exp": "The CVV is the 3-digit security code on the back."},
]

# --- SCORING WEIGHTS ---
SCORE_WEALTH_DIVIDER = 10     
SCORE_HEALTH_MULTIPLIER = 100 
SCORE_TASK_MULTIPLIER = 150   
SCORE_FINISH_BONUS = 500      

# --- FINANCIAL TIP CARDS (Feature 12) ---
SCAM_TIPS = {
    "OTP":        ("TIP: OTP Security",        "Never share your OTP with anyone — not even\nyour bank or a support agent. OTPs expire in\n10 minutes and are single-use only."),
    "PICKPOCKET": ("TIP: Cash Safety",          "Always keep cash in a secured wallet. Prefer\nUPI or card payments in public places.\nReport theft immediately to police."),
    "QUIZ":       ("TIP: Digital Payments",     "Always verify before you pay. Check the\nrecipient's UPI ID carefully. Use only\nofficial bank apps to transact."),
}

# --- RANDOM EVENTS (Feature 2) ---
RANDOM_EVENTS = [
    {"name": "Salary Bonus!",       "desc": "Company paid a bonus!",           "type": "wallet",  "amount":  300},
    {"name": "Market Crash!",       "desc": "Your savings dipped slightly.",    "type": "bank",    "amount": -200},
    {"name": "Medical Emergency!",  "desc": "Unexpected hospital bill.",        "type": "wallet",  "amount": -150},
    {"name": "Lucky Find!",         "desc": "Found money on the street!",      "type": "wallet",  "amount":  100},
    {"name": "Tax Refund!",         "desc": "Government refunded tax.",         "type": "wallet",  "amount":  250},
    {"name": "Phone Bill!",         "desc": "Monthly phone bill due.",         "type": "wallet",  "amount": -80},
    {"name": "Investment Return!",  "desc": "Your FD earned extra interest.",  "type": "bank",    "amount":  150},
    {"name": "Theft!",              "desc": "Pickpocket stole some cash!",     "type": "wallet",  "amount": -120},
]
RANDOM_EVENT_INTERVAL = 4   # trigger every N turns

# --- MINI-BUDGET CHALLENGE (Feature 4) ---
BUDGET_CHALLENGE_INTERVAL = 6   # every N turns
BUDGET_AMOUNT = 500
BUDGET_OPTIONS = [
    {"label": "Save More",    "desc": "+Rs.350 to Bank, +5 Health",       "bank": 350, "wallet": 0,   "health": 5,  "happy": 0},
    {"label": "Stay Healthy", "desc": "+Rs.150 to Bank, +20 Health, +5 Happy", "bank": 150, "wallet": 0, "health": 20, "happy": 5},
    {"label": "Enjoy Life",   "desc": "+Rs.100 to Bank, +5 Health, +30 Happy", "bank": 100, "wallet": 0, "health": 5,  "happy": 30},
]

# --- AVATAR COLORS (Feature 9) ---
AVATAR_COLORS = [
    (46, 204, 113),    # Emerald green
    (52, 152, 219),    # Sky blue
    (231, 76, 60),     # Red
    (241, 196, 15),    # Yellow
    (155, 89, 182),    # Purple
    (230, 126, 34),    # Orange
]
AVATAR_NAMES = ["Emerald", "Sky", "Red", "Yellow", "Purple", "Orange"]