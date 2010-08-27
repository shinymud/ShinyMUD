#!/usr/bin/env python
"""shinycron.py

This script is meant to be called by a cron job. It's purpose is to make sure
that the shinymud server is running, and if not, to restart it. If you have your
email settings configured in your shinymud config file, this script will also
attempt to email anyone in the CRON_NOTIFY list (also in the shinymud config) of
its escapades. Don't worry, it will only email you if the mud actually crashed.

Type the following command in a terminal to edit your crontab file:
crontab -e

Add a new entry to your crontab file that calls the shinycron.py file, like
this one:
0 * * * * python /home/someuser/shinymud/src/shinymud/data/shinycron.py

That one calls the shinycron.py file every hour. Make sure you include the
absolute path to the shinycron.py file, or things won't work.
"""

import os
import sys
import traceback

path = os.path.abspath(os.path.dirname(__file__))
index = path.rfind('shinymud')
path = path[:index]
pypath = path + ':' + os.environ.get('PYTHONPATH', '')
sys.path.insert(0, path)

from shinymud.lib.shinymail import ShinyMail
from shinymud.data.config import CRON_NOTIFY, GAME_NAME, EMAIL_ENABLED
from shinymud.main import start

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
        # Since we got here, we know the mud crashed because it didn't have time
        # to clean up its pid file.
        result = start()
        if EMAIL_ENABLED and CRON_NOTIFY:
            mail = ShinyMail(CRON_NOTIFY, 'Warning: %s Crashed!' % GAME_NAME)
            mail.message = """This is an automatic notification that your %s \
game server has crashed. I tried restarting the server with the following result:

*****************************************************
%s
*****************************************************

Cheers,
Your Friendly %s Cron-job
""" % (GAME_NAME, result, GAME_NAME)
            death_path = path + 'shinymud/data/logs/death_errors.log'
            print "Deathpath is : " + death_path
            if os.path.exists(death_path):
                print "Death path exists."
                mail.message += """\nP.S. - I've attached the death_errors.log \
file to help you figure out what went wrong. Good luck!\n"""
                fp = open(death_path, 'r')
                mail.attach_text_file('death_errors.log', fp.read())
                fp.close()
            
            mail.send()
    else:
        # The game is running. No action necessary
        pass
else:
    # The server hasn't been started yet, or was shut down on purpose. No action
    # necessary.
    pass
