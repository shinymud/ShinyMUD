
class Npc(object):
    def __init__(self, area=None, id=0, **args):
        self.area = area
        self.id = str(id)
        self.name = args.get('name', 'Shiny McShinerson')
        self.dbid = args.get('dbid')
    
    def to_dict(self):
        d = {}
        d['area'] = self.area.dbid
        d['id'] = self.id
        d['name'] = self.name
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    @classmethod
    def create(cls, area=None, npc_id=0):
        """Create a new npc"""
        new_npc = cls(area, npc_id)
        return new_npc
    
