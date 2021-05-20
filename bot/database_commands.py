import discord
from discord.ext import commands
import logging
log = logging.getLogger(__name__)
import re
from typing import List

from .commands import Commands
from .database import Database, ItemDefinition, BackpackItem
from .permissions import check_user, is_admin

URL_REGEX = re.compile(
r'^(?:http|ftp)s?://' # http:// or https://
r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
r'localhost|' #localhost...
r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
r'(?::\d+)?' # optional port
r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def validate_url(s: str):
    return re.match(URL_REGEX, s) is not None

class DatabaseCommands(Commands):
    """WIP: Commands for interacting with and updating the bot's database"""

    def __init__(self, database: Database):
        self.database = database

    def setup(self, bot):
        item_group = self.group(bot, self.item_group_entry, name="items")
        self.command(item_group, self.list_items, name="list")
        self.command(bot, self.list_items, name="list")
        self.command(item_group, self.register_item, name="register")
        self.command(item_group, self.unregister_item, name="unregister")
        self.command(item_group, self.item_details, name="details")
        self.command(bot, self.item_details, name="details")

        user_group = self.group(bot, self.user_group_entry, name="user")
        self.command(user_group, self.register_user_admin, name="register")
        self.command(user_group, self.get_user_backpack, name="backpack")
        self.command(bot, self.get_user_backpack, name="backpack")

        self.command(bot, self.buy_item, name="buy")
        self.command(bot, self.give_coins, name="givecoin")

    def make_item_list_embed(self, items: List[ItemDefinition]) -> discord.Embed:
        embed = discord.Embed(title="Item List", type="rich")
        for item in items:
            embed.add_field(name=item.title, value=f"{item.cost} coins")

        return embed

    def make_backpack_embed(self, items: List[BackpackItem]) -> discord.Embed:
        embed = discord.Embed(title="Backpack", type="rich")

        item_data = []
        for bpi in items:
            item = self.database.backpack_item_to_definition(bpi)
            if item is not None:
                item_data.append((item.title, bpi.count))

        item_data.sort(key=lambda t: t[1], reverse=True)

        for title, count in item_data:
            embed.add_field(name=title, value=f"x{count}")

        return embed

    async def item_group_entry(self, ctx):
        """
        Command group relating to managing and viewing items
        """
        if ctx.invoked_subcommand is None:
            await self.list_items(ctx)

    async def list_items(self, ctx):
        """
        List all the items in the store
        """
        await ctx.channel.trigger_typing()
        items = self.database.get_item_definitions()

        if len(items) == 0:
            await ctx.send("Items? We don't have any yet!")
        else:
            await ctx.send(embed=self.make_item_list_embed(items))

    @check_user(is_admin)
    async def register_item(self, ctx, title: str, desc: str, image_url: str, cost: int):
        """
        (ADMIN ONLY) Add a new item to the store
        """
        if cost < 0:
            await ctx.send(f"A cost of **{cost} coins** doesn't really make sense...")
            return

        if not validate_url(image_url):
            await ctx.send(f"Image url {image_url} doesn't look like a URL to me...")
            return

        await ctx.channel.trigger_typing()
        did_register = self.database.register_item(title, desc, image_url, cost)

        if did_register:
            await ctx.send(f"Successfully registered item **\"{title}\"**!")
        else:
            await ctx.send(f"Item \"{title}\" already registered.")

    @check_user(is_admin)
    async def unregister_item(self, ctx, title: str):
        """
        (ADMIN ONLY) Remove an item from the store
        """
        await ctx.channel.trigger_typing()
        self.database.unregister_item(title)

        await ctx.send(f"Item \"{title}\" removed from store (if it existed!)")

    async def item_details(self, ctx, title: str):
        """
        View details about an item
        """
        await ctx.channel.trigger_typing()
        if (item := self.database.find_item(title)) is None:
            await ctx.send(f"Could not find item \"{title}\"! Did you spell it wrong?")
            return

        embed = discord.Embed(
            type="rich",
            title=item.title,
            description=item.desc
        )
        embed.add_field(name="Cost", value=f"{item.cost} coins")
        embed.set_image(url=item.image_url)

        await ctx.send(embed=embed)

    async def user_group_entry(self, ctx):
        """
        Get information about yourself or other users
        """
        if ctx.invoked_subcommand is None:
            await ctx.channel.trigger_typing()
            balance = self.database.get_balance_discord(ctx.author.id)
            await ctx.send(f"Your fake balance is **{balance} coins**!")

    @check_user(is_admin)
    async def register_user_admin(self, ctx, user: discord.User):
        """
        (ADMIN ONLY) Register another user in the coin system
        """
        await ctx.channel.trigger_typing()

        _, already_registered = self.database.register_user(user.id)
        if already_registered:
            await ctx.send(f"User {user} already registered!")
        else:
            await ctx.send(f"User {user} successfully registered!")

    async def register_user_self(self, ctx):
        """
        Register yourself for the coin system
        """
        await ctx.channel.trigger_typing()

        _, already_registered = self.database.register_user(ctx.author.id)
        if already_registered:
            await ctx.send(f"User {ctx.author} already registered!")
        else:
            await ctx.send(f"User {ctx.author} successfully registered!")

    async def buy_item(self, ctx, item: str):
        """
        Buy an item from the store
        """
        await ctx.channel.trigger_typing()

        if (item_def := self.database.find_item(item)) is None:
            await ctx.send(f"Item \"{item}\" doesn't exist!")
            return

        if self.database.buy_item_discord(
            ctx.author.id,
            ctx.message.id, ctx.message.created_at,
            item_def):
            await ctx.send(f"Cha-ching! You bought **{item}**! No refunds!")
        else:
            await ctx.send("You don't have enough coins :(")

    @check_user(is_admin)
    async def give_coins(self, ctx, user: discord.User, coins: int):
        """
        (ADMIN ONLY): Users can have a little coin, as a treat
        """
        await ctx.channel.trigger_typing()

        if self.database.give_coins_discord(
            user.id,
            ctx.message.id, ctx.message.created_at,
            coins):
            await ctx.send(f"Gave {user} **{coins} coins**!")
        else:
            await ctx.send(f"Error giving {user} coins; are they registered?")

    async def get_user_backpack(self, ctx, *, user: discord.User = None):
        """
        List the items in your or another user's backpack
        """
        await ctx.channel.trigger_typing()

        if user is None: user = ctx.author

        items = self.database.get_backpack_items(user.id)
        await ctx.send(embed=self.make_backpack_embed(items))
