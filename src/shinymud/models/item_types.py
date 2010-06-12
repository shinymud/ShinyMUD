from shinymud.data.config import EQUIP_SLOTS, DAMAGE_TYPES
from shinymud.models import Column, model_list
from shinymud.models.shiny_types import *
from shinymud.lib.world import World
from shinymud.models.char_effect import *

import re

class ItemType(Model):
    db_columns = Model.db_columns + [
        Column('build_item', type="INTEGER", read=int, write=int, foreign_key=('build_item','dbid'), cascade="ON DELETE"),
        Column('game_item', type="INTEGER", read=int, write=int, foreign_key=('game_item','dbid'), cascade="ON DELETE")
    ]
    log = World.get_world().log
    """The base class that must be inherited by all item types.
     
    If you're going to build a new item type, the first stop is to inherit from
    this class and implement its required functions (explained below!).
    """
    def __init__(self, args={}):
        """ An ItemType's __init__ function should take a dictionary of keyword
        arguments which could be empty (if this is a brand new instance), or hold
        the saved values of your attributes loaded from the database.
        Your init function should look something like the following:
         
        # initialize your class-specific attributes:
        self.foo = args.get('foo', 'My default foo value.')
        self.bar = args.get('bar', 'My default bar value.')
        """
        raise ItemTypeInterfaceError('You need to implement the init function.')
    
    def to_dict(self):
        """To dict converts all of the item type's attributes that aught to be
        saved to the database into a dictionary, with the name of the attribute
        being the key and its value being the value.
         
        to_dict takes no arguments, and should return a dictionary.
        the code for a to_dict function aught to look something like the following:
         
        d = {}
        if self.dbid:
            d['dbid'] = self.dbid
        if self.game_item:
            d['game_item'] self.game_item.dbid
        if self.build_item:
            d['build_item'] = self.build_item.dbid
        # The names of your attributes must be the same as the ones specified
        # in the schema.
        d['foo'] = self.foo
        d['bar'] = self.bar
        return d
        """
        raise ItemTypeInterfaceError('You need to implement the to_dict function.')
    
    def save(self, save_dict=None):
        """The save function saves this ItemType to the database.
         
        If passed a save_dict, the save function should only save the data
        specified in the dictionary to the database. If save_dict is somehow
        empty or None, the entire instance should be saved to the database.
        Your save function should look like the following:
         
        world = World.get_world()
        if self.dbid:
            # This item has a dbid, so it already exists in the database. We just
            # need to update it.
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('table_name', save_dict)
            else:    
                world.db.update_from_dict('table_name', self.to_dict())
        else:
            # This ItemType doesn't exist in the database if it doesn't have a dbid
            # yet, so we need to insert it and save its new dbid
            self.dbid = world.db.insert_from_dict('table_name', self.to_dict())
        """
        raise ItemTypeInterfaceError('You need to implement the save function.')
    
    def load(self, game_item):
        """The load function makes a copy of a ItemType instance so that it can
        be attached to a GameItem and loaded in-game.
         
        Your load function should look something like the following:
        # The easiest way to copy the data from this instance is to use the
        # to_dict function to get a dictionary of all of this item type's
        # attributes
        d = self.to_dict()
        # Delete the previous instance's dbid from the dictionary - we don't
        # want to save over the old one!
        if 'dbid' in d:
            del d['dbid']
        # Remove the old build_item reference -- this copy belongs to a game
        # item
        if 'build_item' in d:
            del d['build_item']
        d['game_item'] = game_item
        return Furniture(d)
        """
        raise ItemTypeInterfaceError('You need to implement the load function.')
    
    def __str__(self):
        """Return a string representation of this item type to be displayed
        during BuildMode.
         
        To be consistent throughout BuildMode, It should have a heading in all
        caps, and each of its attributes labeled and indented by two spaces
        beneath it. 
        The string returned should look something like the following:
         
        ITEMTYPE ATTRIBUTES:
          foo: The value of the foo attribute
          bar: The value of the bar attribute
        """
        raise ItemTypeInterfaceError('You need to implement the str function.')
    
    
    # ****************************************************************************
    # THE FUNCTIONS BELOW THIS POINT ARE NOT MEANT TO BE IMPLEMENTED BY SUBCLASSES
    # ****************************************************************************
    
    def _set_build_item(self, val):
        """This handles setting the build_item attribute.
        Because bad things happen when an ItemType has both its build_item
        and its game_item set, we won't allow on to be set if the other exists.
        THIS FUNCTION SHOULD NOT BE IMPLEMENTED/OVERLOADED BY THE CHILD CLASS.
        """
        if self.game_item:
            self.log.critical('Trying to set build_item when game_item is set!')
            # raise Exception('Cannot set build_item AND game_item')
        else:
            self._build_item = val
    
    def _set_game_item(self, val):
        """This handles setting the game_item attribute.
        Because bad things happen when an ItemType has both its build_item
        and its game_item set, we won't allow on to be set if the other exists.
        THIS FUNCTION SHOULD NOT BE IMPLEMENTED/OVERLOADED BY THE CHILD CLASS.
        """
        if self.build_item:
            self.log.critical('Trying to set game_item when build_item is set!')
            # raise Exception('Cannot set game_item AND build_item')
        else:
            self._game_item = val
    
    build_item = property((lambda self: getattr(self, '_build_item', None)),
                            _set_build_item)
    
    game_item = property((lambda self: getattr(self, '_game_item', None)),
                            _set_game_item)

