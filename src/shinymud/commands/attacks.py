from shinymud.commands import CommandRegister
from shinymud.lib.world import World
from random import randint

NORMAL_ACTION_COST = 5
FAST_ACTION_COST = 3
SLOW_ACTION_COST = 7


class BattleAction(object):
    cost = NORMAL_ACTION_COST
    def __init__(self, attacker, target, battle):
        self.attacker = attacker
        self.target = target
        self.bonuses = 0
        self.battle = battle
        self.log = World.get_world().log
    
    def roll_to_hit(self):
        # Remove the attack points for this action
        self.attacker.atk -= self.cost
        roll = randint(1,20) + self.attacker.hit.calculate() + self.bonuses - self.target.evade.calculate()
        if not (self.target in self.battle.teamA or self.target in self.battle.teamB):
            # If our attack target is no longer part of this battle (died, ran, etc)
            if self.attacker in self.battle.teamA:
                self.target = self.battle.teamB[0]
            else:
                self.target = self.battle.teamA[0]
        if roll > 20:
            self.log.debug("CRITICAL HIT!")
            self.critical()
        elif roll > 10:
            self.log.debug("Hit!")
            self.hit()
        else:
            self.log.debug("Miss!")
            self.miss()
        if not self.target.battle:
            # If the target is killed, let everyone know
            self.attacker.update_output("You kill %s!" % self.target.fancy_name())
            self.attacker.location.tell_room('%s killed %s.' % (self.attacker, self.target),
                                            [self.attacker.name, self.target.name])
            
Action_list = CommandRegister()
class Attack(BattleAction):
    def hit(self):
        """Calculates damage based on the player's damage object, (1-2 if none).
        """
        damage = self.attacker.damage.calculate()
        if not damage:
            damage = {'impact': randint(1,2)}
        total = self.target.takes_damage(damage, self.attacker.fancy_name())
        self.attacker.update_output("You attack %s for %s damage!" % (self.target.fancy_name(), str(total)))
    
    def miss(self):
        self.attacker.update_output("You attack %s but miss!" % self.target.fancy_name())
        self.target.update_output("%s tried to attack you, but missed" % (self.attacker.fancy_name()))
    
    def critical(self):
        """Critical attacks do up to twice as much damage.
        """
        base_damage = self.attacker.damage.calculate()
        if not base_damage:
            base_damage = {'impact': 3}
        damage = dict([(key, randint(int(1.5 * val + 0.5), 2* val)) for key, val in base_damage.items()])
        total = self.target.takes_damage(damage, "Critical Hit! %s" % self.attacker.fancy_name())
        self.attacker.update_output("Critical Hit! You strike %s for %s damage!" % (self.target.fancy_name(), str(total)))
    

Action_list.register(Attack, ['attack'])

class Run(BattleAction):
    cost = FAST_ACTION_COST
    def roll_to_hit(self):
        if randint(0,3):
            loc = self.attacker.location
            world = World.get_world()
            self.attacker.go(world.get_location(self.target[0], self.target[1]))
            self.battle.tell_all(self.attacker.fancy_name() + " ran away!", [self.attacker.name])
            self.attacker.mode.active = False
            self.battle.remove_character(self.attacker)
            self.attacker.battle = None
        else:
            self.attacker.update_output("You try to run, but can't get away!")
    

Action_list.register(Run, ['run'])