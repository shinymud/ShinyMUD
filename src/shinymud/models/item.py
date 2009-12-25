from shinymud.models import to_bool
import types

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
                
class Damage(object):
    def __init__(self, dmgmin, dmgmax, dmgtype, probability):
        self.range = (dmgmin, dmgmax)
        self.type = dmgtype, 
        self.probability = probability
    def __str__(self):
        string = self.type + ': ' + self.range[0] + '-' + self.range[1], self.probability + '%'

class Item(object):
    
    def __init__(self, area=None, id='0', **args):
        self.area = area
        self.id = str(id)
        self.name = args.get('name', 'New Item')
        self.title = args.get('title', 'A shiny new object sparkles happily.')
        self.description = args.get('description', 'This is a shiny new object.')
        self.keywords = []
        kw = args.get('keywords')
        if kw and type(kw) == str:
            self.keywords = kw.split(',')
        self.weight = int(args.get('weight', 0))
        self.base_value = int(args.get('base_value', 0))
        self.carryable = True
        if 'carryable' in args:
            self.carryable = to_bool(args.get('carryable'))
        self.equip_slot = args.get('equip_slot')
        self.is_container = False
        if 'is_container' in args:
            self.is_container = to_bool(args.get('is_container'))
    
    def to_dict(self):
        d = {}
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
        d['is_container'] = str(self.is_container)
        
        return d
    
    @classmethod
    def create(cls, area=None, item_id=0):
        """Create a new room."""
        new_item = cls(area, item_id)
        return new_item
    
    def __str__(self):
        string = 'id: ' + str(self.id) + '\n' + \
                 'name: ' + self.name + '\n' + \
                 'title: ' + self.title + '\n' + \
                 'description: ' + self.description + '\n' + \
                 'equip location: ' + str(self.equip_slot) + '\n' + \
                 'keywords: ' + str(self.keywords) + '\n' + \
                 'weight: ' + str(self.weight) + '\n' + \
                 'carryable: ' + str(self.carryable) + '\n' + \
                 'base value: ' + str(self.base_value) + '\n'
        # for attr in self.other_attributes:
        #     a = getattr(self, attr)
        #     if hasattr(a, '__iter__'):
        #         string += attr + ":\n"
        #         for i in range(len(a)):
        #             string += "\t" + str(i) + ' ' + str(attr[i])
        #     else:
        #         string += attr + ": " + str(a) + '\n'
        return string
    
    #***************** Set Basic Attribute Functions *****************
    def set_description(self, desc):
        """Set the description of this item."""
        self.description = desc
        return 'Item description set.\n'
    
    def set_title(self, title):
        """Set the title of this item."""
        self.title = title
        return 'Item title set.\n'
    
    def set_name(self, name):
        self.name = name
        return 'Item name set.\n'
    
    def set_equip_loc(self, loc):
        """Set the equip location for this item."""
        if loc in SLOT_TYPES:
            self.equip_slot = loc
            return 'Item location set.\n'
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
            return 'Item weight set.\n'
    
    def set_base_value(self, value):
        """Set the base currency value for this item."""
        try:
            value = int(value)
        except:
            return 'Item value must be a number.\n'
        else:
            self.base_value = value
            return 'Item base_value has been set.\n'
    
    def set_keywords(self, keywords):
        """Set the keywords for this item.
        The argument keywords should be a string of words separated by commas.
        """
        word_list = keywords.split(',')
        # Make sure to take out any accidental whitespace between the keywords passed
        self.keywords = [word.strip() for word in word_list]
        return 'Item keywords have been set.\n'
        
    def set_carryable(self, boolean):
        """Set the carryable status for this item."""
        try:
            val = to_bool(boolean)
        except Exception, e:
            return str(e)
        else:
            self.carryable = val
            return 'Item carryable status set.\n'
    
    def weaponize(self, **args):
        """Make this item into a weapon.
        """
        self.dmg = args.get('dmg', [])
        self.other_attributes.append('dmg')
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
    
    def containerize(self):
        pass
    
    def load_item(self):
        """Create an inventory item with the same attributes as this prototype item.
        """
        item = InventoryItem()
        item.area = self.area
        item.id = self.id
        item.name = self.name
        item.title = self.title
        item.description = self.description
        item.keywords = [word for word in self.keywords]
        item.weight = self.weight
        item.base_value = self.base_value
        item.carryable = self.carryable
        item.equip_slot = self.equip_slot
        item.is_container = self.is_container
        return item
    

class InventoryItem(Item):
    def __init__(self):
        self.owner = None

    

