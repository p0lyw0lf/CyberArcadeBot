import sqlite3
import os
from os.path import dirname, abspath, join

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

        CREATE TABLE rewards (
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

        CREATE TABLE items (
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
