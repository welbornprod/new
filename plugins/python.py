""" Python plugin for New.
    -Christopher Welborn 12-25-14
"""
from plugins import Plugin


class PythonPlugin(Plugin):

    def __init__(self):
        self.name = ('python', 'py')
        self.extensions = ('.py',)

    def create(self):
        print('PYTHON NOT IMPLENTED')
        return False

plugins = (PythonPlugin(),)
