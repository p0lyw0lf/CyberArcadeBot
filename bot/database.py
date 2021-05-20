from dataclasses import dataclass
import datetime
import logging
log = logging.getLogger(__name__)
import os
from os.path import dirname, abspath, join
import sqlite3
from typing import Optional, List, Tuple

import discord

DATABASE_FILE = join(dirname(abspath(__file__)), "coins.db")


def create_database(conn: sqlite3.Connection):
    """
    Given a connection to an SQLite3 database, initialize it with all the
    tables required to run the both with.

    conn: the connection
    """

    c = conn.cursor()
    c.executescript('''
        PRAGMA foreign_keys = ON;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL, -- Discord uses bigints, don't fit into regular int
            coins INT NOT NULL
        );

        CREATE TABLE coin_gains (
            id INTEGER PRIMARY KEY,
            message_id TEXT,
            user_id INT NOT NULL,
            date_entered TEXT NOT NULL,
            coins INT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE item_definitions (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            -- Create an uppercase title column for quicker searching
            -- Ubuntu sqlite3 doesn't have generated columns yet :(
            title_upper TEXT NOT NULL, -- GENERATED ALWAYS AS (UPPER(title)) STORED,
            desc TEXT NOT NULL,
            image_url TEXT NOT NULL,
            cost INT NOT NULL
        );

        CREATE TABLE item_backpack (
            item_id INT NOT NULL,
            user_id INT NOT NULL,
            count INT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (item_id) REFERENCES item_definitions(id)
        );
    ''')

    conn.commit()
    c.close()

def delete_database():
    """
    Deletes the database file. All connections to the database should be closed
    before calling this.
    """
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)

@dataclass
class CoinGain:
    """Class for keeping track of data about how coins were given out"""
    tid: int
    message_id: Optional[int]
    user_id: int
    date_entered: datetime.datetime
    coins: int

@dataclass
class ItemDefinition:
    """Defines an item in the store"""
    tid: int
    title: str
    desc: str
    image_url: str
    cost: int

@dataclass
class BackpackItem:
    """Records a user buying an item"""
    item_tid: int
    user_tid: int
    count: int

