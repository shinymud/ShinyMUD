from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.models import to_bool
from shinymud.models.item_types import *
from shinymud.lib.world import World

import types
import logging
import re

class Item(object):
    """The base class that both BuildItem and GameItem should inherit from."""
    def __init__(self, **args):
        self.name = args.get('name', 'New Item')
        self.title = str(args.get('title', 'A shiny new object sparkles happily.'))
        self.description = args.get('description', 'This is a shiny new object.')
        self.keywords = []
        kw = args.get('keywords')
        if kw:
            self.keywords = [str(w) for w in kw.split(',')]
        else:
            self.keywords = self.name.lower().split()
        self.weight = int(args.get('weight', 0))
        self.base_value = int(args.get('base_value', 0))
        self.carryable = True
        if 'carryable' in args:
            self.carryable = to_bool(args.get('carryable'))
        self.world = World.get_world()
        self.dbid = args.get('dbid')
        self.log = logging.getLogger('BuildItem')
        self.item_types = {}
    
    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['title'] = self.title
        d['description'] = self.description
        d['keywords'] = ','.join(self.keywords)
        d['weight'] = self.weight
        d['base_value'] = self.base_value
        d['carryable'] = str(self.carryable)
        if self.dbid:
            d['dbid'] = self.dbid
        
        return d
    
    def __str__(self):
        s = ', '.join(['%s: %s' % (key,val) for key,val in self.to_dict() if key != 'dbid'])
        return s
    
    def has_type(self, t):
        """Return true if this item has an item type t, false if it does not.
        """
        return t in self.item_types
    

