""" Bash plugin for New.
    -Christopher Welborn 12-25-14
"""
from plugins import Plugin
from datetime import datetime
date = lambda: datetime.strftime(datetime.today(), '%m-%d-%y')

template = """#!/bin/bash

# ...
# -Christopher Welborn {date}
APPPATH=\"\$(realpath \${{BASH_SOURCE[0]}})\"
APPDIR=\"\$(dirname \"\$APPPATH\")\"
APPNAME=\"\$(basename \"\$APPPATH\")\"
VERSION=\"0.0.1\"
""".format(date=date())

template_func = """
function XXXX {

}
"""


class BashPlugin(Plugin):

    """ A bash template with only the basics. """

    def __init__(self):
        self.name = ('bash', 'sh')
        self.extensions = ('.sh', '.bash')
        self.usage = """
    Usage:
        bash f

    Options:
        f,func  : Include an empty function.
    """

    def create(self, args):
        if ('f' in args) or ('func' in args):
            return '\n\n'.join((template, template_func))

        return template

plugins = (BashPlugin(), )
