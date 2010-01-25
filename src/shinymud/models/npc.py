from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.lib.world import World
import logging

class Npc(object):
    def __init__(self, area=None, id=0, **args):
        self.area = area
        self.id = str(id)
        self.name = str(args.get('name', 'Shiny McShinerson'))
        self.dbid = args.get('dbid')
        self.title = args.get('title', '%s is here.' % self.name)
        self.keywords = [name.lower() for name in self.name.split()]
        self.keywords.append(self.name.lower())
        kw = str(args.get('keywords', ''))
        if kw:
            self.keywords = kw.split(',')
        self.description = args.get('description', 'You see nothing special about this person.')
        self.world = World.get_world()
        self.spawn_id = None
        self.inventory = []
        self.actionq = []
        self.log = logging.getLogger('Npc')
    
    def to_dict(self):
        d = {}
        d['keywords'] = ','.join(self.keywords)
        d['area'] = self.area.dbid
        d['id'] = self.id
        d['name'] = self.name
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
        npc = room_list ="""______________________________________________
NPC: 
    id: %s
    area: %s
    name: %s
    title: %s
    keywords: %s
    description: 
%s
______________________________________________\n""" % (self.id, self.area.name, self.name,
                                                       self.title, str(self.keywords),
                                                       self.description)
        return npc
    
    def destruct(self):
        if self.dbid:
            self.world.db.delete('FROM npc WHERE dbid=?', [self.dbid])
    
    def save(self, save_dict=None):
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict('npc', save_dict)
            else:    
                self.world.db.update_from_dict('npc', self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict('npc', self.to_dict())
    
    def load(self, spawn_id=None):
        new_npc = Npc(**self.to_dict())
        new_npc.area = self.area
        new_npc.spawn_id = spawn_id
        new_npc.dbid = None
        return new_npc
    
    def update_output(self, message):
        self.actionq.append(message)
    
    def fancy_name(self):
        return self.name
    
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
    
    def item_add(self, item):
        self.inventory.append(item)
    
    def item_remove(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
    
