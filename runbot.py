#!/bin/env python3
"""
This file is meant to be run directly, never imported
"""

import logging
logging.basicConfig(level=logging.INFO)

from bot import bot, setup

with open("discord-oauth2.tok", "r") as f:
    setup(bot)
    bot.run(f.read().strip())
