from discord.ext import commands
import logging
log = logging.getLogger(__name__)
import traceback

class Commands:
    """
    Base class that command registries are expected to inherit from
    """

    def setup(self, bot):
        """
        Initializes a bot with the commands in this registry
        """
        pass

    def command(self, bot, function, error_handler=None, **kwargs):
        command_obj = commands.Command(function, **kwargs)

        if error_handler is None:
            error_handler = self.default_error

        command_obj.error(error_handler)
        bot.add_command(command_obj)

        return command_obj

    def group(self, bot, group_function, error_handler=None, **kwargs):
        group = commands.Group(group_function, **kwargs)

        if error_handler is None:
            error_handler = self.default_error

        group.error(error_handler)
        bot.add_command(group)

        return group

    async def default_error(self, ctx, error):
        """Default error handler for discord commands"""
        log.error(traceback.format_exc())
        await ctx.send(f"Oopsie Woopsie: {error}")
