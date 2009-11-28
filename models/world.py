from models import ShinyModel
import threading
import time
import logging

class World(ShinyModel):
    
    def __init__(self):
        self.user_list = {}
        self.user_delete = []
        self.user_list_lock = threading.Lock()
        self.shutdown_flag = False
        self.listening = True
        self.areas = {}
        self.log = logging.getLogger('World')
        
        
    def cleanup(self):
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
            
            # time.sleep(0.25)
        self.listening = False
    
