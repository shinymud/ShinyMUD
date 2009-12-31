from shinymud.models import to_bool
from shinymud.world import World
import types
import logging

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
SLOT_TYPES =    [   None,
                    'one-handed',
                    'two-handed',
                    'head',
                    'neck',
                    'ring',
                    'crown',
                    'hands',
                    'wrist',
                    'earring',
                    'arms',
                    'legs',
                    'feet',
                    'torso',
                    'waist',
                    'back',
                    'face',
                    'eyes',
                ]

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
        self.equip_slot = args.get('equip_slot')
        self.world = World.get_world()
        self.dbid = args.get('dbid')
        self.log = logging.getLogger('Item')
        self.item_types = {}
    
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
        if loc in SLOT_TYPES:
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
        self.item_types[item_type] = ITEM_TYPES[item_type]()
        return 'This item is now of type %s.\n' % item_type
    
    def remove_type(self, item_type):
        if not item_type in ITEM_TYPES:
            return 'That\'s not a valid item type.\n'
        if not item_type in self.item_types:
            return 'This isn\'t of type %s.\n' % item_type
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
        
        if self.owner:
            d['owner'] = self.owner
        if self.dbid:
            d['dbid'] = self.dbid
        return d

    
class Damage(object):
    def __init__(self, dmgmin, dmgmax, dmgtype, probability):
        self.range = (dmgmin, dmgmax)
        self.type = dmgtype, 
        self.probability = probability
    
    def __str__(self):
        string = self.type + ': ' + self.range[0] + '-' + self.range[1], self.probability + '%'
    

class Weapon(object):
    
    def __init__(self, **args):
        self.dmg = args.get('dmg', [])
    
    def to_dict(self):
        d = {}
        d['dmg'] = self.dmg
        
    def setDmg(self, params, index=1):
        # Match a number followed by a dash followed by a number,
        # OR one or more lowercase letters,
        # OR a number that may or may not be followed by a percent sign '%'
        # OR any number of the above, separated by spaces.
        exp = r'((((?P<min>\d+)\-(?P<max>\d+))|(?P<type>[a-z]+)|((?P<probability>\d+)[\%]?))[ ]*)+'
        match = re.search(exp, params.lower(), re.I)
        if match:
            if index and len(self.dmg) < index:
                damage = Damage()
            else:
                damage = self.dmg[index-1]
            if match.group('min') and match.group('max') and match.group('min') <= match.group('max'):
                damage.range = (match.group('min'), match.group('max'))
            if match.group('type') and match.group('type') in DAMAGE_TYPES:
                damage.type = match.group('type')
            if match.group('probability') and match.group('probability') <= 100 and match.group('probability') > 0:
                damage.probability = match.group('probability')
            if len(self.dmg) < index:
                self.dmg.append(damage)
            else:
                self.dmg[index-1] = damage
        
        self.setDmg = types.MethodType(setDmg, self, self.__class__)
    
    def addDmg(self, params):
        self.setDmg(params, len(self.dmg) + 1)
        self.addDmg = types.MethodType(addDmg, self, self.__class__)
    
    def removeDmg(self, index):
        if index <= len(self.dmg):
            del self.dmg[index -1]
        
        self.removeDmg = types.MethodType(removeDmg, self, self.__class__)

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
        self.leave_message = args.get('leave_message', '#name enters a portal.\n')
        self.entrance_message = args.get('entrance_message', 'You enter a portal.\n')
        self.emerge_message = args.get('emerge_message', '#name steps out of a shimmering portal.\n')
        self.location = None
        if 'location' in args:
            location = args.get('location').split(',')
            try:
                self.location = World.get_world().get_area(location[0]).get_room(location[1])
            except:
                self.location = None
    
    def __str__(self):
        location = 'None'
        if self.location:
            location = 'Room %s in area %s' % (self.location.id, self.location.area.name)
        string = 'PORTAL ATTRIBUTES:\n' +\
                 '  port location: ' + location + '\n' +\
                 '  entrance message: ' + self.entrance_message + '\n' +\
                 '  leave message: ' + self.leave_message + '\n' +\
                 '  emerge message: ' + self.emerge_message + '\n'
        return string
        
    
    def set_port(self, args):
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
        return 'This portal now connects to room %s in area %s.\n' % (self.location.id,
                                                                      self.location.area.name)
    def set_leave(self, message):
        """Set this portal's leave message."""
        self.leave_message = message
        return 'Leave message set.\n'
    
    def set_entrance(self, message):
        """Set this portal's entrance message."""
        self.entrance_message = message
        return 'Entrance message set.\n'
    
    def set_emerge(self, message):
        """Set this portal's emerge message."""
        self.emerge_message = message
        return 'Emerge message set.\n'
    
    def load(self):
        """Return a new copy of this instance so it can be loaded for an inventory item."""
        newp = Portal()
        newp.location = self.location
        newp.leave_message = self.leave_message
        newp.entrance_message = self.entrance_message
        newp.emerge_message = self.emerge_message
        return newp


ITEM_TYPES = {'weapon': Weapon,
              'food': Food,
              'container': Container,
              'furniture': Furniture,
              'portal': Portal
             }

