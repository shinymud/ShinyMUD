from shinymud.lib.world import World
import logging

class Battle(object):
    """A battle is a fight between two teams until one team is unable to continue.
    """
    def __init__(self):
        self.teamA = []
        self.teamB = []
        self.remove_list = []
        self.id = None
        self.log = logging.getLogger("Battle")
        self.world = World.get_world()
    active = lambda self: len(self.teamA) > 0 and len(self.teamB) > 0
    
    def perform_round(self):
        ready_characters = []
        ready_characters.extend(self.teamA)
        ready_characters.extend(self.teamB)
        for character in ready_characters:
            character.atk += 1.0
            self.log.debug("%s has %s ATK points" % (character.fancy_name(), str(character.atk)))
        while len(ready_characters) and self.active():
            # while we have someone ready to attack AND both teams are still active
            #sort the list
            ready_characters.sort(lambda x,y: -1 if (x.atk < y.atk) else 1)
            attacker = ready_characters[0]
            if attacker.next_action_cost() > attacker.atk:
                self.log.debug(attacker.fancy_name() + " has no more attacks this round")
                del ready_characters[0]
                continue
            #perform the attack
            attacker.attack()
            self.cleanup()
        self.log.debug("No more ready characters this round")
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
        self.log.debug("cleaning up %s" % str([x.fancy_name() for x in self.remove_list]))
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
        