class ItemTypeInterfaceError(Exception):
    """Raise this error if the ItemType interface hasn't been properly
    implemented.
    """
    pass

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
    

class Equippable(ItemType):
    plural = 'equippable items'
    db_columns = ItemType.db_columns + [
        Column('equip_slot'),
        Column('hit', type="INTEGER", read=int, write=int, default=0),
        Column('evade', type="INTEGER", read=int, write=int, default=0),
        Column('absorb', read=Equippable.read_absorb, write=Equippable.write_absorb, copy=copy_dict),
        Column('dmg', read=Equippable.read_damage, write=Equippable.write_damage, copy=lambda d: [Damage(str(x)) for x in d ))
        Column('is_equipped', read=to_bool, default=False)
    ]
    
    def __init__(self, args={}):
        ItemType.__init__(self, args)
        self.hit_id = None
        self.evade_id = None
        self.absorb_ids = []
        self.dmg_ids = []
    
    @classmethod
    def read_absorb(cls, val):
        d = {}
        if val:
            for a in val.split(','):
                key, val = a.split('=')
                d[key] = int(val)
        return d
    
    @classmethod
    def write_absorb(cls, val):
        s = []
        if val:
            for key, val in val.items():
                s.append("%s=%s" % (str(key), str(val)))
        return ",".join(s)
    
    @classmethod
    def read_damage(cls, val):
        dmg = []
        if val:
            for d in val.split('|'):
                dmg.append(Damage(d))
        return dmg
    
    @classmethod
    def write_damage(cls, val):
        return '|'.join([str(d) for d in val])
    
    def build_set_damage(self, params, player=None):
        if not params:
            return 'Sets a damage type of an equippable item.\nExample: set damage slashing 1-4 100%\n'
        exp = r'((?P<index>\d+)[ ]+)?(?P<params>.+)'
        m = re.match(exp, params)
        #if not m:
        #    return 'What damage do you want to set?'
        if m.group('index'):
            index = int(m.group('index'))
            if index < 1:
                return 'I can\'t set that!'
        else:
            index = 1
        try:
            dmg = Damage(m.group('params'))
        except Exception, e:
            return str(e)
        else:
            if len(self.dmg) < index:
                self.dmg.append(dmg)
            else:
                self.dmg[index - 1] = dmg
        self.save()
        # world = World.get_world()
        # world.db.update_from_dict('equippable', self.to_dict())
        return 'damage ' + str(index) + ' set.\n'
    
    def build_set_equip(self, loc, player=None):
        """Set the equip location for this item."""
        if loc in EQUIP_SLOTS.keys():
            self.equip_slot = loc
            self.save({'equip_slot': self.equip_slot})
            return 'Item equip location set.\n'
        else:
            return 'That equip location doesn\'t exist.\n'
    
    def build_add_damage(self, params):
        #Currently broken will be fixed when the add class in commands is updated.
        if not params:
            return 'What damage would you like to add?\n'
        try:
            self.dmg.append(Damage(params))
            self.save()
            # world = World.get_world()
            # world.db.update_from_dict('equippable', self.to_dict())
            return 'damage has been added.\n'
        except Exception, e:
            return str(e)
    
    def build_set_hit(self, params):
        self.hit = self.parse_value(params) or 0
        self.save({'hit': self.hit})
        return "set hit to " + str(self.hit)
    
    def build_set_evade(self, params):
        self.evade = self.parse_value(params) or 0
        self.save({'evade': self.evade})
        return "set evade to " + str(self.evade)
    
    def build_add_absorb(self, params):
        # params should be of the form "absorb_type amount"
        exp = r'(?P<absorb_type>\w+)[ ]+(?P<amount>[^ ]+)'
        m = re.match(exp, params)
        if not m:
            return "what type of damage does this absorb?"
        absorb_type = m.group('absorb_type')
        if absorb_type not in DAMAGE_TYPES:
            return "what type of damage does this absorb?"
        amount = self.parse_value(m.group('amount'))
        if not amount:
            if absorb_type in self.absorb:
                del self.absorb[absorb_type]
                return "items absorbs 0 %s damage" % absorb_types
            return "how much damage does this absorb?"
        self.absorb[absorb_type] = int(amount)
        self.save()
        return 'item absorbs %s %s damage' % (str(self.absorb[absorb_type]), absorb_type)
    
    build_set_absorb = build_add_absorb # alias these to be the same
    def parse_value(self, params):
        exp = r'(-(?P<penalty>)\d+)|(\+?(?P<bonus>\d+))'
        m = re.match(exp, params)
        if not m:
            return None
        if m.group('bonus'):
            return int(m.group('bonus')) or None
        elif m.group('penalty'):
            return -int(m.group('penalty')) or None
        else:
            return None
    
    def __str__(self):
        string = 'EQUIPPABLE ATTRIBUTES:\n' +\
            '  equip location: ' + str(self.equip_slot) + '\n' + \
            '  hit: ' + str(self.hit) + '\n' +\
            '  evade: ' + str(self.evade) + '\n' +\
            '  absorb:\n'
            
        dstring =  '    %s: %s\n' 
        keys = self.absorb.keys()
        keys.sort() # Keep them in the same order, visually.
        for k in keys:
            string += dstring % (k, str(self.absorb[k]))
        string += '  damage: \n'
        for dmg in range(len(self.dmg)):
            string += dstring % (str(dmg + 1), str(self.dmg[dmg]) )
        return string
    
    def load(self, game_item):
        e = Equippable(self.copy_save_attrs())
        e.build_item = None
        e.game_item = game_item
        return e
    
    def on_equip(self):
        #only Inventory items can be equipped, so make sure
        # this is an Inventory itemtype.
        if not self.game_item or not self.game_item.owner:
            return
        if self.hit:
            self.hit_id = self.game_item.owner.hit.append(self.hit)
            self.log.debug('hit_id:  %s' % str(self.hit_id))
        if self.evade:
            self.evade_id = self.game_item.owner.evade.append(self.evade)
            self.log.debug('evade_id:  %s' % str(self.evade_id))
        if self.absorb:
            for key, val in self.absorb.items():
                if val:
                    self.absorb_ids.append(self.game_item.owner.absorb.append((key, val)))
            self.log.debug('absorb_ids: %s' % str(self.absorb_ids))
        if self.dmg:
            for d in self.dmg:
                self.dmg_ids.append(self.game_item.owner.damage.append(d))
            self.log.debug('dmg_ids: %s' % str(self.dmg_ids))    
        self.is_equipped = True
        self.save()
    
    def on_unequip(self):
        if (not self.game_item) or (not self.game_item.owner) or (not self.is_equipped):
            self.log.debug('unequip: nothing to do')
            return
        self.log.debug('hit_id:  %s' % str(self.hit_id))
        if self.hit_id is not None:
            del self.game_item.owner.hit[self.hit_id]
            self.hit_id = None
        self.log.debug('evade_id:  %s' % str(self.evade_id))
        if self.evade_id is not None:
            del self.game_item.owner.evade[self.evade_id]
            self.evade_id = None
        self.log.debug('absorb_ids: %s' % str(self.absorb_ids))
        for a_id in self.absorb_ids:
            del self.game_item.owner.absorb[a_id]
        self.absorb_ids = []
        self.log.debug('dmg_ids: %s' % str(self.dmg_ids))
        for d_id in self.dmg_ids:
            del self.game_item.owner.damage[d_id]
        self.dmg_ids = []
        self.is_equipped = False
        self.save()
        
    def build_remove_damage(self, index):
        if len(self.dmg) == 0:
            return "this item does not do any damage"
        elif not index and len(self.dmg) > 1:
            return 'which damage would you like to remove?'
        elif len(self.dmg) == 1:
            del self.dmg[0]
            self.save()
            return "damage removed"
        else:
            index = int(index)
            if index <= len(self.dmg) and index > 0:
                del self.dmg[index -1]
                self.save()
                return "damage removed"
            return "you must specify which damage to remove: 1 - %s" % str(len(self.dmg))
                # world.db.update_from_dict('equippable', self.to_dict())
    

