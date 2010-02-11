from shinymud.commands import *

import re
import random

class CharacterEffect(object):
    
    def __init__(self, **args):
        self.duration = args.get('duration')
        self.char = args.get('char')
        self.dbid = args.get('dbid')
        self.intensity = args.get('intensity')
    
    def copy(self):
        new_me = CharacterEffect(**self.to_dict())
        return new_me
    
    def to_dict(self):
        d = {}
        d['duration'] = self.duration
        d['char'] = self.char
        d['intensity'] = self.intensity
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def save(self, save_dict=None):
        pass
    

EFFECTS = CommandRegister()
class Drunk(CharacterEffect):
    """A drunkeness effect."""
    name = 'drunk'
    def execute(self):
        if self.duration > 0:
            self.duration -= 1
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
        """Some words appear in a different order than the user wrote them.
        """
        words = text.split()
        if len(words) < 4:
            return args
        else:
            x = random.randrange(0, len(words)-1)
            swap = words[x]
            words[x] = words[x + 1]
            words[x + 1] = swap
        return " ".join(words)
    
    def hiccup_filter(self, text):
        """Adds *hic* in between random words.
        """
        if random.randint(1):
            return text
        words = text.split()
        x = random.randrange(len(words))
        ret = words[:x]
        ret.append['*hic*']
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
    
    def __str__(self):
        string = 'drunkeness +' + str(self.drunk_level)
        return string

EFFECTS.register(Drunk, Drunk.name)
