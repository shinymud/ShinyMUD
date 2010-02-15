from shinymud.models.character import Character
from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.lib.world import World
from shinymud.lib.event_handler import EVENTS
from shinymud.commands import PLAYER, DM
from shinymud.models.npc_event import NPCEvent
import logging
import re

class Npc(Character):
    """Represents a non-player character."""
    char_type = 'npc'
    def __init__(self, area=None, id=0, **args):
        self.characterize(**args)
        self.area = area
        self.id = str(id)
        self.name = str(args.get('name', 'Shiny McShinerson'))
        self.dbid = args.get('dbid')
        self.title = args.get('title', '%s is here.' % self.name)
        self.gender = args.get('gender', 'neutral')
        self.keywords = [name.lower() for name in self.name.split()]
        self.keywords.append(self.name.lower())
        kw = str(args.get('keywords', ''))
        if kw:
            self.keywords = kw.split(',')
        self.description = args.get('description', 'You see nothing special about this person.')
        self.world = World.get_world()
        self.spawn_id = None
        self.log = logging.getLogger('Npc')
        self.events = {}
        if self.dbid:
            self.load_events()
    
    def to_dict(self):
        d = Character.to_dict(self)
        d['keywords'] = ','.join(self.keywords)
        d['area'] = self.area.dbid
        d['id'] = self.id
        d['name'] = self.name
        d['gender'] = self.gender
        d['title'] = self.title
        d['description'] = self.description
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    @classmethod
    def create(cls, area=None, npc_id=0):
        """Create a new npc"""
        new_npc = cls(area, npc_id)
        return new_npc
    
    def __str__(self):
        string = ('NPC %s from Area %s' % (self.id, self.area.name)
                   ).center(50, '-') + '\n'
        if self.events:
            scripts = '\n  '
            scripts += '\n  '.join([str(val) for val in self.events.values()])
        else:
            scripts = 'None.'
        string += """name: %s
title: %s
gender: %s
keywords: %s
description:
    %s
events: %s""" % (self.name, self.title, self.gender, str(self.keywords), 
                 self.description, scripts)
        string += '\n' + ('-' * 50)
        return string
    
    def load(self, spawn_id=None):
        args = self.to_dict()
        args['dbid'] = None
        args['area'] = self.area
        new_npc = Npc(**args)
        new_npc.spawn_id = spawn_id
        new_npc.events = self.events
        new_npc.permissions = PLAYER | DM
        new_npc.location = None
        new_npc.inventory = []
        new_npc.actionq = []
        new_npc.remember = []
        return new_npc
    
    def fancy_name(self):
        """Return a capitalized version of the character's name."""
        return self.name
    
    def load_events(self):
        events = self.world.db.select('* FROM npc_event WHERE prototype=?', [self.dbid])
        self.log.debug(events)
        for event in events:
            s_id = self.world.db.select('id FROM script WHERE dbid=?', 
                                        [event['script']])
            s = self.area.get_script(str(s_id[0].get('id')))
            if s:
                # Only load this event if its script exists
                event['script'] = s
                event['prototype'] = self
                e = NPCEvent(**event)
                self.events[event['event_trigger']] = e
            else:
                self.log.error('The script this event points to is gone! '
                               'NPC (id:%s, area:%s)' % (self.id, self.area.name))
    
    def update_output(self, message):
        self.actionq.append(message)
    
    def set_description(self, description, user=None):
        """Set the description of this npc."""
        user.last_mode = user.mode
        user.mode = TextEditMode(user, self, 'description', self.description)
        return 'ENTERING TextEditMode: type "@help" for help.\n'
    
    def set_name(self, name, user=None):
        """Set the name of this NPC."""
        self.name = name
        self.save({'name': self.name})
        return 'Npc name saved.\n'
    
    def set_title(self, title, user=None):
        self.title = title
        self.save({'title': self.title})
        return 'Npc title saved.\n'
    
    def set_keywords(self, keywords, user=None):
        """Set the keywords for this npc.
        The argument keywords should be a string of words separated by commas.
        """
        if keywords:
            word_list = keywords.split(',')
            self.keywords = [word.strip().lower() for word in word_list]
            self.save({'keywords': ','.join(self.keywords)})
            return 'Npc keywords have been set.\n'
        else:
            self.keywords = [name.lower() for name in self.name.split()]
            self.keywords.append(self.name.lower())
            self.save({'keywords': ','.join(self.keywords)})
            return 'Npc keywords have been reset.\n'
    
    def set_gender(self, gender, user=None):
        if gender.lower() not in ['female', 'male', 'neutral']:
            return 'Valid genders are: female, male, neutral.'
        self.gender = gender.lower()
        self.save({'gender': self.gender})
        return '%s\'s gender has been set to %s.' % (self.name, self.gender)
    
    def add_event(self, args):
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
        e = self.events.get(trigger)
        if e:
            e.destruct()
        new_event = NPCEvent(**{'condition': condition, 
                              'script': script,
                              'prototype': self,
                              'probability': int(prob),
                              'event_trigger': trigger})
        new_event.save()
        self.events[trigger] = new_event
        return 'Event added.'
    
    def remove_event(self, event):
        """Remove an event from an npc."""
        if event in self.events:
            self.events[event].destruct()
            del self.events[event]
            return 'Event "%s" removed.' % event
        return 'Npc %s doesn\'t have an event "%s".' % (self.id, event)
    
    def notify(self, event_name, args):
        if event_name in self.events.keys():
            args['obj'] = self
            args.update(self.events[event_name].get_args())
            EVENTS[event_name](**args).run()
    
    def set_mode(self, mode):
        pass