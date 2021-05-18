import discord
import logging
log = logging.getLogger(__name__)

from .reactions import Reactions
from .database import Database, ItemDefinition, BackpackItem
from .permissions import admin_check

class DatabaseReactions(Reactions):
    """
    TODO: actually make this useful for managing the database using admin
    reactions. Currently just a PoC with a robot face.
    """
    def setup(self, bot):
        super().setup(bot)
        self.reaction(self.also_add_robot, None, '\U0001f916')

    async def also_add_robot(self, message, user, channel, guild):
        if message is not None:
            await message.add_reaction('\U0001f916')
            log.info(f"Saw a robot from {user}!")
