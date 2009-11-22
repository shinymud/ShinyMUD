import threading
import socket
from models.user import User
import logging

class ConnectionHandler(threading.Thread):
    
    def __init__(self, port, host, world):
        threading.Thread.__init__(self)
        self.log = logging.getLogger('ConnectionHandler')
        self.daemon = True
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set the listener to non-blocking so that the listener will die when the main
        # thread dies.
        self.listener.setblocking(0)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((host, port))
        self.log.info("Running on host: %s and port: %s." % (host, port))
        self.world = world
    
    def run(self):
        self.listener.listen(5)
        self.log.debug("Listener started")
        while self.world.listening:
            try:
                new_user = User(self.listener.accept(), self.world)
            except:
                pass
            else:
                new_user.conn.setblocking(0)
                self.log.info("Client logging in from: %s" % str(new_user.addr))
                self.world.user_list_lock.acquire()
                self.world.user_list[new_user.conn] = new_user
                self.world.user_list_lock.release()
        self.log.info('Listener closing down.')
        self.listener.close()