An easy to setup custom Memecoin trading bot that monitors trading signals and automatically executes trades on Solana DEX (Raydium, Pumpfun)

## Features
- Monitors Discord channels for trading signals
- Automated buying and selling on Solana
- Configurable trading parameters  
- Trade logging and history tracking
- Auto-selling based on hold time
- Optional Raydium-only trading

## Complete Setup Guide

### Requirements
- Python 3.7+
- Discord Bot Token
- Solana Wallet
- Helius RPC URL & Webhook

### Helius Setup
1. Go to [Helius](https://dev.helius.xyz/dashboard/app) and create an account
2. Create a new API key
3. Copy your RPC URL
4. Create a new webhook:
  - Set event type to "SWAP"
  - Copy the webhook URL for your config

### Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and name it
3. Go to "Bot" section and click "Add Bot"
4. Enable these settings under Privileged Gateway Intents:
  - Message Content Intent
  - Server Members Intent
  - Presence Intent
5. Copy the bot token
6. Generate invite link:
  - Go to OAuth2 > URL Generator
  - Select scopes: 'bot' and 'applications.commands'
  - Select permissions: 'Read Messages/View Channels'
  - Copy and use the generated URL to invite bot to your server
7. Enable Developer Mode in Discord:
  - User Settings > App Settings > Advanced > Developer Mode
8. Right-click the channel you want to monitor and click "Copy ID"

### Installation
```bash
git clone https://github.com/sammysunboy/SolanaSwapBotPython.git
cd SolanaSwapBotPython
pip install -r requirements.txt
```

### Configuration
Edit `config.py` with your details:
```python
RPC = "YOUR_HELIUS_RPC_URL"
PRIVATE_KEY = "YOUR_WALLET_PRIVATE_KEY"
# Discord Settings
DISCORD_TOKEN = "YOUR_BOT_TOKEN"
DISCORD_CHANNEL = 123456789  # Channel ID you copied
```

### Trading Settings
Edit `botconfig.py` to adjust trading parameters:
```python
HOLD_TIME = 1  # Seconds before selling
SOL_AMOUNT = 0.01  # SOL per trade
BUY_SLIPPAGE = 30  # Buy slippage %
SELL_SLIPPAGE = 30  # Sell slippage %
```

## Usage
Run the bot:
```bash
python main.py
```
Bot will start monitoring the channel and execute trades

## Security Tips
1) Keep your private key secure
2) Start with small amounts
3) Use a dedicated wallet
4) Monitor the bot regularly

## Support
Create an issue on GitHub for bugs or feature requests.

## Disclaimer
This bot trades real assets. Use at your own risk. Not financial advice.
```
