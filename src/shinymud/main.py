import os
import sys
import time
from subprocess import Popen
import signal
import hashlib
import logging

# H'Okay, so, first we need to set the python path...
# using __file__ and os.environ
path = os.path.abspath(os.path.dirname(__file__))
index = path.rfind('shinymud')
path = path[:index]
pypath = path + ':' + os.environ.get('PYTHONPATH', '')
sys.path.insert(0, path)

from shinymud.data.config import GAME_NAME, DB_NAME, PORT
from shinymud.lib.ansi_codes import CLEAR, CONCEAL
from shinymud.lib.world import World
from shinymud.models.user import *
from shinymud.lib.db import DB
from shinymud.models.schema import initialize_database
from shinymud.lib.sport import SPort


# Create the logs folder if it doesn't exist
if not os.path.exists(path + 'shinymud/data/logs'):
    os.mkdir(path + 'shinymud/data/logs')

def check_running():
    """Return true if the MUD is running, false if it's not."""
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
    #   Fork new process, that calls "python shiny_server.py"
    #   write the Process Id in shinymud/data/.shinypid
    #   close the file, and we are done
    
    # build the path to the directory above shinymud
    if not check_running():
        pid = Popen(['python', path + 'shinymud/lib/shiny_server.py'], env={'PYTHONPATH': pypath}).pid
        f = open(path + 'shinymud/data/.shinypid', 'w')
        f.write(str(pid))
        f.close()
        print "%s is now running on port %s." % (GAME_NAME, str(PORT))
    else:
        print "%s is already running!" % GAME_NAME

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
        print '%s has been stopped.' % GAME_NAME
    else:
        print "%s is not running!" % GAME_NAME

def create_god(world):
    """Create a god character and save it to this MUD's db."""
    save = {'permissions': GOD | PLAYER}
    user = User(('foo', 'bar'))
    
    save['name'] = ''
    print "Please choose a name for your character. It should contain \n" +\
          "alphanumeric characters (letters and numbers) ONLY."
    while not save['name']:
        username = (raw_input("Name: ")).strip()
        if not username.isalpha():
            print "That is not a valid name. Please choose another."
        else:
            row = user.world.db.select('password,dbid FROM user WHERE name=?', [username])
            if row:
                print "A user with that name already exists. Please choose Another."
            else:
                print "You're sure you want your name to be '%s'?" % username
                choice = (raw_input("Yes/No: ")).strip()
                if choice.lower().startswith('y'):
                    save['name'] = username
                else:
                    print "Ok, we'll start over. Which name do you REALLY want?"
    
    save['password'] = ''
    while not save['password']:
        passwd1 = (raw_input(CLEAR + "Choose a password: " + CONCEAL)).strip()
        passwd2 = (raw_input(CLEAR + "Re-enter password to confirm: " + CONCEAL)).strip()
        if passwd1 == passwd2:
            save['password'] = hashlib.sha1(passwd1).hexdigest()
            print CLEAR
        else:
            print CLEAR + "Your passwords did not match. Please try again."
    
    save['gender'] = ''
    print "What gender shall your character be?"
    while not save['gender']:
        print "Choose from: neutral, female, or male."
        gender = (raw_input('Gender: ')).strip()
        if gender in ['male', 'female', 'neutral']:
            save['gender'] = gender
        else:
            print "That's not a valid gender."
    
    user.userize(**save)
    user.save()
    print 'Your character, %s, has been created.' % user.fancy_name()

def setup():
    """Initialize the game!"""
    if os.path.exists(DB_NAME):
        print "\nYou already have a game set up.\n\n" +\
              "If you're trying to create a god character, call this script again with the \n" +\
              "create_god option. If you want to import ShinyMUD's pre-packaged game areas, \n" +\
              "you can already do that in-game (see 'help import')."
    else:
        world = setup_stub_world()
        print "\nWelcome to the ShinyMUD setup wizard! First, we'll have you create a \n" +\
              "God character (a character with full in-game priviliges).\n"
        create_god(world)
        r = SPort.list_importable_areas()
        if os.path.exists(PREPACK):
            print "\nDo you want to import our pre-packaged starting areas?"
            print "You can always delete them later in-game if you don't want them anymore."
            choice = (raw_input("Yes/No: ")).strip()
            if choice.lower().startswith('y'):
                try:
                    print ' Importing Built-in Areas '.center(50, '-')
                    result = SPort(PREPACK).import_list('all')
                    print result
                except Exception, e:
                    print "Oops, there was an error importing our areas.\n" +\
                          "No worries, we'll just start your game and you can try again later."
            else:
                print "Skipping the area import then. You can always import them later in-game anyway."
        print "\nOk, you're done with the game setup! Now starting your game server..."
        start()

def setup_stub_world():
    world = World()
    world.db = DB()
    initialize_database(world.db.conn)
    return world

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
    elif option == 'setup':
        setup()
    elif option == 'create_god':
        if check_running():
            print "%s is currently running. " % GAME_NAME +\
                  "You'll have to stop it to create a God character."
        else:
            create_god(setup_stub_world())
    else:
        print "options: start | stop | restart | setup | create_god\n"
else:
    print "options: start | stop | restart | setup | create_god\n"

