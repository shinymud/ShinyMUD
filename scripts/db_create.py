import sqlite3
from shinymud.config import DB_NAME
from shinymud.models import SAVE_MODELS

con = sqlite3.Connection(DB_NAME)
cursor = con.cursor()

# Import all the models
IMPORTED_MODELS = []
for m in SAVE_MODELS:
    path = m.split('.')
    klass = __import__('.'.join(path[:-1]))
    for attr in path[1:]:
        klass = getattr(klass, attr)
    IMPORTED_MODELS.append(klass)


# Build Create-table strings
for klass in IMPORTED_MODELS:
    instance = klass()
    query = "CREATE TABLE "+ klass.__name__ + " ("
    for name, value in instance.save_attr.items():
        query += str(name) + ' TEXT,'
    query = query[:-1] + ')'
    print query
    cursor.execute(query)