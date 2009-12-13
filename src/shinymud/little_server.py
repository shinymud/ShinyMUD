from connection_handler import ConnectionHandler
from shinymud.models.world import World
from config import *

import logging
format = "%(asctime)s %(levelname)s %(name)s %(funcName)s %(lineno)d %(message)s"
logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL, format=format)
logger = logging.getLogger('little_server')
world = World()

# Start listening for connections on a different thread
conn_handler = ConnectionHandler(PORT, HOST, world)
conn_handler.start()
logger.debug('Started the connection handler. Now listening.')

# Let there be light!
logger.info('The world is about to start turning')
world.start_turning()
logger.info('The world has stopped turning.')
conn_handler.join()