class Database:
    """
    A python-friendly interface for interacting with the sqlite3 database that
    this file defines.
    """

    def __init__(self, conn):
        self.conn = conn

        # Initialize proxy functions
        self.give_item_discord = self._discordify(self.give_item)
        self.give_coins_discord = self._discordify(self.give_coins)
        self.buy_item_discord = self._discordify(self.buy_item)
        self.use_item_discord = self._discordify(self.use_item)

    def _select_user_unchecked(self, sql_statement: str, user_tid: int) -> Optional[int]:
        """
        Utility function to execute an SQL SELECT statement based on
        table user id that may or may not exist.

        We can skip checking if there are multiple rows that match this query
        """
        c = self.conn.cursor()

        c.execute(sql_statement, [user_tid])
        matches = c.fetchall()

        if len(matches) == 0:
            log.debug(f"User for {user_tid=} doesn't exist")
            return None
        else:
            return matches[0]

    def _select_user_checked(self, sql_statement: str, discord_id: int) -> Optional[int]:
        """
        Utility function to execute an SQL SELECT statement based on a discord
        user id that may or may not be registered.

        For safety, in addition to checking if the user is registered, we also
        check to make sure the user is not registered multiple times.
        """
        c = self.conn.cursor()

        c.execute(sql_statement, [str(discord_id)])
        matches = c.fetchall()

        if len(matches) == 0:
            log.debug(f"User {discord_id} not found in database")
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            log.warn(f"User {discord_id} present multiple times in table! Affected rows: {matches}")
            return matches[0]

    def _discordify(self, function) -> bool:
        """
        Make a Discord ID version of any function that takes a `user_tid` as
        its first parameter and returns a boolean indicating success. As it
        turns out, there are a lot of functions in this class that do this.
        """
        def inner(discord_id: int, *args, **kwargs) -> bool:
            if (user_tid := self.get_user_tid(discord_id)) is None:
                return False

            return function(user_tid, *args, **kwargs)

        return inner

    def get_user_tid(self, discord_id: int) -> Optional[int]:
        """
        Returns the database id associated with a discord user's id
        """
        if (row := self._select_user_checked('SELECT id FROM users WHERE user_id=?', discord_id)) is not None:
            return row[0]
        else:
            return None

    def get_user_discord_id(self, user_tid: int) -> Optional[int]:
        """
        Returns the associated discord user id given a database user id
        """
        if (row := self._select_user_unchecked('SELECT user_id FROM users WHERE id=?', user_tid)) is not None:
            return int(row[0])
        else:
            return None

    def get_balance_discord(self, discord_id: int) -> Optional[int]:
        """
        Returns the discord user's coin balance
        """
        if (row := self._select_user_checked('SELECT coins FROM users WHERE user_id=?', discord_id)) is not None:
            return row[0]
        else:
            return None

    def get_balance(self, user_tid: int) -> Optional[int]:
        """
        Returns the database user's coin balance
        """
        if (row := self._select_user_unchecked('SELECT coins FROM users WHERE id=?', user_tid)) is not None:
            return row[0]
        else:
            return None

    def get_coin_gains(self, discord_id: int) -> List[CoinGain]:
        """
        Returns a list of all the user's coin bank transactions. This is
        always the empty list if the user is not registered.
        """
        if (user_id := self.get_user_tid(discord_id)) is None:
            log.debug(f"Attempted to get coin gains for unregistered user {discord_id}")
            return []

        c = self.conn.cursor()
        c.execute('''SELECT id, message_id, user_id, date_entered, coins
                     FROM coin_gains
                     WHERE user_id=?''', [user_id])
        rows = c.fetchall()

        return [CoinGain(*row) for row in rows]

    def get_coin_gain_from_message(self, message_id: int) -> Optional[CoinGain]:
        """
        Returns the CoinGain corresponding to a recorded message, or None if it
        doesn't exist
        """

        c = self.conn.cursor()
        c.execute('''SELECT id, message_id, user_id, date_entered, coins
                     FROM coin_gains
                     WHERE message_id=?''', [message_id])
        rows = c.fetchall()

        if len(rows) == 0:
            return None
        else:
            if len(rows) > 1:
                # Unexpected condition
                log.warn(f"Message {message_id} recorded multiple times as a coin gain!")
            return CoinGain(*row[0])

    def get_item_definitions(self) -> Optional[List[ItemDefinition]]:
        """
        Returns a list of all registered items
        """
        c = self.conn.cursor()
        c.execute('''SELECT id, title, desc, image_url, cost
                     FROM item_definitions''')
        rows = c.fetchall()

        return [ItemDefinition(*row) for row in rows]

    def get_backpack_items(self, discord_id: int) -> List[BackpackItem]:
        """
        Returns a list of all items a user has in their backpack. This is
        always the empty list if the user is not registered.
        """
        if (user_id := self.get_user_tid(discord_id)) is None:
            log.debug(f"Attempted to get items for unregistered user {discord_id}")
            return []

        c = self.conn.cursor()
        c.execute('''SELECT item_id, user_id, count
                     FROM item_backpack
                     WHERE user_id=?''', [user_id])
        rows = c.fetchall()

        return [BackpackItem(*row) for row in rows]

    def backpack_item_to_definition(self, bpi: BackpackItem) -> Optional[BackpackItem]:
        """
        Looks up the item id of the backpack item in the item definition table
        """

        c = self.conn.cursor()
        c.execute('''SELECT id, title, desc, image_url, cost
                     FROM item_definitions
                     WHERE id=?''', [bpi.item_tid])
        rows = c.fetchall()

        if len(rows) == 0:
            log.debug(f"Item definition for {bpi.item_tid=} not found")
            return None
        else:
            return ItemDefinition(*(rows[0]))

    def register_user(self, discord_id: int) -> Tuple[int, bool]:
        """
        Registers a user in the database given their discord id

        Returns the associated id of the user (same as future calls to
        `get_user_id` will return), as well as a boolean describing whether or
        not the user was already registered.
        """

        if (user_tid := self.get_user_tid(discord_id)) is not None:
            log.debug(f"Attempted to register user {discord_id}, but they were already present!")
            return user_tid, True

        c = self.conn.cursor()
        c.execute('INSERT INTO users (user_id, coins) VALUES (?, ?)', [str(discord_id), 0])
        self.conn.commit()
        c.close()

        return self.get_user_tid(discord_id), False

    def user_has_item(self, user_tid: int, item_tid: int) -> Optional[BackpackItem]:
        """
        Checks the user's backpack to see if they own an item. Returns the
        corresponding `BackpackItem` object if they do, `None` if they don't.
        """
        c = self.conn.cursor()
        c.execute('''SELECT count FROM item_backpack
                     WHERE user_id=? AND item_id=?''', [user_tid, item_tid])
        rows = c.fetchall()

        if len(rows) == 0:
            return None
        else:
            return BackpackItem(item_tid, user_tid, rows[0][0])

    def update_backpack_item(self, bpi: BackpackItem):
        """
        Given the `BackpackItem` data, update or insert it into the
        `item_backpack` table.
        """
        c = self.conn.cursor()
        if (old_bpi := self.user_has_item(bpi.user_tid, bpi.item_tid)) is not None:
            # Item already exists, do an update
            c.execute('''UPDATE item_backpack
                         SET count=?
                         WHERE user_id=? AND item_id=?''',
                         [bpi.count, bpi.user_tid, bpi.item_tid])
        else:
            # Item is not yet owned or does not exist, insert it fresh
            c.execute('''INSERT INTO item_backpack (item_id, user_id, count)
                         VALUES (?, ?, ?)''',
                         [bpi.item_tid, bpi.user_tid, bpi.count])

        self.conn.commit()
        c.close()

    def find_item(self, item_title: str) -> Optional[ItemDefinition]:
        """
        Searches the item definition table for an item with a matching title.
        Returns None if no item with that title could be found.
        """
        c = self.conn.cursor()
        c.execute('''SELECT id, title, desc, image_url, cost
                     FROM item_definitions
                     WHERE title_upper=?''', [item_title.upper()])
        rows = c.fetchall()

        if len(rows) == 0:
            return None
        elif len(rows) == 1:
            return ItemDefinition(*(rows[0]))
        else:
            log.warn(f"Multiple items with {item_title=} found in database! {rows}")
            return ItemDefinition(*(rows[0]))

    def register_item(self, title: str, desc: str, image_url: str, cost: int) -> bool:
        """
        Inserts an item into the item definition table.

        Returns a boolean that describes whether or not the update completed
        successfully. A return value of `False` means that an item with the
        same title was already present.
        """
        if (existing_item := self.find_item(title)) is not None:
            return False

        c = self.conn.cursor()
        c.execute('''INSERT INTO item_definitions (title, title_upper, desc, image_url, cost)
                     VALUES (?, ?, ?, ?, ?)''',
                     [title, title.upper(), desc, image_url, cost])
        self.conn.commit()
        c.close()

        return True

    def unregister_item(self, item_title: str):
        """
        Deletes an item from the item definition table. This action cannot be
        undone (feasibly).
        """
        c = self.conn.cursor()
        c.execute('''DELETE FROM item_definitions
                     WHERE title_upper=?''', [item_title.upper()])
        self.conn.commit()
        c.close()

    def give_coins(self, user_tid: int, message_id: int, message_date: datetime.datetime, num_coins: int) -> bool:
        """
        Updates the balance of the specified user to include more or less
        coins. Does not do bounds checking on the amount of coins. Also assumes
        that `user_tid` is a valid table user id.
        """

        balance = self.get_balance(user_tid)
        if balance is None or balance + num_coins < min(balance, 0):
            return False

        c = self.conn.cursor()
        c.execute('''INSERT INTO coin_gains (message_id, user_id, date_entered, coins)
                     VALUES (?, ?, ?, ?)''',
                     [str(message_id), user_tid, message_date, num_coins])
        c.execute('''UPDATE users
                     SET coins=?
                     WHERE id=?''', [balance + num_coins, user_tid])
        self.conn.commit()
        c.close()

        return True

    def update_coin_gain(self, coin_gain_tid: int, new_coins: int) -> bool:
        """
        Updates a specified coin gain to reflect a new number of coins. Also
        updates the user's main balance based on this change. Possible for a
        user to have negative coins after this, although unlikely.

        Returns True iff the update succeeded
        """

        c = self.conn.cursor()
        c.execute('''SELECT id, message_id, user_id, date_entered, coins
                     FROM coin_gains
                     WHERE id=?''', [coin_gain_tid])
        rows = c.fetchall()

        if len(rows) == 0:
            return False # No coin gain to update
        if len(rows) > 1:
            # Unexpected condition, log and continue
            log.warn(f"Coin Gain {coin_gain_tid} recorded multiple times??")

        coin_gain = CoinGain(*row[0])

        if (user_tid := self.get_user_tid(coin_gain.user_id)) is None:
            log.debug(f"No corresponding user {coin_gain.user_id} to update coin gain for")
            return False
        if (balance := self.get_balance(user_tid)) is None:
            log.warn(f"User {coin_gain.user_id} registered but no balance?")
            return False

        new_balance = balance + new_coins - coin_gain.coins
        c.execute('''UPDATE coin_gains
                     SET coins=?
                     WHERE id=?''', [new_coins, coin_gain_tid])
        c.execute('''UPDATE users
                     SET coins=?
                     WHERE id=?''', [new_balance, user_tid])
        self.conn.commit()
        c.close()

        return True

    def give_item(self, user_tid: int, item_tid: int) -> bool:
        """
        Unconditionally gives a user the specified item. Assumes that both
        user_tid and item_tid are valid table ids.
        """
        if (bpi := self.user_has_item(user_tid, item_tid)) is None:
            bpi = BackpackItem(item_tid, user_tid, 1)
        else:
            bpi.count += 1

        self.update_backpack_item(bpi)

        return True

    def buy_item(self, user_tid: int, message_id: int, message_date: datetime.datetime, item: ItemDefinition) -> bool:
        """
        Notes that a user attempted to buy an item. This can fail (return False)
        if the user is not registered or doesn't have enough coins. If the item
        is successfully bought, return True.

        The ItemDefinition to buy must be acquired by find_item or through
        the get_item_definitions function calls, not constructed manually
        (bad idea).
        """
        if not self.give_coins(user_tid, message_id, message_date, -item.cost):
            return False

        if not self.give_item(user_tid, item.tid):
            return False

        return True

    def use_item(self, user_tid: int, item_tid: int) -> bool:
        """
        Record a user's usage of an item. Assumes user_tid and item_tid are
        valid. Returns False when the user doesn't have the item or doesn't
        have enough of that item.

        Really, there should be a Lock here so that we don't have races for
        using an item multiple times when there's only one, but as long as we
        aren't multithreaded we should be fine (thank goodness for Asyncio!).
        """
        if (bpi := self.user_has_item(user_tid, item_tid)) is None:
            return False

        if bpi.count <= 0:
            return False
        else:
            bpi.count -= 1
            self.update_backpack_item(bpi)
            return True

if __name__ == "__main__":
    """
    If we are run directly, recreate the database
    """
    resp = input("This will delete the database and start fresh, are you sure you want to do this? [y/N]: ")
    if 'y' in resp.lower():
        delete_database()
        conn = sqlite3.connect(DATABASE_FILE)
        create_database(conn)
        conn.close()
