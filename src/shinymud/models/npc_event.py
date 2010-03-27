from shinymud.lib.world import World

class NPCEvent(object):
    
    def __init__(self, **args):
        self.prototype = args.get('prototype')
        self.probability = args.get('probability')
        self.event_trigger = args.get('event_trigger')
        self.script = args.get('script')
        self.condition = args.get('condition')
        self.dbid = args.get('dbid')
    
    def to_dict(self):
        d = {}
        d['prototype'] = self.prototype.dbid
        d['script'] = self.script.dbid
        d['probability'] = self.probability
        d['event_trigger'] = self.event_trigger
        if self.condition:
            d['condition'] = self.condition
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
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
        d = self.to_dict()
        d['script'] = self.script
        return d
    
    def save(self, save_dict=None):
        """Save this npc_event to the database."""
        world = World.get_world()
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('npc_event', save_dict)
            else:    
                world.db.update_from_dict('npc_event', self.to_dict())
        else:
            self.dbid = world.db.insert_from_dict('npc_event', self.to_dict())
    
    def destruct(self):
        """Remove this npc_event from the database."""
        world = World.get_world()
        if self.dbid:
            world.db.delete('FROM npc_event WHERE dbid=?', [self.dbid])
    
