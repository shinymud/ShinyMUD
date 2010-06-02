import threading
import socket

class StatSender(threading.Thread):
    """StatSender is a stand-alone thread that sends game-statistics to any
    client that connects on its port.
     
    When a client connects to StatSender, StatSender sends back a string
    containing a list of players currently logged in and the date the server was
    last restarted, then closes the connection.
     
    NOTE: The host and port that StatSender uses are defined in ShinyMUD's
    config file. This StatSender thread can also be enabled or disabled by
    setting the STATS_ENABLED variable to True or False (respectively) in the
    config file.
     
    The string of game information sent to clients is formatted with each of the
    player's names separated by commas, and the reset date separated from the
    name list by a colon like the following example:
        Player1,Player2,PlayerN:ResetDate
     
    The ResetDate is given as a floating point number expressed in seconds since
    the epoch, in UTC (as returned by Python's time.time() function). See the
    time documentation (http://docs.python.org/library/time.html) for details.
    """
    
    def __init__(self, port, host, world):
        threading.Thread.__init__(self)
        self.daemon = True # So this thread will exit when the main thread does
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((host, port))
        self.world = world
    
    def run(self):
        """Start the StatSender thread running.
        """
        self.listener.listen(5)
        while 1:
            try:
                conn, info = self.listener.accept()
            except Exception, e:
                self.world.log.debug(str(e))
            else:
                # Send them the game-stats!
                plist = ','.join([name for name in self.world.player_list if isinstance(name, str)])
                conn.send(plist + ':' + str(self.world.uptime))
                # conn.send(str(self.world.uptime))
                conn.close()
    

