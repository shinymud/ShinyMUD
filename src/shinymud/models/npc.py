from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.world import World

class Npc(object):
    def __init__(self, area=None, id=0, **args):
        self.area = area
        self.id = str(id)
        self.name = args.get('name', 'Shiny McShinerson')
        self.dbid = args.get('dbid')
        self.description = args.get('description', 'You see nothing special about this person.')
        self.world = World.get_world()
    
    def to_dict(self):
        d = {}
        d['area'] = self.area.dbid
        d['id'] = self.id
        d['name'] = self.name
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
    description: 
%s
______________________________________________\n""" % (self.id, self.area.name, self.name,
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
    
