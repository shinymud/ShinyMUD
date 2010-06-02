import re

class TextEditMode(object):
    """The mode for editing large amounts of text, such as rooms or descriptions."""
    
    def __init__(self, player, obj, obj_attr, edit_text, format='paragraph'):
        self.pc = player
        self.active = True
        self.state = self.edit_intro
        self.name = 'TextEditMode'
        self.edit_object = obj
        self.edit_attribute = obj_attr
        self.format = format
        self.command_form = re.compile(r'(@(?P<cmd>\w+))([ ]+(?P<line>\d+))?([ ]+(?P<args>.*))?')
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
        self.edit_lines = self._format_for_editor(edit_text)
    
    def edit_intro(self):
        """What TextEditMode should do when it first starts up."""
        self.show_progress()
        self.state = self.process_input
    
    def process_input(self):
        if self.pc.inq:
            line = self.pc.inq[0].replace('\n', '').replace('\r', '')
            if line.startswith('@'):
                # player is submitting a command, parse it!
                cmd, line_num, args = self.command_form.match(line).group('cmd', 'line', 'args')
                args = {'line': line_num, 'args': args}
                if cmd and cmd in self.edit_commands:
                    self.edit_commands[cmd](**args)
                else:
                    self.pc.update_output('Type @help for a list of editor commands.')
            else:
                if self.format == 'paragraph':
                    if len(self.edit_lines) < 1:
                        # OMG, the list is empty! Start the first line!
                        self.edit_lines.append(line)
                    elif self.edit_lines[-1].endswith(('.', '?', '!')):
                        # The last line was finished, put this text on a new
                        # line
                        self.edit_lines.append(line)
                    else:
                        # The last line wasn't finished, let's append this
                        # input to the last line
                        self.edit_lines[-1] = self.edit_lines[-1] + ' ' + line
                else:
                    # For a script, we want each command to start on a new line
                    self.edit_lines.append(line)
                self.pc.update_output('')
            del self.pc.inq[0]
    
    def show_progress(self, **args):
        show_text = '%s for %s so far:\n' % (self.edit_attribute.capitalize(), 
                                             self.edit_object.name)
        lines = ''
        i = 1 # Lists start at 1 for mere-mortals ;)
        for line in self.edit_lines:
                lines += '%s) %s\n' % (str(i), line)
                i += 1
        if not lines:
            lines = '1)\n'
        self.pc.update_output(show_text + lines)
    
    def preview_text(self, **args):
        preview = 'Preview %s of %s:\n' % (self.edit_attribute, self.edit_object.name)
        preview += '    ' + self._format()
        self.pc.update_output(preview)
    
    def help(self, **args):
        desc = "Enter your " + self.edit_attribute + ", one sentence per line, until you are\n" +\
        "finished. The following commands are quite useful:\n"
        self.pc.update_output(desc)
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
        self.pc.update_output(commands)
    
    def finish_editing(self, **args):
        """The player has finished editing their text; save it and exit TextEditMode."""
        self.pc.update_output('%s for %s has been saved.\n' % (self.edit_attribute.capitalize(),
                                                                 self.edit_object.name))
        self.active = False
        save_text = self._format()
        setattr(self.edit_object, self.edit_attribute, save_text)
        self.edit_object.save({self.edit_attribute: save_text})
    
    def cancel_edit(self, **args):
        self.pc.update_output('Reverting to original %s. Any changes have been discarded.' %
                                                                                self.edit_attribute)
        self.active = False
    
    def clear_description(self, **args):
        self.edit_lines = []
        self.pc.update_output('%s cleared.' % self.edit_attribute.capitalize())
    
    def replace_line(self, **args):
        try:
            line_number = int(args.get('line'))
        except:
            self.pc.update_output('%s is not a valid line number.' % args.get('line'))
        else:
            if (line_number > 0) and (line_number <= len(self.edit_lines)):
                self.edit_lines[line_number-1] = args.get('args')
                self.pc.update_output('Line replaced.')
                self.show_progress()
            else:
                self.pc.update_output('%s is not a valid line number.' % str(line_number))
        
    def insert_line(self, **args):
        try:
            line_number = int(args.get('line'))
        except:
            self.pc.update_output('%s is not a valid line number.' % args.get('line'))
        else:
            if (line_number > 0) and (line_number <= len(self.edit_lines)):
                self.edit_lines.insert(line_number-1, args.get('args'))
                self.pc.update_output('Line replaced.\n')
                self.show_progress()
            else:
                self.pc.update_output('%s is not a valid line number.' % args.get('line'))
    
    def delete_line(self, **args):
        try:
            line_number = int(args.get('line'))
        except:
            self.pc.update_output('%s is not a valid line number.' % line_number)
        else:
            if (line_number > 0) and (line_number <= len(self.edit_lines)):
                del self.edit_lines[line_number-1]
                self.pc.update_output('Line deleted.\n')
                self.show_progress()
            else:
                self.pc.update_output('%s is not a valid line number.' % str(line_number))
    
    def _format_for_editor(self, edit_text):
        """Format the text to be edited so that it looks nice in the editor."""
        if self.format == 'paragraph':
            edit_text = edit_text.replace('\n', ' ').replace(
                                          '.', '.\n').replace(
                                          '?', '?\n').replace(
                                          '!', '!\n')
            lines = [line.strip() for line in edit_text.split('\n') if line]
        else:
            lines = edit_text.split('\n')
        return lines
    
    def _format(self):
        """Formats the text according to the style specified by self.format."""
        if self.format == 'paragraph':
            text = ' '.join(self.edit_lines).strip()
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
        elif self.format == 'script':
            text = '\n'.join(self.edit_lines)
        return text
    
