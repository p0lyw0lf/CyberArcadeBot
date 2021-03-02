class Commands:
    """
    Base class that command registries are expected to inherit from
    """

    def setup(self, bot):
        """
        Initializes a bot with the commands in this registry
        """
        pass

    async def default_error(self, ctx, error):
        """Default error handler for discord commands"""
        await ctx.send(f"Oopsie Woopsie: {error}")
