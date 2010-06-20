from shinymud.commands import *
from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *

import re
import random

class CharacterEffect(Model):
    db_columns = Model.db_columns + [
        Column('duration', type="INTEGER", read=int, write=int),
        Column('item'),
        Column('item_type')
    ]
    def __init__(self, args):
        self.duration = args.get('duration')
        self.char = args.get('char')
        self.dbid = args.get('dbid')
        self.item = args.get('item')
        self.item_type = args.get('item_type')
    
    def copy(self):
        # Want a new copy of the same class as this instance
        new_me = self.__class__(self.copy_save_attrs())
        return new_me
    
    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['duration'] = self.duration
        if self.char:
            d['char'] = self.char.dbid
        d['item'] = self.item.dbid
        d['item_type'] = self.item_type
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
EFFECTS = CommandRegister()
class Drunk(CharacterEffect):
    """A drunkeness effect."""
    name = 'drunk'
    def execute(self):
        if self.duration > 0:
            self.duration -= 1
        # We also aught to do some drunken things randomly, like the following:
        # randomly hiccup if drunk level is above 3
        # vomit and pass out if drunk level is above 5
    
    drunk_level = property(lambda self: int(self.duration / 180) + 1)
    
    def filter_speech(self, text):
        if self.drunk_level < 1:
            return text
        # disorder
        text = self.disorder_filter(text)
        if self.drunk_level < 2:
            return text
        # typos
        text = self.typo_filter(text)
        if self.drunk_level < 3:
            return text
        # yelling
        text = self.volume_filter(text)
        if self.drunk_level < 4:
            return text
        # hiccups
        text = self.hiccup_filter(text)
        if self.drunk_level < 5:
            return text
        # slurred
        return self.slurred_filter(text)
        
    
    def slurred_filter(self, text):
        """Replace any s (not immediately followed by an h) with sh to 
        imitate drunken slurring.
        """
        new_text = re.sub(r's+[^h]', 'sh', text)
        return new_text
    
    def volume_filter(self, text):
        """Make certain words upper case to imitate YELLING.
        Yells should occur for every 1 + (1/5) random words in a sentence.
        """
        words = text.split()
        yells = 1 + len(words)/5
        for i in range(yells):
            x = random.randrange(0, len(words))
            words[x] = words[x].upper()
        return ' '.join(words)
    
    def disorder_filter(self, text):
        """Some words appear in a different order than the player wrote them.
        """
        words = text.split()
        if len(words) < 4:
            return text
        else:
            x = random.randrange(0, len(words)-1)
            swap = words[x]
            words[x] = words[x + 1]
            words[x + 1] = swap
        return " ".join(words)
    
    def hiccup_filter(self, text):
        """Adds *hic* in between random words.
        """
        if random.randrange(5):
            return text
        words = text.split()
        x = random.randrange(len(words))
        ret = words[:x]
        ret.append('*hic*')
        ret.extend(words[x:])
        return " ".join(ret)
    
    def typo_filter(self, text):
        """Individual letters in a word become disordered, lending to words
        that have different meanings or become gibberish.
        """
        letters = [_ for _ in text]
        typos = 1 + len(letters)/10
        for i in range(typos):
            x = random.randrange(len(letters)-1)
            swap = letters[x]
            letters[x] = letters[x + 1]
            letters[x+1] = swap
        return "".join(letters)
    
    def combine(self, effect):
        """Combine this and another drunk effect.
        """
        self.duration += effect.duration
    
    def get_drunkness(self):
        drunk_list = {1: 'You feel slightly tipsy.',
                      2: 'You feel a bit drunk.',
                      3: 'You are drunk.',
                      4: 'You are very drunk.',
                      5: 'You are on your way to alcohol poisoning.',
                      'default': 'You are drunk.'
                     }
        if self.drunk_level > 5:
            return drunk_list.get(5)
        return drunk_list.get(self.drunk_level)
    
    def end(self):
        """What should happen when this effect ends."""
        self.char.update_output('You are sober.')
    
    def begin(self):
        """What should happen when this effect begins."""
        self.char.update_output(self.get_drunkness())
    
    def __str__(self):
        # string = 'drunkeness +' + str(self.drunk_level)
        return self.get_drunkness()
    

EFFECTS.register(Drunk, [Drunk.name])
