import discord
from discord.ext import commands
import logging
log = logging.getLogger(__name__)
import sqlite3

from .sheet_commands import SheetCommands
from .database_commands import DatabaseCommands
from .database import Database, DATABASE_FILE

description = '''See your Cyber Arcade Coin balance!'''
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="ca!", description=description, intents=intents)

@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user}")

def setup(bot):
    db = Database(sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_COLNAMES))
    d = DatabaseCommands(db)
    s = SheetCommands(db)
    s.setup(bot)
