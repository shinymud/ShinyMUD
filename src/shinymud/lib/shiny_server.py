from shinymud.lib.world import World
# Initialize the World
world = World()
from shinymud.lib.setup import initialize_database
from shinymud.models.area import Area
from shinymud.data.config import *
from shinymud.lib.connection_handlers import con_handlers

import traceback
import datetime

initialize_database()
world.db.delete('from game_item where (owner is null or owner=\'None\') and container is null')

# load the entities in the world from the database
# This should probably happen inside the world itself...
for area in world.db.select("* from area"):
    world.area_add(Area.create(area))
for area in world.areas.values():
    area.load()

world.default_location = world.get_location(DEFAULT_LOCATION[0],
                                            DEFAULT_LOCATION[1])

# Start up all of our connection handlers
for port, conn_handler in CONNECTIONS:
    handler_class = getattr(con_handlers, conn_handler)
    handler_obj = handler_class(port, HOST, world)
    handler_obj.start()

world.log.info('Started the connection handlers. Now listening for Players.')
world.log.debug('The world is about to start turning.')

try:
    world.start_turning()
except:
    with open(ROOT_DIR + "/logs/death_errors.log", 'w') as fp:
        fp.write('\n' + (str(datetime.datetime.today())).center(50, '*') + '\n')
        traceback.print_exc(file=fp)
        fp.write('\n' + ('*' * 50))
    world.log.critical('OH NOES! The server died! More information in the death_errors.log.')
    player_error = [
        "Bloody hell, the game server crashed!",
        "Don't worry, we've done our best to save your data.",
        "Try logging on again in a minute or two."
    ]
    for player in world.player_list.values():
        player.conn.send(player_error)
