from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.models import to_bool
from shinymud.lib.world import World
from shinymud.lib.char_effect import *
import types
import logging
import re

DAMAGE_TYPES =  [   'slashing', 
                    'piercing', 
                    'impact', 
                    'fire', 
                    'ice', 
                    'shock', 
                    'sonic', 
                    'poison',
                    'holy'
                ]
SLOT_TYPES =    {   'main-hand': 'You wield #item in your main-hand.',
                    'off-hand': 'You weild #item in your off-hand.',
                    'head': 'You place #item on your head.',
                    'neck': 'You wear #item around your neck.',
                    'ring': 'You wear #item on your finger.',
                    'crown': 'You place #item upon your head.',
                    'hands': 'You wear #item on your hands.',
                    'wrist': "You wear #item on your wrist.",
                    'earring': 'You slip #item into your ear.',
                    'arms': 'You wear #item on your arms.',
                    'legs': 'You wear #item on your legs.',
                    'feet': 'You pull #item on to your feet.',
                    'torso': 'You wear #item on your body.',
                    'waist': 'You wear #item around your waist.',
                    'back': 'you throw #item over your back.'
                    #'face',
                    #'eyes',
                }

class Item(object):
    
    def __init__(self, area=None, id='0', **args):
        self.area = area
        self.id = str(id)
        self.name = args.get('name', 'New Item')
        self.title = str(args.get('title', 'A shiny new object sparkles happily.'))
        self.description = args.get('description', 'This is a shiny new object.')
        self.keywords = []
        kw = str(args.get('keywords'))
        if kw:
            self.keywords = kw.split(',')
        self.weight = int(args.get('weight', 0))
        self.base_value = int(args.get('base_value', 0))
        self.carryable = True
        if 'carryable' in args:
            self.carryable = to_bool(args.get('carryable'))
        self.equip_slot = str(args.get('equip_slot', ''))
        self.world = World.get_world()
        self.dbid = args.get('dbid')
        self.log = logging.getLogger('Item')
        self.item_types = {}
        if self.dbid:
            for key, value in ITEM_TYPES.items():
                row = self.world.db.select('* FROM %s WHERE item=?' % key,
                                           [self.dbid])
                if row:
                    row[0]['item'] = self
                    self.item_types[key] = value(**row[0])
    
    def to_dict(self):
        d = {}
        
        if type(self.area) == int:
            d['area'] = self.area
        else:
            d['area'] = self.area.dbid
        d['id'] = self.id
        d['name'] = self.name
        d['title'] = self.title
        d['description'] = self.description
        d['keywords'] = ','.join(self.keywords)
        d['weight'] = self.weight
        d['base_value'] = self.base_value
        d['carryable'] = str(self.carryable)
        d['equip_slot'] = self.equip_slot
        if self.dbid:
            d['dbid'] = self.dbid
        
        return d
    
    @classmethod
    def create(cls, area=None, item_id=0):
        """Create a new room."""
        new_item = cls(area, item_id)
        return new_item
    
    def __str__(self):
        if self.item_types:
            item_types = ', '.join(self.item_types.keys())
        else:
            item_types = 'No special item types.'
        string = (' Item %s in Area %s ' % (self.id, self.area.name)
                  ).center(50, '-') + '\n'
        string += 'name: ' + self.name + '\n' + \
                  'title: ' + self.title + '\n' + \
                  'item types: ' + item_types + '\n' +\
                  'description:\n    ' + self.description + '\n' + \
                  'equip location: ' + str(self.equip_slot) + '\n' + \
                  'keywords: ' + str(self.keywords) + '\n' + \
                  'weight: ' + str(self.weight) + '\n' + \
                  'carryable: ' + str(self.carryable) + '\n' + \
                  'base value: ' + str(self.base_value) + '\n'
        for itype in self.item_types.values():
            string += str(itype)
        string += ('-' * 50)
        return string
    
    def destruct(self):
        """Remove this instance and all of its item types from the database."""
        if self.dbid:
            for key, value in self.item_types.items():
                self.world.db.delete('FROM %s WHERE dbid=?' % key, [value.dbid])
            if hasattr(self, 'owner'):
                # if this instance has an owner attribute, we know it is saved
                # to the inventory table in the database; otherwise it will
                # have been saved in the item table.
                self.world.db.delete('FROM inventory WHERE dbid=?', [self.dbid])
            else:
                self.world.db.delete('FROM item WHERE dbid=?', [self.dbid])
    
    #***************** Set Basic Attribute Functions *****************
    def set_description(self, desc, user=None):
        """Set the description of this item."""
        user.last_mode = user.mode
        user.mode = TextEditMode(user, self, 'description', self.description)
        return 'ENTERING TextEditMode: type "@help" for help.\n'
    
    def set_title(self, title, user=None):
        """Set the title of this item."""
        if not title:
            title = ''
        else:
            # If the builder prepends an '@' symbol on their title, it means
            # they don't want us fiddling with it. Strip off the @ and then
            # leave the title as-is.
            if title.startswith('@'):
                title = title.lstrip('@')
            # Otherwise we'll correct for basic sentence format (capital at
            # the beginning, period at the end)
            else:
                if not title.endswith(('.', '?', '!')):
                    title = title + '.'
                title = title.capitalize()
        self.title = title
        self.save({'title': self.title})
        return 'Item title set.\n'
    
    def set_name(self, name, user=None):
        self.name = name
        self.save({'name': self.name})
        # self.world.db.update_from_dict('item', self.to_dict())
        return 'Item name set.\n'
    
    def set_equip(self, loc, user=None):
        """Set the equip location for this item."""
        if loc in SLOT_TYPES.keys():
            self.equip_slot = loc
            self.save({'equip_slot': self.equip_slot})
            # self.world.db.update_from_dict('item', self.to_dict())
            return 'Item equip location set.\n'
        else:
            return 'That equip location doesn\'t exist.\n'
    
    def set_weight(self, weight, user=None):
        """Set the weight for this object."""
        try:
            weight = int(weight)
        except:
            return 'Item weight must be a number.\n'
        else:
            self.weight = weight
            self.save({'weight': self.weight})
            # self.world.db.update_from_dict('item', self.to_dict())
            return 'Item weight set.\n'
    
    def set_basevalue(self, value, user=None):
        """Set the base currency value for this item."""
        try:
            value = int(value)
        except:
            return 'Item value must be a number.\n'
        else:
            self.base_value = value
            self.save({'base_value': self.base_value})
            # self.world.db.update_from_dict('item', self.to_dict())
            return 'Item base_value has been set.\n'
    
    def set_keywords(self, keywords, user=None):
        """Set the keywords for this item.
        The argument keywords should be a string of words separated by commas.
        """
        word_list = keywords.split(',')
        # Make sure to take out any accidental whitespace between the keywords passed
        self.keywords = [word.strip() for word in word_list]
        self.save({'keywords': ','.join(self.keywords)})
        # self.world.db.update_from_dict('item', self.to_dict())
        return 'Item keywords have been set.\n'
    
    def set_carryable(self, boolean, user=None):
        """Set the carryable status for this item."""
        try:
            val = to_bool(boolean)
        except Exception, e:
            return str(e)
        else:
            self.carryable = val
            self.save({'carryable': self.carryable})
            # self.world.db.update_from_dict('item', self.to_dict())
            return 'Item carryable status set.\n'
    
    def add_type(self, item_type, item_dict=None):
        """Add a new item type to this item."""
        if not item_type in ITEM_TYPES:
            return 'That\'s not a valid item type.\n'
        if item_type in self.item_types:
            return 'This item is already of type %s.\n' % item_type
        if item_dict:
            new_type = ITEM_TYPES[item_type](**item_dict)
        else:
            new_type = ITEM_TYPES[item_type]()
        new_type.item = self
        new_type.save()
        # new_type.dbid = self.world.db.insert_from_dict(item_type, new_type.to_dict())
        self.item_types[item_type] = new_type
        return 'This item is now of type %s.\n' % item_type
    
    def remove_type(self, item_type):
        if not item_type in ITEM_TYPES:
            return 'That\'s not a valid item type.\n'
        if not item_type in self.item_types:
            return 'This isn\'t of type %s.\n' % item_type
        self.world.db.delete('FROM %s where dbid=?' % item_type, [self.item_types[item_type].dbid])
        del self.item_types[item_type]
        return 'This item is no longer of type %s.\n' % item_type
    
    def load(self, spawn_id=None):
        """Create an inventory item with the same attributes as this prototype item.
        """
        self.log.debug(str(self.to_dict()))
        item = InventoryItem(spawn_id, **self.to_dict())
        # Clear the prototype's dbid so we don't accidentally overwrite it in the db
        item.dbid = None
        # to_dict will return the area as an integer -- make sure we reset it here
        # as the actual instance of the area
        item.area = self.area
        for key,value in self.item_types.items():
            item.item_types[key] = value.load()
            item.item_types[key].inv_item = item
        return item
    
    def save(self, save_dict=None):
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict('item', save_dict)
            else:    
                self.world.db.update_from_dict('item', self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict('item', self.to_dict())
            for key, value in self.item_types.items():
                value.item = item.dbid
                value.save()
    
    def is_container(self):
        if 'container' in self.item_types:
            return True
        return False
    

class InventoryItem(Item):
    def __init__(self, spawn_id=None, **args):
        Item.__init__(self, **args)
        self.owner = args.get('owner')
        self.spawn_id = spawn_id
        self.container = args.get('container')
        
        if self.dbid:
            for key, value in ITEM_TYPES.items():
                row = self.world.db.select('* FROM %s WHERE inv_item=?' % key,
                                           [self.dbid])
                if row:
                    row[0]['inv_item'] = self
                    self.item_types[key] = value(**row[0])
    
    def to_dict(self):
        d = Item.to_dict(self)
        
        d['owner'] = self.owner
        if self.dbid:
            d['dbid'] = self.dbid
        if self.container:
            d['container'] = self.container.dbid
        return d
    
    def save(self, save_dict=None):
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict('inventory', save_dict)
            else:    
                self.world.db.update_from_dict('inventory', self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict('inventory', self.to_dict())
            # If an item has not yet been saved, its item types will not have been
            # saved either.
        for key, value in self.item_types.items():
            value.inv_item = self
            value.item = None
            value.save()
    

class Damage(object):
    def __init__(self, dstring):
        exp = r'(?P<d_type>\w+)[ ]+(?P<d_min>\d+)-(?P<d_max>\d+)[ ]+(?P<d_prob>\d+)'
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
                raise Exception('Bad damage probability given.\n')
        else:
            raise Exception('Bad damage type given.\n')
    
    def __str__(self):
        return self.type + ' ' + str(self.range[0]) + '-' + str(self.range[1]) + ' ' + str(self.probability) + '%'
    

class Weapon(object):
    def __init__(self, **args):
        dmg = args.get('dmg')
        self.item = args.get('item')
        self.inv_item = args.get('inv_item')
        self.dmg = []
        if dmg:
            d_list = dmg.split('|')
            for d in d_list:
                self.dmg.append(Damage(d))
        self.dbid = args.get('dbid')
    
    def __str__(self):
        string = 'WEAPON ATTRIBUTES:\n' +\
            '  dmg: \n'
            
        dstring =  '    %s: %s\n' 
        for dmg in range(len(self.dmg)):
            string += dstring % (str(dmg + 1), str(self.dmg[dmg]) )
        return string
    
    def load(self):
        wep = Weapon()
        for d in self.dmg:
            wep.add_dmg(str(d))
        return wep
        
        
    
    def to_dict(self):
        d = {}
        if self.item:
            d['item'] = self.item.dbid
        if self.inv_item:
            d['inv_item'] = self.inv_item.dbid
        d['dmg'] = '|'.join([str(eachone) for eachone in self.dmg])
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def set_dmg(self, params, user=None):
        if not params:
            return 'Sets a damage type to a weapon.\nExample: set dmg slashing 1-4 100%\n'
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
        # world.db.update_from_dict('weapon', self.to_dict())
        
        return 'dmg ' + str(index) + ' set.\n'
    
    def add_dmg(self, params):
        #Currently broken will be fixed when the add class in commands is updated.
        if not params:
            return 'What damage would you like to add?\n'
        try:
            self.dmg.append(Damage(params))
            self.save()
            # world = World.get_world()
            # world.db.update_from_dict('weapon', self.to_dict())
            return 'dmg has been added.\n'
        except Exception, e:
            return str(e)
    
    def remove_dmg(self, index):
        if not index:
            return 'which dmg would you like to remove?'
        else:
            if index <= len(self.dmg) and index > 0:
                del self.dmg[index -1]
                self.save()
                # world.db.update_from_dict('weapon', self.to_dict())
    
    def save(self, save_dict=None):
        world = World.get_world()
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('weapon', save_dict)
            else:    
                world.db.update_from_dict('weapon', self.to_dict())
        else:
            self.dbid = world.db.insert_from_dict('weapon', self.to_dict())
    

class Food(object):
    food_verbs = {'food': 'eat', 'drink': 'drink from'}
    def __init__(self, **args):
        self.on_eat = args.get('on_eat', [])
        self.dbid = args.get('dbid')
        self.item = args.get('item')
        self.inv_item = args.get('inv_item')
        self.food_type = args.get('food_type', 'food')
        self.replace_obj = None
        self.ro_id = args.get('ro_id')
        self.ro_area = args.get('ro_area')
        self.actor_use_message = args.get('actor_use_message', '')
        self.room_use_message = args.get('room_use_message', '')
        self.effects = {}
        if self.dbid:
            world = World.get_world()
            row = world.db.select('* FROM char_effect WHERE item_type=? AND dbid=?',
                                  ['food', self.dbid])
            for e in row:
                e['item'] = self
                effect = EFFECTS[e['name']](**e)
                self.effects[effect.name] = effect
    
    def _resolve_ro(self):
        world = World.get_world()
        if self._ro:
            return self._ro
        try: 
            self.replace_obj = world.get_area(self.ro_area).get_item(self.ro_id)
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
    
    def to_dict(self):
        d = {}
        # d['on_eat'] = ','.join(self.eat_effects)
        d['ro_area'] = self.ro_area
        d['ro_id'] = self.ro_id
        d['food_type'] = self.food_type
        d['actor_use_message'] = self.actor_use_message
        d['room_use_message'] = self.room_use_message
        if self.item:
            d['item'] = self.item.dbid
        if self.inv_item:
            d['inv_item'] = self.inv_item.dbid
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def save(self, save_dict=None):
        world = World.get_world()
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('food', save_dict)
            else:    
                world.db.update_from_dict('food', self.to_dict())
        else:
            self.dbid = world.db.insert_from_dict('food', self.to_dict())
    
    def load(self):
        new_f = Food(**self.to_dict())
        new_f.replace_obj = self.replace_obj
        new_f.dbid = None
        new_f.item = None
        effects = {}
        for e in self.load_effects():
            e.item = new_f
            e.save()
            effects[e.name] = e
        new_f.effects = effects
        return new_f
    
    def load_effects(self):
        """Return a list of copies of this food item's effects."""
        e = [effect.copy() for effect in self.effects.values()]
        return e
    
    def add_effect(self, args):
        """Add an effect to this food item that will be transferred to the
        user when the item is eaten.
        """
        # return 'Sorry, this functionality is not finished, yet.'
        # FINISH THIS FUNCTION LOL
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
    
    def remove_effect(self, args):
        """Remove an effect from this item."""
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
        item = self.item or self.inv_item
        if self.food_type == 'food':
            m = 'You eat %s.' % (item.name)
        else:
            m = 'You drink from %s.' % (item.name)
        return m
    
    def get_room_message(self):
        if self.room_use_message:
            return self.room_use_message
        item = self.item or self.inv_item
        if self.food_type == 'food':
            m = '#actor eats %s.' % (item.name)
        else:
            m = '#actor drinks from %s.' % (item.name)
        return m
    
    def set_food_type(self, use, user=None):
        """Set the verb used to consume the object."""
        if not use or (use.lower().strip() not in ['food', 'drink']):
            return 'Valid values for food_type are "food" or "drink".'
        self.food_type = use.lower().strip()
        self.save({'food_type': self.food_type})
        return 'Food_type is now set to %s.' % use
    
    def set_replace(self, replace, user=None):
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
        elif user:
            area = user.mode.edit_area
        else:
            return 'You need to specify the area that the item is from.'
        item = area.get_item(item_id)
        if not item:
            'Item %s doesn\'t exist.' % item_id
        self.replace_obj = item
        self.save({'ro_id': item.id, 'ro_area': item.area.name})
        return '%s will be replaced with %s when consumed.' %\
                (self.item.name.capitalize(), item.name)
    
    def set_actor_message(self, message):
        self.actor_use_message = message or ''
        self.save({'actor_use_message': self.actor_use_message})
        if not message:
            return 'Use message (actor) has been reset to the default.'
        return 'Use message (actor) has been set.'
    
    def set_room_message(self, message):
        self.room_use_message = message or ''
        self.save({'room_use_message': self.room_use_message})
        if not message:
            return 'Use message (room) has been reset to the default.'
        return 'Use message (room) has been set.'
    

class Container(object):
    def __init__(self, **args):
        self.weight_capacity = args.get('weight_capacity')
        self.item_capacity = args.get('item_capacity')
        self.weight_reduction = args.get('weight_reduction', 0)
        self.inventory = []
        self.dbid = args.get('dbid')
        self.item = args.get('item')
        self.inv_item = args.get('inv_item')
        self.log = logging.getLogger('Container')
        self.openable = to_bool(str(args.get('openable'))) or False
        self.closed = to_bool(str(args.get('closed'))) or False
        self.locked = to_bool(str(args.get('locked'))) or False
        self.key = None
        self.key_area = str(args.get('key_area', ''))
        self.key_id = str(args.get('key_id', ''))
    
    def _resolve_key(self):
        if self._key:
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
                 '  item capacity: ' + str(self.item_capacity) + '\n' +\
                 '  weight reduction: ' + str(self.weight_reduction) + '%\n' +\
                 '  openable: ' + str(self.openable) + '\n' +\
                 '  closed: ' + str(self.closed) + '\n' +\
                 '  locked: ' + str(self.locked) + '\n' +\
                 '  key: ' + key + '\n'
        return string
    
    def to_dict(self):
        d = {}
        d['weight_capacity'] = self.weight_capacity
        d['item_capacity'] = self.item_capacity
        d['weight_reduction'] = self.weight_reduction
        d['key_area'] = self.key_area
        d['key_id'] = self.key_id
        d['openable'] = self.openable
        d['closed'] = self.closed
        d['locked'] = self.locked
        self.log.debug('ITEM: ' + str(self.item))
        if self.item:
            d['item'] = self.item.dbid
        if self.inv_item:
            d['inv_item'] = self.inv_item.dbid
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def save(self, save_dict=None):
        world = World.get_world()
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('container', save_dict)
            else:    
                world.db.update_from_dict('container', self.to_dict())
        else:
            self.dbid = world.db.insert_from_dict('container', self.to_dict())
        
        for item in self.inventory:
            if item.container != self.inv_item:
                item.container = self.inv_item
            item.save()
    
    def load(self):
        newc = Container(**self.to_dict())
        newc.dbid = None
        newc.item = None
        return newc
    
    def destroy_inventory(self):
        for item in self.inventory:
            item.destruct()
    
    def item_add(self, item):
        self.inventory.append(item)
        if self.inv_item.dbid and (item.container != self.inv_item):
            item.container = self.inv_item
            item.save({'container': item.container.dbid})
        return True
    
    def load_contents(self):
        rows = World.get_world().db.select("* FROM inventory WHERE container=?", [self.inv_item.dbid])
        self.log.debug(rows)
        for row in rows:
            item = InventoryItem(**row)
            if item.is_container():
                item.item_types.get('container').load_contents()
            self.item_add(item)
    
    def item_remove(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
            item.container = None
            if self.inv_item.dbid:
                item.save({'container':item.container})
    
    def get_item_by_kw(self, keyword):
        for item in self.inventory:
            if keyword in item.keywords:
                return item
        return None
    
    def display_inventory(self):
        if self.closed:
            return '%s is closed.\n' % self.inv_item.name.capitalize()
        i = ''
        for item in self.inventory:
            i += '  ' + item.name + '\n'
        if not i:
            return '%s is empty.\n' % self.inv_item.name.capitalize()
        return '%s contains:\n%s' % (self.inv_item.name.capitalize(), i)
    
    def set_openable(self, args, user=None):
        boolean = to_bool(args)
        if not boolean:
            return 'Acceptable values for this attribute are true or false.'
        else:
            self.openable = boolean
            self.save({'openable': self.openable})
            return 'Openable has been set to %s.' % boolean
    
    def set_closed(self, args, user=None):
        boolean = to_bool(args)
        if not boolean:
            return 'Acceptable values for this attribute are true or false.'
        else:
            self.closed = boolean
            self.save({'closed': self.closed})
            return 'Closed has been set to %s.' % boolean
    
    def set_key(self, args, user=None):
        return 'Not implemented yet.'
    
    def set_locked(self, args, user=None):
        return 'Not implemented yet.'
    

class Furniture(object):
    def __init__(self, **args):
        self.sit_effects = args.get('sit_effects', [])
        self.sleep_effects = args.get('sleep_effects', [])
        self.users = []
        # of users that can use this piece of furniture at one time.
        self.capacity = args.get('capacity')
        self.dbid = args.get('dbid')
        self.item = args.get('item')
        self.inv_item = args.get('inv_item')
    
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
    
    def to_dict(self):
        d = {}
        d['sit_effects'] = ','.join(self.sit_effects)
        d['sleep_effects'] = ','.join(self.sleep_effects)
        if self.capacity:
            d['capacity'] = self.capacity
        if self.item:
            d['item'] = self.item.dbid
        if self.inv_item:
            d['inv_item'] = self.inv_item.dbid
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def save(self, save_dict=None):
        world = World.get_world()
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('furniture', save_dict)
            else:    
                world.db.update_from_dict('furniture', self.to_dict())
        else:
            self.dbid = world.db.insert_from_dict('furniture', self.to_dict())
    
    def load(self):
        newf = Furniture(**self.to_dict())
        newf.dbid = None
        newf.item = None
        return newf
    
    def user_add(self, user):
        if self.capacity:
            pass
        else:
            self.users.append(user)
            return True
    
    def user_remove(self, user):
        if user in self.users:
            self.users.remove(user)
    

class Portal(object):
    def __init__(self, **args):
        self.leave_message = args.get('leave_message', '#actor enters a portal.')
        self.entrance_message = args.get('entrance_message', 'You enter a portal.')
        self.emerge_message = args.get('emerge_message', '#actor steps out of a shimmering portal.')
        self.item = args.get('item')
        self.inv_item = args.get('inv_item')
        self.dbid = args.get('dbid')
        # The actual room object this portal points to
        # The id of the room this portal points to
        self.to_room = args.get('to_room')
        # the area of the room this portal points to
        self._location = None
        self.to_area = args.get('to_area')
        self.world = World.get_world()
    
    def to_dict(self):
        d = {}
        d['leave_message'] = self.leave_message
        d['entrance_message'] = self.entrance_message
        d['emerge_message'] = self.emerge_message
        if self.item:
            d['item'] = self.item
        if self.inv_item:
            d['inv_item'] = self.inv_item.dbid
        d['to_room'] = self.to_room
        d['to_area'] = self.to_area
        if self.dbid:
            d['dbid'] = self.dbid
        
        return d
    
    def load(self):
        """Return a new copy of this instance so it can be loaded for an inventory item."""
        newp = Portal()
        newp.location = self.location
        newp.to_area = self.to_area
        newp.to_room = self.to_room
        newp.leave_message = self.leave_message
        newp.entrance_message = self.entrance_message
        newp.emerge_message = self.emerge_message
        return newp
    
    def save(self, save_dict=None):
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict('portal', save_dict)
            else:    
                self.world.db.update_from_dict('portal', self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict('portal', self.to_dict())
    
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
        if self._location:
            return self._location
        try:
            self._location = self.world.get_area(str(self.to_area)).get_room(str(self.to_room))
            return self._location
        except:
            return None
    
    def _set_location(self, location):
        self._location = location
    
    location = property(_resolve_location, _set_location)
    
    def set_portal(self, args, user=None):
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
    
    def set_leave(self, message, user=None):
        """Set this portal's leave message."""
        self.leave_message = message
        self.save({'leave_message': self.leave_message})
        return 'Leave message set.\n'
    
    def set_entrance(self, message, user=None):
        """Set this portal's entrance message."""
        self.entrance_message = message
        self.save({'entrance_message': self.entrance_message})
        return 'Entrance message set.\n'
    
    def set_emerge(self, message, user=None):
        """Set this portal's emerge message."""
        self.emerge_message = message
        self.save({'emerge_message': self.emerge_message})
        return 'Emerge message set.\n'
    

ITEM_TYPES = {'weapon': Weapon,
              'food': Food,
              'container': Container,
              'furniture': Furniture,
              'portal': Portal
             }


