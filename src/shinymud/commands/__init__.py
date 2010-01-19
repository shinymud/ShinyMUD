from shinymud.lib.world import *
# Define Permission Constants
PLAYER = 1
BUILDER = 2
DM = 4
ADMIN = 8
GOD = 16

class CommandRegister(object):
    
    def __init__(self):
        self.commands = {}
    
    def __getitem__(self, key):
        return self.commands.get(key)
    
    def register(self, func, aliases):
        for alias in aliases:
            self.commands[alias] = func
    

# Create the list of command-related Help Pages
command_help = CommandRegister()


class BaseCommand(object):
    required_permissions = PLAYER
    help = ("We Don't have a help page for this command yet."
    )
    def __init__(self, user, args, alias):
        self.args = args
        self.user = user
        self.alias = alias
        self.world = World.get_world()
        self.log = logging.getLogger('Command')
        self.allowed = True
        if not (self.user.permissions & GOD):
            if not (self.user.permissions & self.required_permissions):
                self.allowed = False
    
    def run(self):
        if self.allowed:
            self.execute()
        else:
            self.user.update_output("You don't have the authority to do that!\n")
    
    def personalize(self, actor, target, message):
        """Personalize an action message for a user.
        
        This function replaces certain keywords in generic messages with 
        user-specific data to make the message more personal. Below is a list
        of the keywords that will be replaced if they are found in the message:
        
        #actor - replaced with the name of the actor (user commiting the action)
        #a_she/he - replaced with the gender-specific pronoun of the actor
        #a_her/him - replaced with the gender-specific pronoun of the actor (grammatical alternative)
        #a_hers/his - replace with the gender-specific possessve-pronoun of the actor
        #a_her/his - replace with the gender-specific possessve-pronoun of the actor (grammatical alternative)
        
        #target - replace with the name of the target (user being acted upon)
        #t_she/he - replaced with the gender-specific pronoun of the target
        #t_her/him - replace with the gender-specific pronoun of the target (grammatical alternative)
        #t_hers/his - replace with a gender-specific possessive-pronoun of the target
        #t_her/his - replace with the gender-specific possessve-pronoun of the actor (grammatical alternative)
        """
                                                             #Examples:
        she_pronouns = {'female': 'she', 'male': 'he', 'neutral': 'it'} #she/he looks tired
        her_pronouns = {'female': 'her', 'male': 'him', 'neutral': 'it'} #Look at her/him.
        hers_possesive = {'female': 'hers', 'male': 'his', 'neutral': 'its'} #That thing is hers/his.
        her_possesive = {'female': 'her', 'male': 'his', 'neutral': 'its'} #Person lost her/his thingy.
        
        message = message.replace('#actor', actor.get_fancy_name())
        message = message.replace('#a_she/he', she_pronouns.get(actor.gender)) 
        message = message.replace('#a_her/him', her_pronouns.get(actor.gender)) 
        message = message.replace('#a_hers/his', hers_possesive.get(actor.gender))
        message = message.replace('#a_her/his', her_possesive.get(actor.gender)) 
        
        # We should always have an actor, but we don't always have a target.
        # Expect them to be able to pass None for the target
        if target:
            message = message.replace('#target', target.get_fancy_name())
            message = message.replace('#t_she/he', she_pronouns.get(target.gender))
            message = message.replace('#t_her/him', her_pronouns.get(target.gender))
            message = message.replace('#t_hers/his', hers_possesive.get(target.gender))
            message = message.replace('#t_her/his', her_possesive.get(target.gender))
        return message
    
