import pygame
import os

# Define the dictionary of assets to load
# Key Name : File Path
ASSET_MAP = {
    "map": "assets/images/map.png",
    "p1": "assets/images/p1.png",
    "p2": "assets/images/p2.png",
    "scammer": "assets/images/scammer.png",
    # We leave walls/roads empty or commented out because they are part of the map.png
    # "wall": "assets/images/wall.png", 
    # "road": "assets/images/road.png",
}

class AssetLoader:
    def __init__(self):
        self.images = {}
        self.load_all()

    def load_all(self):
        print("--- LOADING ASSETS ---")
        for key, path in ASSET_MAP.items():
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path)
                    self.images[key] = img
                    print(f"Loaded: {key} -> {path}")
                except Exception as e:
                    print(f"Failed to load image {path}: {e}")
                    self.images[key] = None
            else:
                print(f"File Missing: {path}")
                self.images[key] = None
        print("----------------------")

    def get(self, key):
        return self.images.get(key)

# Create a single instance to be imported elsewhere
loader = AssetLoader()