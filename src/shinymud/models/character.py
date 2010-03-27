from shinymud.commands.attacks import *
from shinymud.models.item import *
import logging 



from random import randint

class IntRegister(object):
    """Keeps a dictionary of id:integer pairs, so we can keep track
    of the things affecting a particular attribute.
    """
    def __init__(self):
        self.things = {}
        self.next_id = 0
        self.changed = True
        self._calculated = None
    
    def evaluate(self, thing):
        # evaluate the value of the thing
        # This should be overloaded by baseclasses if 
        # they have something other than an int.
        return int(thing)
    
    def __getitem__(self, key):
        return self.things.get(key)
    
    def __setitem__(self, key, val):
        self.things[key] = val
        self.changed = True
    
    def append(self, val):
        self.effects[self.next_id] = val
        self.next_id += 1
        self.changed = True
    
    def __delitem__(self, key):
        if key in self.things:
            del self.things[key]
            self.changed = True
    
    def calculate(self):
        if self.changed:        
            self._calculated = 0
            for val in self.things.values():
                self._calculated += self.evaluate(val)
            self.changed = False
        return self._calculated
    

class DictRegister(IntRegister):
    """Keeps a dictionary of id:(group, val) pairs,
    and returns a dictionary of group:sum(val) pairs.
    """
    def evaluate(self, thing):
        return thing
    
    def calculate(self):
        if self.changed:
            self._calculated = {}
            for value in self.things.values():
                key, val = self.evaluate(value)
                self._calculated[key] = self._calculated.get(key) + val
        return self._calculated
    

class DamageRegister(DictRegister):
    """Special case of DictRegister, keeps dictionary of id:Damage pairs,
    and returns a dictionary of Damage.type:sum(calculated_damage) pairs.
    """
    changed = property((lambda x: True), (lambda x, y: None))
    def evaluate(self, thing):
        key = thing.type
        if thing.probability == 100 or thing.probability <= randint(1,100):
            val = randint(thing.range[0], thing.range[1])
        else:
            val = 0
        return key, val
    

