from models import ShinyModel

class Room(ShinyModel):
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
    
