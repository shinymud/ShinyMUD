from shinymud.commands import *
from shinymud.commands.commands import *

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
    
    def run(self):
        result = random.randint(1, 100)
        if result <= self.probability:
            self.execute()
    
    def execute_script(self):
        # Execute each line in 
        self.log.debug('About to execute script %s.' % self.script.id)
        lines = self.script_text.split('\n')
        for line in lines:
            match = re.search(r'\s*(\w+)([ ](.+))?$', line)
            if match:
                cmd_name, _, args = match.groups()
                cmd = command_list[cmd_name]
                if cmd:
                    cmd(self.obj, args, cmd_name).run()
        self.log.debug(self.obj.actionq)
    
    def personalize(self, replace_dict):
        for key, val in replace_dict.items():
            self.script_text = self.script_text.replace(key, val)
    

EVENTS = CommandRegister()

class PCEnter(EventHandler):
    def execute(self):
        user = self.args.get('user')
        # Set the user as the target in the script
        self.script_text = self.script_text.replace('#target_name', user.fancy_name())
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
