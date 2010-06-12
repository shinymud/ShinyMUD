from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.models import Column, model_list
from shinymud.models.shiny_types import *


import re

class Script(Model):
    """A model that represents an in-game script object."""
    db_table_name = 'script'
    db_columns = Model.db_columns + [
        Column('area', type="INTEGER", read=read_area, write=write_area),
        Column('name', default='New Script', null=False),
        Column('body', default='', null=False),
        Column('id')
    ]        
    def __str__(self):
        string = (' Script %s in Area %s ' % (self.id, self.area.name)
                  ).center(50, '-') + '\n'
        body = '\n  '.join([line for line in self.body.split('\n')])
        if not body:
            body = 'Script is empty.'
        string += "Name: %s\nBody:\n  %s" % (self.name, body)
        string += '\n' + ('-' * 50)
        return string
        
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
        if self.dbid:
            self.world.db.delete('FROM script WHERE dbid=?', [self.dbid])
    