class Food(ItemType):
    food_verbs = {'food': 'eat', 'drink': 'drink from'}
    plural = 'food'
    db_table_name = 'food'
    db_columns = ItemType.db_columns + [
        Column('food_type', read=lambda f: f if f in ('food','drink') else 'food'),
        Column('ro_id', type="INTEGER", read=int, write=int),
        Column('ro_area'),
        Column('actor_use_message', null=False, default=''),
        Column('room_use_message', null=False, default=''),
        
        
    ]
    def __init__(self, args={}):
        ItemType.__init__(self, args)
        self.effects = {}

    def load_extras(self):
        pass
        # rows = world.db.select('* FROM char_effect WHERE item_type=? AND dbid=?',
        #                       ['food', self.dbid])
        # for e in rows:
        #     e['build_item'] = self
        #     effect = EFFECTS[e['name']](**e)
        #     self.effects[effect.name] = effect
    
    def _resolve_ro(self):
        if getattr(self, '_ro', None):
            return self._ro
        try: 
            self.replace_obj = self.world.get_area(self.ro_area).get_item(self.ro_id)
            return self._ro
        except:
            return None
    
    def _set_ro(self, ro):
        self._ro = ro
    
    replace_obj = property(_resolve_ro, _set_ro)
    
    def __str__(self):
        if self.replace_obj:
            rep = '%s (id:%s, area:%s)' % (self.replace_obj.name,
                                           self.replace_obj.id,
                                           self.replace_obj.area.name)
        else:
            rep = 'Nothing.'
        if self.effects:
            effects = ('\n'.ljust(18)).join(['%s (%s)' % (e, str(d.duration)) for e, d in self.effects.items()])
        else:
            effects = 'None.'
        string = 'FOOD ATTRIBUTES:' + '\n' +\
                 '  Food_type: ' + self.food_type + '\n' +\
                 '  Replace with: ' + rep + '\n' +\
                 '  use message (actor): ' + self.get_actor_message() + '\n' +\
                 '  use message (room): ' + self.get_room_message() + '\n' +\
                 '  on-eat effects: ' + effects + '\n'
        return string
    
    def load(self, game_item):
        d = self.to_dict()
        if 'dbid' in d:
            del d['dbid']
        if 'build_item' in d:
            del d['build_item']
        d['game_item'] = game_item
        new_f = Food(d)
        # FIXME: This code is super hacky, bloody fix it when 
        # character effects gets refactored
        effects = {}
        for e in self.load_effects():
            e.item = new_f
            effects[e.name] = e
        new_f.effects = effects
        return new_f
    
    def load_effects(self):
        """Return a list of copies of this food item's effects."""
        return [] # TODO: fix character effects.
        e = [effect.copy() for effect in self.effects.values()]
        return e
    
    def build_add_effect(self, args):
        """Add an effect to this food item that will be transferred to the
        player when the item is eaten.
        """
        # TODO: fix character effects
        return "sorry, we're still working on effects."
        if not args:
            return 'Type "help effects" for help on this command.'
        exp = r'(?P<effect>\w+)([ ]+(?P<duration>\d+))'
        match = re.match(exp, args.lower().strip())
        if not match:
            return 'Type "help effects" for help on this command.'
        e, dur = match.group('effect', 'duration')
        if e in self.effects:
            self.effects[e].destruct()
            del self.effects[e]
        effect = EFFECTS[e]
        if not effect:
            return '%s is not a valid effect. Try "help list effects"' % e
        eff = effect(**{'duration': int(dur), 'item_type': 'food',
                        'item': self})
        eff.save()
        self.effects[e] = eff
        return '%s effect added.' % e.capitalize()
    
    def build_remove_effect(self, args):
        """Remove an effect from this item."""
        # TODO: fix character effects
        return "sorry, we're still working on effects."
        if not args:
            return 'Which effect did you want to remove?'
        if args not in self.effects:
            return 'This item doesn\'t have that effect.'
        self.effects[args].destruct()
        del self.effects[args]
        return '%s effect removed.' % args.capitalize()
    
    def get_actor_message(self):
        if self.actor_use_message:
            return self.actor_use_message
        item = self.build_item or self.game_item
        if self.food_type == 'food':
            m = 'You eat %s.' % (item.name)
        else:
            m = 'You drink from %s.' % (item.name)
        return m
    
    def get_room_message(self):
        if self.room_use_message:
            return self.room_use_message
        item = self.build_item or self.game_item
        if self.food_type == 'food':
            m = '#actor eats %s.' % (item.name)
        else:
            m = '#actor drinks from %s.' % (item.name)
        return m
    
    def build_set_food_type(self, use, player=None):
        """Set the verb used to consume the object."""
        if not use or (use.lower().strip() not in ['food', 'drink']):
            return 'Valid values for food_type are "food" or "drink".'
        self.food_type = use.lower().strip()
        self.save({'food_type': self.food_type})
        return 'Food_type is now set to %s.' % use
    
    def build_set_replace(self, replace, player=None):
        world = World.get_world()
        if not replace or (replace.strip().lower() == 'none'):
            self.replace_obj = None
            self.save({'ro_id': '', 'ro_area': ''})
            return 'Replace item reset to none.'
        exp = r'((to)|(with)[ ]?)?(item[ ]+)?(?P<id>\d+)([ ]+from)?([ ]+area)?([ ]+(?P<area_name>\w+))?'
        match = re.match(exp, replace, re.I)
        if not match:
            return 'Try "help food" for help on setting food attributes.'
        item_id, area_name = match.group('id', 'area_name')
        if area_name:
            area = world.get_area(area_name)
            if not area:
                return 'Area %s doesn\'t exist.' % area_name
        elif player:
            area = player.mode.edit_area
        else:
            return 'You need to specify the area that the item is from.'
        item = area.get_item(item_id)
        if not item:
            'Item %s doesn\'t exist.' % item_id
        self.replace_obj = item
        self.save({'ro_id': item.id, 'ro_area': item.area.name})
        return '%s will be replaced with %s when consumed.' %\
                (self.build_item.name.capitalize(), item.name)
    
    def build_set_actor_message(self, message, player=None):
        self.actor_use_message = message or ''
        self.save({'actor_use_message': self.actor_use_message})
        if not message:
            return 'Use message (actor) has been reset to the default.'
        return 'Use message (actor) has been set.'
    
    def build_set_room_message(self, message, player=None):
        self.room_use_message = message or ''
        self.save({'room_use_message': self.room_use_message})
        if not message:
            return 'Use message (room) has been reset to the default.'
        return 'Use message (room) has been set.'
    

