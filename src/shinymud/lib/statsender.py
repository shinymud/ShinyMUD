import threading
import socket
import logging

class StatSender(threading.Thread):
    
    def __init__(self, port, host, world):
        threading.Thread.__init__(self)
        self.log = logging.getLogger('StatSender')
        self.daemon = True # So this thread will exit when the main thread does
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((host, port))
        self.world = world
    
    def run(self):
        """Start the connection-handler thread running.
        This thread will accept connections, create a User object for the
        player logging in, and then add that User object to the world.
        """
        self.listener.listen(5)
        while 1:
            try:
                conn, info = self.listener.accept()
            except Exception, e:
                self.log.debug(str(e))
            else:
                # Send them the game-stats!
                plist = ','.join([name for name in self.world.user_list if isinstance(name, str)])
                conn.send(plist)
                conn.close()
    

