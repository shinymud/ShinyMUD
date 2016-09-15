from shinymud.commands import *
from shinymud.commands.commands import *
from shinymud.commands.emotes import *
from shinymud.lib.world import World

import re
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
    def __init__(self, args={}):
        self.obj = args.get('obj')
        self.script = args.get('script')
        self.script_text = self.script.body
        self.probability = args.get('probability')
        self.args = args
        self.log = World.get_world().log
        self.script_cmds = {'record': self.record_player
                           }
        self.conditions = {'remember': self.remember_player,
                           'equal': self.equal,
                           'target_has': self.has_item
                          }
    
    def run(self):
        result = random.randint(1, 100)
        if result <= self.probability:
            self.execute()
    
    def compile_script(self):
        """Execute each command in a parsed script."""
        # Execute each line in 
        self.log.debug('About to execute script %s.' % self.script.id)
        try:
            lines = self.parse_script()
        except ParseError as e:
            self.log.error(str(e))
            self.obj.actionq.append(str(e))
        except ConditionError as e:
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
                        except CommandError as e:
                            self.obj.actionq.append(str(e))
                    else:
                        cmd = command_list[cmd_name]
                        if cmd:
                            self.obj.cmdq.append(cmd(self.obj, args, cmd_name))
    
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
                nl.append(lines[i].lstrip())
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
        self.log.debug(str(final))
        return final
    
    def parse_if(self, pl, lines, index):
        """Parse an if statement."""
        T = []
        F = []
        state = T
        self.log.debug(index)
        condition = self.parse_condition(lines[index].lstrip('if '))
        index += 1
        try:
            while not 'endif' in lines[index]:
                if not (lines[index].startswith('if') or lines[index].startswith('else')):
                    state.append(lines[index])
                elif lines[index].startswith('if'):
                    index = self.parse_if(state, lines, index)
                    continue
                elif lines[index].startswith('else'):
                    state = F
                index += 1
        except IndexError as e:
            raise ParseError('Script %s Error: "if" block was not terminated by an "endif"' % self.script.id)
        self.log.debug('Parse If status:\nTrue: %s\nFalse: %s\nCondition: %s\n' % (str(T), str(F), str(condition)))
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
    
    def record_player(self, name=None):
        """Record the name in this object's memory."""
        if not name:
            raise CommandError("Script %s Error: record command requires a name argument" % self.script.id)
        name = name.lower().strip()
        if not name in self.obj.remember:
            self.obj.remember.append(name.lower().strip())
    
    # *********** CONDITION FUNCTIONS ***********
    def remember_player(self, name=None):
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
    
    def has_item(self, *args):
        """Returns true if the target PLAYER has a specific ITEM"""
        bad_args = "Script %s Error: You must provide both the player and the item they may have." % self.script.id
        player = self.args.get('player')     
        if not args:
            raise ConditionError(bad_args)
        else:
            args = " ".join(args)
            exp = r'(#target_name[ ]+)?(item[ ]+)?(?P<id>\d+)[ ]+(from[ ]+)?(area[ ]+)?(?P<area>\w+)'
            match = re.match(exp, args, re.I)
            if not match:
                raise ConditionError(bad_args)
            item_id, area_name = match.group('id', 'area')
            #Check for the item in the players inventory. We don't need to check if the item exists
            #in the world since the player then couldn't possibly have it.
            for each in player.inventory:
                if ((item_id == each.build_id) and \
                        (area_name.lower() == each.build_area)):
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
    help = (
    """<title>PC Enter (Script trigger)</title>
This event is triggered when a player enters a room.
\nUSAGE:
To add a 'PC Enter' event:
  add event pc_enter call script <script-id>
\nCONDITIONS:
This event has no conditions.
\nPERSONALIZERS
When this event is triggered and calls a script, that script will replace the
following personalizers with their corresponding values:
<b>#target_name</b> Will be replaced with the name of the player entering the
  room
<b>#from_room</b> Will be replaced with a signature of the room the player left
  when they entered this room. The signature will be of the form:
  "<room-id>_<area-name>". For example, the signature of room 4 from area foo
  will be: "4_foo".
    """
    )
    def execute(self):
        player = self.args.get('player')
        prev = self.args.get('from')
        rep = {'#target_name': player.fancy_name(),
               '#from_room': prev}
        # Set the player as the target in the script
        self.personalize(rep)
        self.compile_script()
    

EVENTS.register(PCEnter, ['pc_enter'])
command_help.register(PCEnter.help, ['pc_enter', 'pcenter'])

