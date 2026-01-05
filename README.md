# Pixel Literacy Quest - Design Document

## 1. Game Overview
A turn-based strategy game for 11-13 year olds teaching financial literacy.
**Goal:** Achieve highest Net Worth + Happiness while avoiding scams.

## 2. Architecture: MVC Pattern
* **Models (Entities):** Pure data classes (Player, Bank, Scammer). They don't know about Pygame or drawing.
* **Views (UI):** Handle rendering. They take Data and draw it to the screen.
* **Controllers (Core):** `GameManager` handles the rules, input, and updates models.

## 3. Key Mechanics
* **Grid Map:** 10x10 tile system.
* **Turn System:** Round-robin turns (Player 1 -> Player 2 -> Scammer).
* **Banking:** Interest calculation on turn end.
* **Needs/Wants:** Random events affecting budget.

## 4. Visual Style
Pixel Literacy Quest - Deployment Guide

# Stage and Commit
git add .
git commit -m "Initial setup"
git branch -M main

# Link Repo (Replace TOKEN with your actual token)
git remote add origin https://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@github.com/jaswanthkumarreddy999/pixel-literacy-quest.git

# Upload Source Code
git push -u origin main
2. First Time Web Deployment
Run this to create the website branch and upload the game files.

Bash

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
git remote add origin https://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@github.com/jaswanthkumarreddy999/pixel-literacy-quest.git
git push -u origin gh-pages --force
3. Routine Update Workflow (Use this often)
Follow these steps every time you change your Python code.

Phase 1: Update the Website (What players see)

Bash

# 1. Go to project folder
cd "~/PowerHouse/GAME TRADE HACKTHON/PixelLiteracyQuest"

# 2. Rebuild the web files (Clear cache)
pygbag --no_opt .

# 3. Go to build folder
cd build/web

# 4. Push to GitHub Pages
git add .
git commit -m "New update"
git push origin gh-pages
Phase 2: Save Source Code (For you)

Bash

# 1. Go back to main folder
cd ../..

# 2. Push source code to Main branch
git add .
git commit -m "Saved code changes"
git push origin main
4. Troubleshooting
Black Screen on Web? Ensure main.py has the sys.platform == "emscripten" check to disable SCALED flags.

Updates not showing? Open your game link and press Ctrl + Shift + R to force a hard refresh.

Git Password Error? Ensure your remote URL includes your Personal Access Token (as shown in the commands above).