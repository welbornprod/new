""" Perl plugin for New.
    -Christopher Welborn 5-21-15
"""
from plugins import Plugin, date, fix_author

# Not much here right now.
template = """#!/usr/bin/env perl

# ...{description}
# {author}{date}

"""


class PerlPlugin(Plugin):

    """ A very basic perl template. """

    name = ('perl', 'pl')
    extensions = ('.pl', '.perl')
    version = '0.0.2'

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a basic perl source file. """
        return template.format(
            author=fix_author(self.config.get('author', None)),
            date=date(),
            description=' '.join(self.argv))


exports = (PerlPlugin, )
