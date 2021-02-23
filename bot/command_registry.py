class Commands:
    """
    Base class that command registries are expected to inherit from
    """

    NAME = ""

    def setup(self, bot):
        """
        Initializes a bot with the commands in this registry
        """
        pass
