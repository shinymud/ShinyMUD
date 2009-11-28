from models.area import Area

class CommandRegister(object):
    commands = {}
    
    def __getitem__(self, key):
        return self.commands.get(key)
    
    def register(self, func, aliases):
        for alias in aliases:
            self.commands[alias] = func
    
# ************************ GENERIC COMMANDS ************************
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
            self.user.world.user_list[person].update_output(self.args + '\n')

command_list.register(WorldEcho, ['wecho', 'worldecho'])

class Apocalypse(BaseCommand):
    """Ends the world. The server gets shutdown."""
    def execute(self):
        # This should definitely require admin privileges in the future.
        message = "%s has stopped the world from turning. Goodbye." % self.user.get_fancy_name()
        WorldEcho(self.user, message).execute()
        
        self.user.world.shutdown_flag = True
    
command_list.register(Apocalypse, ['apocalypse', 'die'])

class Chat(BaseCommand):
    """Sends a message to every user on the chat channel."""
    def execute(self):
        if not self.user.channels['chat']:
            self.user.channels['chat'] = True
            self.user.update_output('Your chat channel has been turned on.\n')
        message = '%s chats, "%s"\n' % (self.user.get_fancy_name(), self.args)
        for person in self.user.world.user_list:
            if self.user.world.user_list[person].channels['chat']:
                self.user.world.user_list[person].update_output(message)
    
command_list.register(Chat, ['chat', 'c'])

class Channel(BaseCommand):
    """Toggles communication channels on and off."""
    def execute(self):
        toggle = {'on': True, 'off': False}
        args = self.args.split()
        channel = args[0].lower()
        choice = args[1].lower()
        if channel in self.user.channels.keys():
            if choice in toggle.keys():
                self.user.channels[channel] = toggle[choice]
                self.user.update_output('The %s channel has been turned %s.\n' % (channel, choice))
            else:
                self.user.update_output('You can only turn the %s channel on or off.\n' % channel)
        else:
            self.user.update_output('Which channel do you want to change?\n')

command_list.register(Channel, ['channel'])

class Build(BaseCommand):
    """Activate or deactivate build mode."""
    def execute(self):
        if self.args == 'exit':
            self.user.set_mode('normal')
            self.user.update_output('Exiting BuildMode.\n')
        else:
            self.user.set_mode('build')
            self.user.update_output('Entering BuildMode.\n')

command_list.register(Build, ['build'])

# ************************ BUILD COMMANDS ************************
build_list = CommandRegister()

class Create(BaseCommand):
    """Create a new item, npc, or area."""
    def execute(self):
        # creates = ['obj', 'area', 'npc', 'room']
        if not self.args:
            self.user.update_output('What do you want to create?\n')
        else:
            args = self.args.lower().split()
            if args[0] == 'area':
                # Areas need to be created with a name argument -- make sure the user has passed one
                if len(args) > 1:
                    new_area = Area.create(args[1], self.user.world.areas)
                    if type(new_area) == str:
                        self.user.update_output(new_area)
                    else:
                        self.user.mode.edit_area = new_area
                        new_area.add_builder(self.user.name)
                        self.user.update_output('New area "%s" created.\n' % new_area.name)
            else:
                self.user.update_output('You can\'t create that.\n')
    
build_list.register(Create, ['create'])

class Edit(BaseCommand):
    """Edit an area, object, npc, or room."""
    def execute(self):
        args = self.args.lower().split()
        if len(args) < 2:
            self.user.update_output('Type "help edit" to get help using this command.\n')
        else:
            if args[0] == 'area':
                if args[1] in self.user.world.areas.keys():
                    self.user.mode.edit_area = self.user.world.areas[args[1]]
                    self.user.update_output('Now editing area "%s".\n' % args[1])
                else:
                    self.user.update_output('That area doesn\'t exist. You should create it first.\n')
    

build_list.register(Edit, ['edit'])

class List(BaseCommand):
    """List the attributes of the object or area currently being edited."""
    def execute(self):
        # Let's match a regular expression to figure out what they gave us..
        message = 'Type "help list" to get help using this command.\n'
        if not self.args:
            # The user didn't give a specific item to be listed; show them the current one,
            # if there is one
            if self.user.mode.edit_object:
                message = self.user.mode.edit_object.list_me()
            elif self.user.mode.edit_area:
                message = self.user.mode.edit_area.list_me()
            else:
                message = self.user.update_output('You\'re not editing anything right now.\n')
        self.user.update_output(message)

build_list.register(List, ['list'])