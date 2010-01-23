import os
import sys
import time
from subprocess import Popen
import signal


# H'Okay, so, first we need to set the python path...
# using __file__ and os.environ
path = os.path.abspath(os.path.dirname(__file__))
index = path.rfind('shinymud')
path = path[:index]
pypath = path + ':' + os.environ.get('PYTHONPATH', '')



def check_running():
    if os.path.exists(path + 'shinymud/data/.shinypid'):
        f = open(path + 'shinymud/data/.shinypid', 'r')
        pid = int(f.read())
        f.close()
        try:
            # Only works for unix/linux/osx that we know of. 
            # basically sends "are you there?" signal.
            os.kill(pid, 0)
        except OSError:
            # Sending signal 0 to a pid will raise an OSError exception 
            # if the pid is not running, and do nothing otherwise.
            return False
        else:
            return pid
    return False
    

def start():
    # if 'start':
    #   Fork new process, that calls "python little_server.py"
    #   write the Process Id in shinymud/data/.shinypid
    #   close the file, and we are done
    
    # build the path to the directory above shinymud
    if not check_running():
        pid = Popen(['python', path + 'shinymud/lib/little_server.py'], env={'PYTHONPATH': pypath}).pid
        f = open(path + 'shinymud/data/.shinypid', 'w')
        f.write(str(pid))
        f.close()
        print "ShinyMUD is now running."
    else:
        print "ShinyMUD is already running!"

def stop():
    # if 'stop':
    #   if .shinypid file:
    #       open the .shinypid file and read out the Process Id.
    #       call os.kill() on that process id
    #       remove the .shinypid file
    #       done
    #   else:
    #       error: shinymud not running
    pid = check_running()
    if pid:
        os.kill(pid, signal.SIGKILL)
        os.remove(path + 'shinymud/data/.shinypid')
        print 'ShinyMUD has been stopped.'
    else:
        print "ShinyMUD is not running!"



# Then we check input for 'start' 'restart' and 'stop' (maybe 'help' later?)
if len(sys.argv) == 2:
    option = sys.argv[1].lower()
    if option == 'start':
        start()
    elif option == 'stop':
        stop()
    elif option == 'restart':
        stop()
        print "Restarting in a sec!"
        for i in range(3):
            print "."
            time.sleep(1)
        start()
    else:
        print "options: start | stop | restart\n"
else:
    print "options: start | stop | restart\n"
