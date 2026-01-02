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
* 16-bit Pixel Art.
* 4-Corner HUD Layout (Static UI, Active Map).
no that is not the game logic  This is a strong game loop because it naturally creates tension between Safety (Banking) and Risk (Scams/Wants). Since you are designing this for a hackathon, I have mapped your specific mechanics to the concepts in the guide and provided three "Game Polish" suggestions to make the gameplay smoother.



Part 1: How Your Mechanics Teach the Concepts

Here is the filled-out list based on your design and the GUIDE.pdf:



What Banks do: The Bank is the "Safe Zone." Money deposited here cannot be stolen by the Scammer, whereas money in the player's "Pocket" can be lost.

How accounts work: You split the player's UI into Wallet (Cash for moving/Needs) and Bank Balance (Savings). This visualizes two different storage spaces.

What interest means: The Fixed Deposit (FD) mechanic. Players lock money away to get higher returns, teaching them that money grows over time if left untouched.



How digital payments work: Allow players to pay for "Needs" directly from the Bank Balance (simulating UPI/Apps) without having to travel to a "Shop Tile".

Debit Cards & ATMs: The "Math Question" minigame represents the PIN. Solving the math correctly simulates entering the correct PIN to access cash.

Staying safe with PIN, OTP, scams: The "OTP Hunt" mechanic. Players must physically collect digits on the map, symbolizing that OTPs are private keys you must possess and not share.

Needs vs Wants: The "Random List" mechanic. Needs (Food/School) must be paid to survive (keep Health up), while Wants (Toys) are optional and just increase the score.

+1



Simple budgeting: The player must calculate: "Do I have enough cash for the 'Need' that is coming next turn before I deposit everything into Fixed Deposit?".

Basics of loans: If a player runs out of cash for a "Need," they are forced to take a Loan. The game deducts interest every turn until they repay it.

Part 2: Design Improvements & Suggestions

1. Refine the Roles (The "AI Scammer" Fix)

Critique: If one human player is the "Scammer" and others are "Family Men" in a turn-based game, the Scammer might get bored just waiting. Also, if players are new, being the Scammer is less educational about banking.Suggestion:



Make the Scammer a Bot (NPC): The Scammer is an AI character that moves 2 steps toward the nearest rich player every turn.

Make the Banker the "System": Don't have a player be the banker. The Bank is a building/menu everyone interacts with.

Players = Family Men: All human players compete to be the "Richest & Happiest Family."

2. The "Fixed Deposit" Twist (Liquidity)

Critique: If FDs just give high interest, players will dump all money there.Suggestion: Add a "Lock-in Period".



If a player puts money in FD, it is locked for 3 Turns.

The Trap: A "Need" (like a Medical Emergency) pops up during those 3 turns. Since their cash is locked, they are forced to take a Loan (high interest) to pay for the Need.

Lesson: This teaches why we need liquid cash (Savings Account) vs locked investments (FD).

3. Scoring Logic (Balancing Needs vs. Wants)

Critique: You mentioned "highest money and wants meter and needs meter will win." This can be confusing.Suggestion: Use this simple formula:



Health (Needs): If this hits 0 (missed too many Needs), the player gets "Game Over" immediately. (Needs are survival).

Happiness (Wants): Buying Wants adds "Victory Points."

Net Worth: Bank Balance + Cash.

Winner: The survivor with the highest (Net Worth + Victory Points).

4. The "OTP Map" Mechanic (Turn-Based Chase)

Since it is turn-based, "escaping" can be tricky. Use a Grid Map (10x10).



Turn 1: Player moves 3 tiles to grab an OTP Digit.

Turn 2: Scammer Bot moves 2 tiles toward the Player.

Tension: The player must calculate: "Can I grab the digit and reach the Bank Tile before the Scammer catches me?"

Part 3: One-Turn Gameplay Example

Here is how a single turn would look in your code logic:



Start Turn: Player gets monthly income (e.g., ₹500).

Event Card: A random Need appears: "School Fees: ₹200 due!" and a Want appears: "Video Game: ₹300 (gives +50 Happiness)".

Action Phase (Movement): Player rolls dice/moves on grid.

Option A: Go to Bank Tile to Deposit money (Safe).

Option B: Go to OTP Tile to collect a digit (Risk: Scammer is nearby).

Bank Phase: If at Bank, player chooses:

Deposit: 5% Interest (Safe, available next turn).

Fixed Deposit: 10% Interest (Locked for 3 turns).

Payment Phase:

Must Pay: ₹200 for School Fees. If Cash < 200 -> Auto Loan (Debt + 10% interest).

Can Pay: ₹300 for Video Game. (Only if budget allows).

End Turn: Scammer Bot moves closer.

This structure covers almost every educational point in the guide while keeping the game fun and strategic.