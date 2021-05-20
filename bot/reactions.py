import discord
from collections import defaultdict
import logging
log = logging.getLogger(__name__)

from .commands import Commands

class Reactions(Commands):
    """
    Class that watches messages for certain reactions, automatically calling
    handlers when certain reactions appear/disappear.
    """

    def __init__(self):
        self.handler_map = defaultdict(list, dict())

    def setup(self, bot):
        self.bot = bot
        bot.add_listener(self.on_raw_reaction_add, "on_raw_reaction_add")
        bot.add_listener(self.on_raw_reaction_remove, "on_raw_reaction_remove")

    def reaction(self, add_function, remove_function, emoji_id):
        """
        Adds a new reaction handler to the specified bot.

        Whenever `bot` sees an emoji with id or unicode codepoint `emoji_id`
        being added to a message, it will call
        `add_function(message_id, user_id, channel_id, guild_id)` where
        all items are `int`s except for `guild_id`, which may be optional if
        this was called from a DM. This corresponds with the fields returned by
        a `discord.RawReactionAddEvent`.

        Whenever `bot` sees an emoji with id or unicode codepoint `emoji_id`
        begin removed from a message, it will call
        `remove_function(message_id, user_id, channel_id, guild_id)` for each
        user that removed a reaction from the message. This *is not* called
        when the message is deleted instead of simply un-reacted to. A lot of
        state would need to be kept for that to happen, so we just don't.
        """

        # Append handlers to end of list of existing ones
        self.handler_map[emoji_id] += [(add_function, remove_function)]

    def partial_emoji_to_key(self, pe):
        """
        Converts a `discord.PartialEmoji` into a key for our `handler_map`.
        """
        if pe.is_custom_emoji():
            return pe.id
        else:
            return pe.name

    async def rrae_to_objects(self, rrae):
        """
        Converts a `discord.RawReactionActionEvent` to a series of full discord
        objects. Requires the user and message intents enabled to work fully.
        """
        channel = self.bot.get_channel(rrae.channel_id)
        if channel is None:
            log.debug(f"Channel {rrae.channel_id} was None")
            message = None
        else:
            message = await channel.fetch_message(rrae.message_id)
        user = self.bot.get_user(rrae.user_id)
        guild = self.bot.get_guild(rrae.guild_id)

        return message, user, channel, guild

    async def on_raw_reaction_add(self, rrae):
        emoji_id = self.partial_emoji_to_key(rrae.emoji)
        message, user, channel, guild = await self.rrae_to_objects(rrae)
        if message is None:
            log.error(f"Message {rrae.message_id} not found!")
        else:
            for add_fn, _ in self.handler_map[emoji_id]:
                if add_fn is not None:
                    await add_fn(message, user, channel, guild)

    async def on_raw_reaction_remove(self, rrae):
        emoji_id = self.partial_emoji_to_key(rrae.emoji)
        message, user, channel, guild = await self.rrae_to_objects(rrae)
        if message is None:
            log.error(f"Message {rrae.message_id} not found!")
        else:
            for _, remove_fn in self.handler_map[emoji_id]:
                if remove_fn is not None:
                    await remove_fn(message, user, channel, guild)
