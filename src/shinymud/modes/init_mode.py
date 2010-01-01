from shinymud.commands import *
from shinymud.world import World
import hashlib

class InitMode(object):
    
    def __init__(self, user):
        self.user = user
        intro_message = 'Type "new" if you\'re a new player. Otherwise, enter your username.\n>'
        self.user.update_output(intro_message)
        self.state = self.verify_username
        self.inner_state = None
        self.active = True
        self.name = 'InitMode'
        self.world = World.get_world()
    
    def verify_username(self):
        if len(self.user.inq) > 0:
            username = self.user.inq[0]
            if username:
                if username == 'new':
                    self.state = self.new_username
                    self.user.update_output('Please choose a username. It should be a single word, using only letters.\n>')
                else:
                    self.username = username.replace('\n', '')
                    row = self.world.db.select('password,dbid FROM user WHERE name=?', [self.username])
                    if row:
                        # Awesome, a user with this name does exist! Let's check their password!
                        self.password = row[0]['password']
                        self.dbid = row[0]['dbid']
                        self.state = self.verify_password
                        self.user.update_output("Enter password: ")
                    else:
                        # The user entered a name that doesn't exist.. they should create
                        # a new character or try entering the name again.
                        self.user.update_output('That user doesn\'t exist. Would you like to create a new character by the name of %s? (Yes/No)\n>' % self.username)
                        self.state = self.verify_new_character
            del self.user.inq[0]
    
    def verify_password(self):
        if len(self.user.inq) > 0:
            password = hashlib.sha1(self.user.inq[0]).hexdigest()
            if password == self.password:
                # Wicked cool, our user exists AND the right person is logging in
                self.user.userize(**self.world.db.select('* FROM user WHERE dbid=?', [self.dbid])[0])
                self.state = self.character_cleanup
            else:
                self.state = self.verify_username
                self.user.update_output("Bad username or password.\nEnter username: ")
            del self.user.inq[0]
    
    def verify_new_character(self):
        if len(self.user.inq) > 0:
            if self.user.inq[0][0].lower() == 'y':
                self.user.name = self.username
                self.user.update_output('Please choose a password.\n>')
                self.state = self.create_password
            else:
                self.user.update_output('Type "new" if you\'re a new player. Otherwise, enter your username.\n>')
                self.state = self.verify_username
            del self.user.inq[0]
    
    def join_world(self):
        self.active = False
        WorldEcho(self.user, "%s has entered the world." % self.user.get_fancy_name(), ['wecho']).execute()
    
    def character_cleanup(self):
        self.user.inq = []
        self.world.user_add(self.user)
        self.world.user_remove(self.user.conn)
        self.state = self.join_world
    
    # ************Character creation below!! *************
    def new_username(self):
        if len(self.user.inq) > 0:
            username = self.user.inq[0]
            row = self.world.db.select("dbid from user where name=?", [username.lower()])
            if row:
                self.user.update_output('That username is already taken.\n')
                self.user.update_output('Please choose a username. It should be a single word, using only letters.\n>')
            else:
                #TODO: CHECK FOR VALIDITY!
                self.user.name = username
                self.user.update_output('Please choose a password.\n>')
                self.state = self.create_password
            del self.user.inq[0]
    
    def create_password(self):
        if len(self.user.inq) > 0:
            self.user.password = hashlib.sha1(self.user.inq[0]).hexdigest()
            del self.user.inq[0]
            self.user.update_output("What gender shall your character be?\n" +\
                                    "Choose from: neutral, female, or male.\n>")
            self.state = self.choose_gender
            
    
    def choose_gender(self):
        if len(self.user.inq) > 0:
            if self.user.inq[0] in ['male', 'female', 'neutral']:
                self.user.gender = self.user.inq[0]
                self.user.update_output('If you add an e-mail to this account, we can help you reset ' +\
                                        'your password if you forget it (otherwise, you\'re out of luck ' +\
                                        'if you forget!).\n' +\
                                        'Would you like to add an e-mail address to this character? ' +\
                                        '(Y/N)\n>')
                self.state = self.add_email
            else:
                self.user.update_output('Please choose from: male, female, or neutral.\n>')
            del self.user.inq[0]
    
    def add_email(self):
        if len(self.user.inq) > 0:
            if self.user.inq[0][0].lower() == 'y':
                self.inner_state = 'yes_email'
                self.user.update_output('We promise not to use your e-mail for evil ' +\
                                        '(you can type "help email" for details).\n' +\
                                        'Please enter your e-mail address:\n>')
            elif self.user.inq[0][0].lower() == 'n':
                self.state = self.assign_defaults
                self.user.email = None
                self.user.update_output('All done, now you\'re ready to play!\n')
            
            # We should only get to this state if the user said they want to enter their e-mail
            # address to be saved
            elif self.inner_state == 'yes_email':
                self.user.email = self.user.inq[0]
                self.state = self.assign_defaults
                self.user.update_output('All done, now you\'re ready to play!\n')
            else:
                self.user.update_output('This is a "yes or no" type of question. Try again:\n\n')
            del self.user.inq[0]
    
    def assign_defaults(self):
        self.user.description = 'You see nothing special about this person.'
        self.user.strength = 0
        self.user.intelligence = 0
        self.user.dexterity = 0
        self.user.channels = {'chat': True}
        self.user.inventory = []
        self.user.location = None
        self.user.dbid = self.world.db.insert_from_dict('user', self.user.to_dict())
        self.state = self.character_cleanup
    

