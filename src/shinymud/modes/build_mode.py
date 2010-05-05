from shinymud.commands.commands import *
from shinymud.commands.build_commands import *
import re

class BuildMode(object):
    
    def __init__(self, player):
        self.player = player
        self.edit_area = None
        self.edit_object = None
        self.active = True
        self.state = self.parse_command
        self.name = 'BuildMode'
    
    def parse_command(self):
        """Parses the lines in the player's input buffer and then calls
        the appropriate commands (if they exist)"""
        
        while len(self.player.inq) > 0:
            raw_string = self.player.inq.pop(0)
            match = re.search(r'\s*(\w+)([ ](.+))?$', raw_string)
            if match:
                cmd_name, _, args = match.groups()
                cmd = build_list[cmd_name]
                if not cmd:
                    cmd = command_list[cmd_name]
                if cmd:
                    cmd(self.player, args, cmd_name).run()
                else:
                    # The command the player sent was invalid... tell them so
                    self.player.update_output("I don't understand \"%s\"\n" % raw_string)
    
