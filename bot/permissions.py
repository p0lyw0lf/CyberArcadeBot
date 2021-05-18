from discord.ext import commands

# TODO: change this to be customizable per server. Not needed atm tho
ADMIN_ROLE_ID = 765320566739435550


def has_role(role_id):
    async def predicate(ctx):
        if hasattr(ctx.author, "roles"):
            return any(role_id == role.id for role in ctx.author.roles)
        else:
            return False

    return commands.check(predicate)

def has_any_role(role_ids):
    role_id_set = set(role_ids)

    async def predicate(ctx):
        if hasattr(ctx.author, "roles"):
            return any((role.id in role_id_set) for role in ctx.author.roles)
        else:
            return False

    return commands.check(predicate)

def admin_check():
    return has_role(ADMIN_ROLE_ID)
