"""
pathfinding.py — BFS pathfinding for navigating the game map.
"""
from collections import deque

def get_bfs_path(start, goal, map_layout):
    """
    Finds the shortest path from start to goal on the grid using BFS.
    map_layout: 2D list where 0 is walkable and 1 is blocked.
    Returns: List of (x, y) coordinates representing the path, or None if no path exists.
    """
    start = tuple(start)
    goal = tuple(goal)
    
    if start == goal:
        return []

    rows = len(map_layout)
    cols = len(map_layout[0])
    
    queue = deque([start])
    visited = {start: None}  # Maps position -> parent
    
    while queue:
        curr = queue.popleft()
        
        if curr == goal:
            path = []
            node = curr
            while node is not None:
                path.append(node)
                node = visited[node]
            return path[::-1][1:] # Reverse and exclude start position
            
        cx, cy = curr
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            
            if 0 <= nx < cols and 0 <= ny < rows:
                if map_layout[ny][nx] == 0 and (nx, ny) not in visited:
                    visited[(nx, ny)] = curr
                    queue.append((nx, ny))
                    
    return None
