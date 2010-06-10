from shinymud.models import Model, Column, ShinyTypes, model_list

class NPCEvent(Model):
    db_table_name = 'npc_event'
    db_columns = Model.db_columns + [
        # Prototype and script are expected to be passed in by Npc.new_event()
        # as Npc and Script objects, respectively. NPC events should not be
        # created any other way.
        Column('prototype', read=lambda x: x, write=lambda x: x.dbid,
                foreign_key=('npc', 'dbid'), null=False),
        Column('script', read=lambda x: x, write=lambda x: x.id),
        Column('event_trigger'),
        Column('condition'),
        Column('probability', read=int, write=int, default=100)
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
        passed as arguments to the event handler."""
        d = {}
        d['prototype'] = self.prototype
        d['script'] = self.script
        d['probability'] = self.probability
        d['event_trigger'] = self.event_trigger
        if self.condition:
            d['condition'] = self.condition
        return d
    

model_list.register(NPCEevent)