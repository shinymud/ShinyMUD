import sqlite3
from shinymud.config import DB_NAME
from shinymud.models import SAVE_MODELS, ShinyModel

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
    query = "CREATE TABLE "+ klass.__name__ + " (dbid INTEGER PRIMARY KEY, "
    for name, defn in klass.save_attrs.items():
        if issubclass(defn[1], ShinyModel):
            query += str(name) + '_id INTEGER REFERENCES ' + defn[1].__name__ + ' (dbid), '
        else:
            query += str(name) + ' TEXT' + ', '
    for x in instance.UNIQUE:
        if hasattr(x, '__iter__'):
            query += "UNIQUE (" + ','.join(x) + '),'
        else:
            query += "UNIQUE (" + x + "),"
    query = query[:-1] + ')'
    print query
    cursor.execute(query)