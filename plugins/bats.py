""" Bats plugin for New.
    -Christopher Welborn 05-06-15
"""

import os.path

from plugins import Plugin, date, fix_author

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

    docopt = True
    usage = """
    Usage:
        bats [-s] [-t]

    Options:
        -s,--setup     : Include setup() function.
        -t,--teardown  : Include teardown() function.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a Bats test file (bash automated testing). """
        if self.argd['--setup']:
            setup = template_setup
        else:
            setup = ''
        if self.argd['--teardown']:
            teardown = template_teardown
        else:
            teardown = ''

        return template.format(
            author=fix_author(self.config.get('author', None)),
            date=date(),
            name=os.path.splitext(os.path.split(filename)[-1])[0],
            setup=setup,
            teardown=teardown
        )

exports = (BatsPlugin,)
