from shinymud.commands import CommandRegister
from random import randint
import logging
BASE_ATTACK_COST = 5
FAST_ATTACK_COST = 3
SLOW_ATTACK_COST = 7


class BattleAction(object):
    cost = BASE_ATTACK_COST
    def __init__(self, attacker, target, battle):
        self.attacker = attacker
        self.target = target
        self.bonuses = 0
        self.battle = battle
        self.log = logging.getLogger("BattleAction")
    
    def roll_to_hit(self):
        # Remove the attack points for this action
        self.attacker.atk -= (self.cost /(1 + (self.attacker.speed/10)))
        roll = randint(1,20) + self.attacker.hit + self.bonuses
        if not (self.target in self.battle.teamA or self.target in self.battle.teamB):
            # If our attack target is no longer part of this battle (died, ran, etc)
            if self.attacker in self.battle.teamA:
                self.target = self.battle.teamB[0]
            else:
                self.target = self.battle.teamA[0]
        if roll > self.target.evade + 10:
            self.log.debug("CRITICAL HIT!")
            self.critical()
        elif roll > self.target.evade:
            self.log.debug("Hit!")
            self.hit()
        else:
            self.log.debug("Miss!")
            self.miss()
    
Attack_list = CommandRegister()
class Punch(BattleAction):
    def hit(self):
        """Damage for a punch is based on a character's DMG bonus. Damage is 
        from 1 to 2, plus any DMG bonuses.
        """
        damage = randint(1,2) + self.attacker.dmg
        total = self.target.takes_damage({'impact':damage})
        self.attacker.update_output("You attack %s for %s damage!" % (self.target.fancy_name(), str(total)))
        self.target.update_output("%s attacks you for %s damage!" % (self.attacker.fancy_name(), str(total)))
    
    def miss(self):
        self.attacker.update_output("You attack %s but miss!" % self.target.fancy_name())
        self.target.update_output("%s tried to attack you, but missed" % (self.attacker.fancy_name()))
    
    def critical(self):
        """Critical punches do twice as much damage, and 1 to 3
        Attack points from the target due to stun.
        """
        base_damage = 1 + self.attacker.dmg
        damage = randint(base_damage, 2* (base_damage+1))
        total = self.target.takes_damage({'impact':damage})
        self.target.atk -= randint(1,3)
        self.attacker.update_output("You attack %s for %s damage!" % (self.target.fancy_name(), str(total)))
        self.target.update_output("%s attacks you for %s damage!" % (self.attacker.fancy_name(), str(total)))
    

Attack_list.register(Punch, ['punch'])

class Weapon(BattleAction):
    def hit(self):
        self.apply_damage()
    
    def critical(self):
        multiplier = getattr(self.attacker, 'critical_multiplier', 2)
        self.apply_damage(multiplier)
        # then apply any critical effects for this attacker
    
    def apply_damage(self, multiplier=1):
        wep1 = self.attacker.equipped['main-hand']
        if wep1 and 'weapon' in wep1.item_types:
            damages = {}
            bonuses = True
            for dmg in wep1.item_types.get('weapon').dmg:
                if dmg.probability == 100 or randint(1, 100) <= dmg.probability:                        
                    d = damages.get(dmg.type, 0) + randint(dmg.range[0], dmg.range[1])
                    if bonuses and dmg.type in ['slashing', 'impact', 'piercing']:
                        d += self.attacker.dmg
                        bonuses = False
                    d *= multiplier
                    damages[dmg.type] = d
            self.target.takes_damage(damages)
    

Attack_list.register(Weapon, ['weapon'])

class Run(BattleAction):
    cost = FAST_ATTACK_COST
    def roll_to_hit(self):
        if randint(0,3):
            loc = self.user.location
            self.target()
            if loc != self.user.location:
                self.attacker.mode.active = False
                self.battle.remove_character(self.user)
                self.attacker.battle = None
        else:
            self.user.update_output("You try to run, but can't get away!")
    

Attack_list.register(Run, ['run'])