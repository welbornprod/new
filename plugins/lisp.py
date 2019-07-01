""" Clisp plugin for New.
    -Christopher Welborn 9-10-15
"""
import os
from plugins import Plugin, date, fix_author

template = """#!/usr/bin/env clisp
;;; {name}
;;; ...
;;; {author}{date}

"""


class LispPlugin(Plugin):

    """ Creates a basic lisp file (no content). """

    name = ('lisp', 'clisp')
    extensions = ('.lsp', '.lisp', '.cl')
    version = '0.0.3'
    config_opts = {'author': 'Default author name for all files.'}

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a blank text file (no content). """
        _, basename = os.path.split(filename)
        return template.format(
            name=os.path.splitext(basename)[0],
            author=fix_author(self.config.get('author', None)),
            date=date()
        )


exports = (LispPlugin, )
