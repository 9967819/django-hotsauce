#!/usr/bin/env
# Copyright (C) 2011-2017 Jack Bortone <jack@isotopesoftware.ca>

# Provides the argparse2.ArgumentParser class with an extra
# method to load pre-defined parser options/arguments by using
# the add_argument method. 

import argparse
import yaml
import sys

class ArgumentParserError(Exception):
    pass

class ArgumentParser(argparse.ArgumentParser):

    def __init__(self, f):
        super(ArgumentParser, self).__init__(f)

    def loadArgumentsFromString(self, source, label="command_spec", 
        nargs=1, default=None, dest=None):
        """Loads a set of predefined options from a yaml stream.
        
        Options are in the format:

        command_spec:
            name: 'config spec for project bar'
            option1:    
                alternatives: --option1
            option2:
                dest: "filename",
                nargs: 2    
            option3:
                action: "store_true"
                help_text: "runs commands xyz"
                default: False
        """
        argmap = yaml.safe_load(source)
        if not label in argmap.keys():
            raise ArgumentParserError('invalid command spec!')
        else:
            for name, opts in argmap[label].iteritems():

                arglist = ["--%s"%name,]
                
                if 'alternatives' in opts:
                    alternatives = ["-%s"%item for item in opts['alternatives'].split(',')]
                
                if len(alternatives) >= 1:
                    arglist.extend(alternatives)

                if not 'action' in opts:
                    action = 'store_true'
                else:
                    action = opts.pop('action')
                    
                help_text = opts.pop('help_text')
                default = opts.pop('default')
                dest = opts.pop('dest')

                self.add_argument(arglist, action=action, \
                    help=help_text, default=default)
                    
