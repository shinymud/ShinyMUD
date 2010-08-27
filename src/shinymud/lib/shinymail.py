from shinymud.data.config import EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER,\
                                 EMAIL_HOST_PASSWORD, EMAIL_USE_TLS

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

class ShinyMail(object):
    """ShinyMail constructs and sends emails."""
    
    def __init__(self, to, subject, message='', from_addr=None):
        """Initialize our mail object.
        
        to - a list of email addresses
        subject - a string containing the email subject
        message - a string containing the body of the email message (optional)
        from_addr - a string containing the from address (optional, will be
        replaced with EMAIL_HOST_USER from the shinymud config file if not given)
        """
        self.email = MIMEMultipart()
        self.email['Subject'] = subject
        self.email['To'] = ', '.join(to)
        self.email['From'] = from_addr or EMAIL_HOST_USER
        self.message = message
        self.files = []
    
    def attach_text_file(self, filename, content):
        """Attach a text file to this email.
        """
        msg = MIMEText(content)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        self.files.append(msg)
    
    def send(self):
        """Actually send an email.
        """
        self._construct_email()
        con = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        con.set_debuglevel(1)
        if EMAIL_USE_TLS:
            con.starttls()
        if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
            # Don't bother logging in if USER and PASS don't exist
            con.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        con.sendmail(self.email['From'], self.email['To'], self.email.as_string())
        con.quit()
    
    def _construct_email(self):
        """Construct the email in a sensible order.
        
        Make sure the message text comes before any extra attachments.
        """
        if self.message:
            self.email.attach(MIMEText(self.message))
        for f in self.files:
            self.email.attach(f)
        if not self.email.get_payload():
            # Don't let people send blank emails. That's mean.
            raise Exception("You can't send an email without any content!")
    
