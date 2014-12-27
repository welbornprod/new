""" Html plugin for New.
    -Christopher Welborn 12-25-14
"""
from plugins import Plugin


class HtmlPlugin(Plugin):

    def __init__(self):
        self.name = ('html', 'htm')
        self.extensions = ('.html', '.htm')

    def create(self):
        print('HTML NOT IMPLENTED!')
        return False

plugins = (HtmlPlugin(),)
