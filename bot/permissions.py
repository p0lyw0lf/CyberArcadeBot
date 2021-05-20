from discord import User
from discord.ext import commands

from typing import Callable
import inspect

# TODO: change this to be customizable per server. Not needed atm tho
ADMIN_ROLE_ID = 765320566739435550

def has_role(role_id):
    def predicate(user: User):
        if hasattr(user, "roles"):
            return any(role_id == role.id for role in user.roles)
        else:
            return False

    return predicate

def has_any_role(role_ids):
    role_id_set = set(role_ids)

    def predicate(user: User):
        if hasattr(user, "roles"):
            return any((role.id in role_id_set) for role in user.roles)
        else:
            return False

    return predicate

is_admin = has_role(ADMIN_ROLE_ID)

def check_user(predicate: Callable[[User], bool]):
    """
    Given a check that only looks at the user, return a full
    `discord.ext.commands` wrapper for it that takes in a `commands.Context`
    instead.
    """
    if inspect.iscoroutinefunction(predicate):
        async def mod_predicate(ctx: commands.Context):
            return await predicate(ctx.author)
    else:
        async def mod_predicate(ctx: commands.Context):
            return predicate(ctx.author)

    return commands.check(mod_predicate)
