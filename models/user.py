from commands import *
from wizards import CharacterInit
from models import ShinyModel
import re
import logging

class User(ShinyModel):
    """This is a basic user object."""
    
    def __init__(self, conn_info, world):
        self.conn, self.addr = conn_info        
        self.world = world
        self.inq = []
        self.outq = []
        self.quit_flag = False
        self.game_state = 'init'
        self.log = logging.getLogger('User')
        self.char_init = CharacterInit(self)
        self.location = ''
        self.prompt = ''
        
        # The following dictionary contains the attributes of this model that will
        # be saved to the database. The key should be the name of the attribute, and the value
        # should be a list with the following values in the following order: the value of the 
        # attribute, the type of the attribute, and the default value of the attribute.
        self.model_attr = {
            'channels': [None, dict, {'chat': True}],
            'name': [None, str, ''],
            'password': [None, str, '']
        }
    
    def update_output(self, data):
        """Helpfully inserts data into the user's output queue."""
        self.outq.append(data)
    
    def get_input(self):
        """Gets raw input from the user and queues it for later processing."""
        try:
            new_stuff = self.conn.recv(256)
            self.inq.append(new_stuff.replace('\n', ''))
        except Exception, e:
            pass
    
    def send_output(self):
        """Sends all data from the user's output queue to the user."""
        try:
            sent_output = False
            while len(self.outq) > 0:
                self.conn.send(self.outq[0])
                del self.outq[0]
                sent_output = True
            if sent_output:
                self.conn.send(self.prompt)
        except Exception, e:
            # If we die here, it's probably because we got a broken pipe.
            # In this case, we should disconnect the user
            self.user_logout(True)
            print str(e)
    
    def set_prompt(self, new_prompt):
        self.prompt = new_prompt
    
    def parse_command(self):
        """Parses the lines in the user's input buffer and then calls
        the appropriate commands (if they exist)"""
        
        while len(self.inq) > 0:
            raw_string = self.inq.pop(0)
            match = re.search(r'\s*(\w+)([ ](.+))?$', raw_string)
            if match:
                cmd_name, _, args = match.groups()
                cmd = command_list[cmd_name]
                if cmd:
                    cmd(self, args).execute()
                else:
                    # The command the user sent was invalid... tell them so
                    self.update_output("I don't understand \"%s\"\n" % raw_string)
    
    def do_tick(self):
        """What should happen to the user everytime the world ticks."""
        if self.quit_flag:
            self.user_logout()
        else:
            self.get_input()
            # do authorization, if needed
            if self.game_state == 'init':
                self.char_init.state()
                if self.game_state != 'init':
                    del self.char_init
            else:
                self.parse_command()
    
    def user_logout(self, broken_pipe=False):
        #TO DO: Save the user to the database
        if not broken_pipe:
            self.conn.send('Bye!\n')
        self.conn.close()
        self.world.user_delete.append(self.name)
    
    def get_fancy_name(self):
        return self.name.capitalize()
    
