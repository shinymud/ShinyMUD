from shinymud.models import to_bool
from shinymud.world import World
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
        self.title = args.get('title', 'A shiny new object sparkles happily.')
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
        for key, value in ITEM_TYPES.items():
            row = self.world.db.select('* FROM %s WHERE item=?' % key, [self.dbid])
            if row:
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
        string = 'id: ' + str(self.id) + '\n' + \
                 'name: ' + self.name + '\n' + \
                 'title: ' + self.title + '\n' + \
                 'item types: ' + item_types + '\n' +\
                 'description: ' + self.description + '\n' + \
                 'equip location: ' + str(self.equip_slot) + '\n' + \
                 'keywords: ' + str(self.keywords) + '\n' + \
                 'weight: ' + str(self.weight) + '\n' + \
                 'carryable: ' + str(self.carryable) + '\n' + \
                 'base value: ' + str(self.base_value) + '\n'
        for itype in self.item_types.values():
            string += str(itype)
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
    def set_description(self, desc):
        """Set the description of this item."""
        self.description = desc
        self.world.db.update_from_dict('item', self.to_dict())
        return 'Item description set.\n'
    
    def set_title(self, title):
        """Set the title of this item."""
        self.title = title
        self.world.db.update_from_dict('item', self.to_dict())
        return 'Item title set.\n'
    
    def set_name(self, name):
        self.name = name
        self.world.db.update_from_dict('item', self.to_dict())
        return 'Item name set.\n'
    
    def set_equip(self, loc):
        """Set the equip location for this item."""
        if loc in SLOT_TYPES.keys():
            self.equip_slot = loc
            self.world.db.update_from_dict('item', self.to_dict())
            return 'Item equip location set.\n'
        else:
            return 'That equip location doesn\'t exist.\n'
    
    def set_weight(self, weight):
        """Set the weight for this object."""
        try:
            weight = int(weight)
        except:
            return 'Item weight must be a number.\n'
        else:
            self.weight = weight
            self.world.db.update_from_dict('item', self.to_dict())
            return 'Item weight set.\n'
    
    def set_base_value(self, value):
        """Set the base currency value for this item."""
        try:
            value = int(value)
        except:
            return 'Item value must be a number.\n'
        else:
            self.base_value = value
            self.world.db.update_from_dict('item', self.to_dict())
            return 'Item base_value has been set.\n'
    
    def set_keywords(self, keywords):
        """Set the keywords for this item.
        The argument keywords should be a string of words separated by commas.
        """
        word_list = keywords.split(',')
        # Make sure to take out any accidental whitespace between the keywords passed
        self.keywords = [word.strip() for word in word_list]
        self.world.db.update_from_dict('item', self.to_dict())
        return 'Item keywords have been set.\n'
    
    def set_carryable(self, boolean):
        """Set the carryable status for this item."""
        try:
            val = to_bool(boolean)
        except Exception, e:
            return str(e)
        else:
            self.carryable = val
            self.world.db.update_from_dict('item', self.to_dict())
            return 'Item carryable status set.\n'
    
    def add_type(self, item_type):
        """Add a new item type to this item."""
        if not item_type in ITEM_TYPES:
            return 'That\'s not a valid item type.\n'
        if item_type in self.item_types:
            return 'This item is already of type %s.\n' % item_type
        new_type = ITEM_TYPES[item_type]()
        new_type.item = self.dbid
        new_type.dbid = self.world.db.insert_from_dict(item_type, new_type.to_dict())
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
    
    def load_item(self):
        """Create an inventory item with the same attributes as this prototype item.
        """
        self.log.debug(str(self.to_dict()))
        item = InventoryItem(**self.to_dict())
        self.log.debug(str(item))
        # Clear the prototype's dbid so we don't accidentally overwrite it in the db
        item.dbid = None
        # to_dict will return the area as an integer -- make sure we reset it here
        # as the actual instance of the area
        item.area = self.area
        for key,value in self.item_types.items():
            item.item_types[key] = value.load()
        return item
    
    
class InventoryItem(Item):
    def __init__(self, **args):
        Item.__init__(self, **args)
        self.owner = None
    
    def to_dict(self):
        d = Item.to_dict(self)
        
        d['owner'] = self.owner
        if self.dbid:
            d['dbid'] = self.dbid
        return d

    
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
        d['item'] = self.item
        d['dmg'] = '|'.join([str(eachone) for eachone in self.dmg])
        if self.dbid:
            d['dbid'] = self.dbid
        return d

    def set_dmg(self, params):
        if not params:
            return '\nSets a damage type.\nExample: set dmg slashing 1-4 100%\n'
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
        world = World.get_world()
        world.db.update_from_dict('weapon', self.to_dict())
        
        return 'dmg ' + str(index) + ' set.\n'
                
            
    
    def add_dmg(self, params):
        #Currently broken will be fixed when the add class in commands is updated.
        try:
            self.dmg.append(Damage(params))
            world.db.update_from_dict('weapon', self.to_dict())
        except:
            return 'Error'
    
    def remove_dmg(self, index):
        if index <= len(self.dmg) and index > 0:
            del self.dmg[index -1]
            world.db.update_from_dict('weapon', self.to_dict())

