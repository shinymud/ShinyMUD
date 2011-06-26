import re
from socket import error as socket_error

class ShinyConnection(object):
    
    def __init__(self, conn_info, log):
        self.conn, self.addr = conn_info
        self.log = log
    
    def send(self):
        pass
    
    def recv(self):
        pass


class TelnetConnection(ShinyConnection):
    
    win_change_regexp = re.compile(r"\xff\xfa\x1f(?P<size>.*?)\xff\xf0")
    
    def __init__(self, conn_info, log):
        ShinyConnection.__init__(self, conn_info, log)
        self.win_size = None
        self.set_telnet_options()
        # Put our socket into non-blocking mode - we'll periodically poll for data
        # instead of blocking until we get it
        self.conn.setblocking(0)
    
    def send(self, queue):
        try:
            for index, line in enumerate(queue):
                if index != (len(queue) - 1):
                    line += '\r\n'
                self.conn.send(line)
            del queue[:]
        except socket_error:
            # If we die here, it's probably because we got a broken pipe...
            # tell the function that's calling us we're not alive anymore
            return False
        else:
            return True
    
    def recv(self):
        try:
            new_stuff = self.conn.recv(256)
        except socket_error:
            # In non-blocking mode, recv generates an error if it doesn't find
            # any data to recieve. We want to ignore that error and quitely wait until
            # there is data.
            pass
        else:
            # Get rid of the \r \n line terminators
            new_stuff = new_stuff.replace('\n', '').replace('\r', '')
            # See if the input is a notice of window size change
            self.parse_winchange(new_stuff)
            # Ignore any other telnet negotiations
            new_stuff = re.sub(r"\xff((\xfa.*?\xf0)|(..))", '', new_stuff)
            if new_stuff:
                return new_stuff
            return False
    
    
    def close(self):
        self.conn.close()
    
    def set_telnet_options(self):
        """Petition client to run in linemode and to send window size change
        notifications.
        Some telnet clients, such as putty, start in non-linemode by default
        (they transmit each character as they receive it from the player). We want
        them to switch to linemode in this case, where they transmit each line
        after it's been assembled. We also wan't the client to tell us their
        screen size so we can display things appropriately.
        """
        # IAC + WILL + LINEMODE
        self.conn.send(chr(255) + chr(251) + chr(34) + '\r\n')
        # We should get a response from their client (immediately)
        self.conn.settimeout(1.0)
        try:
            result = list(self.conn.recv(256))
        except socket.timeout:
            # This just means that their telnet client didn't send us a timely
            # response to our initiating linemode... we should just move on
            result = 'Client response FAIL for linemode.'
        finally:
            self.log.debug(result)
            
        # IAC DO NAWS (Negotiate About Window Size)
        self.conn.send(chr(255) + chr(253) + chr(31) + '\r\n')
        try:
            result = list(self.conn.recv(256))
        except:
            result = 'Client response FAIL for NAWS.'
        else:
            # IAC WILL NAWS
            if result[0:3] == ['\xff', '\xfb', '\x1f']:
                # win, they're willing to do NAWS! Parse their window info
                stuff = ''.join(result[3:])
                self.parse_winchange(stuff)
        finally:
            self.conn.settimeout(None)
            self.log.debug(str(result))
    
    def parse_winchange(self, data):
        """Parse and set the terminal size of the player."""
        match = self.win_change_regexp.match(data)
        if match:
            size = match.group('size')
            self.win_size = (ord(size[1]), ord(size[3]))
    

