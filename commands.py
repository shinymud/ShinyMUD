
class CommandRegister(object):
    commands = {}
    
    def __getitem__(self, key):
        return self.commands.get(key)
    
    def register(self, func, aliases):
        for alias in aliases:
            self.commands[alias] = func
command_list = CommandRegister()

class BaseCommand(object):
    
    def __init__(self, user, args):
        self.args = args
        self.user = user
    
class Quit(BaseCommand):
    def execute(self):
        self.user.quit_flag = True
    
command_list.register(Quit, ['quit', 'exit'])

class WorldEcho(BaseCommand):
    """Echoes a message to everyone in the world.
    args:
        args = message to be sent to every user in the wold.
    """
    def execute(self):
        # This should definitely require admin privileges in the future.
        for person in self.user.world.user_list:
            self.user.world.user_list[person].update_output(self.args)

command_list.register(WorldEcho, ['wecho', 'worldecho'])

class Apocalypse(BaseCommand):
    """Ends the world. The server gets shutdown."""
    def execute(self):
        # This should definitely require admin privileges in the future.
        message = "%s has stopped the world from turning. Goodbye.\n" % self.user.get_fancy_name()
        WorldEcho(self.user, message).execute()
        
        self.user.world.shutdown_flag = True
    
command_list.register(Apocalypse, ['apocalypse'])
