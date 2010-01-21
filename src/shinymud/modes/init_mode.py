from shinymud.commands.commands import *
from shinymud.lib.world import World
import hashlib
import re

choose_class_string = """Choose a class, or pick custom:
Fighter    Thief      Wizard     Custom
STR:  3    STR:  1    STR:  1    STR: ?
DEX:  1    DEX:  3    DEX:  1    DEX: ?
INT:  0    INT:  1    INT:  3    INT: ?
SPD:  1    SPD:  3    SPD:  0    SPD: ?
 HP: 35     HP: 20     HP: 20     HP: ?
 MP:  0     MP:  0     MP:  6     MP: ?
"""


class InitMode(object):
    
    def __init__(self, user):
        self.user = user
        intro_message = 'Type "new" if you\'re a new player. Otherwise, enter your username.>'
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
                    self.user.update_output('Please choose a username. It should be a single word, using only letters.')
                else:
                    self.username = username
                    row = self.world.db.select('password,dbid FROM user WHERE name=?', [self.username])
                    if row:
                        # Awesome, a user with this name does exist! Let's check their password!
                        self.password = row[0]['password']
                        self.dbid = row[0]['dbid']
                        self.state = self.verify_password
                        self.user.update_output("Enter password: ", False)
                    else:
                        # The user entered a name that doesn't exist.. they should create
                        # a new character or try entering the name again.
                        self.user.update_output('That user doesn\'t exist. Would you like to create a new character by the name of %s? (Yes/No)' % self.username)
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
                self.user.update_output('Please choose a password:')
                self.state = self.create_password
            else:
                self.user.update_output('Type "new" if you\'re a new player. Otherwise, enter your username.')
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
                self.user.update_output('Please choose a username. It should be a single word, using only letters.')
            else:
                #TODO: CHECK FOR VALIDITY!
                self.user.name = username
                self.user.update_output('Please choose a password.')
                self.state = self.create_password
            del self.user.inq[0]
    
    def create_password(self):
        if len(self.user.inq) > 0:
            self.user.password = hashlib.sha1(self.user.inq[0]).hexdigest()
            del self.user.inq[0]
            self.user.update_output("What gender shall your character be?\n" +\
                                    "Choose from: neutral, female, or male.")
            self.state = self.choose_gender
            
    
    def choose_gender(self):
        if len(self.user.inq) > 0:
            gender = self.user.inq[0]
            if gender in ['male', 'female', 'neutral']:
                self.user.gender = gender
                self.user.update_output('If you add an e-mail to this account, we can help you reset ' +\
                                        'your password if you forget it (otherwise, you\'re out of luck ' +\
                                        'if you forget!).\n' +\
                                        'Would you like to add an e-mail address to this character? ' +\
                                        '(Y/N)')
                self.state = self.add_email
            else:
                self.user.update_output('Please choose from: male, female, or neutral:')
            del self.user.inq[0]
    
    def add_email(self):
        if len(self.user.inq) > 0:
            if self.user.inq[0][0].lower() == 'y':
                self.inner_state = 'yes_email'
                self.user.update_output('We promise not to use your e-mail for evil ' +\
                                        '(you can type "help email" for details).\n' +\
                                        'Please enter your e-mail address:')
            elif self.user.inq[0][0].lower() == 'n':
                self.state = self.assign_defaults
                self.user.email = None
                self.user.update_output(choose_class_string)
            
            # We should only get to this state if the user said they want to enter their e-mail
            # address to be saved
            elif self.inner_state == 'yes_email':
                self.user.email = self.user.inq[0]
                self.state = self.assign_defaults
                self.user.update_output(choose_class_string)
            else:
                self.user.update_output('This is a "yes or no" type of question. Try again:')
            del self.user.inq[0]
    
    def assign_defaults(self):
        if len(self.user.inq) > 0:
            if len(self.user.inq[0]) > 0 and self.user.inq[0][0].lower() in 'ctfw':
                self.user.channels = {'chat': True}
                self.user.inventory = []
                self.user.location = None
                self.user.permissions = 1
                self.user.description = 'You see nothing special about this person.'
                if self.user.inq[0][0].lower() == 'c':
                    # Custom stats creation
                    self.state = self.custom_create
                    self.custom_points = {'left':8, 'STR':0, 'INT':0, 'DEX':0, 'SPD':0, 'HP':0, 'MP':0}
                    self.display_custom_create()
                    del self.user.inq[0]
                    return
                elif self.user.inq[0][0].lower() == 't':
                    # Set Thief defaults
                    self.user.strength = 1
                    self.user.dexterity = 3
                    self.user.intelligence = 1
                    self.user.speed = 3
                    self.user.max_hp = 20
                    self.user.max_mp = 0
                    self.user.hp = self.user.max_hp
                    self.user.mp = self.user.max_mp
                elif self.user.inq[0][0].lower() == 'f':
                    # Set Fighter defaults
                    self.user.strength = 3
                    self.user.dexterity = 1                
                    self.user.intelligence = 0
                    self.user.speed = 1
                    self.user.max_hp = 35
                    self.user.max_mp = 0
                    self.user.hp = self.user.max_hp
                    self.user.mp = self.user.max_mp
                elif self.user.inq[0][0].lower() == 'w':
                    # Set wizard defaults
                    self.user.strength = 1
                    self.user.dexterity = 1                
                    self.user.intelligence = 3
                    self.user.speed = 0
                    self.user.max_hp = 20
                    self.user.max_mp = 9
                    self.user.hp = self.user.max_hp
                    self.user.mp = self.user.max_mp
                self.state = self.character_cleanup
                self.user.dbid = self.world.db.insert_from_dict('user', self.user.to_dict())
            else:
                # user's input didn't make any sense
                del self.user.inq[0]
                self.user.update_output("I don't understand." + choose_class_string)
    
    def display_custom_create(self):
        header = []
        header.append("You have %s points to spend:" % self.custom_points['left'])
        header.append("Ability:    Cost:    Effect:")
        for ability in ['STR', 'DEX', 'INT', 'SPD', 'HP', 'MP']:
            if ability == 'HP':
                base = 20
                delta = 5
            elif ability == 'MP':
                base = 0
                delta = 3
            else:
                base = 0
                delta = 1
            a = self.custom_points[ability]
            if a < 3:
                values = (ability," " * (14-len(ability)), '1', str(base + (a * delta)), str(base + ((a + 1) * delta)))
            else:
                values = (ability," " * (14-len(ability)), '*', str(base + (a * delta)), str(base + (a * delta)))
            header.append("%s%s%s      %s -> %s" % values)
        header.append('Choose an ability and how many points to add (up to three)')
        header.append('or negative numbers to remove points. Type "Done" when finished.')
        header.append("") # one more newline for easier to read input
        self.user.update_output('\n'.join(header))
    
    def custom_create(self):
        if len(self.user.inq) > 0:
            m = re.match('(?P<attr>[a-zA-Z]+)[ ]*(?P<amount>-?\d+)?', self.user.inq[0])
            if m:
                attr, amount = m.group('attr', 'amount')
                if amount:
                    amount = int(amount)
                attr = attr.upper()
                if attr in self.custom_points:
                    new_val = self.custom_points[attr] + amount
                    new_balance = self.custom_points['left'] - amount
                    if new_val < 0 or new_val > 3 or new_balance < 0 or new_balance > 8:
                        self.user.update_output("You can't do that!\n")
                    else:
                        self.custom_points[attr] = new_val
                        self.custom_points['left'] = new_balance
                elif attr == 'DONE':
                    if self.custom_points['left'] > 0:
                        self.user.update_output('You still have points left to spend!')
                    else:
                        self.user.strength = self.custom_points['STR']
                        self.user.intelligence = self.custom_points['INT']
                        self.user.dexterity = self.custom_points['DEX']
                        self.user.speed = self.custom_points['SPD']
                        self.user.max_mp = 3 * int(self.custom_points['MP'])
                        self.user.mp = self.user.max_mp
                        self.user.max_hp = 20 + 5 * int(self.custom_points['HP'])
                        self.user.hp = self.user.max_hp
                        del self.user.inq[0]
                        self.state = self.character_cleanup
                        self.user.dbid = self.world.db.insert_from_dict('user', self.user.to_dict())
                        return
                else:
                    self.user.update_output("I don't understand.")
            else:
                self.user.update_output("I don't understand.")
            self.display_custom_create()
            del self.user.inq[0]
    
