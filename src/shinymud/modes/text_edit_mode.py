import re
import logging

class TextEditMode(object):
    
    def __init__(self, user, obj, obj_attr, edit_text, formatted=True):
        self.user = user
        self.active = True
        self.state = self.edit_intro
        self.name = 'TextEditMode'
        self.edit_object = obj
        self.edit_attribute = obj_attr
        self.formatted = formatted
        self.command_form = re.compile(r'(@(?P<cmd>\w+))([ ]+(?P<line>\d+))?([ ]+(?P<args>.*))?')
        self.log = logging.getLogger('TextEditMode')
        self.edit_commands = {'show': self.show_progress,
                              'help': self.help,
                              'done': self.finish_editing,
                              'clear': self.clear_description,
                              'preview': self.preview_text,
                              'delete': self.delete_line,
                              'cancel': self.cancel_edit,
                              'replace': self.replace_line,
                              'insert': self.insert_line
                             }
        self.unfinished_line = ''
        edit_text = edit_text.replace('\n', ' ').replace(
                                      '.', '.\n').replace(
                                      '?', '?\n').replace(
                                      '!', '!\n')
        self.edit_lines = [line.strip() for line in edit_text.split('\n') if line]
        
    
    def edit_intro(self):
        self.show_progress()
        self.state = self.process_input
    
    def process_input(self):
        if self.user.inq:
            line = self.user.inq[0].replace('\n', '')
            if line.startswith('@'):
                # user is submitting a command, parse it!
                cmd, line_num, args = self.command_form.match(line).group('cmd', 'line', 'args')
                args = {'line': line_num, 'args': args}
                if cmd and cmd in self.edit_commands:
                    self.edit_commands[cmd](**args)
                else:
                    self.user.update_output('Type @help for a list of editor commands.\n')
            
            else:
                if line.endswith(('.', '?', '!')):
                    if self.unfinished_line:
                        self.edit_lines.append(self.unfinished_line + line)
                        self.unfinished_line = ''
                    else:
                        self.edit_lines.append(line)
                else:
                    self.unfinished_line += line
                self.user.update_output('')
            del self.user.inq[0]
    
    def show_progress(self, **args):
        show_text = '%s for %s so far:\n' % (self.edit_attribute.capitalize(), self.edit_object.name)
        lines = ''
        i = 1
        for line in self.edit_lines:
                lines += '%s) %s\n' % (str(i), line)
                i += 1
        if self.unfinished_line:
            lines += '%s) %s\n' % (str(i), self.unfinished_line)
        if not lines:
            lines = '1)\n'
        self.user.update_output(show_text + lines)
    
    def preview_text(self, **args):
        preview = 'Preview %s of %s:\n' % (self.edit_attribute, self.edit_object.name)
        if self.formatted:
            if self.unfinished_line:
                preview += self._format(' '.join(self.edit_lines.append(self.unfinished_line)))
            else:
                preview += self._format(' '.join(self.edit_lines))
        self.user.update_output(preview + '\n')
    
    def help(self, **args):
        desc = "Enter your " + self.edit_attribute + ", one sentence per line, until you are\n" +\
        "finished. The following commands are quite useful:\n"
        self.user.update_output(desc)
        commands = "    @done - saves your progress and exits the editor.\n" +\
                   "    @cancel - quit the editor without saving changes.\n" +\
                   "    @show - display your progress so far, line by line.\n" +\
                   "    @preview - preview the formatted version of your text.\n" +\
                   "    @clear - clears ALL of your progress, giving you an empty slate.\n" +\
                   "    @delete line# - delete a specific line.\n" +\
                   "    @replace line# new_sentence - replace a line with a new sentence:\n" +\
                   "        e.g. \"@replace 5 My new sentence.\"\n" +\
                   "    @insert line# new_sentence - inserts a sentence at line#:\n" +\
                   "        e.g. \"@insert 1 My new sentence.\"\n"
        self.user.update_output(commands)
    
    def finish_editing(self, **args):
        """The user has finished editing their text; save it and exit TextEditMode."""
        self.user.update_output('%s for %s has been saved.\n' % (self.edit_attribute.capitalize(),
                                                                 self.edit_object.name))
        self.active = False
        if self.unfinished_line:
            self.edit_lines.append(self.unfinished_line)
        save_text = self._format(' '.join(self.edit_lines))
        setattr(self.edit_object, self.edit_attribute, save_text)
        self.edit_object.save({self.edit_attribute: save_text})
    
    def cancel_edit(self, **args):
        self.user.update_output('Reverting to original %s. Any changes have been discarded.\n' %
                                                                                self.edit_attribute)
        self.active = False
    
    def clear_description(self, **args):
        self.edit_lines = []
        self.user.update_output('%s cleared.\n' % self.edit_attribute.capitalize())
    
    def replace_line(self, **args):
        try:
            line_number = int(args.get('line'))
        except:
            self.user.update_output('%s is not a valid line number.\n' % line_number)
        else:
            if (line_number > 0) and (line_number <= len(self.edit_lines)):
                self.edit_lines[line_number-1] = args.get('args')
                self.user.update_output('Line replaced.\n')
                self.show_progress()
            else:
                self.user.update_output('%s is not a valid line number.\n' % str(line_number))
        
    def insert_line(self, **args):
        try:
            line_number = int(args.get('line'))
        except:
            self.user.update_output('%s is not a valid line number.\n' % args.get('line'))
        else:
            if (line_number > 0) and (line_number <= len(self.edit_lines)):
                self.edit_lines.insert(line_number-1, args.get('args'))
                self.user.update_output('Line replaced.\n')
                self.show_progress()
            else:
                self.user.update_output('%s is not a valid line number.\n' % args.get('line'))
    
    def delete_line(self, **args):
        try:
            line_number = int(args.get('line'))
        except:
            self.user.update_output('%s is not a valid line number.\n' % line_number)
        else:
            if (line_number > 0) and (line_number <= len(self.edit_lines)):
                del self.edit_lines[line_number-1]
                self.user.update_output('Line deleted.\n')
                self.show_progress()
            else:
                self.user.update_output('%s is not a valid line number.\n' % str(line_number))
    
    def _format(self, text):
        """Formats the text into an english-style paragraph."""
        # add an indent to the beginning of the paragraph
        text = '    ' + text.strip()
        text = text.replace('\n', ' ')
        index = 0
        while len(text[index:]) > 72:
            new_index = text.rfind(' ', index, index+72)
            if new_index == -1:
                text = text[0:index+72] + '\n' + text[index+72:]
                index = index + 72
            else:
                text = text[0:new_index] + '\n' + text[new_index+1:]
                index = new_index
        return text
    
