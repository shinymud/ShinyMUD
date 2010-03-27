from shinymud.models.user import User

import threading
import socket
import logging

class ConnectionHandler(threading.Thread):
    
    def __init__(self, port, host, world):
        threading.Thread.__init__(self)
        self.log = logging.getLogger('ConnectionHandler')
        self.daemon = True # So this thread will exit when the main thread does
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((host, port))
        self.log.info("Running on host: %s and port: %s." % (host, port))
        self.world = world
    
    def run(self):
        """Start the connection-handler thread running.
        This thread will accept connections, create a User object for the
        player logging in, and then add that User object to the world.
        """
        self.listener.listen(5)
        self.log.debug("Listener started")
        while 1:
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
    
    def negotiate_line_mode(self, con):
        """Petition client to run in linemode.
        Some telnet clients, such as putty, start in non-linemode by default
        (they transmit each character as they receive it from the user). We
        want them to switch to linemode in this case, where they tranmit each
        line after it's been assembled.
        """
        # IAC + WILL + LINEMODE
        con.send(chr(255) + chr(251) + chr(34) + '\r\n')
        # We should get a response from their client (immediately)
        con.settimeout(1.0)
        try:
            result = list(con.recv(256))
        except socket.timeout:
            # This just means that their telnet client didn't send us a timely
            # response to our initiating linemode... we should just move on
            result = 'Client response FAIL for linemode.'
        finally:
            con.settimeout(None)
            self.log.debug(result)
    
