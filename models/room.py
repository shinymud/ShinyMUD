from models import ShinyModel

class Room(ShinyModel):
    def __init__(self, area=None):
        self.id = 0
        self.items = {}
        self.exits = {'north': None,
                      'south': None,
                      'east': None,
                      'west': None}
        self.area = area
        self.title = 'New Room'
        self.description = 'This is a shiny new room!'
        self.resets = {}
        self.users = {}
    
    @classmethod
    def create(cls, area):
        """Create a new room."""
        new_room = cls(area)
        new_room.id = area.get_id('room')
        new_room.area.add_room(new_room)
        return new_room
    
    def list_me(self):
        
        room_list ="""______________________________________________
Room: 
    id: %s
    area: %s
    title: %s
    description: %s
    exits: %s
______________________________________________\n""" % (self.id, self.area.name, self.title,
                                                       self.description, str(self.exits))
        return room_list
    
    def user_add(self, user):
        self.users[user.name] = user
    
    def user_remove(self, user):
        if self.users.get(user.name):
            del self.users[user.name]
    
    def set_title(self, title):
        """Set the title of a room."""
        self.title = title
        return 'Room %s title set.\n' % self.id
    
    def set_description(self, desc):
        """Set the description of a room."""
        self.description = desc
        return 'Room %s description set.\n' % self.id
    
    def look(self):
        exit_list = [key for key, value in self.exits.items() if value != None]
        xits = 'exits: None'
        if exit_list:
            xits = 'exits: ' + ', '.join(exit_list)
        look = """%s\n%s\n%s\n""" % (self.title, xits, self.description)
        return look