import threading
import time
import logging
from shinymud.lib.db import DB
from shinymud.data.config import *

class World(object):
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(World, cls).__new__(
                                  cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        self.user_list = {}
        self.user_delete = []
        self.battles = {}
        self.battles_delete = []
        self.user_list_lock = threading.Lock()
        self.shutdown_flag = False
        self.listening = True
        self.areas = {}
        self.log = logging.getLogger('World')
        self.db = DB()
        self.default_location = None
        self.login_greeting = ''
        
        try:
            greet_file = open(ROOT_DIR + '/login_greeting.txt', 'r')
        except Exception, e:
            self.log.error('Error opening login_greeting.txt: ' + str(e))
        else:
            self.login_greeting = greet_file.read()
        finally:
            greet_file.close()
        if not self.login_greeting:
            self.login_greeting = 'Welcome to %s' % GAME_NAME
    
    @classmethod
    def get_world(cls):
        """This will return None if world has never been initialized. Since
        the first thing we do in our main thread is create and initialize a
        new world instance, the only way this could fail is if somehow we
        tried to grab the world before the main thread started, which really
        aught to be impossible."""
        return cls._instance
    
    def cleanup(self):
        """Do any cleanup that needs to be done after a turn. This includes
        deleting users from the userlist if they have logged out."""
        for user in self.user_delete:
            del self.user_list[user]
        self.user_delete = []
        for battle in self.battles_delete:
            del self.battles[battle]
        self.battles_delete = []
    
    def start_turning(self):
        while not self.shutdown_flag:
            start = time.time()
            # Manage user list
            self.user_list_lock.acquire()
            list_keys = self.user_list.keys()
            for key in list_keys:
                self.user_list[key].do_tick()
            self.cleanup()
            list_keys = self.user_list.keys()
            for key in list_keys:
                self.user_list[key].send_output()
            self.user_list_lock.release()
            
            # Perform round actions for active battles
            for key in self.battles.keys():
                self.battles[key].perform_round()
            
            # Reset areas that have had activity
            for area in self.areas.values():
                if area.times_visited_since_reset > 0:
                    now = time.time()
                    if (now - area.time_of_last_reset) >= RESET_INTERVAL:
                        area.reset()
                        self.log.info('Area %s has been reset.' % area.name)
            
            finish = time.time() - start
            if finish >= 1:
                self.log.critical('WORLD: Turn took longer than a sec!')
            elif finish < 0.25:
                time.sleep(0.25 - finish)
        self.listening = False
    
    def has_location(self, area_name, room_id):
        """Check if a location (room) exists given an area name and a room id.
        Returns True if the room exists, false if it doesn't.
        """
        if area_name in self.areas:
            room = self.areas.get(area_name).get_room(str(room_id))
            if room:
                return True
        return False
    
    def get_location(self, area_name, room_id):
        """Get a location (room) given an area name and a room id.
        Returns a room object, if the location exists.
        Returns false if the location doesn't exist.
        """
        if not self.has_location(area_name, room_id):
            return None
        room = self.areas.get(area_name).get_room(str(room_id))
        return room
    
# ************************ Area Functions ************************
# Here exist all the functions that the world uses to manage the areas
# it contains.
    
    def new_area(self, area):
        self.areas[area.name] = area
    
    def list_areas(self):
        names = ['%s - "%s"' % (key, value.title) for key,value in self.areas.items()]
        area_list = ' Areas '.center(50, '-') + '\n'
        if names:
            area_list += '\n'.join(names)
        else:
            area_list += 'You have no areas yet. Create some!\n'
        area_list += '\n' + '-'.center(50, '-')
        
        return area_list
    
    def area_exists(self, area_name):
        if area_name in self.areas:
            return True
        return False
    
    def get_area(self, area_name):
        if self.area_exists(area_name):
            return self.areas[area_name]
        return None
    
    def destroy_area(self, area_name, username):
        """Destroy an entire area! TODO: whoa nelly, they want to destroy a
        whole area! We should really make sure that's what they want by adding
        an extra game state that blocks all actions until they confirm. """
        area = self.get_area(area_name)
        if not area:
            return 'Area %s doesn\'t exist.\n' % area_name
        if self.default_location and self.default_location.area == area:
            self.default_location = None
        for user in self.user_list.values():
            if user.location and (user.location.area.name == area.name):
                user.update_output('You are wisked to safety as the world collapses around you.\n')
                user.location.user_remove(user)
                user.location = self.default_location
            if user.mode and (user.mode.name == 'BuildMode'):
                if user.mode.edit_area and (user.mode.edit_area.name == area_name):
                    user.mode.edit_area = None
                    user.mode.edit_object = None
                    if username != user.name:
                        user.update_output('The area you were working on was just nuked by %s.\n' % 
                                                                            username.capitalize())
            if user.last_mode and (user.last_mode.name == 'BuildMode'):
                if user.last_mode.edit_area and (user.last_mode.edit_area.name == area_name):
                    user.last_mode.edit_area = None
                    user.last_mode.edit_object = None
                    if username != user.name:
                        user.update_output('The area you were working on was just nuked by %s.\n' %
                                                                            username.capitalize())
        item_keys = area.items.keys()
        for item in item_keys:
            self.log.debug(area.destroy_item(item))
        script_keys = area.scripts.keys()
        for script in script_keys:
            self.log.debug(area.destroy_script(script))
        npc_keys = area.npcs.keys()
        for npc in npc_keys:
            self.log.debug(area.destroy_npc(npc))
        room_keys = area.rooms.keys()
        for room in room_keys:
            self.log.debug(area.destroy_room(room))
        area.destruct()
        del self.areas[area.name]
        area.name = None
        self.log.info('%s desroyed area %s.' % (username, area_name))
        return 'Area %s was successfully destroyed. I hope you meant to do that.\n' % area_name
    
# ************************ User Functions ************************
# Here exist all the functions that the world uses to manage the users
# it contains.
    def tell_users(self, message, exclude_list=[], color=wecho_color):
        """Tell all available users in the world a message.
        A user is considered unavailable if the are on the exclude list,
        or not in BuildMode or NormalMode."""
        message = color + message + clear_fcolor
        for user in self.user_list.values():
            if user.name in exclude_list:
                pass
            elif user.mode and user.mode.name != 'BuildMode':
                pass
            else:
                user.update_output(message)
    
    def has_user(self, name):
        """Return true if the world has this user's name in its user list."""
        if name in self.user_list:
            return True
        return False
    
    def get_user(self, name):
        """Return a user if that user's name exists in the user list."""
        return self.user_list.get(name)
    
    def user_add(self, user):
        key = user.name
        if isinstance(key, str):
            key = key.lower()
        self.user_list[key] = user
    
    def user_remove(self, username):
        """Add a user's name to the world's delete list so they get removed
        from the userlist on the next turn."""
        if isinstance(username, str):
            username = username.lower()
        self.user_delete.append(username)
    
# ********************** Battle Functions **********************
# Here exist all the function that the world uses to manage battles
# it contains.
    def battle_add(self, battle):
        if not self.battles:
            battle.id = 1
        else:
            battle.id = max(self.battles.keys()) + 1
        self.battles[battle.id] = battle
        self.log.debug("Battles: %s" % str(self.battles))
    
    def battle_remove(self, battle_id):
        if battle_id in self.battles:
            self.battles_delete.append(battle_id)