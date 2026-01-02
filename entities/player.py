class Player:
    def __init__(self, id, name, color):
        self.id = id
        self.name = name
        self.color = color
        self.wallet = 500
        self.bank_balance = 0
        self.grid_pos = [0, 0] # [col, row]
        self.needs = ["Food"]
        self.wants = []

    def move(self, dx, dy):
        self.grid_pos[0] = max(0, min(9, self.grid_pos[0] + dx))
        self.grid_pos[1] = max(0, min(9, self.grid_pos[1] + dy))