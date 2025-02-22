import discord
from discord.ext import commands
import config

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    channel = bot.get_channel(config.TARGET_CHANNEL_ID)
    if channel:
        print(f'Monitoring channel: #{channel.name}')
    else:
        print(f'Warning: Could not find channel with ID {config.TARGET_CHANNEL_ID}')

@bot.event
async def on_message(message):
    # Only process messages from the target channel
    if message.channel.id == config.TARGET_CHANNEL_ID:
        print(f'\nNew message detected:')
        print(f'  Channel: #{message.channel.name}')
        print(f'  Author: {message.author.name}')
        print(f'  Content: {message.content or "No text content"}')
        
        # Print embed information if present
        if message.embeds:
            for i, embed in enumerate(message.embeds, 1):
                print(f'\n  Embed #{i}:')
                print(f'    Title: {embed.title}')
                print(f'    Description: {embed.description}')
                if embed.fields:
                    print('    Fields:')
                    for field in embed.fields:
                        print(f'      - {field.name}: {field.value}')
        
        print(f'  Has attachments: {len(message.attachments) > 0}')
        if message.attachments:
            for attachment in message.attachments:
                print(f'    - {attachment.filename}: {attachment.url}')
        
    await bot.process_commands(message)

# Run the bot
bot.run(config.DISCORD_TOKEN)