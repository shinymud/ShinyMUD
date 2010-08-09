import os
from shinymud.models import __file__ as model_file
from shinymud.lib.world import World
model_path = os.path.abspath(os.path.dirname(model_file))
model_files = [f[:-3] for f in os.listdir(model_path) if f.endswith('.py') and not f.startswith(('_','.'))]

for module in model_files:
    temp = __import__('shinymud.models.%s' % module, globals(), locals(), [])

from shinymud.models import model_list

EXISTING_TABLES = {}

def initialize_database():
    world = World.get_world()
    world.db.conn.cursor().execute('PRAGMA foreign_keys = true')
    db_table_names = [x['name'] for x in world.db.select("name from sqlite_master where type='table'")]
    for table_name in db_table_names:
        columns = world.db.select("* from %s limit 1" % table_name)
        if columns and len(columns):
            EXISTING_TABLES[table_name] = columns[0].keys()
    
    for mod in model_list.values():
        if mod.db_table_name not in EXISTING_TABLES:
            create_table(mod)
    for mod in model_list.values():
        for col in mod.db_columns:
            if col.name not in EXISTING_TABLES[mod.db_table_name]:
                add_column(mod, col.name)

def create_table(model):
    if model.db_table_name in EXISTING_TABLES:
        return
    # check for dependencies
    dependencies = [col.foreign_key for col in model.db_columns if col.foreign_key and col.foreign_key[0] != model.db_table_name]
    for mod, col in dependencies:
        M = model_list.get(mod)
        if not M:
            raise Exception('Dependency on unknown model: %s' % str(mod))
        if M.db_table_name not in EXISTING_TABLES:
            create_table(M)
        elif col not in EXISTING_TABLES[M.db_table_name]:
            add_column(M, col)
    # generate create table string
    table_string = []
    table_string.append('CREATE TABLE IF NOT EXISTS %s (' % model.db_table_name)
    columns_string = []
    for col in model.db_columns:
        columns_string.append(str(col))
    for extra in model.db_extras:
        columns_string.append(unicode(extra))
    table_string.append(','.join(columns_string))
    table_string.append(')')
    create_stmt = "".join(table_string)
    cursor = World.get_world().db.conn.cursor()
    cursor.execute(create_stmt)
    EXISTING_TABLES[model.db_table_name] = [col.name for col in model.db_columns]

def add_column(mod, col):
    # check for dependencies
    if mod.db_table_name not in EXISTING_TABLES:
        create_table(mod)
    else:
        if col in EXISTING_TABLES[mod.db_table_name]:
            return # Column already exists!?
        column = None
        for c in mod.db_columns:
            if c.name == col:
                column = c
                break
        if not column:
            raise Exception('Trying to create undefined column!')
        if column.foreign_key:
            m, c = column.foreign_key
            M = model_list.get(m)
            if M.db_table_name not in EXISTING_TABLES:
                create_table(M)
            elif c not in EXISTING_TABLES[M.db_table_name]:
                add_column(M, c)
        alter_stmt = 'ALTER TABLE %s ADD COLUMN %s' % (mod.db_table_name, str(column))
        cursor = World.get_world().db.conn.cursor()
        cursor.execute(alter_stmt)
        EXISTING_TABLES[mod.db_table_name].append(col)
