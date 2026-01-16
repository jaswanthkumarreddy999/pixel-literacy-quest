from config.settings import FD_PER_TURN_RATE

class BankSystem:
    @staticmethod
    def deposit(player, amount):
        if amount <= 0: return False, "Invalid amount."
        if player.wallet >= amount:
            player.wallet -= amount
            player.bank_balance += amount
            return True, f"Deposited Rs. {amount}."
        return False, "Not enough cash in wallet!"

    @staticmethod
    def withdraw(player, amount):
        if amount <= 0: return False, "Invalid amount."
        if player.bank_balance >= amount:
            player.bank_balance -= amount
            player.wallet += amount
            return True, f"Withdrew Rs. {amount}."
        return False, "Insufficient bank balance!"

    @staticmethod
    def create_fd(player, amount, turns):
        if amount <= 0 or turns <= 0: return False, "Invalid amount or duration."
        if player.bank_balance >= amount:
            player.bank_balance -= amount
            player.fd_balance = amount
            player.fd_timer = turns
            # Calculate interest based on turns locked
            player.fd_rate = FD_PER_TURN_RATE * turns
            return True, f"FD created for {turns} turns."
        return False, "Insufficient bank balance for FD!"

    @staticmethod
    def redeem_fd(player):
        if player.fd_balance > 0:
            # Check if FD has matured (timer is 0)
            if player.fd_timer <= 0:
                interest = int(player.fd_balance * player.fd_rate)
                total = player.fd_balance + interest
                player.bank_balance += total
                msg = f"FD Matured! Received Rs. {total} (Interest: Rs. {interest})"
            else:
                # Early withdrawal: No interest
                player.bank_balance += player.fd_balance
                msg = "Early Redemption: Only Principal returned (No interest)."
            
            player.fd_balance = 0
            player.fd_timer = 0
            player.fd_rate = 0.0
            return True, msg
        return False, "No active FD to redeem."