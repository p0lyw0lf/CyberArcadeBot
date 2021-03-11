import discord
from discord.ext import commands
import logging
log = logging.getLogger(__name__)

from .command_registry import Commands
from .database import Database
from .permissions import admin_check
from .sheet.google_auth import GoogleAPI

class SheetCommands(Commands):
    """
    WIP: Commands for interfacing with the official Google Sheet for data
    visualization
    """

    def __init__(self, database: Database):
        self.google_api = GoogleAPI()
        self.sheet = self.google_api.make_sheet()
        self.database = database

    def setup(self, bot):
        self.command(bot, self.balance, self.balance_error)
        self.command(bot, self.import_sheet, name="import")
        self.command(bot, self.export_sheet, name="export")

    async def balance(self, ctx, *, user: discord.Member = None):
        """Check the current coin balance for yourself or another user"""
        if not user:
            user = ctx.author

        await ctx.channel.trigger_typing()
        await ctx.send(self.get_balance(user))

    async def balance_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("I couldn't find that member, sorry :(")
        else:
            await self.default_error(ctx, error)

    def get_balance(self, user):
        discriminator = '#' + str(user.discriminator)
        balance = None
        sheet_data = self.sheet.fetch("'User Backpack'!A3:C")
        for row in sheet_data:
            if len(row) >= 2:
                row_user, row_disc, *rest = row
                if row_user == user.name and row_disc == discriminator:
                    if len(rest) > 0: balance = rest[0]
                    else: balance = 0

        log.info(f"{user}: {balance}")

        if balance is None:
             return f"Error: Balance not found for user {user}!"
        else:
            return f"{user.display_name} has **{balance}** coins!"

    async def import_sheet(self, ctx):
        """INCOMPLETE: Imports data from the Google Sheet into the bot's database"""
        await ctx.send("I didn't do anything!")

    async def export_sheet(self, ctx):
        """INCOMPLETE: Exports data from the bot's database into the Google Sheet"""
        await ctx.send("I didn't do anything!")
