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

    def command(self, bot_or_group, function, error_handler=None, **kwargs):
        """
        Adds a command to the specified bot or group. Uses
        `discord.ext.commands.Command` to wrap the `function` handler, all extra
        `**kwargs` are passed through. If no error handler is specified, the
        default one is attached.
        """
        command_obj = commands.Command(function, **kwargs)

        if error_handler is None:
            error_handler = self.default_error

        command_obj.error(error_handler)
        bot_or_group.add_command(command_obj)

        return command_obj

    def group(self, bot_or_group, group_function, error_handler=None, **kwargs):
        """
        Adds a command group to the specified bot or group. Uses
        `discord.ext.commands.Group` to wrap the `group_function` default group
        handler. Commands can be added to the returned group using
        `self.command`. Like before, if no error handler is specified, the
        default one is used.
        """
        group = commands.Group(group_function, **kwargs)

        if error_handler is None:
            error_handler = self.default_error

        group.error(error_handler)
        bot_or_group.add_command(group)

        return group

    async def default_error(self, ctx, error):
        """Default error handler for discord commands"""
        log.error(traceback.format_exc())
        await ctx.send(f"Oopsie Woopsie: {error}")
