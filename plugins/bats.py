""" Bats plugin for New.
    -Christopher Welborn 05-06-15
"""

import os.path

from plugins import Plugin, date

template = """#!/usr/bin/env bats

# {name}
# ...
# {author}{date}
{setup}
@test "..." {{
    x=""
    [ -z "$x" ]
}}
{teardown}
"""

template_setup = """
setup() {
    # Setup for each test.

}
"""

template_teardown = """
teardown() {
    # Teardown for each test.

}
"""


class BatsPlugin(Plugin):
    name = ('bats',)
    extensions = ('.bats',)
    version = '0.0.1'
    usage = """
    Usage:
        bats [s] [t]

    Options:
        s,setup     : Include setup() function.
        t,teardown  : Include teardown() function.
    """
    
    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a Bats test file (bash automated testing). """
        author = self.config.get('author', None)
        return template.format(
            author='-{} '.format(author) if author else '',
            date=date(),
            name=os.path.splitext(os.path.split(filename)[-1])[0],
            setup=template_setup if self.has_arg('^s(etup)?') else '',
            teardown=template_teardown if self.has_arg('^t(eardown)?') else ''
        )

exports = (BatsPlugin,)
