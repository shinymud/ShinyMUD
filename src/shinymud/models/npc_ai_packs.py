from shinymud.lib.world import World
from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *
from shinymud.models.item_types import ITEM_TYPES
from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *
from shinymud.data.config import CURRENCY

import json
import re

class NpcAiPack(Model):
    log = World.get_world().log
    """The base class that must be inherited by all ai pack.
     
    If you're going to build a new ai pack, the first stop is to inherit from
    this class and implement its required functions (explained below!).
    """
    def __init__(self, args={}):
        """ An AiPack's __init__ function should take a dictionary of keyword
        arguments which could be empty (if this is a brand new instance), or hold
        the saved values of your attributes loaded from the database.
        Your init function should look something like the following:
         
        # You'll need to initialize these first three attributes
        # regardless of what kind of ai pack you're creating:
        self.dbid = args.get('dbid')
        self.npc = args.get('npc')
         
        # Now we'll initialize our class-specific attributes:
        self.foo = args.get('foo', 'My default foo value.')
        self.bar = args.get('bar', 'My default bar value.')
        """
        raise NpcAiTypeInterfaceError('You need to implement the init function.')
    
    def to_dict(self):
        """To dict converts all of the ai pack's attributes that aught to be
        saved to the database into a dictionary, with the name of the attribute
        being the key and its value being the value.
         
        to_dict takes no arguments, and should return a dictionary.
        the code for a to_dict function aught to look something like the following:
         
        d = {}
        if self.dbid:
            d['dbid'] = self.dbid
        d['npc'] = self.npc.dbid
        # The names of your attributes must be the same as the ones specified
        # in the schema.
        d['foo'] = self.foo
        d['bar'] = self.bar
        return d
        """
        raise NpcAiTypeInterfaceError('You need to implement the to_dict function.')
    
    def save(self, save_dict=None):
        """The save function saves this AiPack to the database.
         
        If passed a save_dict, the save function should only save the data
        specified in the dictionary to the database. If save_dict is somehow
        empty or None, the entire instance should be saved to the database.
        Your save function should look like the following:
         
        world = World.get_world()
        if self.dbid:
            # This pack has a dbid, so it already exists in the database. We just
            # need to update it.
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('table_name', save_dict)
            else:    
                world.db.update_from_dict('table_name', self.to_dict())
        else:
            # This pack doesn't exist in the database if it doesn't have a dbid
            # yet, so we need to insert it and save its new dbid
            self.dbid = world.db.insert_from_dict('table_name', self.to_dict())
        """
        raise NpcAiTypeInterfaceError('You need to implement the save function.')
    
    def __str__(self):
        """Return a string representation of this ai pack to be displayed
        during BuildMode.
         
        To be consistent throughout BuildMode, It should have a heading in all
        caps, and each of its attributes labeled and indented by two spaces
        beneath it. 
        The string returned should look something like the following:
         
        ITEMTYPE ATTRIBUTES:
          foo: The value of the foo attribute
          bar: The value of the bar attribute
        """
        raise NpcAiTypeInterfaceError('You need to implement the str function.')
    

class NpcAiTypeInterfaceError(Exception):
    """The default error to be raised if a required function is not implemented
    in a NpcAiPack subclass.
    """
    pass


