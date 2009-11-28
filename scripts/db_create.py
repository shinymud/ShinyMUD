import sqlite3
from shinymud.config import DB_NAME
from shinymud.models import *

con = sqlite3.Connection(DB_NAME)
cursor = con.cursor()

# Import all the models

# Build Create-table strings
