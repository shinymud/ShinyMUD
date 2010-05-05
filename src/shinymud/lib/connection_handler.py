from shinymud.models.player import Player

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
        This thread will accept connections, create a Player object for the
        player logging in, and then add that Player object to the world.
        """
        self.listener.listen(5)
        self.log.debug("Listener started")
        while 1:
            try:
                new_player = Player(self.listener.accept())
            except Exception, e:
                self.log.debug(str(e))
            else:
                self.set_telnet_options(new_player)
                self.log.info("Client logging in from: %s" % str(new_player.addr))
                new_player.conn.setblocking(0)
                # The player_add function in the world requires access to the player_list,
                # which the main thread edits quite a bit -- that's why we need a lock 
                # before we add a player
                self.world.player_list_lock.acquire()
                self.world.player_add(new_player)
                self.world.player_list_lock.release()
    
    def set_telnet_options(self, pc):
        """Petition client to run in linemode and to send window size change
        notifications.
        Some telnet clients, such as putty, start in non-linemode by default
        (they transmit each character as they receive it from the player). We want
        them to switch to linemode in this case, where they transmit each line
        after it's been assembled. We also wan't the client to tell us their
        screen size so we can display things appropriately.
        """
        # IAC + WILL + LINEMODE
        pc.conn.send(chr(255) + chr(251) + chr(34) + '\r\n')
        # We should get a response from their client (immediately)
        pc.conn.settimeout(1.0)
        try:
            result = list(pc.conn.recv(256))
        except socket.timeout:
            # This just means that their telnet client didn't send us a timely
            # response to our initiating linemode... we should just move on
            result = 'Client response FAIL for linemode.'
        finally:
            self.log.debug(result)
        
        # IAC DO NAWS (Negotiate About Window Size)
        pc.conn.send(chr(255) + chr(253) + chr(31) + '\r\n')
        try:
            result = list(pc.conn.recv(256))
        except:
            result = 'Client response FAIL for NAWS.'
        else:
            # IAC WILL NAWS
            if result[0:3] == ['\xff', '\xfb', '\x1f']:
                # win, they're willing to do NAWS! Parse their window info
                stuff = ''.join(result[3:])
                pc.parse_winchange(stuff)
        finally:
            pc.conn.settimeout(None)
            self.log.debug(str(result))
    
