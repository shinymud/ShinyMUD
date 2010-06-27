from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *

class NPCEvent(Model):
    db_table_name = 'npc_event'
    db_columns = Model.db_columns + [
        Column('prototype', write=lambda npc: npc.dbid,
                foreign_key=('npc', 'dbid'), null=False, type='INTEGER'),
        Column('script', write=lambda script: script.id),
        Column('event_trigger'),
        Column('condition'),
        Column('probability', read=read_int, write=int, default=100, type='INTEGER')
    ]
    def __str__(self):
        string = '%s' % self.event_trigger
        if self.condition:
            string += ' "%s"' % self.condition
        string += ' [script: %s, probability: %s%s]' % (self.script.id,
                                                              self.probability,
                                                              '%')
        return string
    
    def get_args(self):
        """Build a dictionary of this event's attributes so that they can be
        passed as arguments to the event handler.
        """
        d = {}
        d['prototype'] = self.prototype
        d['script'] = self.script
        d['probability'] = self.probability
        d['event_trigger'] = self.event_trigger
        if self.condition:
            d['condition'] = self.condition
        return d
    

model_list.register(NPCEvent)