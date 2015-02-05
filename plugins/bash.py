""" Bash plugin for New.
    -Christopher Welborn 12-25-14
"""
import os.path
from plugins import Plugin, date
DATE = date()

template = """#!/bin/bash

# ...{description}
# -{author}{date}
appname="{filename}"
appversion="0.0.1"
apppath="$(realpath ${{BASH_SOURCE[0]}})"
appscript="${{apppath##*/}}"
appdir="${{apppath%/*}}"
"""

template_func = """
function XXXX {{

}}
"""


class BashPlugin(Plugin):

    """ A bash template with only the basics. """

    def __init__(self):
        self.name = ('bash', 'sh')
        self.extensions = ('.sh', '.bash')
        self.version = '0.0.1-4'
        self.load_config()
        self.usage = """
    Usage:
        bash [f] [description]

    Options:
        description  : Description for the doc str, quoting is optional.
        f,func       : Include an empty function.
    """

    def create(self, filename, args):
        """ Creates a basic bash source file. """
        if not args:
            args = self.get_default_args()

        if ('f' in args) or ('func' in args):
            self.pop_args(args, ('f', 'func'))
            tmplate = '\n\n'.join((template, template_func))
        else:
            tmplate = template
        author = self.config.get('author', '')
        date = ' {}'.format(DATE) if author else DATE
        description = ' '.join(args) if args else ''

        return tmplate.format(
            author=author,
            date=date,
            description=description,
            filename=os.path.splitext(os.path.split(filename)[-1])[0])

    def pop_args(self, lst, args):
        """ Removes any occurrence of an argument from a list.
            Modifies the list that is passed in.
            Arguments:
                lst   : List to remove from.
                args  : List/Tuple of args to remove.
        """
        for a in args:
            while lst.count(a) > 0:
                lst.remove(a)

plugins = (BashPlugin(), )
