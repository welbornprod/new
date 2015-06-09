""" Bash plugin for New.
    -Christopher Welborn 12-25-14
"""
import os.path
from plugins import Plugin, date

template = """#!/bin/bash

# ...{description}
# {author}{date}
appname="{filename}"
appversion="0.0.1"
apppath="$(realpath "${{BASH_SOURCE[0]}}")"
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
        self.version = '0.0.3'
        self.load_config()
        self.usage = """
    Usage:
        bash [f] [description]

    Options:
        description  : Description for the doc str, quoting is optional.
        f,func       : Include an empty function.
    """

    def create(self, filename):
        """ Creates a basic bash source file. """

        if self.has_arg('f(unc)?'):
            self.debug(
                'Using function template, user args: {!r}'.format(self.args))
            self.pop_args(self.args, ('f', 'func'))
            tmplate = '\n\n'.join((template, template_func))
        else:
            tmplate = template
        author = self.config.get('author', '')
        description = ' '.join(self.args) if self.args else ''

        return tmplate.format(
            author='-{} '.format(author) if author else author,
            date=date(),
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

exports = (BashPlugin(), )