class Container(ItemType):
    plural = 'containers'
    db_table_name = 'container'
    db_columns = ItemType.db_columns + [
        Column('weight_capacity', type="NUMBER", read=float),
        Column('build_item_capacity', type="INTEGER", read=int, write=int),
        Column('weight_reduction', type="INTEGER", read=int, write=int, default=0),
        Column('openable', read=to_bool, default=False),
        Column('closed', read=to_bool, default=False),
        Column('locked', read=to_bool, defult=False),
        Column('key_area'),
        Column('key_id')
    ]
    def __init__(self, args={}):
        ItemType.__init__(self, args)
        self.inventory = []
    
    def _resolve_key(self):
        if getattr(self,'_key', None):
            return self._key
        try: 
            self.key = self.world.get_area(self.key_area).get_item(self.key_id)
            return self._key
        except:
            return None
    
    def _set_key(self, key):
        self._key = key
    
    key = property(_resolve_key, _set_key)
        
    def __str__(self):
        key = 'None'
        if self.key:
            key = '%s (id: %s from area: %s)' % (self.key.name, self.key.id, self.key.area.name)
        string = 'CONTAINER ATTRIBUTES:\n' +\
                 '  weight capacity: ' + str(self.weight_capacity) + '\n' +\
                 '  item capacity: ' + str(self.build_item_capacity) + '\n' +\
                 '  weight reduction: ' + str(self.weight_reduction) + '%\n' +\
                 '  openable: ' + str(self.openable) + '\n' +\
                 '  closed: ' + str(self.closed) + '\n' +\
                 '  locked: ' + str(self.locked) + '\n' +\
                 '  key: ' + key + '\n'
        return string
        
    def save(self):
        ItemType.save(self)
        for item in self.inventory:
            if item.container != self.game_item:
                item.container = self.game_item
            item.save()
    
    def load(self, game_item):
        d = self.copy_save_attrs()
        if 'dbid' in d:
            del d['dbid']
        if 'build_item' in d:
            del d['build_item']
        d['game_item'] = game_item
        return Container(d)
    
    def destroy_inventory(self):
        for item in self.inventory:
            item.destruct()
    
    def item_add(self, item):
        self.inventory.append(item)
        if self.game_item.dbid and (item.container != self.game_item):
            item.container = self.game_item
            item.save({'container': item.container.dbid})
        return True
    
    def item_remove(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
            item.container = None
            if self.game_item.dbid:
                item.save({'container':item.container})
    
    def get_item_by_kw(self, keyword):
        for item in self.inventory:
            if keyword in item.keywords:
                return item
        return None
    
    def display_inventory(self):
        if self.closed:
            return '%s is closed.\n' % self.game_item.name.capitalize()
        i = ''
        for item in self.inventory:
            i += '  ' + item.name + '\n'
        if not i:
            return '%s is empty.\n' % self.game_item.name.capitalize()
        return '%s contains:\n%s' % (self.game_item.name.capitalize(), i)
    
    def build_set_openable(self, args, player=None):
        boolean = to_bool(args)
        if not boolean:
            return 'Acceptable values for this attribute are true or false.'
        else:
            self.openable = boolean
            self.save({'openable': self.openable})
            return 'Openable has been set to %s.' % boolean
    
    def build_set_closed(self, args, player=None):
        boolean = to_bool(args)
        if not boolean:
            return 'Acceptable values for this attribute are true or false.'
        else:
            self.closed = boolean
            self.save({'closed': self.closed})
            return 'Closed has been set to %s.' % boolean
    
    def build_set_key(self, args, player=None):
        return 'Not implemented yet.'
    
    def build_set_locked(self, args, player=None):
        return 'Not implemented yet.'
    

class Furniture(ItemType):
    plural = 'furniture'
    db_table_name = 'furniture'
    db_columns = ItemType.db_columns + [
        # TODO: fix character effects
        Column('sit_effects', read=lambda x: [], write=write_list, copy=lambda x: []),
        Column('sleep_effects', read=lambda x: [], write=write_list, copy=lambda x: []),
        Column('capacity', type="INTEGER", read=int, write=int),
    ]
    def __init__(self, args={}):
        ItemType.__init__(self, args)
        self.players = []
    
    def __str__(self):
        if self.sit_effects:
            sit_effects = ', '.join(self.sit_effects)
        else:
            sit_effects = 'None'
        if self.sleep_effects:
            sleep_effects = ', '.join(self.sit_effects)
        else:
            sleep_effects = 'None'
            
        string = 'FURNITURE ATTRIBUTES:\n' +\
                 '  sit effects: ' + sit_effects + '\n' +\
                 '  sleep effects: ' + sleep_effects + '\n' +\
                 '  capacity: ' + str(self.capacity) + '\n'
        return string
    
    def load(self, game_item):
        d = self.to_dict()
        if 'dbid' in d:
            del d['dbid']
        if 'build_item' in d:
            del d['build_item']
        d['game_item'] = game_item
        return Furniture(d)
    
    def player_add(self, player):
        if self.capacity:
            pass
        else:
            self.players.append(player)
            return True
    
    def player_remove(self, player):
        if player in self.players:
            self.players.remove(player)
    

class Portal(ItemType):
    plural = 'portals'
    db_table_name = 'portal'
    db_columns = ItemType.db_columns + [
        Column('leave_message', default="#actor enters a portal."),
        Column('entrance_message', default="You enter a portal."),
        Column('emerge_message', default="#actor steps out of a shimmering portal."),
        Column('to_room'),
        Column('to_area')
    ]
    
    def load(self, game_item):
        """Return a new copy of this instance so it can be loaded for an inventory item."""
        newp = Portal()
        newp.game_item = game_item
        newp.to_area = self.to_area
        newp.to_room = self.to_room
        newp.leave_message = self.leave_message
        newp.entrance_message = self.entrance_message
        newp.emerge_message = self.emerge_message
        return newp
    
    def __str__(self):
        location = 'None'
        if self.location:
            location = 'Room %s in area %s' % (self.location.id, self.location.area.name)
        string = 'PORTAL ATTRIBUTES:\n' +\
                 '  port location: ' + location + '\n' +\
                 '  entrance message: "' + self.entrance_message + '"\n'+\
                 '  leave message: "' + self.leave_message + '"\n' +\
                 '  emerge message: "' + self.emerge_message + '"\n'
        return string
    
    def _resolve_location(self):
        if getattr(self, '_location'):
            return self._location
        try:
            self.location = self.world.get_area(str(self.to_area)).get_room(str(self.to_room))
            return self._location
        except:
            return None
    
    def _set_location(self, location):
        self._location = location
    
    location = property(_resolve_location, _set_location)
    
    def build_set_portal(self, args, player=None):
        """Set the location of the room this portal should go to."""
        if not args:
            return 'Usage: set portal to room <room-id> in area <area-name>\n'
        exp = r'([ ]+)?(to)?([ ]+)?(room)?([ ]+)?(?P<room_id>\d+)([ ]+in)?([ ]+area)?([ ]+(?P<area_name>\w+))'
        match = re.match(exp, args, re.I)
        if not match:
            return 'Usage: set portal to room <room-id> in area <area-name>\n'
        room_id, area_name = match.group('room_id', 'area_name')
        area = World.get_world().get_area(area_name)
        if not area:
            return 'That area doesn\'t exist.\n'
        room = area.get_room(room_id)
        if not room:
            return 'That room doesn\'t exist.\n'
        self.location = room
        self.save({'to_room': self.location.id, 'to_area': self.location.area.name})
        return 'This portal now connects to room %s in area %s.\n' % (self.location.id,
                                                                      self.location.area.name)
    
    def build_set_leave(self, message, player=None):
        """Set this portal's leave message."""
        self.leave_message = message
        self.save({'leave_message': self.leave_message})
        return 'Leave message set.'
    
    def build_set_entrance(self, message, player=None):
        """Set this portal's entrance message."""
        self.entrance_message = message
        self.save({'entrance_message': self.entrance_message})
        return 'Entrance message set.'
    
    def build_set_emerge(self, message, player=None):
        """Set this portal's emerge message."""
        self.emerge_message = message
        self.save({'emerge_message': self.emerge_message})
        return 'Emerge message set.'
    

class Book(ItemType):
    plural = 'books'
    pass


ITEM_TYPES = {'equippable': Equippable,
              'food': Food,
              'container': Container,
              'furniture': Furniture,
              'portal': Portal
              # 'book': Book
             }

for klass in ITEM_TYPES.values():
    model.register(klass)