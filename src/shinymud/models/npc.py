from shinymud.models.character import Character
from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.models import Model, Column, read_list, write_list, model_list
from shinymud.lib.event_handler import EVENTS
from shinymud.commands import PLAYER, DM
from shinymud.commands.commands import command_list
from shinymud.models.npc_event import NPCEvent
from shinymud.models.npc_ai_packs import NPC_AI_PACKS

import re

class Npc(Character):
    """Represents a non-player character."""
    LOG_LINES = 25 # The number of lines an npc should "remember"
    char_type = 'npc'
    db_table_name = 'npc'
    db_columns = Character.db_columns + [
        Column('area', read=Npc.world.get_area, write=(lambda x: x.name),
               foreign_key=('area', 'name'), null=False),
        Column('id', null=False),
        Column('name', default='Shiny McShinerson'),
        Column('gender', default='neutral'),
        Column('keywords', read=read_list, write=write_list),
        Column('title')
    ]
    def __init__(self, args):
        self.characterize(args)
        if not self.title:
            self.title = args.get('title', '%s is here.' % self.name)
        if not self.keywords:
            self.keywords = [name.lower() for name in self.name.split()]
        self.spawn_id = None
        self.events = {}
        self.ai_packs = {}
    
    def load_extras(self):
        self.load_events()
        self.load_ai_packs()
    
    @classmethod
    def create(cls, area, npc_id):
        """Create a brand new npc"""
        new_npc = cls({'area': area, 'id':npc_id})
        return new_npc
    
    def __str__(self):
        string = ('NPC %s from Area %s' % (self.id, self.area.name)
                   ).center(50, '-') + '\n'
        events = ''
        for trigger, e_list in self.events.items():
            events += '\n  %s:' % trigger
            i = 0
            for e in e_list:
                events += '\n    [%s] %s' % (str(i), str(e))
                i += 1
        if not events:
            events = 'None.'
        ai_packs = ', '.join([p for p in self.ai_packs]) or 'None.'
        string += """name: %s
title: %s
gender: %s
keywords: %s
ai packs: %s
description:
    %s\n""" % (self.name, self.title, self.gender, str(self.keywords), 
                     ai_packs, self.description)
        for ai in self.ai_packs.values():
            string += str(ai)
        string += 'NPC EVENTS:\n' + events
        string += '\n' + ('-' * 50)
        return string
    
    def load(self, spawn_id=None):
        """Create a copy of this npc, then add the necessary attributes for the
        npc to survive in the game-environment.
        """
        args = self.copy_save_attrs()
        args['dbid'] = None
        new_npc = Npc(args)
        new_npc.spawn_id = spawn_id
        new_npc.events = self.events
        new_npc.ai_packs = self.ai_packs
        new_npc.permissions = PLAYER | DM
        new_npc.location = None
        new_npc.inventory = []
        new_npc.actionq = []
        new_npc.cmdq = []
        new_npc.remember = []
        return new_npc
    
    def set_mode(self, mode):
        pass
    
    def death(self):
        # Call any events related to death, and drop a corpse.
        pass
    
    def fancy_name(self):
        """Return a capitalized version of the character's name."""
        return self.name
    
    def load_events(self):
        """Load the events associated with this NPC."""
        events = self.world.db.select('* FROM npc_event WHERE prototype=?', [self.dbid])
        self.world.log.debug(events)
        for event in events:
            s_id = self.world.db.select('id FROM script WHERE dbid=?', 
                                        [event['script']])
            s = self.area.get_script(str(s_id[0].get('id')))
            if s:
                # Only load this event if its script exists
                event['script'] = s
                self.new_event(event)
            else:
                self.world.log.error('The script this event points to is gone! '
                               'NPC (id:%s, area:%s)' % (self.id, self.area.name))
    
    def load_ai_packs(self):
        for key, value in NPC_AI_PACKS.items():
            row = self.world.db.select('* FROM %s WHERE npc=?' % key,
                                       [self.dbid])
            if row:
                row[0]['npc'] = self
                self.ai_packs[key] = value(row[0])
    
    def update_output(self, message):
        """Append any updates to this npc's action queue.
        Only log up to LOG_LINES worth of updates - once the limit is
        hit, delete the oldest messages to stay within the limit."""
        self.actionq.append(message)
        if len(self.actionq) > self.LOG_LINES:
            del self.actionq[0]
    
    def do_tick(self):
        """Cycle through this npc's commands, if it has any."""
        if not self.cmdq:
            return False
        self.cmdq.pop(0).run()
        return True
    
# ***** BuildMode accessor functions *****
    def build_set_description(self, description, player=None):
        """Set the description of this npc."""
        player.last_mode = player.mode
        player.mode = TextEditMode(player, self, 'description', self.description)
        return 'ENTERING TextEditMode: type "@help" for help.\n'
    
    def build_set_name(self, name, player=None):
        """Set the name of this NPC."""
        self.name = name
        self.save({'name': self.name})
        return 'Npc name saved.\n'
    
    def build_set_title(self, title, player=None):
        self.title = title
        self.save({'title': self.title})
        return 'Npc title saved.\n'
    
    def build_set_keywords(self, keywords, player=None):
        """Set the keywords for this npc.
        The argument keywords should be a string of words separated by commas.
        """
        if keywords:
            word_list = keywords.split(',')
            self.keywords = [word.strip().lower() for word in word_list]
            self.save({'keywords': ','.join(self.keywords)})
            return 'Npc keywords have been set.'
        else:
            self.keywords = [name.lower() for name in self.name.split()]
            self.keywords.append(self.name.lower())
            self.save({'keywords': ','.join(self.keywords)})
            return 'Npc keywords have been reset.'
    
    def build_set_gender(self, gender, player=None):
        """Set the gender of this npc."""
        if not gender:
            return 'Try "set gender <gender>", or see "help npc".'
        if gender.lower() not in ['female', 'male', 'neutral']:
            return 'Valid genders are: female, male, neutral.'
        self.gender = gender.lower()
        self.save({'gender': self.gender})
        return '%s\'s gender has been set to %s.' % (self.name, self.gender)
    
