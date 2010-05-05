import hashlib

from shinymud.lib.ansi_codes import CONCEAL, CLEAR

class PassChangeMode(object):
    """A mode for changing a player's password."""
    
    def __init__(self, player):
        self.player = player
        self.active = True
        self.state = self.get_input
        self.next_state = self.verify_password
        self.name = 'PassChangeMode'
        self.verify_count = 1
        self.password = None
        self.intro = 'Type your current password, or "cancel" to cancel.\n' +\
                     'Current password: ' + CONCEAL
        header = ' Password Change '.center(self.player.win_size[0], '-') + '\n'
        self.player.update_output(header + self.intro, False)
    
    def get_input(self):
        """Get the player's input if there is any.
        """
        if len(self.player.inq) > 0:
            # We've got something to work with!
            arg = self.player.inq[0].strip().replace('\r', '').replace('\n', '')
            del self.player.inq[0]
            self.next_state(arg)
    
    def verify_password(self, p):
        """Verify the player's current password before we change it.
        p -- the player's input (supposed to be their current password)
        """
        if p.lower() == 'cancel':
            self.player.update_output(CLEAR + 'CANCEL: Aborting password change.')
            self.active = False
        else:
            passwd = hashlib.sha1(p).hexdigest()
            if passwd == self.player.password:
                self.player.update_output(CLEAR + 'New password: ' + CONCEAL, False)
                self.next_state = self.new_password
            else:
                if self.verify_count >= 3:
                    self.player.update_output(CLEAR + 'Three incorrect password attempts; aborting password change.')
                    self.active = False
                else:
                    self.player.update_output(CLEAR + 'Incorrect password.')
                    self.player.update_output(self.intro, False)
                    self.verify_count += 1
    
    def new_password(self, p):
        """Change the password the player's password.
        p -- the player's input (their desired new password)
        """
        if self.password:
            passwd = hashlib.sha1(p).hexdigest()
            if passwd == self.password:
                self.player.password = passwd
                self.player.save({'password': self.player.password})
                self.player.update_output(CLEAR + 'Password change successful. Don\'t forget it!')
                self.active = False
            else:
                self.player.update_output(CLEAR + 'Those passwords didn\'t match.\nNew password: ' + CONCEAL, False)
                self.password = None
        else:
            self.password = hashlib.sha1(p).hexdigest()
            self.player.update_output(CLEAR + 'Type new password again to confirm: ' + CONCEAL, False)
    
