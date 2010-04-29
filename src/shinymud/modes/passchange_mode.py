import hashlib

from shinymud.lib.ansi_codes import CONCEAL, CLEAR

class PassChangeMode(object):
    """A mode for changing a user's password."""
    
    def __init__(self, user):
        self.user = user
        self.active = True
        self.state = self.get_input
        self.next_state = self.verify_password
        self.name = 'PassChangeMode'
        self.verify_count = 1
        self.password = None
        self.intro = 'Type your current password, or "cancel" to cancel.\n' +\
                     'Current password: ' + CONCEAL
        header = ' Password Change '.center(self.user.win_size[0], '-') + '\n'
        self.user.update_output(header + self.intro, False)
    
    def get_input(self):
        """Get the user's input if there is any.
        """
        if len(self.user.inq) > 0:
            # We've got something to work with!
            arg = self.user.inq[0].strip().replace('\r', '').replace('\n', '')
            del self.user.inq[0]
            self.next_state(arg)
    
    def verify_password(self, p):
        """Verify the user's current password before we change it.
        p -- the user's input (supposed to be their current password)
        """
        if p.lower() == 'cancel':
            self.user.update_output(CLEAR + 'CANCEL: Aborting password change.')
            self.active = False
        else:
            passwd = hashlib.sha1(p).hexdigest()
            if passwd == self.user.password:
                self.user.update_output(CLEAR + 'New password: ' + CONCEAL, False)
                self.next_state = self.new_password
            else:
                if self.verify_count >= 3:
                    self.user.update_output(CLEAR + 'Three incorrect password attempts; aborting password change.')
                    self.active = False
                else:
                    self.user.update_output(CLEAR + 'Incorrect password.')
                    self.user.update_output(self.intro, False)
                    self.verify_count += 1
    
    def new_password(self, p):
        """Change the password the user's password.
        p -- the user's input (their desired new password)
        """
        if self.password:
            passwd = hashlib.sha1(p).hexdigest()
            if passwd == self.password:
                self.user.password = passwd
                self.user.save({'password': self.user.password})
                self.user.update_output(CLEAR + 'Password change successful. Don\'t forget it!')
                self.active = False
            else:
                self.user.update_output(CLEAR + 'Those passwords didn\'t match.\nNew password: ' + CONCEAL, False)
                self.password = None
        else:
            self.password = hashlib.sha1(p).hexdigest()
            self.user.update_output(CLEAR + 'Type new password again to confirm: ' + CONCEAL, False)
    
