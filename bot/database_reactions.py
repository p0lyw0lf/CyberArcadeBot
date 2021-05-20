import discord
import logging
log = logging.getLogger(__name__)

from .reactions import Reactions
from .database import Database, ItemDefinition, BackpackItem
from .permissions import is_admin

"""
Provisional emoji plan:
:star: = when admin reacts, piece is counted (reactions can still be updated afterwards)
:ocean: = "oc" original art
art-share channel detected automatically
:date: = daily prompt
:sweet_potato: = weekly prompt
:money_mouth: = monthly prompt
:full_moon: = full-fledged
:seven: = collaboration event art
how emojis were chosen: what comes up first when you type the first letters of each of the names
"""

ART_SHARE_CHANNEL = 765585366215819265

EMOJI_SET = {
    '\U0001f30a': "oc",         # :ocean:
    '\U0001f4c5': "daily",      # :date:
    '\U0001f360': "weekly",     # :sweet_potato:
    '\U0001f911': "monthly",    # :money_mouth:
    '\U0001f315': "full",       # :full_moon:
    '\U0000fe0f': "event"       # :seven:
}

class DatabaseReactions(Reactions):
    """
    Watches for certain reactions signalling and art message to be counted and
    updates the user's point total in the database accordingly.

    TODO: also update the google sheet
    """
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

    def setup(self, bot):
        super().setup(bot)
        self.reaction(self.also_add_robot, None, '\U0001f916') # :robot:
        self.reaction(self.record_piece, self.try_erase_piece, '\U00002b50') # :star:

    async def also_add_robot(self, message, user, channel, guild):
        await message.add_reaction('\U0001f916') # :robot:
        log.info(f"Saw a robot from {user}!")

    async def record_piece(self, message, user, channel, guild):
        """
        Check if an admin has reacted to a piece with :star:, updating the point
        total awarded to the user by that piece if necessary.
        """
        if user is None or not is_admin(user):
            return # Ignore non-admin responses

        # Check if piece was already recorded
        # TODO: finish this code
        if (coin_gain := self.db.get_coin_gain_from_message(message.id)) is not None:
            pass
        else:
            pass

    async def try_erase_piece(self, message, user, channel, guild):
        pass
