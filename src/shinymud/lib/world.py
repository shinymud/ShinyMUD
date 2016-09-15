import threading
import time
import logging
import logging.handlers

from shinymud.lib.db import DB
from shinymud.data.config import *

class World(object):
    _instance = None
    @classmethod
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(World, cls).__new__(
                                  cls)
        return cls._instance
    
    def __init__(self, conn=None):
        if getattr(self, '_initialized', False):
            return # don't overwrite old values!
        self._initialized = True
        self.configure_logs()
        self.player_list = {}
        self.player_delete = []
        self.battles = {}
        self.battles_delete = []
        self.player_list_lock = threading.Lock()
        self.shutdown_flag = False
        self.areas = {}
        self.db = DB(self.log, conn=conn)
        self.default_location = None
        self.currency_name = CURRENCY
        self.login_greeting = ''
        self.uptime = time.time()
        self.active_npcs = []
        
        try:
            greet_file = open(ROOT_DIR + '/login_greeting.txt', 'r')
        except Exception as e:
            self.log.error('Error opening login_greeting.txt: ' + str(e))
        else:
            text = greet_file.read()
            self.login_greeting = text.split('\n')
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
    
    def configure_logs(self):
        format = "%(asctime)s %(levelname)s %(funcName)s:%(lineno)d | %(message)s"
        self.log = logging.getLogger('SHINYMUD')
        shiny_handler = logging.handlers.RotatingFileHandler(
                        SHINYMUD_LOGFILE, 'a', SHINYMUD_MAXBYTES, SHINYMUD_NUMFILES)
        shiny_handler.setFormatter(logging.Formatter(format))
        self.log.addHandler(shiny_handler)
        self.log.setLevel(SHINYMUD_LOGLEVEL)
        
        self.play_log = logging.getLogger('SOCIAL')
        social_handler = logging.handlers.RotatingFileHandler(
                         SOCIAL_LOGFILE, 'a', SOCIAL_MAXBYTES, SOCIAL_NUMFILES)
        social_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        self.play_log.addHandler(social_handler)
        self.play_log.setLevel(SOCIAL_LOGLEVEL)
    
    def cleanup(self):
        """Do any cleanup that needs to be done after a turn. This includes
        deleting players from the playerlist if they have logged out."""
        for player in self.player_delete:
            del self.player_list[player]
        self.player_delete = []
        for battle in self.battles_delete:
            del self.battles[battle]
        self.battles_delete = []
    
    def start_turning(self):
        while not self.shutdown_flag:
            start = time.time()
            # Go through active npcs
            for i in reversed(xrange(len(self.active_npcs))):
                if not self.active_npcs[i].do_tick():
                    del self.active_npcs[i]
            # Manage player list
            self.player_list_lock.acquire()
            list_keys = self.player_list.keys()
            for key in list_keys:
                self.player_list[key].do_tick()
            self.cleanup()
            list_keys = self.player_list.keys()
            for key in list_keys:
                self.player_list[key].send_output()
            self.player_list_lock.release()
            
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
    
    def area_add(self, area):
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
    
    def destroy_area(self, area_name, playername):
        """Destroy an entire area! TODO: whoa nelly, they want to destroy a
        whole area! We should really make sure that's what they want by adding
        an extra game state that blocks all actions until they confirm. """
        self.log.warning('%s is attempting to destroy area %s.' % (playername, area_name))
        area = self.get_area(area_name)
        if not area:
            return 'Area %s doesn\'t exist.\n' % area_name
        if self.default_location and self.default_location.area == area:
            self.default_location = None
        for player in self.player_list.values():
            if player.location and (player.location.area.name == area.name):
                player.update_output('You are wisked to safety as the world collapses around you.\n')
                player.location.remove_char(player)
                player.location = self.default_location
            if player.mode and (player.mode.name == 'BuildMode'):
                if player.mode.edit_area and (player.mode.edit_area.name == area_name):
                    player.mode.edit_area = None
                    player.mode.edit_object = None
                    if playername != player.name:
                        player.update_output('The area you were working on was just nuked by %s.\n' % 
                                                                            playername.capitalize())
            if player.last_mode and (player.last_mode.name == 'BuildMode'):
                if player.last_mode.edit_area and (player.last_mode.edit_area.name == area_name):
                    player.last_mode.edit_area = None
                    player.last_mode.edit_object = None
                    if playername != player.name:
                        player.update_output('The area you were working on was just nuked by %s.\n' %
                                                                            playername.capitalize())
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
        self.log.debug('About to destroy the rooms.')
        for room in room_keys:
            self.log.debug(area.destroy_room(room))
        self.log.debug('Should have destroyed the rooms')
        area.destruct()
        del self.areas[area.name]
        area.name = None
        self.log.info('%s destroyed area %s.' % (playername, area_name))
        return 'Area %s was successfully destroyed. I hope you meant to do that.\n' % area_name
    
# ************************ Player Functions ************************
# Here exist all the functions that the world uses to manage the players
# it contains.
    def tell_players(self, message, exclude_list=[], color=wecho_color):
        """Tell all available players in the world a message.
        A player is considered unavailable if the are on the exclude list,
        or not in BuildMode or NormalMode."""
        message = color + message + clear_fcolor
        for player in self.player_list.values():
            if player.name in exclude_list:
                pass
            elif player.mode and player.mode.name != 'BuildMode':
                pass
            else:
                player.update_output(message)
    
    def has_player(self, name):
        """Return true if the world has this player's name in its player list."""
        if name in self.player_list:
            return True
        return False
    
    def player_exists(self, player_name):
        """ See if a player's character exists in the database. Return True if
        it exists, false if it does not.
        """
        row = self.db.select('* from player where name=?', [player_name])
        if row:
            return True
        return False
    
    def get_player(self, name):
        """Return a player if that player's name exists in the player list."""
        return self.player_list.get(name)
    
    def player_add(self, player):
        key = player.name
        if isinstance(key, basestring):
            key = key.lower()
        self.player_list[key] = player
    
    def player_remove(self, playername):
        """Add a player's name to the world's delete list so they get removed
        from the playerlist on the next turn."""
        if isinstance(playername, basestring):
            playername = playername.lower()
        self.player_delete.append(playername)
    
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
    
# ********************** NPC Functions **********************
# Here exist all the function that the world uses to manage active npcs
    def npc_subscribe(self, npc):
        """Add an npc to the world's active_npcs list."""
        self.active_npcs.append(npc)
    
