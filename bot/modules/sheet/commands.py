import discord
from discord.ext import commands

from ...command_registry import Commands
from .google_auth import GoogleAPI

class SheetCommands(Commands):
    NAME = "sheet"

    def __init__(self):
        self.google_api = GoogleAPI()
        self.sheet = self.google_api.make_sheet()

    def setup(self, bot):
        balance_command = commands.Command(self.balance)
        balance_command.error(self.balance_error)
        bot.add_command(balance_command)

    async def balance(self, ctx, *, user: discord.Member = None):
        if not user:
            user = ctx.author

        await ctx.channel.trigger_typing()
        await ctx.send(self.get_balance(user))

    async def balance_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("I couldn't find that member, sorry :(")
        else:
            await ctx.send(f"Oopsie Woopsie: {error}")

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

        print(user, balance)
        if balance is None:
             return f"Error: Balance not found for user {user}!"
        else:
            return f"{user.display_name} has **{balance}** coins!"
