from shinymud.lib.world import World
import re

class Damage(object):
    def __init__(self, dstring):
        exp = r'(?P<d_type>\w+)[ ]+(?P<d_min>\d+)-(?P<d_max>\d+)([ ]+(?P<d_prob>\d+))?'
        m = re.match(exp, dstring)
        if m and m.group('d_type') in DAMAGE_TYPES:
            self.type = m.group('d_type')
            if m.group('d_min') and m.group('d_max') and int(m.group('d_min')) <= int(m.group('d_max')):
                self.range = (int(m.group('d_min')), int(m.group('d_max')))
            else:
                raise Exception('Bad damage range.\n')
            if m.group('d_prob'):
                self.probability = int(m.group('d_prob'))
                if self.probability > 100:
                    self.probability = 100
                elif self.probability < 0:
                    self.probability = 0
            else:
                self.probability = 100
        else:
            raise Exception('Bad damage type given.\n')
    
    def __str__(self):
        return self.type + ' ' + str(self.range[0]) + '-' + str(self.range[1]) + ' ' + str(self.probability) + '%'
    

class Battle(object):
    """A battle is a fight between two teams until one team is unable to continue.
    """
    def __init__(self):
        self.teamA = []
        self.teamB = []
        self.remove_list = []
        self.id = None
        self.world = World.get_world()
    active = lambda self: len(self.teamA) > 0 and len(self.teamB) > 0
    
    def perform_round(self):
        ready_characters = []
        ready_characters.extend(self.teamA)
        ready_characters.extend(self.teamB)
        for character in ready_characters:
            character.atk += 1.0
            self.world.log.debug("%s has %s ATK points" % (character.fancy_name(), str(character.atk)))
        while len(ready_characters) and self.active():
            # while we have someone ready to attack AND both teams are still active
            #sort the list
            ready_characters.sort(lambda x,y: -1 if (x.atk < y.atk) else 1)
            attacker = ready_characters[0]
            if attacker.next_action_cost() > attacker.atk:
                self.world.log.debug(attacker.fancy_name() + " has no more attacks this round")
                del ready_characters[0]
                continue
            #perform the attack
            attacker.attack()
            self.cleanup()
        self.world.log.debug("No more ready characters this round")
        if not self.active():
            self.end_battle()

    def end_battle(self):
        self.world.battle_remove(self.id)
        for x in self.teamA if len(self.teamA) else self.teamB:
            x.battle = None
            x.set_mode('normal')
            x.update_output("You won the battle!")
    
    def remove_character(self, character):
        self.remove_list.append(character)
    
    def cleanup(self):
        self.world.log.debug("cleaning up %s" % str([x.fancy_name() for x in self.remove_list]))
        for c in self.remove_list:
            if c in self.teamA:
                self.teamA.remove(c)
            elif c in self.teamB:
                self.teamB.remove(c)
        self.remove_list = []
    
    def tell_all(self, message, exclude=[]):
        r = self.teamA[:]
        r.extend(self.teamB[:])
        for player in r:
            if player.name not in exclude:
                player.update_output(message)
        