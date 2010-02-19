#ANSI color codes

# This is the reset for ALL attributes, COLOR and MISC attributes included
CLEAR = chr(27) + '[0m'

#Foreground colors:
COLOR_FG_BLACK = chr(27) + '[30m'
COLOR_FG_RED = chr(27) + '[31m'
COLOR_FG_GREEN = chr(27) + '[32m'
COLOR_FG_YELLOW = chr(27) + '[33m'
COLOR_FG_BLUE = chr(27) + '[34m'
COLOR_FG_MAGENTA = chr(27) + '[35m'
COLOR_FG_CYAN = chr(27) + '[36m'
COLOR_FG_WHITE = chr(27) + '[37m'
COLOR_FG_RESET = chr(27) + '[39m'

# Background colors:
COLOR_BG_BLACK = chr(27) + '[40m'
COLOR_BG_RED = chr(27) + '[41m'
COLOR_BG_GREEN = chr(27) + '[42m'
COLOR_BG_YELLOW = chr(27) + '[43m'
COLOR_BG_BLUE = chr(27) + '[44m'
COLOR_BG_MAGENTA = chr(27) + '[45m'
COLOR_BG_CYAN = chr(27) + '[46m'
COLOR_BG_WHITE = chr(27) + '[47m'
COLOR_BG_RESET = chr(27) + '[49m'

# MISC
BOLD = chr(27) + '[1m'
BRIGHT = chr(27) + '[2m'
DIM = chr(27) + '[3m'
UNDERSCORE = chr(27) + '[4m'
BLINK = chr(27) + '[5m'
REVERSE = chr(27) + '[7m'
CONCEAL = chr(27) + '[8m'
