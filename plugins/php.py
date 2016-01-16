""" PHP plugin for New.
    Creates executable PHP scripts.
    -Christopher Welborn 12-25-14
"""
import os.path
from plugins import Plugin, date

# I'm not a php developer, and I wouldn't recommend it to someone wanting
# to learn about programming.
# However, when I run across php "oddities" I like to test them out.
# That's why this plugin exists.
template = """#!/usr/bin/env php
<?php

/*  {name}
    ...
    {author}{date}
*/


"""


class PhpPlugin(Plugin):

    name = ('php',)
    extensions = ('.php',)
    version = '0.0.1'
    description = 'Creates an executable php script.'
    
    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates an executable php script. """
        basename = os.path.split(filename)[-1]
        author = self.config.get('author', '')
        if author:
            author = '-{} '.format(author)
        return template.format(name=basename, author=author, date=date())

exports = (PhpPlugin,)
