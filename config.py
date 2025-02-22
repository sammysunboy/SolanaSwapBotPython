from solana.rpc.api import Client
from solders.keypair import Keypair

# ==== CONFIGURATION (Edit these values) ====

# Solana Configuration
RPC = "YOUR_RPC"  # Example: A free RPC from Helius
                  # Get one at: https://dev.helius.xyz/dashboard/app

# Wallet Configuration 
PRIVATE_KEY = "YOUR_PRIVATE_KEY"  # Your Solana wallet's private key in base58
                                 # WARNING: Keep this secret and secure!

# Discord Configuration
DISCORD_TOKEN = "YOUR_DISCORD_TOKEN"    # Get from Discord Developer Portal
DISCORD_CHANNEL = 123456789             # Right-click channel → Copy ID 
                                       # (Need Developer Mode enabled in Discord)

# ==== DO NOT EDIT BELOW THIS LINE ====

# Initialize connections
payer_keypair = Keypair.from_base58_string(PRIVATE_KEY)
client = Client(RPC)