class Character(object):
    """The basic functionality that both player characters (users) and 
    non-player characters share.
    """
    def characterize(self, **args):
        self.gender = str(args.get('gender', 'neutral'))
        self.hp = args.get('hp', 20)
        self.mp = args.get('mp', 5)
        self.atk = 0
        self.max_mp = args.get('max_mp', 5)
        self.max_hp = args.get('max_hp', 20)
        self.battle = None
        self._battle_target = None
        self.inventory = []
        self.equipped = {} #Stores current item in each slot from SLOT_TYPES
        for i in SLOT_TYPES.keys():
            self.equipped[i] = ''
        self.isequipped = [] #Is a list of the currently equipped items
        self._attack_queue = []
        self.hit = IntRegister()
        self.evade = IntRegister()
        self.absorb = DictRegister()
        self.damage = DamageRegister()
        self.effects = {}
        self.position = ('standing', None)
    
    def to_dict(self):
        d = {}
        d['gender'] = self.gender
        d['hp'] = self.hp
        d['mp'] = self.mp
        d['max_mp'] = self.max_mp
        d['max_hp'] = self.max_hp
        return d
    
    def __str__(self):
        return self.fancy_name()
    
    def load_inventory(self):
        pass
    
    def is_npc(self):
        """Return True if this character is an npc, false if it is not."""
        if self.char_type == 'npc':
            return True
        return False
    
    def save(self, save_dict=None):
        """Save the character to the database."""
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict(self.char_type, save_dict)
            else:    
                self.world.db.update_from_dict(self.char_type, self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict(self.char_type, 
                                                       self.to_dict())
    
    def destruct(self):
        """Remove the character from the database."""
        if self.dbid:
            self.world.db.delete('FROM %s WHERE dbid=?' % self.char_type, 
                                 [self.dbid])
    
    def item_add(self, item):
        """Add an item to the character's inventory."""
        item.owner = self.dbid
        item.save({'owner': item.owner})
        self.inventory.append(item)
    
    def item_remove(self, item):
        """Remove an item from the character's inventory."""
        if item in self.inventory:
            item.owner = None
            item.save({'owner': item.owner})
            self.inventory.remove(item)
    
    def check_inv_for_keyword(self, keyword):
        """Check all of the items in a character's inventory for a specific
        keyword. Return the item that matches that keyword, else return None.
        """
        keyword = keyword.strip().lower()
        for item in self.inventory:
            if keyword in item.keywords:
                return item
        return None
    
    def go(self, room, tell_new=None, tell_old=None):
        """Go to a specific room."""
        if self.position[0] == 'standing':
            if room:
                if self.location:
                    if tell_old:
                        self.location.tell_room(tell_old, [self.name])
                    self.location.user_remove(self)
                if self.location and self.location == room:
                    self.update_output('You\'re already there.\n')
                else:
                    self.location = room
                    self.update_output(self.look_at_room())
                    self.location.user_add(self)
                    if tell_new:
                        self.location.tell_room(tell_new, [self.name])
            else:
                self.log.debug('We gave %s a nonexistant room.' % self.name)
        else:
            self.update_output('You better stand up first.')
    
    def change_position(self, pos, furniture=None):
        """Change the user's position."""
        
        if self.position[1]:
            self.position[1].item_types['furniture'].user_remove(self)
        if furniture:
            furniture.item_types['furniture'].user_add(self)
        self.position = (pos, furniture)
        # self.log.debug(pos + ' ' + str(furniture))
    
    # Battle specific commands
    def _get_battle_target(self):
        if self in self.battle.teamA:
            other_team = self.battle.teamB
        else:
            other_team = self.battle.teamA
        if self._battle_target:
            if not self._battle_target in other_team:
                self._battle_target = other_team[0]
            self.log.debug("%s attack target: %s" % (self.fancy_name(), self._battle_target.fancy_name()))
            return self._battle_target
    
    def _set_battle_target(self, target):
        self._battle_target = target
    
    battle_target = property(_get_battle_target, _set_battle_target)
    
    def _get_next_action(self):
        if len(self._attack_queue):
            self.log.debug("next action: %s" % self._attack_queue[0].__class__.__name__)
            return self._attack_queue.pop(0)
        self.log.debug('next action: Attack')
        return Action_list['attack'](self, self.battle_target, self.battle)
    
    def _queue_attack(self, attack):
        self._attack_queue.append(attack)
    
    next_action = property(_get_next_action, _queue_attack)
    
    def next_action_cost(self):
        if len(self._attack_queue):
            self.log.debug("next action cost: %s" % str(self._attack_queue[0].cost ))
            return self._attack_queue[0].cost
        self.log.debug("next action cost %s:" % str(Action_list['attack'].cost))
        return Action_list['attack'].cost
    
    def attack(self):
        self.log.debug(self.fancy_name() + " is attacking:")
        current_attack = self.next_action
        current_attack.roll_to_hit()
    
    def free_attack(self):
        self.atk += self.next_action_cost()
        self.attack()
    
    def takes_damage(self, damages, attacker=None):
        total = 0
        absorb = self.absorb.calculate()
        for damage_type, damage in damages.items():
            d = (damage - absorb.get(damage_type, 0))
            if d >0:
                total += d
        self.log.debug("%s hit for %s damage" % (self.fancy_name(), str(total)))
        self.hp -= total
        if attacker:
            self.update_output("%s hit you for %s damage." % (attacker, str(total)))
        else:
            self.update_output("You were hit for %s damage." % str(total))
        if self.hp <= 0:
            self.battle.remove_character(self)
            self.battle = None
            self.set_mode('normal')
            self.death()
        # Call any events related to being hit or hp
        return total
    
    def enter_battle(self):
        if self.char_type == 'user':
            self.set_mode('battle')
            self.change_position('standing')
    
    def death(self):
        raise Exception("Not Implemented")
        