class BuildItem(Item):
    """BuildItem represents a prototype item created in BuildMode.
     
    BuildItems are Items that get created by a Builder during BuildMode. They
    are also the prototypes for the items that are used in-game. After a
    BuildItem has been created during BuildMode, its load() function can be used
    to create a GameItem, which is essentially a copy of the BuildItem instance
    and is meant to be used by players in-game.
    """
    def __init__(self, area=None, id='0', **args):
        Item.__init__(self, **args)
        self.area = area
        self.id = str(id)
        if self.dbid:
            for key, value in ITEM_TYPES.items():
                row = self.world.db.select('* FROM %s WHERE build_item=?' % key,
                                           [self.dbid])
                if row:
                    row[0]['build_item'] = self
                    self.item_types[key] = value(row[0])
    
    def to_dict(self):
        d = Item.to_dict(self)
        if isinstance(self.area, int):
            d['area'] = self.area
        else:
            d['area'] = self.area.dbid
        d['id'] = self.id
        return d
    
    @classmethod
    def create(cls, area=None, item_id=0):
        """Create a new item."""
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
                  'keywords: ' + str(self.keywords) + '\n' + \
                  'weight: ' + str(self.weight) + '\n' + \
                  'carryable: ' + str(self.carryable) + '\n' + \
                  'base value: ' + str(self.base_value) + self.world.currency_name + '\n'
        for itype in self.item_types.values():
            string += str(itype)
        string += ('-' * 50)
        return string
    
    def destruct(self):
        """Remove this instance and all of its item types from the database."""
        if self.dbid:
            self.world.db.delete('FROM build_item WHERE dbid=?', [self.dbid])
    
    def save(self, save_dict=None):
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict('build_item', save_dict)
            else:    
                self.world.db.update_from_dict('build_item', self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict('build_item', self.to_dict())
            for value in self.item_types.values():
                value.save()
    
    #***************** Set Basic Attribute (VIA BuildMode) Functions *****************
    def build_set_description(self, desc, player=None):
        """Set the description of this item."""
        player.last_mode = player.mode
        player.mode = TextEditMode(player, self, 'description', self.description)
        return 'ENTERING TextEditMode: type "@help" for help.\n'
    
    def build_set_title(self, title, player=None):
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
                title = title[0].capitalize() + title[1:]
        self.title = title
        self.save({'title': self.title})
        return 'Item title set.'
    
    def build_set_name(self, name, player=None):
        self.name = name
        self.save({'name': self.name})
        return 'Item name set.\n'
    
    def build_set_weight(self, weight, player=None):
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
    
    def build_set_basevalue(self, value, player=None):
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
    
    def build_set_keywords(self, keywords, player=None):
        """Set the keywords for this item.
        The argument keywords should be a string of words separated by commas.
        """
        if keywords:
            word_list = keywords.split(',')
            self.keywords = [word.strip().lower() for word in word_list]
        else:
            self.keywords = [name.lower() for name in self.name.split()]
            self.keywords.append(self.name.lower())
            
        self.save({'keywords': ','.join(self.keywords)})
        return 'Item keywords have been set.'
    
    def build_set_carryable(self, boolean, player=None):
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
    
    def build_add_type(self, item_type, item_dict=None):
        """Add a new item type to this item."""
        if not item_type in ITEM_TYPES:
            return 'That\'s not a valid item type.'
        if item_type in self.item_types:
            return 'This item is already of type %s.' % item_type
        if item_dict:
            new_type = ITEM_TYPES[item_type](item_dict)
        else:
            new_type = ITEM_TYPES[item_type]()
        new_type.build_item = self
        new_type.save()
        self.item_types[item_type] = new_type
        return 'This item is now of type %s.' % item_type
    
    def build_remove_type(self, item_type):
        if not item_type in ITEM_TYPES:
            return 'That\'s not a valid item type.'
        if not item_type in self.item_types:
            return 'This isn\'t of type %s.' % item_type
        self.world.db.delete('FROM %s where dbid=?' % item_type, [self.item_types[item_type].dbid])
        del self.item_types[item_type]
        return 'This item is no longer of type %s.' % item_type
    
    def load(self, spawn_id=None):
        """Create a GameItem with the same attributes as this prototype item.
        spawn_id -- The id of the spawn that is loading this item into a room,
        or None if this item is not being loaded by a spawn
        """
        item = GameItem(spawn_id, **self.to_dict())
        # Clear the prototype's dbid so we don't accidentally overwrite it in the db
        item.dbid = None
        item.build_area = self.area.name
        item.build_id = self.id
        for key, value in self.item_types.items():
            item.item_types[key] = value.load(item)
        return item
    

class GameItem(Item):
    """GameItem represents a "real" in-game item used by characters.
     
    GameItems are what players use in-game, and are 'copies' of their BuildItem
    counterparts.
    """
    def __init__(self, spawn_id=None, **args):
        Item.__init__(self, **args)
        # The build_area and build_id below reference this game_item's prototype;
        # that is, the BuildItem that this item was derived from. 
        self.build_area = args.get('build_area') # The area this item originated from
        self.build_id = args.get('build_id') # The build_item this item originated from
        
        self.owner_id = args.get('owner')
        self.spawn_id = spawn_id
        self.container = args.get('container')
        if self.dbid:
            for key, value in ITEM_TYPES.items():
                row = self.world.db.select('* FROM %s WHERE game_item=?' % key,
                                           [self.dbid])
                if row:
                    row[0]['game_item'] = self
                    self.item_types[key] = value(row[0])
            
    
    def to_dict(self):
        d = Item.to_dict(self)
        if self.owner:
            d['owner'] = self.owner.dbid
        if self.dbid:
            d['dbid'] = self.dbid
        if self.container:
            d['container'] = self.container.dbid
        d['build_area'] = self.build_area
        d['build_id'] = self.build_id
        return d
    
    def save(self, save_dict=None):
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict('game_item', save_dict)
            else:    
                self.world.db.update_from_dict('game_item', self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict('game_item', self.to_dict())
            # If an item has not yet been saved, its item types will not have been
            # saved either.
        for value in self.item_types.values():
            value.save()
    
    def destruct(self):
        """Remove this instance and all of its item types from the database."""
        if self.dbid:
            self.world.db.delete('FROM game_item WHERE dbid=?', [self.dbid])
    

