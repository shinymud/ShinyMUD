import os

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

HOST = ''
PORT = 4111
LOG_FILE = ROOT_DIR + '/logs/shinymud.log'
LOG_LEVEL = 10 # 10 is the equivalent of "DEBUG"
DB_NAME = ROOT_DIR + '/shinymud.db'
AREAS_IMPORT_DIR = ROOT_DIR + '/areas'
AREAS_EXPORT_DIR = ROOT_DIR + '/areas'
RESET_INTERVAL = 120 # Amount of time that should pass before an area resets

