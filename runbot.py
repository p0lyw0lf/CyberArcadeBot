#!/bin/env python3
"""
This file is meant to be run directly, never imported
"""

import logging
logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARN)

from bot import bot, setup

with open("discord-oauth2.tok", "r") as f:
    setup(bot)
    bot.run(f.read().strip())