class Food(object):
    def __init__(self, **args):
        self.on_eat = args.get('on_eat', [])
    
    def __str__(self):
        if self.on_eat:
            eat_effects = ','.join(self.eat_effects)
        else:
            eat_effects = 'None'
        string = 'FOOD ATTRIBUTES:\n' +\
                 '  effects: ' + eat_effects + '\n'
        return string

class Container(object):
    def __init__(self, **args):
        self.weight_capacity = args.get('weight_capacity')
        self.item_capacity = args.get('item_capacity')
        self.weight_reduction = args.get('weight_reduction', 0)
        self.inventory = []
    
    def __str__(self):
        string = 'CONTAINER ATTRIBUTES:\n' +\
                 '  weight capacity: ' + str(self.weight_capacity) + '\n' +\
                 '  weight reduction: ' + str(self.weight_reduction) + '\n' +\
                 '  item capacity: ' + str(self.item_capacity) + '\n'
        return string
    

class Furniture(object):
    def __init__(self, **args):
        self.sit_effects = args.get('sit_effects', [])
        self.sleep_effects = args.get('sleep_effects', [])
        self.users = []
        # of users that can use this piece of furniture at one time.
        self.capacity = args.get('capacity')
    
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

class Portal(object):
    def __init__(self, **args):
        self.leave_message = args.get('leave_message', '#actor enters a portal.')
        self.entrance_message = args.get('entrance_message', 'You enter a portal.')
        self.emerge_message = args.get('emerge_message', '#actor steps out of a shimmering portal.')
        self.item = args.get('item')
        self.dbid = args.get('dbid')
        self.location = None
        self.world = World.get_world()
        if 'location' in args:
            location = str(args.get('location')).split(',')
            logging.getLogger('portal').debug(str(location))
            try:
                self.location = World.get_world().get_area(location[1]).get_room(location[0])
            except:
                self.location = None
    
    def to_dict(self):
        d = {}
        d['leave_message'] = self.leave_message
        d['entrance_message'] = self.entrance_message
        d['emerge_message'] = self.emerge_message
        d['item'] = self.item
        d['location'] = None
        if self.location:
            d['location'] = '%s,%s' % (self.location.id, self.location.area.name)
        if self.dbid:
            d['dbid'] = self.dbid
        
        return d
    
    def load(self):
        """Return a new copy of this instance so it can be loaded for an inventory item."""
        newp = Portal()
        newp.location = self.location
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
    
    def set_portal(self, args):
        """Set the location of the room this portal should go to."""
        args = args.lower().split()
        if not len(args) == 2:
            return 'Usage: set port <room_id> <area_name>\n'
        area = World.get_world().get_area(args[1])
        if not area:
            return 'That area doesn\'t exist.\n'
        room = area.get_room(args[0])
        if not room:
            return 'That room doesn\'t exist.\n'
        self.location = room
        self.world.db.update_from_dict('portal', {'dbid': self.dbid, 'location': '%s,%s' % (self.location.id, self.location.area.name)})
        return 'This portal now connects to room %s in area %s.\n' % (self.location.id,
                                                                      self.location.area.name)
    def set_leave(self, message):
        """Set this portal's leave message."""
        self.leave_message = message
        self.world.db.update_from_dict('portal', {'dbid': self.dbid,
                                                  'leave_message': self.leave_message})
        return 'Leave message set.\n'
    
    def set_entrance(self, message):
        """Set this portal's entrance message."""
        self.entrance_message = message
        self.world.db.update_from_dict('portal', {'dbid': self.dbid, 
                                                  'entrance_message': self.entrance_message})
        return 'Entrance message set.\n'
    
    def set_emerge(self, message):
        """Set this portal's emerge message."""
        self.emerge_message = message
        self.world.db.update_from_dict('portal', {'dbid': self.dbid, 
                                                  'emerge_message': self.emerge_message})
        return 'Emerge message set.\n'
    

ITEM_TYPES = {'weapon': Weapon,
              'food': Food,
              'container': Container,
              'furniture': Furniture,
              'portal': Portal
             }


