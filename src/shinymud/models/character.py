class Character(object):
    """The basic functionality that both player characters (users) and 
    non-player characters share.
    """
    def is_npc(self):
        """Return True if this character is an npc, false if it is not."""
        if self.char_type == 'npc':
            return True
        return False
    
    def save(self, save_dict=None):
        """Save the character to the database."""
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict(self.char_type, save_dict)
            else:    
                self.world.db.update_from_dict(self.char_type, self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict(self.char_type, 
                                                       self.to_dict())
    
    def destruct(self):
        """Remove the character from the database."""
        if self.dbid:
            self.world.db.delete('FROM %s WHERE dbid=?' % self.char_type, 
                                 [self.dbid])
    
    def item_add(self, item):
        """Add an item to the character's inventory."""
        item.owner = self.dbid
        item.save({'owner': item.owner})
        self.inventory.append(item)
    
    def item_remove(self, item):
        """Remove an item from the character's inventory."""
        if item in self.inventory:
            item.owner = None
            item.save({'owner': item.owner})
            self.inventory.remove(item)
    
    def check_inv_for_keyword(self, keyword):
        """Check all of the items in a character's inventory for a specific
        keyword. Return the item that matches that keyword, else return None.
        """
        keyword = keyword.strip().lower()
        for item in self.inventory:
            if keyword in item.keywords:
                return item
        return None
    
    def go(self, room, tell_new=None, tell_old=None):
        """Go to a specific room."""
        if self.position[0] == 'standing':
            if room:
                if self.location:
                    if tell_old:
                        self.location.tell_room(tell_old, [self.name])
                    self.location.user_remove(self)
                if self.location and self.location == room:
                    self.update_output('You\'re already there.\n')
                else:
                    self.location = room
                    self.update_output(self.look_at_room())
                    self.location.user_add(self)
                    if tell_new:
                        self.location.tell_room(tell_new, [self.name])
            else:
                self.log.debug('We gave %s a nonexistant room.' % self.name)
        else:
            self.update_output('You better stand up first.')
    
