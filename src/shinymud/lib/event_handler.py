from shinymud.commands import *
from shinymud.commands.commands import *
from shinymud.commands.emotes import *

import re
import logging
import random

class EventHandler(object):
    """
    We always expect **args to contain at least:
    obj -- the object taking the action
    script -- the script to be executed
    probability -- the probability the event should occur
    
    **args may contain other key-value pairs that it expects its event might
    need
    """
    def __init__(self, **args):
        self.obj = args.get('obj')
        self.script = args.get('script')
        self.script_text = self.script.body
        self.probability = args.get('probability')
        self.args = args
        self.log = logging.getLogger('EventHandler')
        self.script_cmds = {'record': self.record_user
                           }
        self.conditions = {'remember': self.remember_user,
                           'equal': self.equal
                          }
    
    def run(self):
        result = random.randint(1, 100)
        if result <= self.probability:
            self.execute()
    
    def execute_script(self):
        """Execute each command in a parsed script."""
        # Execute each line in 
        self.log.debug('About to execute script %s.' % self.script.id)
        try:
            lines = self.parse_script()
        except ParseError, e:
            self.log.error(str(e))
            self.obj.actionq.append(str(e))
        except ConditionError, e:
            self.obj.actionq.append(str(e))
        else:        
            for line in lines:
                self.log.debug(line)
                match = re.search(r'\s*(\w+)([ ](.+))?$', line)
                if match:
                    cmd_name, _, args = match.groups()
                    if cmd_name in self.script_cmds:
                        try:
                            self.script_cmds[cmd_name](args)
                        except CommandError, e:
                            self.obj.actionq.append(str(e))
                    else:
                        cmd = command_list[cmd_name]
                        if cmd:
                            cmd(self.obj, args, cmd_name).run()
    
    def personalize(self, replace_dict):
        """Replace a set of word place-holders with their real counterparts."""
        for key, val in replace_dict.items():
            self.script_text = self.script_text.replace(key, val)
    
    def parse_script(self):
        """Parse a human generated script with conditionals and broken lines
        into a list of commands to be executed."""
        lines = self.script_text.split('\n')
        # If a line ends in a +, that means the next line should be added to
        # it.
        nl = [lines[0]]
        for i in range(1, len(lines)):
            if nl[len(nl)-1].endswith('+'):
                nl[len(nl)-1] = nl[len(nl)-1].rstrip('+') + lines[i]
            else:
                nl.append(lines[i])
        # Now we should have a list where each command (followed by its
        # arguments) is on its own line.
        self.log.debug(nl)
        final = []
        i = 0
        while i < len(nl):
            if nl[i].startswith('if'):
                i = self.parse_if(final, nl, i)
            else:
                final.append(nl[i])
                i += 1
        # Finally we have a list of lines that are ready to be executed, line
        # by line
        return final
    
    def parse_if(self, pl, lines, index):
        """Parse an if statement."""
        T = []
        F = []
        state = T
        self.log.debug(index)
        condition = self.parse_condition(lines[index].lstrip('if '))
        try:
            while lines[index] != 'endif':
                if lines[index] not in ['if', 'else']:
                    state.append(lines[index])
                elif lines[index] == 'if':
                    index = self.parse_if(state, index)
                elif lines[index] == 'else':
                    state = F
                index += 1
        except IndexError, e:
            raise ParseError('Script %s Error: "if" block was not terminated by an "endif"' % self.script.id)
        pl.extend({True: T, False: F}[condition])
        return index + 1
    
    def parse_condition(self, cond):
        """Parse a ShinyScript conditional."""
        args = [arg.strip().lower() for arg in cond.split()]
        if args[0] in self.conditions:
            return self.conditions[args[0]](*args[1:])
        else:
            raise ParseError('Script %s Error: unrecognized condition: "%s"' % (self.script.id, args[0]))
    
    # *********** SCRIPT COMMANDS ***********
    
    def record_user(self, name=None):
        """Record the name in this object's memory."""
        if not name:
            raise CommandError("Script %s Error: record command requires a name argument" % self.script.id)
        name = name.lower().strip()
        if not name in self.obj.remember:
            self.obj.remember.append(name.lower().strip())
    
    # *********** CONDITION FUNCTIONS ***********
    def remember_user(self, name=None):
        """Return true if this name is in the object's memory, false if
        it isn't.
        """
        if not name:
            raise ConditionError("Script %s Error: remember condition requires a name argument" % self.script.id)
        if name.lower().strip() in self.obj.remember:
            return True
        return False
    
    def equal(self, *args):
        """Check if two strings are equal."""
        bad_args = "Script %s Error: equal condition requires two string arguments to compare" % self.script.id
        if not args:
            raise ConditionError(bad_args)
        if len(args) < 2:
            raise ConditionError(bad_args)
        if args[0] == args[1]:
            return True
        return False
    

class ParseError(Exception):
    """ParseError should be raised if there's an error in parsing a script."""
    pass

class ConditionError(Exception):
    """ConditionError should be raised if there's an error with a ShinyScript
    Conditional
    """
    pass

class CommandError(Exception):
    """CommandError should be raised if there's an error with a ShinyScript
    Command
    """
    pass


EVENTS = CommandRegister()

class PCEnter(EventHandler):
    def execute(self):
        user = self.args.get('user')
        prev = self.args.get('from')
        rep = {'#target_name': user.fancy_name(),
               '#from_room': prev}
        # Set the user as the target in the script
        self.personalize(rep)
        self.execute_script()
    

EVENTS.register(PCEnter, ['pc_enter'])

class GivenItem(EventHandler):
    def execute(self):
        giver = self.args.get('giver')
        item = self.args.get('item')
        rep = {'#target_name': giver.fancy_name(),
               '#item_name': item.name}
        self.personalize(rep)
        self.execute_script()
    

EVENTS.register(GivenItem, ['given_item'])

class Hears(EventHandler):
    def execute(self):
        condition = self.args.get('condition')
        heard_string = self.args.get('string')
        # The person who's responsible for saying/giving the message that the
        # npc heard (may be None)
        teller = self.args.get('teller')
        # If the user never added a condition with this event, then oh well
        if not condition:
            return
        if heard_string.find(condition) != -1:
            # We heard what we were looking for!
            if teller:
                rep = {'#target_name': teller.fancy_name()}
                self.personalize(rep)
            self.execute_script()
    

EVENTS.register(Hears, ['hears'])

class Emoted(EventHandler):
    def execute(self):
        emoter = self.args.get('emoter')
        condition = self.args.get('condition')
        emote = self.args.get('emote')
        rep = {'#target_name': emoter.fancy_name()}
        self.personalize(rep)
        if not condition:
            self.execute_script()
        elif condition == emote:
            self.execute_script()
    

EVENTS.register(Emoted, ['emoted'])