#BotConfig
# Trading Configuration
HOLD_TIME = 1  # Time to hold in seconds before selling (5 seconds)
MAX_BUY_ATTEMPTS = 5  # Maximum number of buy attempts
RAYDIUM_ONLY = True  # Whether to only trade on Raydium
SOL_AMOUNT = 0.01  # Amount of SOL to use per trade
SELL_PERCENTAGE = 100  # Percentage of tokens to sell

# Slippage Configuration
BUY_SLIPPAGE = 30  # Initial buy slippage percentage
SELL_SLIPPAGE = 30  # Initial sell slippage percentage
SLIPPAGE_INCREASE = 5  # Amount to increase slippage by after each failed sell attempt
MAX_SELL_SLIPPAGE = 95  # Maximum allowed sell slippage percentage