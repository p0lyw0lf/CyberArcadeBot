import discord
from discord.ext import commands
import logging
log = logging.getLogger(__name__)
import sqlite3

from .database_commands import DatabaseCommands
from .database_reactions import DatabaseReactions
from .database import Database, DATABASE_FILE
from .sheet_commands import SheetCommands
from .sheet.google_auth import GoogleAPI

description = '''See your Cyber Arcade Coin balance!'''
intents = discord.Intents(
    guilds      =True,
    members     =True,
    bans        =False,
    emojis      =True,
    integrations=False,
    webhooks    =False,
    invites     =False,
    voice_states=False,
    presences   =False,
    messages    =True,
    reactions   =True,
    typing      =True
)

bot = commands.Bot(
    command_prefix=("ca!", "Ca!", "CA!", "ca ", "Ca ", "CA "),
    description=description,
    intents=intents
)

@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user}")

def setup(bot):
    google_api = GoogleAPI()
    sheet = google_api.make_sheet()

    database = Database(
        sqlite3.connect(
            DATABASE_FILE,
            detect_types=sqlite3.PARSE_COLNAMES | sqlite3.PARSE_DECLTYPES
        )
    )
    sc = SheetCommands(sheet, database)
    dc = DatabaseCommands(database)
    dr = DatabaseReactions(database)
    sc.setup(bot)
    dc.setup(bot)
    dr.setup(bot)