class MerchandiseList(object):
    def __init__(self, args=None):
        # The "live" list contains sublists in the form of [item, price]
        # where item is an actual BuildItem object and price is an int
        self.live = []
        # The "dead" list contains any leftover dictionaries in the form of:
        # {'id': item_id, 'area': item_area, 'price': price}
        # These leftover dictionaries could not be resolved into real BuildObjects,
        # either because the item or its area was recently destroyed.
        # We'll set them aside so that they can be saved back to the database,
        # the missing items get restored/re-imported later.
        self.dead = []
        self.pending = json.loads(args) if args else None
    
    def save(self):
        save_list = self.dead[:]
        save_list.extend([{'id': item.id, 'area': item.area.name, 'price': price}
                          for item,price in self.live])
        return json.dumps(save_list)
    
    def resolve(self):
        if not self.pending:
            return
        for group in self.pending:
            if self.world.area_exists(group.get('area')):
                item = self.world.get_area(group.get('area')).get_item(group.get('id'))
                if item:
                    self.live.append([item, int(group.get('price'))])
                else:
                    self.dead.append(group)
            else:
                self.dead.append(group)
        self.pending = None
    
    def resurrect(self):
        """Try to find the items in the self.dead list: if they can now be found
        in the world, remove them from the self.dead list and add them to the
        self.live list.
        """
        for i in reversed(xrange(len(self.dead))):
            d = self.dead[i]
            if self.world.area_exists(d.get('area')):
                item = self.world.get_area(d.get('area')).get_item(d.get('id'))
                if item:
                    self.live.append([item, int(d.get('price'))])
                    del self.dead[i]
    
    def merch_list(self):
        """Get a list of the item's for sale to players."""
        if self.live:
            sl = ''
            for group in self.live:
                sl += '  %s %s -- %s\n' % (str(group[1]), CURRENCY,
                                           group[0].name)
        else:
            sl = None
        return sl
    
    def build_list(self):
        """Gets a list of the sale_items formatted for Builders."""
        if self.dead: 
            self.resurrect()
        sl = ''
        i = 1
        for group in self.live:
            sl += '    [%s] %s %s -- %s (%s:%s)\n' % (str(i), str(group[1]), 
                                                      self.world.currency_name,
                                                      group[0].name,
                                                      group[0].id,
                                                      group[0].area.name)
            i += 1
        if self.dead:
            sl = '---- Missing Items ----\n ' +\
            "This merchant can't find the following items you told him to sell:\n"
            for group in self.dead:
                sl += 'Item %s from area %s: %s %s.\n' % (group['id'], 
                                                          group['area'],
                                                          str(group['price']),
                                                          CURRENCY)
            sl += """
These items or their areas have been removed from the world. You can try
restoring them by re-importing any missing areas, or removing them from this
merchant by typing "remove missing".
            """
        if not sl:
            sl = 'Nothing.'
        return sl
    
    def add_item(self, item_group):
        """Add an item (and its price) to the self.live list.
        """
        self.live.append(item_group)
    
    def get_item(self, keyword):
        """If this merchant has an item with the given keyword, return it and
        its price in [item, price] form, else return None.
        """
        for group in self.live:
            if keyword in group[0].keywords:
                return group
        return None
    
    def pop(self, index):
        """Remove and return the item at the given index for self.live.
        If the index given is invalid, return None.
        """
        if (index > len(self.live)) or (index < 0):
            return None
        return self.live.pop(index)
    
    def reset_dead(self):
        """Set the self.dead list back to an empty list.
        """
        self.dead = []
    

