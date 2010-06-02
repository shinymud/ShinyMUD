from shinymud.commands.commands import *
import re

class BattleMode(object):
    
    def __init__(self, player):
        self.player = player
        self.state = self.parse_command
        self.active = True
        self.name = 'BattleMode'
    
    def parse_command(self):
        while len(self.player.inq) > 0:
            raw_string = self.player.inq.pop(0)
            match = re.search(r'\s*(\w+)([ ](.+))?$', raw_string)
            if match:
                cmd_name, _, args = match.groups()
                cmd = battle_commands[cmd_name]
                if not cmd:
                    cmd = command_list[cmd_name]
                if cmd:
                    cmd(self.player, args, cmd_name).run()
                else:
                    # The command the player sent was invalid... tell them so
                    self.player.update_output("I don't understand \"%s\"\n" % raw_string)