# ***** Event functions *****
    def perform(self, command_string):
        """Parse the command and add its corresponding command object to this
        npc's cmdq (if the command is found).
        """
        match = re.search(r'\s*(\w+)([ ](.+))?$', command_string)
        if match:
            cmd_name, _, args = match.groups()
            cmd = command_list[cmd_name]
            if cmd:
                self.cmdq.append(cmd(self, args, cmd_name))
                self.world.npc_subscribe(self)
    
    def build_add_event(self, args):
        """Add an event to an npc."""
        # add event on_enter call script 1
        # add event listen_for 'stuff' call script 1
        # add event given_item call script 3
        help_message = 'Type "help events" for help with this command.'
        exp = r'(?P<trigger>\w+)([ ]+(?P<condition>\'(.*?)\'))?([ ]+call)([ ]+script)?([ ]+(?P<id>\d+))([ ]+(?P<prob>\d+))?'
        if not args:
            return help_message
        match = re.match(exp, args, re.I)
        if not match:
            return help_message
        trigger, condition, script_id, prob = match.group('trigger', 
                                                          'condition',
                                                          'id',
                                                          'prob')
        if not EVENTS[trigger]:
            return '%s is not a valid event trigger. Type "help event triggers" for help.' % trigger
        script = self.area.get_script(script_id)
        if not script:
            return 'Script %s doesn\'t exist.' % script_id
        # Replace any old events that had the same trigger
        if condition:
            condition = condition.strip('\'')
        if not prob:
            prob = 100
        else:
            prob = int(prob)
            if (prob < 1) or (prob > 100):
                return 'Probability value must be between 1 and 100.'
        self.new_event({'condition': condition, 
                        'script': script,
                        'probability': int(prob),
                        'event_trigger': trigger})
        return 'Event added.'
    
    def new_event(self, event_dict):
        """Add a new npc event to this npc."""
        event_dict['prototype'] = self
        new_event = NPCEvent(**event_dict)
        if not new_event.dbid:
            new_event.save()
        if new_event.event_trigger in self.events:
            self.events[new_event.event_trigger].append(new_event)
        else:
            self.events[new_event.event_trigger] = [new_event]
    
    def build_remove_event(self, event):
        """Remove an event from an npc.
        event -- a string containing the id and trigger type of the event to be removed.
        """
        exp = r'(?P<trigger>\w+)[ ]+(?P<index>\d+)'
        match = re.match(exp, event, re.I)
        if not match:
            return 'Try: "remove event <event-trigger> <event-id>" or see "help npc events".'
        trigger, index = match.group('trigger', 'index')
        if trigger not in self.events:
            return 'Npc %s doesn\'t have an event with the trigger type "%s".' % (self.id, trigger)
        if int(index) > len(self.events[trigger]):
            return 'Npc %s doesn\'t have the event %s #%s.' % (self.id, trigger, index)
        event = self.events[trigger].pop(int(index))
        event.destruct()
        return 'Event %s, number %s has been removed.' % (trigger, index)
    
    def notify(self, event_name, args):
        """An event has been fired and this NPC should check if it should
        react.
        event_name -- the name of the event being fired
        args -- the args that should be passed to the event constructor
        """
        if event_name in self.events.keys():
            args['obj'] = self
            for e in self.events[event_name]:
                args.update(e.get_args())
                EVENTS[event_name](**args).run()
            self.world.npc_subscribe(self)
    
# ***** ai pack functions *****
    def has_ai(self, ai):
        """Return true if this npc has this ai pack, False if it does not."""
        return ai in self.ai_packs
    
    def build_add_ai(self, args):
        """Add an ai pack to this npc via BuildMode."""
        if not args:
            return 'Try: "add ai <ai-pack-name>", or type "help ai packs".'
        if args in self.ai_packs:
            return 'This npc (%s) already has that ai pack.' % self.name
        if args in NPC_AI_PACKS:
            self.new_ai(args)
            return "This npc (%s) is now a %s." % (self.name, args)
        else:
            return '"%s" is not a valid ai pack. See "help ai packs".' % args
    
    def build_remove_ai(self, ai_type):
        """Remove an ai pack from this npc via BuildMode."""
        if not ai_type:
            return 'Try: "remove ai <ai-pack-name>", or type "help ai packs".'
        if not ai_type in self.ai_packs:
            return 'This npc doesn\'t have the "%s" ai type.' % ai_type
        pack = self.ai_packs.pop(ai_type)
        pack.destruct()
        return 'Npc %s (%s) no longer has %s ai.' % (self.id, self.name, ai_type)
    
    def new_ai(self, ai_pack, args={}):
        """Add a new ai pack to this npc."""
        args['npc'] = self
        pack = NPC_AI_PACKS[ai_pack](args)
        pack.save()
        self.ai_packs[ai_pack] = pack
    

model_list.register(Npc)
