import threading
from commands import Commands

MAX_RECV = 256 #Max number of bytes the server will accept from a client in one go
EXIT_PHRASES = ['exit', 'quit']

class RequestHandler(threading.Thread):
    char_list = []
    list_lock = threading.Lock()
    
    def __init__(self, clnt_info):
        #Call threading class' constructor first
        threading.Thread.__init__(self)
        self.conn, self.addr = clnt_info
        
        #add self to the global list of characters
        
    def run(self):
        self.conn.send("Welcome to the MUDD!\n>")
        self.conn.settimeout(0.25)
        while 1:
            #Get everything up to MAX_RECV, but strip-off the newline at the end
            buff = self.conn.recv(MAX_RECV)[0]
            if buff.lower() in EXIT_PHRASES:
                break
            #parse buff into commands/arg list
            #call the correct command
                #if correct command does not exist, result should be a human readible error
            #return the result of that command to the user
            self.conn.send("%s\n>" % buff)
            
        #remove self from global list of characters   
        print "Client logging off from: %s" % str(self.addr) 
        self.conn.close()
                