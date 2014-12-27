""" Bash plugin for New.
    -Christopher Welborn 12-25-14
"""
from plugins import Plugin
from datetime import datetime
date = lambda: datetime.strftime(datetime.today(), '%m-%d-%y')

# TODO: Implement plugin args (hopefully using docopt)
USAGE = """
    Usage:
        {script} [-f]

    Options:
        -f,--function  : Include an empty function in the template.
"""

TEMPLATE = """#!/bin/bash

# ...
# -Christopher Welborn {date}
APPPATH=\"\$(realpath \${{BASH_SOURCE[0]}})\"
APPDIR=\"\$(dirname \"\$APPPATH\")\"
APPNAME=\"\$(basename \"\$APPPATH\")\"
VERSION=\"0.0.1\"
""".format(date=date())

TEMPLATE_FUNC = """
function XXXX {

}
"""


class BashPlugin(Plugin):

    def __init__(self):
        self.name = ('bash', 'sh')
        self.extensions = ('.sh', '.bash')

    def create(self):
        return TEMPLATE

plugins = (BashPlugin(),)
