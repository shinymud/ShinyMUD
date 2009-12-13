from shinymud.models import ShinyModel

class Area(ShinyModel):
    UNIQUE = ['name']
    save_attrs = {
                    'name': ['', str],
                    'level_range': ['ALL', str],
                    'builders': [[], eval]
    }
    def __init__(self, **args):
        self.rooms = {}
        super(Area, self).__init__(**args)
    
    def add_builder(self, username):
        """Add a user to the builder's list."""
        self.builders.append(username)
    
    def remove_builder(self, username):
        """Remove a user from the builder's list."""
        if username in self.builders:
            self.builders.remove(username)
    
    def list_me(self):
        """Print out a nice string representation of this area's attributes."""
        builders = ', '.join(self.builders)
        area_list = """______________________________________________
 Area: %s
        Level Range: %s
        Builders: %s
        Number of rooms: %s
______________________________________________\n""" % (self.name, 
                                                         self.level_range, 
                                                         builders.capitalize(),
                                                         str(len(self.rooms.keys())))
        return area_list
    
    @classmethod
    def create(cls, name, area_list):
        if name not in area_list:
            area_list[name] = cls(name)
            return area_list[name]
        else:
            return "This area already exists.\n"
    
