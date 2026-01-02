class Building:
    def __init__(self, name, type_id, grid_x, grid_y):
        self.name = name
        self.type = type_id # 'bank', 'school', etc.
        self.pos = (grid_x, grid_y)