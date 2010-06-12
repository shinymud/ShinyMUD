# I don't know the format of this file yet, but I do know that it will describe all of the TABLE IF NOT EXISTSs in the
# database. It will probably be in sql, or python, depending on which is easier to build.


import sqlite3
from shinymud.data.config import DB_NAME

def initialize_database(connection=None):
    queries = [\
# '''CREATE TABLE IF NOT EXISTS player (
#     dbid INTEGER PRIMARY KEY,
#     name TEXT NOT NULL UNIQUE,
#     channels TEXT,
#     password TEXT NOT NULL,
#     description TEXT,
#     permissions INTEGER NOT NULL DEFAULT 1,
#     hp INTEGER NOT NULL DEFAULT 0,
#     mp INTEGER NOT NULL DEFAULT 0,
#     max_hp INTEGER NOT NULL DEFAULT 20,
#     max_mp INTEGER NOT NULL DEFAULT 0,
#     default_attack TEXT,
#     email TEXT,
#     gender TEXT,
#     location TEXT,
#     goto_appear TEXT,
#     goto_disappear TEXT,
#     title TEXT,
#     currency INTEGER
# )''',\
# '''CREATE TABLE IF NOT EXISTS area (
#     dbid INTEGER PRIMARY KEY,
#     name TEXT NOT NULL UNIQUE,
#     title TEXT,
#     level_range TEXT,
#     builders TEXT,
#     description TEXT
# )''',\
# '''CREATE TABLE IF NOT EXISTS room (
#     dbid INTEGER PRIMARY KEY,
#     id INTEGER NOT NULL,
#     area INTEGER NOT NULL REFERENCES area(dbid),
#     name TEXT,
#     description TEXT,
#     UNIQUE (area, id)
# )''',\
# '''CREATE TABLE IF NOT EXISTS  build_item (
#     dbid INTEGER PRIMARY KEY,
#     id INTEGER NOT NULL,
#     area INTEGER NOT NULL REFERENCES area(dbid),
#     name TEXT,
#     title TEXT,
#     description TEXT,
#     keywords TEXT,
#     weight INTEGER DEFAULT 0,
#     base_value INTEGER DEFAULT 0,
#     carryable TEXT DEFAULT 'True',
#     UNIQUE (area, id)
# )''',\
# '''CREATE TABLE IF NOT EXISTS room_exit (
#     dbid INTEGER PRIMARY KEY,
#     room_id INTEGER NOT NULL,
#     area TEXT NOT NULL,
#     to_room_id INTEGER NOT NULL,
#     to_area TEXT NOT NULL,
#     linked_exit TEXT,
#     direction TEXT NOT NULL,
#     openable TEXT,
#     closed TEXT,
#     hidden TEXT,
#     locked TEXT,
#     key_id INTEGER,
#     key_area TEXT,
#     UNIQUE (room_id, area, direction)
# )''',\
# '''CREATE TABLE IF NOT EXISTS game_item (
#     dbid INTEGER PRIMARY KEY,
#     build_id TEXT,
#     build_area TEXT,
#     name TEXT,
#     title TEXT,
#     description TEXT,
#     keywords TEXT,
#     weight INTEGER DEFAULT 0,
#     base_value INTEGER DEFAULT 0,
#     carryable TEXT,
#     owner INTEGER REFERENCES player(dbid),
#     container INTEGER REFERENCES game_item(dbid) ON DELETE CASCADE
# )''',\
# '''CREATE TABLE IF NOT EXISTS npc (
#     dbid INTEGER PRIMARY KEY,
#     id INTEGER NOT NULL,
#     area INTEGER NOT NULL REFERENCES area(dbid),
#     name TEXT,
#     gender TEXT,
#     hp INTEGER NOT NULL DEFAULT 0,
#     mp INTEGER NOT NULL DEFAULT 0,
#     max_hp INTEGER NOT NULL DEFAULT 20,
#     max_mp INTEGER NOT NULL DEFAULT 0,
#     default_attack TEXT,
#     title TEXT,
#     keywords TEXT,
#     description TEXT,
#     UNIQUE (area, id)
# )''',\
# '''CREATE TABLE IF NOT EXISTS room_spawns (
#     dbid INTEGER PRIMARY KEY,
#     id INTEGER NOT NULL,
#     room INTEGER NOT NULL REFERENCES room(dbid),
#     spawn_object_id TEXT,
#     spawn_object_area TEXT,
#     container TEXT,
#     spawn_type TEXT
# )''',\
# '''CREATE TABLE IF NOT EXISTS portal (
#     dbid INTEGER PRIMARY KEY,
#     build_item INTEGER NULL REFERENCES build_item(dbid) ON DELETE CASCADE,
#     game_item INTEGER NULL REFERENCES game_item(dbid) ON DELETE CASCADE,
#     to_room TEXT,
#     to_area TEXT,
#     leave_message TEXT,
#     entrance_message TEXT,
#     emerge_message TEXT
# )''',\
# '''CREATE TABLE IF NOT EXISTS food (
#     dbid INTEGER PRIMARY KEY,
#     build_item INTEGER NULL REFERENCES build_item(dbid) ON DELETE CASCADE,
#     game_item INTEGER NULL REFERENCES game_item(dbid) ON DELETE CASCADE,
#     ro_area TEXT,
#     ro_id TEXT,
#     food_type TEXT,
#     actor_use_message TEXT,
#     room_use_message TEXT
# )''',\
# '''CREATE TABLE IF NOT EXISTS container (
#     dbid INTEGER PRIMARY KEY,
#     build_item INTEGER NULL REFERENCES build_item(dbid) ON DELETE CASCADE,
#     game_item INTEGER NULL REFERENCES game_item(dbid) ON DELETE CASCADE,
#     weight_capacity NUMBER,
#     weight_reduction INTEGER,
#     item_capacity INTEGER,
#     openable TEXT,
#     closed TEXT,
#     locked TEXT,
#     key_area TEXT,
#     key_id TEXT
# )''',\
# '''CREATE TABLE IF NOT EXISTS equippable (
#     dbid INTEGER PRIMARY KEY,
#     build_item INTEGER NULL REFERENCES build_item(dbid) ON DELETE CASCADE,
#     game_item INTEGER NULL REFERENCES game_item(dbid) ON DELETE CASCADE,
#     equip_slot TEXT,
#     is_equipped TEXT DEFAULT 'False',
#     hit INTEGER DEFAULT 0,
#     evade INTEGER DEFAULT 0,
#     absorb TEXT,
#     dmg TEXT
# )''',\
# '''CREATE TABLE IF NOT EXISTS furniture (
#     dbid INTEGER PRIMARY KEY,
#     build_item INTEGER NULL REFERENCES build_item(dbid) ON DELETE CASCADE,
#     game_item INTEGER NULL REFERENCES game_item(dbid) ON DELETE CASCADE,
#     capacity INTEGER,
#     sit_effects TEXT,
#     sleep_effects TEXT
# )''',\
# '''CREATE TABLE IF NOT EXISTS script (
#     dbid INTEGER PRIMARY KEY,
#     id INTEGER NOT NULL,
#     area INTEGER NOT NULL REFERENCES area(dbid),
#     name TEXT,
#     body TEXT,
#     UNIQUE (area, id)
# )''',\
# '''CREATE TABLE IF NOT EXISTS npc_event (
#     dbid INTEGER PRIMARY KEY,
#     prototype INTEGER NOT NULL REFERENCES npc(dbid),
#     event_trigger TEXT,
#     condition TEXT,
#     script INTEGER REFERENCES script(dbid),
#     probability INTEGER
# )''',\
# '''CREATE TABLE IF NOT EXISTS char_effect (
#     dbid INTEGER PRIMARY KEY,
#     duration INTEGER,
#     name TEXT,
#     item INTEGER,
#     item_type TEXT,
#     player INTEGER NULL REFERENCES player(dbid)
# )''',\
'''CREATE TABLE IF NOT EXISTS merchant (
    dbid INTEGER PRIMARY KEY,
    npc INTEGER NOT NULL REFERENCES npc(dbid),
    buyer TEXT,
    markup NUMBER,
    buys_types TEXT,
    sale_items TEXT
)'''
]
    
    conn = connection or sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for query in queries:
        cursor.execute(query)
    
