# Pixel Literacy Quest

![Pixel Literacy Quest Intro](ref.png)

A turn-based strategy game designed to teach financial literacy to 11-13 year olds.

**Goal:** Achieve the highest Net Worth and Happiness while avoiding scams and completing your Needs and Wants!

## 🎮 Game Overview

Pixel Literacy Quest is a 2-player competitive educational game built in Python using Pygame. It drops players into a tile-based map where they roll dice, navigate to various buildings (Store, Bank, Hospital, School, Apartment), manage their finances through a fully functional banking system, and avoid a roaming "Scammer" NPC that tests their cybersecurity awareness.

### Key Features
* **Financial Management:** Earn monthly income, manage a wallet, and interact with the Bank (Deposits, Withdrawals, Fixed Deposits with dynamic interest rates).
* **Needs vs. Wants Mechanics:** Real-world scenarios where unfulfilled "Needs" (Groceries, Rent, Medical Emergencies) drain Health, while spending on "Wants" (Video Games, Vacations) boosts Happiness.
* **Scam Encounters:** A roaming Scammer NPC triggers mini-games (OTP math puzzles and Cybersecurity Quizzes) to teach you about real world cybersecurity. Falling for a scam results in a brutal financial penalty!
* **Competitive Turn-Based Gameplay:** Round-robin turns with dice rolls, strategic movement, and an end-game scoring system that rewards balanced financial decisions.
* **Web-Ready:** Designed using asyncio and built around `pygbag`, making it fully playable directly in a web browser!

## 🏗️ Architecture

The game's source code strictly follows the **Model-View-Controller (MVC)** design pattern to separate logic from rendering, ensuring a clean and manageable codebase:
* **Models (Entities):** Pure data classes (`entities/player.py`, `entities/bank.py`, `entities/npc.py`). They handle character statistics, inventory, and logic without relying on Pygame's rendering logic.
* **Views (UI):** Modular UI components (`ui/map_view.py`, `ui/hud.py`) take game data and render it to the screen cleanly.
* **Controllers (Core & Logic):** `GameManager` (in `core/game_manager.py`) and Economy rules (`logic/economy.py`) process input events, enforce gameplay rules, and orchestrate updates between Entities and Views.

## 🚀 Installation & Setup

### Prerequisites
* Python 3.8+
* Pygame
* asyncio (used for web compatibility loops)

### Running Locally
```bash
git clone <repository_url>
cd "PixelLiteracyQuest"
pip install pygame
python main.py
```

## 🌐 Web Deployment Guide

Pixel Literacy Quest is fully compatible with `pygbag` for web deployment. Follow these steps to build the game and deploy it smoothly to GitHub Pages.

### 1. Initial Setup & Push
```bash
git add .
git commit -m "Initial setup"
git branch -M main
git push -u origin main
```

### 2. First Time Web Deployment
Run this to create the website branch and upload the game files for the very first time.

```bash
# Build the game for web
pygbag --no_opt .

# Go to build folder
cd build/web

# Initialize a separate git repo for the build
git init
git add .
git commit -m "Deploy web"
git branch -M gh-pages

# Connect and Force Push to gh-pages branch
# Make sure to replace <YOUR_REPO_URL> with your actual repository URL
git remote add origin <YOUR_REPO_URL>
git push -u origin gh-pages --force
```

### 3. Routine Update Workflow (Use this often)
Follow these steps every time you change your Python code to ensure your web deployment stays up to date.

**Phase 1: Update the Website (What players see)**
```bash
# 1. Be in project root folder
cd "~/PowerHouse/GAME TRADE HACKTHON/PixelLiteracyQuest"

# 2. Rebuild the web files (Clear cache)
pygbag --no_opt .

# 3. Go to build folder
cd build/web

# 4. Push to GitHub Pages
git add .
git commit -m "New update"
git push origin gh-pages
```

**Phase 2: Save Source Code (For you)**
```bash
# 1. Go back to main folder
cd ../..

# 2. Push source code to Main branch
git add .
git commit -m "Saved code changes"
git push origin main
```

### 4. Troubleshooting Support
* **Black Screen on Web?** Ensure `main.py` has the `sys.platform == "emscripten"` check to disable `SCALED` and `FULLSCREEN` flags when running on the web browser.
* **Updates not showing?** Open your game link and press `Ctrl + Shift + R` to force a hard refresh and wipe the browser cache.
* **Git Password Error?** Ensure your Git remote URL includes your Personal Access Token (as shown in the deployment commands above).

---
**Developed for the GAME TRADE HACKTHON.**