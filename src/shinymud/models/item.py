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
    def __init__(self, area=None, item_id=0):
        self.area = area
        self.id = item_id
        self.name = 'New Item'
        self.title = 'A shiny new object sparkles happily.'
        self.description = 'This is a shiny new object.'
        self.keywords = []
        self.weight = 0
        self.base_value = 0
        self.pickup = False
        self.equip_slot = None
        self.is_container = False
    
    @classmethod
    def create(cls, area=None, item_id=0):
        """Create a new room."""
        new_item = cls(area, item_id)
        return new_item
    
    def __str__(self):
        string = 'name: ' + self.name + '\n' + \
                 'title: ' + self.title + '\n' + \
                 'description: ' + self.description + '\n' + \
                 'equip location: ' + str(self.equip_slot) + '\n' + \
                 'keywords: ' + str(self.keywords) + '\n' + \
                 'weight: ' + str(self.weight) + '\n' + \
                 'pickup/carryable: ' + str(self.pickup) + '\n' + \
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
    
    #***************** Set Attribute Functions *****************
    
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

class InventoryItem(Item):
    UNIQUE = ['uid']
    def __init__(self):
        Item.__init__(self)
        self.save_attr['uid'] = [None, str]
        self.save_attr['owner'] = [None, User]
        self.save_attr['container'] = [None, InventoryItem]
    

