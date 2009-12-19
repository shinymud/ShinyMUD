
class Npc(object):
    def __init__(self, area=None, npc_id=0):
        self.area = area
        self.id = npc_id
    
    @classmethod
    def create(cls, area=None, npc_id=0):
        """Create a new npc"""
        new_npc = cls(area, npc_id)
        return new_npc