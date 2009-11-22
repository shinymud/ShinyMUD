import threading
import time

class World(object):
    user_list = {}
    user_delete = []
    user_list_lock = threading.Lock()
    shutdown_flag = False
    listening = True
    
    def __init__(self):
        pass
    
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
            
            time.sleep(0.25)
        self.listening = False
    
