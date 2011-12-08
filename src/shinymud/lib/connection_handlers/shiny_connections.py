import re
import hashlib
from struct import pack
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
        self.win_size = (80,40)
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
            return False
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
    


class WebsocketConnection(ShinyConnection):
    handshake_string = "HTTP/1.1 101 Web Socket Protocol Handshake\r\n\
Upgrade: WebSocket\r\n\
Connection: Upgrade\r\n\
Sec-WebSocket-Origin: %(origin)s\r\n\
Sec-WebSocket-Location: ws://%(host)s/\r\n\r\n"
    
    def __init__(self, conn_info, log, host, port):
        ShinyConnection.__init__(self, conn_info, log)
        self.host = host
        self.port = port
        self.data_fragment = ''
        self.handshake()
        self.conn.setblocking(0)
    
    def send(self, queue):
        try:
            while (len(queue) > 0):
                line = queue.pop(0)
                line = '\x00' + line.encode('utf-8') + '\xFF'
                self.conn.send(line)
        except socket_error:
            # If we die here, it's probably because we got a broken pipe...
            # tell the function that's calling us we're not alive anymore 
            return False
        else:
            return True
    
    
    def recv(self):
        try:
            new_stuff = self.data_fragment + self.conn.recv(256)
        except socket_error:
            # In non-blocking mode, recv generates an error if it doesn't find
            # any data to recieve. We want to ignore that error and quitely wait until
            # there is data.
            return False
        else:
            valid_lines = []
            
            # Split all lines on the terminating character
            lines = new_stuff.split('\xFF')
            
            # Pop the last line off of the end - this will either be an empty string if the
            # last line was terminated, or a left over fragment that should wait for the next batch
            # of lines to be processed
            self.data_fragment = lines.pop()
            
            # Now we should make sure the lines have a valid prefix. Ignore any that don't.
            for line in lines:
                if line[0] == '\x00':
                    valid_lines.append(line[1:])
                elif line == '':
                    # The client wishes to terminate - send the closing handshake and disconnect
                    self.close()
                    # Return None so that the player object knows to log the player out
                    return None
                else:
                    self.log.error('Received invalid message from client '
                                    '(frame did not begin with 0x00 byte): %s' % (line))
                
            if valid_lines:
                return valid_lines
            
            return False
    
    
    def handshake(self):
        data = self.conn.recv(1024)
        host = re.findall(r'Host: (.*?)\r\n', data)[0]
        origin = re.findall(r'Origin: (.*?)\r\n', data)[0]
        response = self.handshake_string % {'origin': origin, 'host': host}
        
        response = response.encode('utf-8') + self.parse_hybi00(data)
        self.conn.send(response)
    
    def close(self):
        self.conn.close()
    
    def parse_hybi00(self, request):
        """ Parses an HTTP request header and forms a response according to
        The WebSocket protocol, draft-ietf-hybi-thewebsocketprotocol-00
        (http://tools.ietf.org/html/draft-ietf-hybi-thewebsocketprotocol-00).
        """
        # The random tokens will be in the last 8 bytes of the request
        random_tokens = request[-8:]
        # Grab the sooper seekret keys hidden away in the request headers
        key1 = re.findall(r'Sec-WebSocket-Key1: (.*?)\r\n', request)[0]
        key2 = re.findall(r'Sec-WebSocket-Key2: (.*?)\r\n', request)[0]
        
        def parse_key(key):
            spaces = 0
            digits = ''
            
            for char in list(key):
                if char.isdigit():
                    # If the character is a digit, concatonate it to our string of digits
                    digits += char
                elif char == ' ':
                    # If the character is a space, add it to our space counter orgecc
                    spaces += 1
            
            result = int(int(digits) / spaces)
            return result
        
        
        response = pack('>II8s', parse_key(key1), parse_key(key2), str(random_tokens))
        hashed_response = hashlib.md5()
        hashed_response.update(response)
        return hashed_response.digest()
    

