# I don't know the format of this file yet, but I do know that it will describe all of the TABLE IF NOT EXISTSs in the
# database. It will probably be in sql, or python, depending on which is easier to build.


import sqlite3
from shinymud.config import DB_NAME

def initialize_database(db_name=None):
    queries = [\
'''CREATE TABLE IF NOT EXISTS user (
    dbid INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    channels TEXT,
    password TEXT NOT NULL,
    description TEXT,
    permissions INTEGER NOT NULL DEFAULT 1,
    strength INTEGER NOT NULL DEFAULT 0,
    intelligence INTEGER NOT NULL DEFAULT 0,
    dexterity INTEGER NOT NULL DEFAULT 0,
    hp INTEGER NOT NULL DEFAULT 0,
    mp INTEGER NOT NULL DEFAULT 0,
    max_hp INTEGER NOT NULL DEFAULT 20,
    max_mp INTEGER NOT NULL DEFAULT 0,
    speed INTEGER NOT NULL DEFAULT 0,
    email TEXT,
    gender TEXT,
    location TEXT
)''',\
'''CREATE TABLE IF NOT EXISTS area (
    dbid INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    level_range TEXT,
    builders TEXT,
    description TEXT
)''',\
'''CREATE TABLE IF NOT EXISTS room (
    dbid INTEGER PRIMARY KEY,
    id INTEGER NOT NULL,
    area INTEGER NOT NULL REFERENCES area(dbid),
    name TEXT,
    description TEXT,
    UNIQUE (area, id)
)''',\
'''CREATE TABLE IF NOT EXISTS  item (
    dbid INTEGER PRIMARY KEY,
    id INTEGER NOT NULL,
    area INTEGER NOT NULL REFERENCES area(dbid),
    name TEXT,
    title TEXT,
    description TEXT,
    keywords TEXT,
    weight INTEGER DEFAULT 0,
    base_value INTEGER DEFAULT 0,
    carryable TEXT DEFAULT 'True',
    equip_slot INTEGER,
    UNIQUE (area, id)
)''',\
'''CREATE TABLE IF NOT EXISTS room_exit (
    dbid INTEGER PRIMARY KEY,
    room INTEGER NOT NULL REFERENCES room(dbid),
    to_room INTEGER NOT NULL REFERENCES room(dbid),
    linked_exit INTEGER REFERENCES room_exit(dbid),
    direction TEXT NOT NULL,
    openable TEXT,
    closed TEXT,
    hidden TEXT,
    locked TEXT,
    key INTEGER REFERENCES item(dbid),
    UNIQUE (room, direction)
)''',\
'''CREATE TABLE IF NOT EXISTS inventory (
    dbid INTEGER PRIMARY KEY,
    id INTEGER,
    area INTEGER REFERENCES area(dbid),
    name TEXT,
    title TEXT,
    description TEXT,
    keywords TEXT,
    weight INTEGER DEFAULT 0,
    base_value INTEGER DEFAULT 0,
    carryable TEXT,
    equip_slot INTEGER,
    owner INTEGER REFERENCES user(dbid),
    container INTEGER REFERENCES inventory(dbid)
)''',\
'''CREATE TABLE IF NOT EXISTS npc (
    dbid INTEGER PRIMARY KEY,
    id INTEGER NOT NULL,
    area INTEGER NOT NULL REFERENCES area(dbid),
    name TEXT,
    title TEXT,
    keywords TEXT,
    description TEXT,
    UNIQUE (area, id)
)''',\
'''CREATE TABLE IF NOT EXISTS room_resets (
    dbid INTEGER PRIMARY KEY,
    room INTEGER NOT NULL REFERENCES room(dbid),
    reset_object_id TEXT,
    reset_object_area TEXT,
    container_id TEXT,
    reset_type TEXT,
    spawn_point TEXT
)''',\
'''CREATE TABLE IF NOT EXISTS portal (
    dbid INTEGER PRIMARY KEY,
    item INTEGER NOT NULL REFERENCES item(dbid),
    to_room TEXT,
    to_area TEXT,
    leave_message TEXT,
    entrance_message TEXT,
    emerge_message TEXT
)''',\
'''CREATE TABLE IF NOT EXISTS food (
    dbid INTEGER PRIMARY KEY,
    item INTEGER NOT NULL REFERENCES item(dbid)
)''',\
'''CREATE TABLE IF NOT EXISTS container (
    dbid INTEGER PRIMARY KEY,
    item INTEGER NOT NULL REFERENCES item(dbid)
)''',\
'''CREATE TABLE IF NOT EXISTS weapon (
    dbid INTEGER PRIMARY KEY,
    item INTEGER NOT NULL REFERENCES item(dbid),
    dmg TEXT
)''',\
'''CREATE TABLE IF NOT EXISTS furniture (
    dbid INTEGER PRIMARY KEY,
    item INTEGER NOT NULL REFERENCES item(dbid)
)''']
    
    conn = sqlite3.connect(db_name or DB_NAME)
    cursor = conn.cursor()
    for query in queries:
        cursor.execute(query)
    
