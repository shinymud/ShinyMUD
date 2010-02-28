from shinymud.models.user import User
import threading
import socket
import logging

class ConnectionHandler(threading.Thread):
    
    def __init__(self, port, host, world):
        threading.Thread.__init__(self)
        self.log = logging.getLogger('ConnectionHandler')
        self.daemon = True
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((host, port))
        self.log.info("Running on host: %s and port: %s." % (host, port))
        self.world = world
    
    def run(self):
        self.listener.listen(5)
        self.log.debug("Listener started")
        while self.world.listening:
            try:
                new_user = User(self.listener.accept())
            except Exception, e:
                self.log.debug(str(e))
            else:
                self.negotiate_line_mode(new_user.conn)
                self.log.info("Client logging in from: %s" % str(new_user.addr))
                new_user.conn.setblocking(0)
                # The user_add function in the world requires access to the user_list,
                # which the main thread edits quite a bit -- that's why we need a lock 
                # before we add a user
                self.world.user_list_lock.acquire()
                self.world.user_add(new_user)
                self.world.user_list_lock.release()
        self.log.info('Listener closing down.')
        self.listener.close()
    
    def negotiate_line_mode(self, con):
        # IAC + WILL + LINEMODE
        con.send(chr(255) + chr(251) + chr(34) + '\r\n')
        result = con.recv(256)
        self.log.debug(list(result))
    