class GivenItem(EventHandler):
    help = (
    """<title>GivenItem (Script trigger)</title>
This event is triggered when an npc is given an item.
\nUSAGE:
To add a 'GivenItem' event:
  add event given_item ['condition'] call script <script-id>
\nCONDITIONS:
You may specify a condition that the item given have a specific id number and
area name in order for the script to be called. If the item given does not match
the id number and area name in the trigger condition, then the script will not
be called. 
The condition syntax for specifying an item is:
 'item <item-id> from area <area-name>'
\nEXAMPLE:
  add event given_item 'item 8 from cubicle' call script 4
\nPERSONALIZERS:
When this event is triggered and calls a script, that script will replace the
following personalizers with their corresponding values:
<b>#target_name</b> Will be replaced with the name of the character giving the item
<b>#item_name</b> Will be replaced with the name of the item given
<b>#item_id</b> Will be replaced with the id of the item given
<b>#item_area</b> Will be replaced with the area-name of the item given
    """
    )
    def execute(self):
        condition = self.args.get('condition')
        giver = self.args.get('giver')
        item = self.args.get('item')
        if condition:
            exp = r'(item[ ]+)?(?P<id>\d+)[ ]+(from[ ]+)?(area[ ]+)?(?P<area>\w+)'
            match = re.match(exp, condition, re.I)
            if not match:
                m = 'Error in given_item event condition: "' + condition +\
                    '" is improper syntax.\nShould be "item <item-id> from area <area-name>". See "help triggers".'
                self.obj.update_output(m)
                return
            item_id, area_name = match.group('id', 'area')
            if not ((item_id == item.build_id) and \
                    (area_name.lower() == item.build_area)):
               return
               
        rep = {'#target_name': giver.fancy_name(),
               '#item_name': item.name,
               '#item_id': item.build_id,
               '#item_area': item.build_area}
        self.personalize(rep)
        self.compile_script()
    

EVENTS.register(GivenItem, ['given_item'])
command_help.register(GivenItem.help, ['given_item', 'givenitem', 'given item'])

class Hears(EventHandler):
    help = (
    """<title>Hears (Event Trigger)</title>
This event is triggered when an npc 'hears' a specific phrase echoed in the
room.
\nUSAGE:
To add a "Hears" event:
  add event hears 'condition' call script <script-id>
\nCONDITIONS:
You must supply the phrase that this npc should hear in order to call the
specified script.
\nEXAMPLE:
  add event hears 'gives a blanket to sampson' call script 4
\nPERSONALIZERS:
When this event is triggered and calls a script, that script will replace the
following personalizers with their corresponding values:
<b>#target_name</b> Will be replaced with the name of the character who was the
source of the phrase
    """
    )
    def execute(self):
        condition = self.args.get('condition')
        heard_string = self.args.get('string')
        # The person who's responsible for saying/giving the message that the
        # npc heard (may be None)
        teller = self.args.get('teller')
        # The NPC that hears the player
        listener = self.args.get('obj')
        # If the player never added a condition with this event, then oh well
        if not condition:
            return
        if (heard_string.find(condition) != -1) and (listener != teller):
            # We heard what we were looking for!
            if teller:
                rep = {'#target_name': teller.fancy_name()}
                self.personalize(rep)
            self.compile_script()
    

EVENTS.register(Hears, ['hears'])
command_help.register(Hears.help, ['hears', 'hears event'])

class Emoted(EventHandler):
    help = (
    """<title>Emoted (Event Trigger)</title>
This event is triggered when an npc receives an emote directed at them.
\nUSAGE:
To add a 'Emoted' event:
  add event emoted ['condition'] call script <script-id>
\nCONDITIONS:
You may specify a condition for a specific emote (not required).
\nEXAMPLE:
  add event emoted 'slap' call script 4
\nPERSONALIZERS:
When this event is triggered and calls a script, that script will replace the
following personalizers with their corresponding values:
<b>#target_name</b> Will be replaced with the name of the character initiating
the emote
<b>#emote</b> Will be replaced with the emote that was used 
    """
    )
    def execute(self):
        emoter = self.args.get('emoter')
        condition = self.args.get('condition')
        emote = self.args.get('emote')
        rep = {'#target_name': emoter.fancy_name(),
               '#emote': emote}
        self.personalize(rep)
        if not condition:
            self.compile_script()
        elif condition == emote:
            self.compile_script()
    

EVENTS.register(Emoted, ['emoted'])
command_help.register(Emoted.help, ['emoted', 'emoted event'])
