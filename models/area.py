from models import ShinyModel

class Area(ShinyModel):
    
    def __init__(self, name, lr='All'):
        self.name = name
        self.level_range = lr
        self.builders = []
    
    
    def add_builder(self, username):
        """Add a user to the builder's list."""
        self.builders.append(username)
    
    def remove_builder(self, username):
        """Remave a user from the builder's list."""
        if username in self.builders:
            self.builders.remove(username)
    
