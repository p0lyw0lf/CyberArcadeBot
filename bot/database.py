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
            id INT NOT NULL PRIMARY KEY,
            user_id TEXT NOT NULL, -- Discord uses bigints, don't fit into regular int
            coins INT NOT NULL
        );

        CREATE TABLE coin_gains (
            id INT NOT NULL PRIMARY KEY,
            message_id TEXT,
            user_id INT NOT NULL,
            date_entered TEXT NOT NULL,
            mod_approved BOOL NOT NULL,
            coins INT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE item_definitions (
            id INT NOT NULL PRIMARY KEY,
            title TEXT NOT NULL,
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
    mod_approved: bool
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
    tid: int
    item_id: int
    user_id: int
    count: int

class Database:
    """
    A python-friendly interface for interacting with the sqlite3 database that
    this file defines.
    """

    def __init__(self, conn):
        self.conn = conn

    def _select_user_unchecked(self, sql_statement: str, user_tid: int) -> Optional[int]:
        c = self.conn.cursor()

        c.execute(sql_statement, user_tid)
        matches = c.fetchall()

        if len(matches) == 0:
            log.debug(f"User for {user_tid=} doesn't exist")
            return None
        else:
            return matches[0]

    def _select_user_checked(self, sql_statement: str, discord_id: int) -> Optional[int]:
        c = self.conn.cursor()

        c.execute(sql_statement, str(discord_id))
        matches = c.fetchall()

        if len(matches) == 0:
            log.debug(f"User {discord_id} not found in database")
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            log.warn(f"User {discord_id} present multiple times in table! Affected rows: {matches}")
            return matches[0]

    def get_user_tid(self, discord_id: int) -> Optional[int]:
        """
        Returns the database id associated with a discord user's id
        """
        if row := self._select_user_checked('SELECT id FROM users WHERE user_id=?', discord_id) is not None:
            return row[0]
        else:
            return None

    def get_user_discord_id(self, user_tid: int) -> Optional[int]:
        """
        Returns the associated discord user id given a database user id
        """
        if row := self._select_user_unchecked('SELECT user_id FROM users WHERE id=?', user_tid) is not None:
            return int(row[0])
        else:
            return None

    def get_balance_discord(self, discord_id: int) -> Optional[int]:
        """
        Returns the discord user's coin balance
        """
        if row := self._select_user_checked('SELECT coins FROM users WHERE user_id=?', discord_id) is not None:
            return row[0]
        else:
            return None

    def get_balance(self, user_tid: int) -> Optional[int]:
        """
        Returns the database user's coin balance
        """
        if row := self._select_user_unchecked('SELECT coins FROM users WHERE id=?', user_tid) is not None:
            return row[0]
        else:
            return None

    def get_coin_gains(self, discord_id: int) -> List[CoinGain]:
        user_id = self.get_user_tid(discord_id)

        if user_id is None:
            log.debug(f"Attempted to get coin gains for unregistered user {discord_id}")
            return []

        c = self.conn.cursor()
        c.execute('''SELECT (id, message_id, user_id, date_entered, coins)
                     FROM coin_gains
                     WHERE user_id=?''', user_id)
        rows = c.fetchall()

        return [CoinGain(*row) for row in rows]

    # TODO: item definitions and item backpacks

    def register_user(self, discord_id: int) -> Optional[int]:
        """
        Registers a user in the database given their discord id

        Returns the associated id of the user (same as future calls to
        `get_user_id` will return).
        """

        if user_id := self.get_user_tid(discord_id) is not None:
            log.debug(f"Attempted to register user {discord_id}, but they were already present!")
            return user_id

        c = self.conn.cursor()
        c.execute('INSERT INTO users (user_id, coins) VALUES (?, ?)', str(discord_id), 0)
        self.conn.commit()
        c.close()

        return self.get_user_tid(discord_id)

    # TODO: buying items, logging messages for coin gains

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
