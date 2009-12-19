import threading
import time
import logging

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
        self.user_list_lock = threading.Lock()
        self.shutdown_flag = False
        self.listening = True
        self.areas = {}
        self.log = logging.getLogger('World')
    
    @classmethod
    def get_world(cls):
        """This will return None if world has never been initialized. Since the first thing 
        we do in our main thread is create and initialize a new world instance, the only
        way this could fail is if somehow we tried to grab the world before the main thread
        started, which really aught to be impossible."""
        return cls._instance
    
    def user_add(self, user):
        self.user_list[user.name] = user
    
    def user_remove(self, username):
        """Add a user's name to the world's delete list so they get removed from the userlist
        on the next turn."""
        self.user_delete.append(username)
    
    def new_area(self, area):
        self.areas[area.name] = area
    
    def cleanup(self):
        """Do any cleanup that needs to be done after a turn.
        This includes deleting users from the userlist if they have
        logged out."""
        for user in self.user_delete:
            del self.user_list[user]
        self.user_delete = []
    
    def start_turning(self):
        while not self.shutdown_flag:
            self.user_list_lock.acquire()
            list_keys = self.user_list.keys()
            for key in list_keys:
                self.user_list[key].do_tick()
            self.cleanup()
            list_keys = self.user_list.keys()
            for key in list_keys:
                self.user_list[key].send_output()
            self.user_list_lock.release()
            
            time.sleep(0.25)
        self.listening = False
    
# ************************ Area Functions ************************
# Here exist all the function that the world uses to manage the areas
# it contains.
    def list_areas(self):
        names = self.areas.keys()
        area_list = """______________________________________________
Areas:
    %s
______________________________________________\n""" % '\n    '.join(names)
        return area_list
    
    def get_area(self, area_name):
        if area_name in self.areas:
            return self.areas[area_name]
        return None
    
    def destroy_area(self, area_name):
        """Destroy an entire area!
        TODO: whoa nelly, they want to destroy a whole area! We should really
        make sure that's what they want by adding an extra game state that
        blocks all actions until they confirm.
        """
        return 'Someone was too lazy to implement this function. Sorry.\n'
    
