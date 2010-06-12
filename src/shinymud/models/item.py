from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.models import Column, model_list
from shinymud.models.shiny_types import *
from shinymud.models.item_types import ITEM_TYPES
from shinymud.lib.world import World

import types
import re

class Item(Model):
    """The base class that both BuildItem and GameItem should inherit from."""
    db_columns = Model.Columns + [
        Column('name', default='New Item'),
        Column('title', default='A shiny new object sparkles happily'),
        Column('description', default='This is a shiny new object'),
        Column('keywords', read=read_list, write=write_list, copy=copy_list, default=[]),
        Column('weight', type="INTEGER", read=int, write=int, default=0),
        Column('base_value', type="INTEGER", read=int, write=int, default=0),
        Column('carryable', read=to_bool, default=True)
    ]
    
    def __init__(self, args={}):
        Model.__init__(self, args)
        if not self.keywords and self.name:
            self.keywords = self.name.lower().split()
        self.item_types = {}
    
    # def to_dict(self):
    #     d = {}
    #     d['name'] = self.name
    #     d['title'] = self.title
    #     d['description'] = self.description
    #     d['keywords'] = ','.join(self.keywords)
    #     d['weight'] = self.weight
    #     d['base_value'] = self.base_value
    #     d['carryable'] = str(self.carryable)
    #     if self.dbid:
    #         d['dbid'] = self.dbid
    # 
    #     return d
    
    def save(self):
        save_all = False
        if not self.dbid:
            save_all = True
        Item.save(self)
        if save_all:
            # First time build item is saved, save item_types.
            for value in self.item_types.values():
                value.save()
    
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
    db_table_name = 'build_item'
    db_columns = Item.db_columns + [
        Column('area', foreign_key=('area', 'name'), read=read_area, write=write_area),
        Column('id')
    ]
    
    def load_extras(self):
        for key, value in ITEM_TYPES.items():
            row = self.world.db.select('* FROM %s WHERE build_item=?' % key,
                                       [self.dbid])
            if row:
                row[0]['build_item'] = self
                self.item_types[key] = value(row[0])
    
    @classmethod
    def create(cls, area=None, item_id=0):
        """Create a new item."""
        new_item = cls({'area':area.name, 'id':item_id})
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
                  'base value: ' + str(self.base_value) + ' '+ self.world.currency_name + '\n'
        for itype in self.item_types.values():
            string += str(itype)
        string += ('-' * 50)
        return string
    
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
        item = GameItem(self.copy_save_attrs(), spawn_id=spawn_id)
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
    db_table_name = 'game_item'
    db_columns = Item.db_columns + [
        Column('build_area'),
        Column('build_id'),
        Column('container', type="INTEGER", read=int, write=int, foreign_key=(GameItem.db_table_name, 'dbid'), cascade="ON DELETE"),
        Column('owner_id', type="INTEGER", read=int, write=int, foreign_key=('player', 'dbid'), cascade='ON DELETE')
    ]
    
    def _set_owner(self, owner):
        self._owner = owner
        self.owner_id = owner.id if owner else None
    
    def _get_owner(self):
        return getattr(self, '_owner', None)
    
    owner = property(_get_owner, _set_owner)
    
    def __init__(self, args={}, spawn_id=None):
        self.spawn_id = spawn_id
        Item.__init__(self, **args)
    
    def load_extras(self):
        for key, value in ITEM_TYPES.items():
            row = self.world.db.select('* FROM %s WHERE game_item=?' % key,
                                       [self.dbid])
            if row:
                row[0]['game_item'] = self
                self.item_types[key] = value(row[0])
    

model.register(BuildItem)
model.register(GameItem)