class Merchant(NpcAiPack):
    help = (
    """<title>Merchant (Npc AI Pack)
The Merchant AI pack is meant to give NPCs the ability to become merchants.
    """
    )
    plural_map = {'plain':'plain items'}
    plural_map.update(dict([(key, val.plural) for key,val in ITEM_TYPES.items()]))
    db_table_name = 'merchant'
    db_columns = Model.db_columns + [
        Column('npc', foreign_key=('npc', 'dbid'), null=False, type='INTEGER',
               write=lambda npc: npc.dbid),
        Column('buyer', read=to_bool, default=True),
        Column('markup', read=read_float, type='NUMBER', default=1),
        Column('buys_types', read=read_list, write=write_list),
        Column('sale_items', read=MerchandiseList,
               write=lambda ml: ml.save if ml else None)
    ]
    def __str__(self):
        if self.buyer:
            bt = ', '.join(self.buys_types) or 'Buys all types.'
        else:
            bt = 'Merchant is not a buyer.'
        
        s = '\n'.join(("MERCHANT ATTRIBUTES:",
                       "  For sale:\n" + self.sale_items.build_list(),
                       "  Buys items: " + str(self.buyer),
                       "  Buys only these types: " + bt,
                       "  Markup: " + str(self.markup) + 'x item\'s base value.',
                       ""
                     ))
        return s
    
    def player_sale_list(self):
        merch = self.sale_items.merch_list()
        if merch:
            l = '%s\'s sale list:\n%s' % (self.npc.name, merch)
        else:
            l = '%s doesn\'t have anything for sale.' % self.npc.name
        return l
    
    def tell_buy_types(self):
        """Return a sentence formatted list of the types this merchant buys."""
        if not self.buyer:
            return 'I\'m not interested in buying anything.'
        if not self.buys_types:
            return "I'll buy whatever you've got!"
        # only a single thing in the list
        p = self.plural_map
        if len(self.buys_types) == 1:
            m = "I only buy %s." % p[self.buys_types[0]]
        # Two or more types
        if len(self.buys_types) >= 2:
            m = "I only buy %s and %s." % (', '.join(map(lambda x: p[x], self.buys_types[:-1])), p[self.buys_types[-1]])
        return m
    
    def get_item(self, keyword):
        """If this merchant has an item with the given keyword, return it and
        its price in [item, price] form, else return None.
        """
        return self.sale_items.get_item(keyword)
    
    def will_buy(self, item):
        """Return True if merchant will buy a certain item, false if they will 
        not.
        """
        # If the merchant is not a buyer, return False by definition
        if not self.buyer:
            return False
        # If there are no specific types specified (the buys_types list is 
        # empty), then the merchant buys ALL types and we should return True
        # by default
        if not self.buys_types:
            return True
        # If item has no item types, then merchant will only buy the item if 
        # they accept "plain" items
        if (not item.item_types) and ('plain' in self.buys_types):
            return True
        # If this item has at least one item type that is listed in this
        # merchant's buys_types list, then the item is eligible to be bought and
        # we should return True
        for t in item.item_types:
            if t in self.buys_types:
                return True
        # If we made it to here, then this merchant doesn't want this item type.
        return False
    
    def build_set_markup(self, markup, player=None):
        """Set the markup percentage for this merchant."""
        if not markup.strip():
            return 'Try: "set markup <mark-up>", or see "help merchant".'
        try:
            mark = float(markup)
        except:
            return 'Markup must be a number. See "help merchant" for details.'
        else:
            if mark < 0:
                return 'Markup must number greater than zero.'
            self.markup = mark
            self.save()
            return 'Markup is now set to %s.' % (markup)
    
    def build_set_buys(self, buyer, player=None):
        """Set whether or not this merchant is a buyer."""
        if not buyer.strip():
            return 'Try "set buys <true/false>", or see "help merchant".'
        b = to_bool(buyer)
        if b is None:
            return 'Buys items can only be set to true or false.'
        self.buyer = b
        self.save()
        return 'Buys items has been set to %s.' % str(self.buyer)
    
    def build_add_type(self, itype):
        """Add an item type that this merchant should specialize in buying."""
        if not self.buyer:
            return 'This merchant is not a buyer.\n' +\
            'You must set buys to True before this merchant will buy anything from players.'
        itype = itype.strip().lower()
        if not itype:
            return 'Try "add type <item-type>", or see "help merchant".'
        if itype == 'all':
            self.buys_types = []
            self.save()
            return 'Merchant now buys all item types.'
        if (itype != 'plain') and (itype not in ITEM_TYPES):
            return '%s is not a valid item type. See "help merchant" for details.' % itype
        self.buys_types.append(itype)
        self.save()
        return 'Merchant will now buy items of type %s from players.' % itype
    
    def build_remove_type(self, itype):
        """Remove an item type that this merchant should specialize in buying."""
        if not self.buyer:
            return 'This merchant is not a buyer.\n' +\
            'You must set buys to True before this merchant will buy anything from players.'
        if not itype:
            return 'Try "add type <item-type>", or see "help merchant".'
        if itype == 'all':
            self.buys_types = []
            self.save()
            return 'Merchant now buys all item types.'
        itype = itype.strip().lower()
        if itype in self.buys_types:
            self.buys_types.remove(itype)
            self.save()
            return 'Merchant no longer buys items of type %s.' % itype
        return 'Merchant already doesn\'t buy items of type %s.' % itype
    
    def build_add_item(self, args):
        """Add an item for this merchant to sell."""
        if not args:
            return 'Try "add item <item-id> from area <area-name> price <price>" or see "help merchant".'
        # check if the item they gave exists
        
        exp = r'((?P<id1>\d+)[ ]+(at[ ]+)?(price[ ]+)?(?P<price1>\d+))|' +\
              r'((?P<id2>\d+)[ ]+((from[ ]+)?(area[ ]+)?(?P<area>\w+)[ ]+)?(at[ ]+)?(price[ ]+)?(?P<price2>\d+))'
        match = re.match(exp, args, re.I)
        if not match:
            return 'Try "add item <item-id> from area <area-name> price <price>" or see "help merchant".'
        id1, id2, area_name, p1, p2 = match.group('id1', 'id2', 'area', 'price1', 'price2')
        # If the builder didn't give a area_name, just take the area from the npc
        if not area_name:
            area = self.npc.area
            item_id = id1
            price = p1
        else:
            area = self.world.get_area(area_name)
            if not area:
                return 'Area "%s" doesn\'t exist.' % area_name
            item_id = id2
            price = p2
        item = area.get_item(item_id)
        if not item:
            return 'Item %s doesn\'t exist.' % item_id
        if not price.isdigit():
            return 'The price should be a whole number.'
        self.sale_items.add_item([item, price])
        self.save()
        return 'Merchant now sells %s.' % item.name
    
    def build_remove_item(self, item):
        """Remove one of this merchant's sale items."""
        if not item:
            return 'Try "remove item <item-id>", or see "help merchant".'
        if not item.isdigit():
            return 'Try "remove item <item-id>", or see "help merchant".'
        # We do item - 1 because we give the user a list that starts at 1, not 0
        item = self.sale_items.pop(int(item)-1)
        if not item:
            return 'That item doesn\'t exist.'
        self.save()
        return 'Merchant no longer sells %s.' % item_name
    
    def build_remove_missing(self, args):
        """Remove any 'dead' items from this merchant's sale_items.
        """
        self.sale_items.reset_dead()
        self.save()
        return 'Any missing items have been cleared.'
    

model_list.register(Merchant)
NPC_AI_PACKS = {'merchant': Merchant}