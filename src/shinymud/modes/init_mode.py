from shinymud.commands.commands import *
from shinymud.data.config import GAME_NAME
from shinymud.lib.ansi_codes import CONCEAL, CLEAR, COLOR_FG_RED
from shinymud.lib.world import World

import hashlib
import re
import logging

# choose_class_string = """Choose a class, or pick custom:
# Fighter    Thief      Wizard     Custom
# STR:  3    STR:  1    STR:  1    STR: ?
# DEX:  1    DEX:  3    DEX:  1    DEX: ?
# INT:  0    INT:  1    INT:  3    INT: ?
# SPD:  1    SPD:  3    SPD:  0    SPD: ?
#  HP: 35     HP: 20     HP: 20     HP: ?
#  MP:  0     MP:  0     MP:  6     MP: ?
# """

class InitMode(object):
    """InitMode is a giant state machine that handles the log-in and character
    create process.
    Each function in the InitMode class is meant to be (more or less) a single
    state in the log-in or character creation process. Each state-function
    takes care of designating which state-function gets executed next by
    setting the self.state or self.next_state functions (depending on whether
    the next state-function requires user input or not).
    -
    The difference between self.state and self.next_state:
    self.state is what gets executed by the World every turn. It cannot be
    None, or the user will no longer recieve their turn from the world.
    -
    self.next_state gets executed by self.get_input, so that self.get_input
    can guard for user input, clean it, and deliver it to whichever state
    function is stored in self.next_state.
    -
    If your state function needs user input, then self.state should point to
    self.get_input (to guard for user input each turn of the world) and 
    self.next_state should point to your state_function.
    """
    def __init__(self, user):
        """
        user - a User object that has yet to be userized (initialized)
        """
        self.user = user
        self.newbie = False
        self.state = self.get_input
        self.next_state = self.verify_username
        self.active = True
        self.name = 'InitMode'
        self.world = World.get_world()
        self.log = logging.getLogger('InitMode')
        self.save = {}
        
        intro_message = 'Type "new" if you\'re a new player. Otherwise, enter your name.'
        self.user.update_output(self.world.login_greeting + '\r\n', strip_nl=False)
        self.user.update_output(intro_message)
    
    def get_input(self):
        """Get input from the user and pass it to the appropriate function.
        
        This function waits until there is user input (we are not guaranteed
        to get user-input on each turn), then cleans up any newlines or
        whitespace and sends it to the next state-function stored in
        self.next_state.
        """
        if len(self.user.inq) > 0:
            # We've got something to work with!
            arg = self.user.inq[0].strip().replace('\r', '').replace('\n', '')
            del self.user.inq[0]
            self.next_state(arg)
    
    def verify_username(self, arg):
        """Get the name of the user logging in. If the user exists, grab their
        data and verify their password. Otherwise, start the character creation
        process.
        
        PREV STATE: None (this should be the first state function in InitMode)
        NEXT STATE: self.verify_password, if the user logging in exists, OR
                    self.verify_new_character if the user logging in is new
        """
        username = arg
        if username:
            if username.lower() == 'new':
                self.next_state = self.new_username
                self.user.update_output('Please choose a name. It should be a single word, using only letters.')
            else:
                self.username = username
                row = self.world.db.select('password,dbid FROM user WHERE name=?', [self.username])
                if row:
                    # Awesome, a user with this name does exist! Let's check their password!
                    self.password = row[0]['password']
                    self.dbid = row[0]['dbid']
                    # self.state = self.verify_password
                    self.user.update_output("Enter password: " + CONCEAL, False)
                    self.next_state = self.verify_password
                else:
                    # The user entered a name that doesn't exist.. they should create
                    # a new character or try entering the name again.
                    self.user.update_output('That user doesn\'t exist. Would you like to create a new character by the name of %s? (Yes/No)' % self.username)
                    self.next_state = self.verify_new_character
    
    def verify_password(self, arg):
        """Verify that the password provided by the user and the password from
        their database profile are correct.
        
        PREV STATE: self.verify_username
        NEXT STATE: self.character_cleanup, if the correct password was provided
                    self.verify_username, if an incorrect password was provided
        """
        password = hashlib.sha1(arg).hexdigest()
        if password == self.password:
            # Wicked cool, our user exists AND the right person is logging in
            self.user.userize(**self.world.db.select('* FROM user WHERE dbid=?', [self.dbid])[0])
            # Make sure that we clear the concealed text effect that we 
            # initiated when we moved to the password state
            self.user.update_output(CLEAR, False)
            self.state = self.character_cleanup
        else:
            self.next_state = self.verify_username
            self.user.update_output(CLEAR + "\r\nBad username or password. Enter username:")
    
    def join_world(self):
        """The final stop in our InitMode state machine! 
        We set the state of InitMode to inactive and tell the user they have 
        entered the world!
        """
        self.active = False
        self.user.update_output('\nYou have entered the world of %s.\n' % GAME_NAME, strip_nl=False)
        if self.newbie:
            newb = "Welcome, new player!\n" + COLOR_FG_RED + BOLD +\
                   'If you would like some help playing the game, type ' +\
                   '"help newbie".\n' + CLEAR
            self.user.update_output(newb, strip_nl=False)
            self.world.tell_users("%s, a new player, has entered the world." % self.user.fancy_name())
        else:
            self.world.tell_users("%s has entered the world." % self.user.fancy_name())
        if self.user.location:
            self.user.update_output(self.user.look_at_room())
            self.user.location.user_add(self.user)
    
    def character_cleanup(self):
        """This is the final stage before the user enters the world, where any
        cleanup should happen so that the user can be handed off to the main
        parse-command mode.
        
        PREV STATE: self.verify_password OR self.add_email
        NEXT STATE: self.join_world
        """
        # If the user doesn't have a location, send them to the default 
        # location that the World tried to get out of the config file
        if not self.user.location:
            self.user.location = self.world.default_location
        self.user.inq = []
        self.world.user_add(self.user)
        self.world.user_remove(self.user.conn)
        self.state = self.join_world
    
    # ************Character creation below!! *************
    def verify_new_character(self, arg):
        """A user entered a username that doesn't exist; ask if they want to
        create a new user by that name.
        
        PREV STATE: self.verify_username
        NEXT STATE: self.create_password, if the user wants to create a new character, OR
                    self.verify_username, if the user does not want to create a new character OR
                    self.new_username if the user entered an invalid username the first time
        """
        if arg.strip().lower().startswith('y'):
            if self.username.isalpha():
                self.save['name'] = self.username
                self.user.update_output('Please choose a password: ' + CONCEAL, False)
                self.password = None
                self.next_state = self.create_password
            else:
                self.user.update_output("Invalid name. Names should be a single word, using only letters.\r\n" +\
                "Choose a name: ", False)
                self.next_state = self.new_username
        else:
            self.user.update_output('Type "new" if you\'re a new player. Otherwise, enter your username.')
            self.next_state = self.verify_username
    
    def new_username(self, arg):
        """The user is choosing a name for their new character.
        
        PREV STATE: self.verify_username
        NEXT STATE: self.create_password
        """
        if arg.isalpha():
            row = self.world.db.select("dbid from user where name=?", [arg.lower()])
            if row:
                self.user.update_output('That username is already taken.\r\n')
                self.user.update_output('Please choose a username. It should be a single word, using only letters.')
            else:
                #verify here!
                self.save['name'] = arg
                self.user.update_output('Please choose a password: ' + CONCEAL, False)
                self.password = None
                self.next_state = self.create_password
        else:
            self.user.update_output("Invalid name. Names should be a single word, using only letters.\r\n" +\
            "Choose a name: ", False)
    
    def create_password(self, arg):
        """The user is choosing a password for their new character.
        
        PREV STATE: self.new_username OR self.verify_new_character
        NEXT STATE: This state will repeat until a password has been chosen and
                    confirmed, then will change to self.choose_gender
        """
        if not self.password:
            self.password = arg
            self.user.update_output(CLEAR + '\r\nRe-enter your password to confirm: ' + CONCEAL, False)
        else:
            if self.password == arg:
                self.save['password'] = hashlib.sha1(arg).hexdigest()
                self.next_state = self.choose_gender
                self.user.update_output(CLEAR + "\r\nWhat gender shall your character be? Choose from: neutral, female, or male.")
            else:
                self.user.update_output(CLEAR + '\r\nPasswords did not match.' +\
                                        '\r\nPlease choose a password: ' + CONCEAL, False)
                self.password = None
            
    
    def choose_gender(self, arg):
        """The user is choosing a gender for their new character.
        
        PREV STATE: self.create_password
        NEXT STATE: This state will repeat until a gender is chosen, then change
                    to self.add_email
        """
        if arg[0].lower() in 'mfn':
            genders = {'m': 'male', 'f': 'female', 'n': 'neutral'}
            self.save['gender'] = genders.get(arg[0])
            self.user.update_output('If you add an e-mail to this account, we can help you reset ' +\
                                    'your password if you forget it (otherwise, you\'re out of luck ' +\
                                    'if you forget!).\n' +\
                                    'Would you like to add an e-mail address to this character? ' +\
                                    '(Y/N)')
            self.next_state = self.add_email
        else:
            self.user.update_output('Please choose from male, female, or neutral:')
    
    def add_email(self, arg):
        """The user is adding (or not adding!) an email address to their new
        character.
        
        PREV STATE: self.choose_gender
        NEXT_STATE: self.character_cleanup
        """
        if arg.lower().startswith('y'):
            self.save['email'] = 'yes_email'
            self.user.update_output('We promise not to use your e-mail for evil!\n' +\
                                    'Please enter your e-mail address:')
        # We should only get to this state if the user said they want to enter their e-mail
        # address to be saved
        elif self.save.get('email') == 'yes_email':
            self.save['email'] = arg
            self.user.userize(**self.save)
            self.user.dbid = self.world.db.insert_from_dict('user', self.user.to_dict())
            # self.user.update_output(choose_class_string)
            self.state = self.character_cleanup
            self.newbie = True
        else:
            self.user.userize(**self.save)
            self.user.dbid = self.world.db.insert_from_dict('user', self.user.to_dict())
            # self.user.update_output(choose_class_string)
            self.state = self.character_cleanup
            self.newbie = True
    
    # def assign_defaults(self):
    #     if len(self.user.inq) > 0:
    #         if len(self.user.inq[0]) > 0 and self.user.inq[0][0].lower() in 'ctfw':
    #             self.user.userize(**self.save)
    #             if self.user.inq[0][0].lower() == 'c':
    #                 # Custom stats creation
    #                 self.state = self.custom_create
    #                 self.custom_points = {'left':8, 'STR':0, 'INT':0, 'DEX':0, 'SPD':0, 'HP':0, 'MP':0}
    #                 self.display_custom_create()
    #                 del self.user.inq[0]
    #                 return
    #             elif self.user.inq[0][0].lower() == 't':
    #                 # Set Thief defaults
    #                 self.user.strength = 1
    #                 self.user.dexterity = 3
    #                 self.user.intelligence = 1
    #                 self.user.speed = 3
    #                 self.user.max_hp = 20
    #                 self.user.max_mp = 0
    #                 self.user.hp = self.user.max_hp
    #                 self.user.mp = self.user.max_mp
    #             elif self.user.inq[0][0].lower() == 'f':
    #                 # Set Fighter defaults
    #                 self.user.strength = 3
    #                 self.user.dexterity = 1                
    #                 self.user.intelligence = 0
    #                 self.user.speed = 1
    #                 self.user.max_hp = 35
    #                 self.user.max_mp = 0
    #                 self.user.hp = self.user.max_hp
    #                 self.user.mp = self.user.max_mp
    #             elif self.user.inq[0][0].lower() == 'w':
    #                 # Set wizard defaults
    #                 self.user.strength = 1
    #                 self.user.dexterity = 1                
    #                 self.user.intelligence = 3
    #                 self.user.speed = 0
    #                 self.user.max_hp = 20
    #                 self.user.max_mp = 9
    #                 self.user.hp = self.user.max_hp
    #                 self.user.mp = self.user.max_mp
    #             self.state = self.character_cleanup
    #             self.user.dbid = self.world.db.insert_from_dict('user', self.user.to_dict())
    #         else:
    #             # user's input didn't make any sense
    #             del self.user.inq[0]
    #             self.user.update_output("I don't understand." + choose_class_string)
    # 
    # def display_custom_create(self):
    #     header = []
    #     header.append("You have %s points to spend:" % self.custom_points['left'])
    #     header.append("Ability:    Cost:    Effect:")
    #     for ability in ['STR', 'DEX', 'INT', 'SPD', 'HP', 'MP']:
    #         if ability == 'HP':
    #             base = 20
    #             delta = 5
    #         elif ability == 'MP':
    #             base = 0
    #             delta = 3
    #         else:
    #             base = 0
    #             delta = 1
    #         a = self.custom_points[ability]
    #         if a < 3:
    #             values = (ability," " * (14-len(ability)), '1', str(base + (a * delta)), str(base + ((a + 1) * delta)))
    #         else:
    #             values = (ability," " * (14-len(ability)), '*', str(base + (a * delta)), str(base + (a * delta)))
    #         header.append("%s%s%s      %s -> %s" % values)
    #     header.append('Choose an ability and how many points to add (up to three)')
    #     header.append('or negative numbers to remove points. Type "Done" when finished.')
    #     header.append("") # one more newline for easier to read input
    #     self.user.update_output('\n'.join(header))
    # 
    # def custom_create(self):
    #     if len(self.user.inq) > 0:
    #         m = re.match('(?P<attr>[a-zA-Z]+)[ ]*(?P<amount>-?\d+)?', self.user.inq[0])
    #         if m:
    #             attr, amount = m.group('attr', 'amount')
    #             if amount:
    #                 amount = int(amount)
    #             attr = attr.upper()
    #             if attr in self.custom_points:
    #                 new_val = self.custom_points[attr] + amount
    #                 new_balance = self.custom_points['left'] - amount
    #                 if new_val < 0 or new_val > 3 or new_balance < 0 or new_balance > 8:
    #                     self.user.update_output("You can't do that!\n")
    #                 else:
    #                     self.custom_points[attr] = new_val
    #                     self.custom_points['left'] = new_balance
    #             elif attr == 'DONE':
    #                 if self.custom_points['left'] > 0:
    #                     self.user.update_output('You still have points left to spend!')
    #                 else:
    #                     self.user.strength = self.custom_points['STR']
    #                     self.user.intelligence = self.custom_points['INT']
    #                     self.user.dexterity = self.custom_points['DEX']
    #                     self.user.speed = self.custom_points['SPD']
    #                     self.user.max_mp = 3 * int(self.custom_points['MP'])
    #                     self.user.mp = self.user.max_mp
    #                     self.user.max_hp = 20 + 5 * int(self.custom_points['HP'])
    #                     self.user.hp = self.user.max_hp
    #                     del self.user.inq[0]
    #                     self.state = self.character_cleanup
    #                     self.user.dbid = self.world.db.insert_from_dict('user', self.user.to_dict())
    #                     return
    #             else:
    #                 self.user.update_output("I don't understand.")
    #         else:
    #             self.user.update_output("I don't understand.")
    #         self.display_custom_create()
    #         del self.user.inq[0]
    
