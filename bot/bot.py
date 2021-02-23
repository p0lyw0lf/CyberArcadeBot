import discord

from .modules.sheet.commands import SheetCommands

def setup(bot):
    s = SheetCommands()
    s.setup(bot)
