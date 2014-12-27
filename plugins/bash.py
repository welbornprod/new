""" Bash plugin for New.
    -Christopher Welborn 12-25-14
"""
from plugins import Plugin


class BashPlugin(Plugin):

    def __init__(self):
        self.name = ('bash', 'sh')
        self.extensions = ('.sh', '.bash')

    def create(self):
        print('BASH NOT IMPLENTED')
        return False

plugins = (BashPlugin(),)
