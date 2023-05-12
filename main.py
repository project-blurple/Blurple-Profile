import discord
from discord.ext import commands

from config import *


class BlurpleProfile(commands.Bot):
    async def setup_hook(self):
        initial_extensions = [
            'owner',
            'profile'
        ]

        for extension in initial_extensions:
            await bot.load_extension(extension)


intents = discord.Intents.all()

description = "Blurple Profile"
get_pre = lambda bot, message: BOT_PREFIX
bot = BlurpleProfile(command_prefix=get_pre, description=description, intents=intents)

bot.recent_cog = None

bot.tasks = {}


@bot.event
async def on_connect():
    print('Loaded Discord')


@bot.event
async def on_ready():
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(discord.utils.utcnow().strftime("%d/%m/%Y %I:%M:%S:%f"))
    print('------')


@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


bot.run(TOKEN, reconnect=True)
