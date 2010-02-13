from shinymud.commands.commands import *
import re
import logging

class BattleMode(object):
    
    def __init__(self, user):
        self.user = user
        self.log = logging.getLogger('BattleMode')
        self.state = self.parse_command
        self.active = True
        self.name = 'BattleMode'
    
    def parse_command(self):
        while len(self.user.inq) > 0:
            raw_string = self.user.inq.pop(0)
            match = re.search(r'\s*(\w+)([ ](.+))?$', raw_string)
            if match:
                cmd_name, _, args = match.groups()
                cmd = battle_commands[cmd_name]
                if not cmd:
                    cmd = command_list[cmd_name]
                if cmd:
                    cmd(self.user, args, cmd_name).run()
                else:
                    # The command the user sent was invalid... tell them so
                    self.user.update_output("I don't understand \"%s\"\n" % raw_string)