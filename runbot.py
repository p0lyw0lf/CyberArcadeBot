#!/bin/env python3

"""
This file is meant to be run directly, never imported
"""

import discord
from discord.ext import commands

description = '''See your Cyber Arcade Coin balance!'''

from bot.bot import setup

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="ca!", description=description, intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

setup(bot)

with open("discord-oauth2.tok", "r") as f:
    bot.run(f.read().strip())
