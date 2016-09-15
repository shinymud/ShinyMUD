import os
import sys
import time
from subprocess import Popen
import signal
import hashlib
import shutil

# H'Okay, so, first we need to set the python path...
# using __file__ and os.environ
path = os.path.abspath(os.path.dirname(__file__))
index = path.rfind('shinymud')
path = path[:index]
pypath = path + ':' + os.environ.get('PYTHONPATH', '')
sys.path.insert(0, path)

try:
    from shinymud.data.config import *
except ImportError:
    shutil.copy(os.path.join(path,'shinymud/data/config.py-sample'),
                os.path.join(path,'shinymud/data/config.py'))
    from shinymud.data.config import *

from shinymud.lib.ansi_codes import CLEAR, CONCEAL
from shinymud.lib.world import World
from shinymud.lib.db import DB

# Create the logs folder if it doesn't exist
if not os.path.exists(os.path.join(path,'shinymud/data/logs')):
    os.mkdir(os.path.join(path,'shinymud/data/logs'))

def check_running():
    """Return true if the MUD is running, false if it's not."""
    if os.path.exists(os.path.join(path, 'shinymud/data/.shinypid')):
        f = open(os.path.join(path,'shinymud/data/.shinypid'), 'r')
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
    #   Fork new process, that calls "python shiny_server.py"
    #   write the Process Id in shinymud/data/.shinypid
    #   close the file, and we are done
    
    # build the path to the directory above shinymud
    if not check_running():
        pid = Popen(['python', os.path.join(path, 'shinymud/lib/shiny_server.py')], env={'PYTHONPATH': pypath}).pid
        f = open(os.path.join(path, 'shinymud/data/.shinypid'), 'w')
        f.write(str(pid))
        f.close()
        conns = [(str(p[0]) + ' (' + p[1] + ')') for p in CONNECTIONS]
        return "%s is now running on port(s) %s." % (GAME_NAME, ', '.join(conns))
    else:
        return "%s is already running!" % GAME_NAME

def stop():
    pid = check_running()
    if pid:
        os.kill(pid, signal.SIGKILL)
        os.remove(os.path.join(path, 'shinymud/data/.shinypid'))
        return '%s has been stopped.' % GAME_NAME
    else:
        return "%s is not running!" % GAME_NAME

def create_god(world):
    """Create a god character and save it to this MUD's db."""
    from shinymud.models.player import Player
    
    save = {'permissions': GOD | PLAYER}
    player = Player(('foo', 'bar'))
    
    save['name'] = ''
    print "Please choose a name for your character. It should contain \n" +\
          "alphanumeric characters (letters and numbers) ONLY."
    while not save['name']:
        playername = (raw_input("Name: ")).strip()
        if not playername.isalpha():
            print "That is not a valid name. Please choose another."
        else:
            row = player.world.db.select('password,dbid FROM player WHERE name=?', [playername])
            if row:
                print "A player with that name already exists. Please choose Another."
            else:
                print "You're sure you want your name to be '%s'?" % playername
                choice = (raw_input("Yes/No: ")).strip()
                if choice.lower().startswith('y'):
                    save['name'] = playername
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
        if len(gender) and gender[0].lower() in ['m', 'f', 'n']:
            save['gender'] = {'m':'male', 'f':'female', 'n':'neutral'}[gender[0].lower()]
        else:
            print "That's not a valid gender."
    
    player.playerize(save)
    player.save()
    print 'Your character, %s, has been created.' % player.fancy_name()

def setup():
    """Initialize the game!"""
    if os.path.exists(DB_NAME):
        print "\nYou already have a game set up.\n\n" +\
              "If you're trying to create a god character, call this script again with the \n" +\
              "create_god option. If you want to import ShinyMUD's pre-packaged game areas, \n" +\
              "you can already do that in-game (see 'help import')."
    else:
        world = setup_stub_world()
        from shinymud.lib.sport import inport_dir
        
        print "\nWelcome to the ShinyMUD setup wizard! First, we'll have you create a \n" +\
              "God character (a character with full in-game priviliges).\n"
        create_god(world)
        if os.path.exists(PREPACK):
            print "\nDo you want to import our pre-packaged starting areas?"
            print "You can always delete them later in-game if you don't want them anymore."
            choice = (raw_input("Yes/No: ")).strip()
            if choice.lower().startswith('y'):
                try:
                    print ' Importing Built-in Areas '.center(50, '-')
                    result = inport_dir('area', source_path=PREPACK)
                    print result
                except Exception as e:
                    print "Oops, there was an error importing our areas.\n" +\
                          "No worries, we'll just start your game and you can try again later."
            else:
                print "Skipping the area import then. You can always import them later in-game anyway."
        print "\nOk, you're done with the game setup! Now starting your game server..."
        start()

def clean():
    """Clean all the pyc files, log files, and the db file that were created by
    running the game.
    """
    def rm_pyc_files(arg, dirname, names):
        """Remove all of the .pyc files in dirname."""
        for name in names:
            if name.endswith('.pyc'):
                try:
                    os.remove(os.path.join(dirname, name))
                except Exception as e:
                    print "Error removing .pyc file: " + str(e)
    
    if check_running():
        stop()
    if os.path.exists(DB_NAME):
        print "Are you sure you want to delete your database? This will delete "
        print "any saved game data you have so far."
        choice = raw_input("Yes/No: ")
        if choice.lower().strip().startswith('y'):
            print 'Deleting database...'
            # delete the database.
            try:
                os.remove(DB_NAME)
            except Exception as e:
                print 'Error removing database: ' + str(e)
    # Delete all .pyc files in the directory
    print 'Deleting pyc files...'
    os.path.walk(path, rm_pyc_files, 'foo')
    # Delete all the .log files in the logs directory
    print 'Deleting log files...'
    if os.path.exists(os.path.join(path, 'shinymud/data/logs')):
        for logfile in os.listdir(os.path.join(path, 'shinymud/data/logs')):
            if logfile.endswith('.log'):
                try:
                    os.remove(os.path.join(path, 'shinymud/data/logs/', logfile))
                except Exception as e:
                    print 'Error removing logfile: ' + str(e)
    print "Cleaning complete!"

def setup_stub_world():
    world = World()
    from shinymud.lib.setup import initialize_database
    initialize_database()
    return world

def main():
# Then we check input for 'start' 'restart' and 'stop' (maybe 'help' later?)
    if len(sys.argv) == 2:
        option = sys.argv[1].lower()
        if option == 'start':
            print start()
        elif option == 'stop':
            print stop()
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
        elif option == 'clean':
            clean()
        else:
            print "options: start | stop | restart | setup | create_god | clean\n"
    else:
        print "options: start | stop | restart | setup | create_god | clean\n"

if __name__ == '__main__':
    main()
