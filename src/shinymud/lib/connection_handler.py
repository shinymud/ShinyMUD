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
        # Set the listener to non-blocking so that the listener can die when the main
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
                # DON'T PUT A LOGGING STATEMENT IN THIS TRY/EXCEPT BLOCK UNLESS
                # YOU ARE TESTING THIS STATEMENT SPECIFICALLY -- THEN REMOVE IT
                # WHEN YOU ARE DONE! This try/except statement will get called several 
                # times each second because the socket is non-blocking. Putting logging
                # statements here will make the logging file HUGE in just a few minutes.
                # Sorry for all the shouting.
                new_user = User(self.listener.accept())
            except socket.error:
                # TODO: We intend that this aught to be blocking once the mud has a 
                # start-up/shut-down script that can handle killing these processes,
                pass
            except Exception, e:
                self.log.debug(str(e))
            else:
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