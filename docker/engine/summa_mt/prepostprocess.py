#!/usr/bin/env python3

import sys, os, select, regex, split_sentences, logging
import unicodedata, yaml, codecs
import apply_bpe

from subprocess import Popen, PIPE

from split_sentences import SentenceSplitter, force_split_long_sentences
from normalize_punctuation import Normalizer
from truecase import Truecaser

logger  = logging.getLogger(__name__)
basedir = os.path.realpath(os.path.dirname(__file__))

class external_call:
    def __init__(self,cmd):
        self.cmd = cmd.split()
        return
    def __call__(self,line):
        pipe = Popen(self.cmd,stdin=PIPE,stdout=PIPE)
        out,err = pipe.communicate(input=line.encode('utf8'))
        return out.decode('utf8')

class BPE_Wrapper:
    def __init__(self,config):
        assert 'codes' in config
        codes = codecs.open(config['codes'], encoding='utf8')
        if 'vocabulary' in config:
            vfile = codecs.open(config['vocabulary'], encoding='utf8')
            vthresh = int(config['vocabulary-threshold'])
            vocab = apply_bpe.read_vocabulary(vfile,vthresh)
        else: vocab = None
        sep = config.get('separator','@@')
        gloss = config.get('glossaries',None)
        merges = int(config.get('merges','-1').replace('K','000'))
        self.bpe = apply_bpe.BPE(codes, merges, sep, vocab, gloss)
        return
    def __call__(self,line):
        return self.bpe.process_line(line)
    pass # end of class definition


class PunctFix:
    def __init__(self):
        self.pattern = regex.compile(r'(\s)([.!?](?:\s*&quot;)?)\s*(\w+)', regex.U)
        return

    def fix(m):
        """
        replace ' .new-sentence' with '. Nextsent'
            and ' ." new-sentence' with '. " Nextsent'
        """
        # Inherited from an older version. These errors should be fixed upstream. UG
        
        w = m.group(3)
        w = w[0].upper() + w[1:]
        punct = m.group(2)
        if punct[-1] == '"':
            w = punct[-1] + ' ' + w
            punct = punct[:-1].strip()
        return '%s%s%s' % (punct, m.group(1), w)

    def __call__(self,line):
        return self.pattern.sub(self.fix, line)

class RegexRule:
    def __init__(self,pattern,replacement):
        self.replacement = replacement
        self.pattern = regex.compile(pattern)
        return

    def __call__(self,line):
        return self.pattern.sub(self.replacement,line)
    
class Step:
    def __init__(self,config):
        self.name = config['action']
        self.external = False
        
        if 'command' in config:
            self.external = True
            self.action = external_call(config['command'])

        elif 'normalize_unicode' == self.name:
            form = config.get('form','NFC')
            self.action = lambda x: unicodedata.normalize(form, x)

        elif 'truecase' == self.name:
            self.action = Truecaser(config['model'])

        elif 'split_sentences' == self.name:
            maxlen = config['max-sentence-length']
            self.action = SentenceSplitter(config['language'],maxlen)

        elif 'bpe' == self.name:
            self.action = BPE_Wrapper(config)

        elif 'de-bpe' == self.name:
            pattern = config.get('pattern',r'@@(?: +|$)')
            self.action = lambda x: regex.sub(pattern,'', x)

        elif 'fix-eos' == self.name:
            self.action = PunctFix()
            
        elif 'fix-quotes' == self.name:
            self.action = RegexRule(r'" (.*?) "','"\1"')

        elif 'apply-regex' == self.name:
            self.action = RegexRule(config['pattern'], config['replacement'])

        else:
            raise "Unknown preprocessing step"
        return

    def __call__(self, input):
        if type(input).__name__ == "list":
            if self.external:
                result = self.action("\n".join(input).strip()+"\n").strip()
                return [line.strip() for line in result.split('\n')]
            else:
                return [self.action(line).strip() for line in input]
        result = self.action(input)
        if type(result).__name__ == "str":
            return result.strip()
        return [line.strip() for line in result]
    
class PrePostProcessor:
    def __init__(self,config):
        if type(config).__name__ == "str":
            config = yaml.load(open(config))
        self.steps = [Step(s) for s in config['steps']]
        return
    
    def __call__(self,text):
        for step in self.steps: text = step(text)
        return text 
    pass # end of class definition

if __name__ == "__main__":
    config = yaml.load(open(sys.argv[1]).read())
    process = PrePostProcessor(config)    
    for line in sys.stdin:
        line = line.strip()
        result = process(line) if len(line) else ""
        print(result)
        # print(result if type(result).__name__ == 'str' else '\n'.join(result))
        # pass
    
            
