""" Clisp plugin for New.
    -Christopher Welborn 9-10-15
"""
import os
from plugins import date, Plugin

template = """#!/usr/bin/env clisp
;;; {name}
;;; ...
;;; {author}{date}

"""


class LispPlugin(Plugin):

    """ Creates a blank text file (no content). """

    name = ('lisp', 'clisp')
    extensions = ('.lsp', '.lisp', '.cl')
    version = '0.0.1'
    
    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a blank text file (no content). """
        author = self.config.get('author', None)
        _, basename = os.path.split(filename)
        return template.format(
            name=os.path.splitext(basename)[0],
            author='-{} '.format(author) if author else '',
            date=date()
        )


exports = (LispPlugin, )
