import discord
from discord.ext import commands
import logging
log = logging.getLogger(__name__)

from .command_registry import Commands
from .database import Database

class DatabaseCommands(Commands):
    """TODO: Commands for interacting with and updating the bot's database"""

    def __init__(self, database: Database):
        self.database = database

    def setup(self, bot):
        pass
