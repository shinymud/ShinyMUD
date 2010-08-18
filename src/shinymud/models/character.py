from shinymud.commands.attacks import *
from shinymud.data.config import EQUIP_SLOTS
from shinymud.lib.registers import IntRegister, DictRegister, DamageRegister
from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *
from random import randint
    
class Character(Model):
    """The basic functionality that both player characters (players) and 
    non-player characters share.
    """
    db_columns = Model.db_columns + [
        Column('gender', default='neutral'),
        Column('hp', type="INTEGER", default=20, read=read_int, write=int),
        Column('mp', type="INTEGER", default=5, read=read_int, write=int),
        Column('max_mp', type="INTEGER", default=5, read=read_int, write=int),
        Column('max_hp', type="INTEGER", default=20, read=read_int, write=int),
        Column('currency', type="INTEGER", default=0, read=read_int, write=int),
        Column('description', default="You see nothing special about this person.")
    ]
    def characterize(self, args={}):
        Model.__init__(self, args)
        self.atk = 0
        self.battle = None
        self._battle_target = None
        self.inventory = []
        self.equipped = {} #Stores current item in each slot from EQUIP_SLOTS
        for i in EQUIP_SLOTS.keys():
            self.equipped[i] = ''
        self.isequipped = [] #Is a list of the currently equipped items
        self._attack_queue = []
        self.hit = IntRegister()
        self.evade = IntRegister()
        self.absorb = DictRegister()
        self.damage = DamageRegister()
        self.effects = {}
        self.position = ('standing', None)
    
    def __str__(self):
        return self.fancy_name()
    
    def load_inventory(self):
        pass
    
    def is_npc(self):
        """Return True if this character is an npc, false if it is not."""
        if self.char_type == 'npc':
            return True
        return False
    
    def item_add(self, item):
        """Add an item to the character's inventory."""
        if not self.is_npc():
            # Don't save this item if it's added to an npc
            item.owner = self
            item.save()
        self.inventory.append(item)
    
    def item_remove(self, item):
        """Remove an item from the character's inventory."""
        if item in self.inventory:
            if not self.is_npc():
                # items don't get saved when they're added to npc inventories
                # Don't bother removing the owner if we're taking it out of
                # an npc's inventory
                item.owner = None
                item.save()
            self.inventory.remove(item)
    
    def has_item(self, build_item):
        """Check if the player has a GameItem in their inventory that descended
        from the given build_item prototype.
        """
        found = False
        for i in self.inventory:
            if i.build_id == build_item.id and i.build_area == build_item.area.name:
                found = True
                break
        return found
    
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
                    prev = '%s_%s' % (self.location.id, self.location.area.name)
                    if tell_old:
                        self.location.tell_room(tell_old, [self.name])
                    self.location.remove_char(self)
                else:
                    prev = 'void'
                if self.location and self.location == room:
                    self.update_output('You\'re already there.\n')
                else:
                    self.location = room
                    self.update_output(self.look_at_room())
                    self.location.add_char(self, prev)
                    if tell_new:
                        self.location.tell_room(tell_new, [self.name])
            else:
                self.world.log.debug('We gave %s a nonexistant room.' % self.name)
        else:
            self.update_output('You better stand up first.')
    
    def change_position(self, pos, furniture=None):
        """Change the player's position."""
        
        if self.position[1]:
            self.position[1].item_types['furniture'].player_remove(self)
        if furniture:
            furniture.item_types['furniture'].player_add(self)
        self.position = (pos, furniture)
        # self.world.log.debug(pos + ' ' + str(furniture))
    
    # Battle specific commands
    def _get_battle_target(self):
        if self in self.battle.teamA:
            other_team = self.battle.teamB
        else:
            other_team = self.battle.teamA
        if self._battle_target:
            if not self._battle_target in other_team:
                self._battle_target = other_team[0]
            self.world.log.debug("%s attack target: %s" % (self.fancy_name(), self._battle_target.fancy_name()))
            return self._battle_target
    
    def _set_battle_target(self, target):
        self._battle_target = target
    
    battle_target = property(_get_battle_target, _set_battle_target)
    
    def _get_next_action(self):
        if len(self._attack_queue):
            self.world.log.debug("next action: %s" % self._attack_queue[0].__class__.__name__)
            return self._attack_queue.pop(0)
        self.world.log.debug('next action: Attack')
        return Action_list['attack'](self, self.battle_target, self.battle)
    
    def _queue_attack(self, attack):
        self._attack_queue.append(attack)
    
    next_action = property(_get_next_action, _queue_attack)
    
    def next_action_cost(self):
        if len(self._attack_queue):
            self.world.log.debug("next action cost: %s" % str(self._attack_queue[0].cost ))
            return self._attack_queue[0].cost
        self.world.log.debug("next action cost %s:" % str(Action_list['attack'].cost))
        return Action_list['attack'].cost
    
    def attack(self):
        self.world.log.debug(self.fancy_name() + " is attacking:")
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
        self.world.log.debug("%s hit for %s damage" % (self.fancy_name(), str(total)))
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
        if self.char_type == 'player':
            self.set_mode('battle')
            self.change_position('standing')
    
    def death(self):
        raise Exception("Not Implemented")
    

        