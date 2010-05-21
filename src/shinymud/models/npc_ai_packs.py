from shinymud.lib.world import World
from shinymud.models import to_bool
from shinymud.models.item_types import ITEM_TYPES

import logging
import json
import re

class NpcAiPack(object):
    """The base class that must be inherited by all ai pack.
     
    If you're going to build a new ai pack, the first stop is to inherit from
    this class and implement its required functions (explained below!).
    """
    log = logging.getLogger('NpcAI')
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

class Merchant(NpcAiPack):
    help = (
    """<title>Merchant (Npc AI Pack)
The Merchant AI pack is meant to give NPCs the ability to become merchants.
    """
    )
    def __init__(self, args={}):
        self.world = World.get_world()
        self.dbid = args.get('dbid')
        self.npc = args.get('npc')
        self.buyer = to_bool(args.get('buyer', True))
        self.markup = args.get('markup', 0)
        self._sale_list = args.get('sale_items')
        if not self._sale_list:
            self.sale_items = []
        else:
            self.sale_items = None
            self._sale_list = json.loads(self._sale_list)
        self.buys_types = args.get('buys_types') or []
        if self.buys_types:
            self.buys_types = self.buys_types.split(',')
    
    def to_dict(self):
        d = {}
        if self.dbid:
            d['dbid'] = self.dbid
        d['npc'] = self.npc.dbid
        d['buyer'] = self.buyer
        d['markup'] = self.markup
        if self.sale_items is not None:
            sl = []
            for group in self.sale_items:
                sl.append({'item_area': group[0].area.name,
                           'item_id': group[0].id,
                           'price': group[1]})
            d['sale_items'] = json.dumps(sl)
        d['buys_types'] = ','.join(self.buys_types)
        
        return d
    
    def __str__(self):
        if self.buyer:
            bt = ', '.join(self.buys_types) or 'Buys all types.'
        else:
            bt = 'Merchant is not a buyer.'
        
        s = '\n'.join(("MERCHANT ATTRIBUTES:",
                       "  For sale: " + self.builder_sale_list(),
                       "  Buys items: " + str(self.buyer),
                       "  Buys only these types: " + bt,
                       "  Markup: " + str(self.markup) + '%',
                       ""
                     ))
        return s
    
    def save(self, save_dict=None):
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict('merchant', save_dict)
            else:    
                self.world.db.update_from_dict('merchant', self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict('merchant', self.to_dict())
    
    def destruct(self):
        if self.dbid:
            self.world.db.delete('FROM merchant WHERE dbid=?', [self.dbid])
    
    def assemble_sale_list(self):
        self.sale_items = []
        for group in self._sale_list:
            if self.world.area_exists(group.get('item_area')):
                item = self.world.get_area(group.get('item_area')).get_item(group.get('item_id'))
                if item:
                    self.sale_items.append([item, group.get('price')])
    
    def player_sale_list(self):
        """Get a list of the item's for sale to players."""
        sl = 'Items for sale:\n'
        if self.sale_items is None:
            self.assemble_sale_list()
        for group in self.sale_items:
            sl += '%s -- %s' % (str(group[1]), group[0].name)
        if not sl:
            sl += '  None.'
        return sl
    
    def builder_sale_list(self):
        """Gets a list formatted for Builders."""
        if self.sale_items is None:
            self.assemble_sale_list()
        sl = ''
        i = 1
        for group in self.sale_items:
            sl += '\n    [%s] %s %s -- %s (%s:%s)' % (str(i), str(group[1]), 
                                                      self.world.currency_name, group[0].name,
                                                      group[0].id, group[0].area.name)
            i += 1
        if not sl:
            sl = 'Nothing.'
        return sl
    
    def has_item(self, keyword):
        """If this merchant have an item with the given keyword, return it,
        else return None.
        """
        if self.sale_items is None:
            self.assemble_sale_list()
        return item in self.sale_items
    
    def build_set_markup(self, markup, player=None):
        """Set the markup percentage for this merchant."""
        if not markup.strip():
            return 'Try: "set markup <mark-up>", or see "help merchant".'
        if not markup.isdigit():
            return 'Markup must be a number between 0 and 100.'
        mark = int(markup)
        if mark < 0 or mark > 100:
            return 'Markup must be a number between 0 and 100.'
        self.markup = mark
        self.save({'markup': self.markup})
        return 'Markup is now set to %s%%.' % (markup)
    
    def build_set_buys(self, buyer, player=None):
        """Set whether or not this merchant is a buyer."""
        if not buyer.strip():
            return 'Try "set buys <true/false>", or see "help merchant".'
        b = to_bool(buyer)
        if b is None:
            return 'Buys items can only be set to true or false.'
        self.buyer = b
        self.save({'buyer': self.buyer})
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
        if self.sale_items is None:
            self.assemble_sale_list()
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
        self.sale_items.append([item, price])
        self.save()
        return 'Merchant now sells %s.' % item.name
    
    def build_remove_item(self, item):
        """Remove one of this merchant's sale items."""
        if not item:
            return 'Try "remove item <item-id>", or see "help merchant".'
        if not item.isdigit():
            return 'Try "remove item <item-id>", or see "help merchant".'
        if self.sale_items is None:
            self.assemble_sale_list()
        item = int(item)
        if (item > len(self.sale_items)) or (item < 1):
            return 'That item doesn\'t exist.'
        # We do item - 1 because we give the user a list that starts at 1, not 0
        item_name = self.sale_items[item -1][0].name
        del self.sale_items[(item - 1)]
        self.save()
        return 'Merchant no longer sells %s.' % item_name
    

NPC_AI_PACKS = {'merchant': Merchant}