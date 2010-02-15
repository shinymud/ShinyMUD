from shinymud.commands.attacks import *
from shinymud.models.item import *
import logging 

class Character(object):
    """The basic functionality that both player characters (users) and 
    non-player characters share.
    """
    def characterize(self, **args):
        self.gender = str(args.get('gender', 'neutral'))
        self.strength = args.get('strength', 0)
        self.intelligence = args.get('intelligence', 0)
        self.dexterity = args.get('dexterity', 0)
        self.hp = args.get('hp', 0)
        self.mp = args.get('mp', 0)
        self.atk = 0
        self.max_mp = args.get('max_mp', 0)
        self.max_hp = args.get('max_hp', 20)
        self.speed = args.get('speed', 0)
        self.battle = None
        self._battle_target = None
        self._default_attack = args.get('default_attack', "punch")
        self.inventory = []
        self.equipped = {} #Stores current weapon in each slot from SLOT_TYPES
        for i in SLOT_TYPES.keys():
            self.equipped[i] = ''
        self.isequipped = [] #Is a list of the currently equipped weapons
        self._attack_queue = []
        self.absorb = {}
    
    hit = property(lambda self: self.dexterity)
    evade = property(lambda self: 8 + self.dexterity)
    dmg = property(lambda self: self.strength)
    def to_dict(self):
        d = {}
        d['gender'] = self.gender
        d['strength'] = self.strength
        d['intelligence'] = self.intelligence
        d['dexterity'] = self.dexterity
        d['speed'] = self.speed
        d['hp'] = self.hp
        d['mp'] = self.mp
        d['max_mp'] = self.max_mp
        d['max_hp'] = self.max_hp
        d['default_attack'] = self._default_attack
        return d
    
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
        self.log.debug("next action: %s" % self._default_attack.capitalize())
        return Attack_list[self._default_attack](self, self.battle_target, self.battle)
    
    def _queue_attack(self, attack):
        self._attack_queue.append(attack)
    
    next_action = property(_get_next_action, _queue_attack)
    
    def next_action_cost(self):
        if len(self._attack_queue):
            self.log.debug("next action cost: %s" % str(self._attack_queue[0].cost / (1.0 + (self.speed/10.0))))
            return self._attack_queue[0].cost/ (1.0 + (self.speed/10.0))
        self.log.debug("next action cost %s:" % str(Attack_list[self._default_attack].cost / (1.0 + (self.speed/10.0))))
        return Attack_list[self._default_attack].cost / (1.0 + (self.speed/10.0))
    
    def attack(self):
        self.log.debug(self.fancy_name() + " is attacking:")
        current_attack = self.next_action
        current_attack.roll_to_hit()
    
    def free_attack(self):
        self.atk += self.next_action_cost()
        self.attack()
    
    def takes_damage(self, damages):
        total = 0
        for damage_type, damage in damages.items():
            d = (damage - self.absorb.get(damage_type, 0))
            if d >0:
                total += d
        self.log.debug("%s hit for %s damage" % (self.fancy_name(), str(total)))
        self.hp -= total
        if self.hp <= 0:
            self.hp = 0
            self.battle.remove_character(self)
            self.set_mode('normal')
        # Call any events related to being hit or hp
        return total
    
    def enter_battle(self):
        if self.char_type == 'user':
            self.set_mode('battle')
    
