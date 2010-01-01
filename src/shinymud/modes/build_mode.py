from commands import *
import re

class BuildMode(object):
    
    def __init__(self, user):
        self.user = user
        self.edit_area = None
        self.edit_object = None
        self.active = True
        self.state = self.parse_command
        self.name = 'BuildMode'
    
    def parse_command(self):
        """Parses the lines in the user's input buffer and then calls
        the appropriate commands (if they exist)"""
        
        while len(self.user.inq) > 0:
            raw_string = self.user.inq.pop(0)
            match = re.search(r'\s*(\w+)([ ](.+))?$', raw_string)
            if match:
                cmd_name, _, args = match.groups()
                cmd = build_list[cmd_name]
                if not cmd:
                    cmd = command_list[cmd_name]
                if cmd:
                    cmd(self.user, args, cmd_name).execute()
                else:
                    # The command the user sent was invalid... tell them so
                    self.user.update_output("I don't understand \"%s\"\n" % raw_string)
    
