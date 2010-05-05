from shinymud.lib.ansi_codes import *
import os

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
VERSION = '0.5' # The codebase version
GAME_NAME = 'ShinyMUD' # Replace this with the name of your game!

HOST = ''
PORT = 4111
LOG_FILE = ROOT_DIR + '/logs/shinymud.log' # path for the logfile
LOG_LEVEL = 10 # 10 is the equivalent of "DEBUG"
DB_NAME = ROOT_DIR + '/shinymud.db' # path/name of the sqlite3 database
AREAS_IMPORT_DIR = ROOT_DIR + '/areas' # directory for inmport areas
AREAS_EXPORT_DIR = ROOT_DIR + '/areas' # directory for exported areas
PREPACK = ROOT_DIR + '/areas/builtin' # directory for built-in areas
RESET_INTERVAL = 320 # Amount of time (in seconds) that should pass before an area resets
DEFAULT_LOCATION = ('library', '4') # The area, room_id that newbies should start in

STATS_ENABLED = False # Whether the StatSender thread should be enabled
STATS_PORT = 4112 # The port that StatSender should listen on

# ************ COLOR THEMES ************

# Player Permissions
PLAYER = 1
BUILDER = 2
DM = 4
ADMIN = 8
GOD = 16



# Color constants:
clear_fcolor = COLOR_FG_RESET # DON'T CHANGE THIS ONE!
clear_bcolor = COLOR_BG_RESET # DON'T CHANGE THIS ONE EITHER!

# Communication colors
chat_color = COLOR_FG_CYAN
say_color = COLOR_FG_YELLOW
wecho_color = COLOR_FG_BLUE

# Object colors
npc_color = COLOR_FG_YELLOW
player_color = COLOR_FG_YELLOW
room_title_color = COLOR_FG_GREEN
room_body_color = COLOR_FG_GREEN
room_exit_color = COLOR_FG_CYAN
room_id_color = COLOR_FG_RED
item_color = COLOR_FG_RED

# Help colors
help_title = BOLD

