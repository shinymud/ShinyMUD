from shinymud.models import ShinyModel

class Room(ShinyModel):
    UNIQUE = ['area', 'id']
    save_attrs =    {   "id": [None, int],
                        "area": [None, Area],
                        "title": ["", str],
                        "description": ["", str]
                    }
    def __init__(self, area):
        self.id
        self.items = {}
        self.exits = {'north': None,
                      'south': None,
                      'east': None,
                      'west': None}
        self.area = area
        self.title = ''
        self.description = ''
        self.resets = {}
    
