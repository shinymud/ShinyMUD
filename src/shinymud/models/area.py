from models import ShinyModel

class Area(ShinyModel):
    
    def __init__(self, name=None, lr='All'):
        self.name = name
        self.level_range = lr
        self.builders = []
        self.description = 'No Description'
        self.rooms = {}
        self.ids = {'room': 1, 'item': 1, 'npc': 1}
    
    def add_builder(self, username):
        """Add a user to the builder's list."""
        self.builders.append(username)
    
    def remove_builder(self, username):
        """Remave a user from the builder's list."""
        if username in self.builders:
            self.builders.remove(username)
    
    def add_room(self, room):
        self.rooms[room.id] = room
    
    def get_room(self, room_id):
        return self.rooms.get(room_id)
    
    def room_exists(self, room_id):
        if room_id in self.rooms.keys():
            return True
        return False
    
    def list_me(self):
        """Print out a nice string representation of this area's attributes."""
        builders = ', '.join(self.builders)
        area_list = """______________________________________________
 Area: %s
    Level Range: %s
    Builders: %s
    Number of rooms: %s
    Description: \n        %s
______________________________________________\n""" % (self.name, 
                                                         self.level_range, 
                                                         builders.capitalize(),
                                                         str(len(self.rooms.keys())),
                                                         self.description)
        return area_list
    
    def list_rooms(self):
        names = self.rooms.keys()
        room_list = '______________________________________________\nRooms in area "%s":\n' % self.name
        for key, value in self.rooms.items():
            room_list += '    %s - %s\n' % (key, value.title)
        room_list += '______________________________________________\n'
        return room_list
    
    @classmethod
    def create(cls, name, area_list):
        if name not in area_list:
            area_list[name] = cls(name)
            return area_list[name]
        else:
            return "This area already exists.\n"
    
    def get_id(self, id_type):
        """Generate a new id for an item, npc, or room associated with this area."""
        if id_type in self.ids.keys():
            your_id = self.ids.get(id_type)
            self.ids[id_type] += 1
            return str(your_id)
    
    def set_description(self, desc):
        self.description = desc
        return 'Area description set.\n'
    
    def set_levelrange(self, lvlrange):
        self.level_range = lvlrange
        return 'Area levelrange set.\n'
