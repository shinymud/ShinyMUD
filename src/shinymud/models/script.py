from shinymud.lib.world import World
from shinymud.modes.text_edit_mode import TextEditMode

import re

class Script(object):
    """A model that represents an in-game script object."""
    def __init__(self, area=None, id='0', **args):
        self.id = str(id)
        self.area = area
        self.dbid = args.get('dbid')
        self.name = args.get('name', 'New Script')
        self.body = args.get('body', '')
    
    def to_dict(self):
        d = {}
        d['id'] = self.id
        d['area'] = self.area.dbid
        d['body'] = self.body
        d['name'] = self.name
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def __str__(self):
        string = (' Script %s in Area %s ' % (self.id, self.area.name)
                  ).center(50, '-') + '\n'
        body = '\n  '.join([line for line in self.body.split('\n')])
        if not body:
            body = 'Script is empty.'
        string += "Name: %s\nBody:\n  %s" % (self.name, body)
        string += '\n' + ('-' * 50)
        return string
    
    def save(self, save_dict=None):
        world = World.get_world()
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('script', save_dict)
            else:    
                world.db.update_from_dict('script', self.to_dict())
        else:
            self.dbid = world.db.insert_from_dict('script', 
                                                       self.to_dict())
    
    def build_set_name(self, name, player=None):
        """Set the name of this script item."""
        if not name:
            return 'Set the name of the the script to what?'
        self.name = name
        self.save({'name': self.name})
        return 'Script %s\'s name has been set to "%s".' % (self.id, self.name)
    
    def build_set_body(self, body, player=None):
        """Set the body of this script item."""
        player.last_mode = player.mode
        player.mode = TextEditMode(player, self, 'body', self.body, 'script')
        return 'ENTERING TextEditMode: type "@help" for help.\n'
    
    def destruct(self):
        world = World.get_world()
        if self.dbid:
            world.db.delete('FROM script WHERE dbid=?', [self.dbid])
    
