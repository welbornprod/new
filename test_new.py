#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" test_new.py
    Unit tests for new.py v. 0.0.1

    -Christopher Welborn 01-26-2016
"""

import os
import sys
import unittest

# If this fails we have problems.
import plugins

# Can be set for more output.
plugins.DEBUG = False
SCRIPTDIR = os.path.abspath(sys.path[0])
PLUGINDIR = os.path.join(SCRIPTDIR, 'plugins')

print('Loading plugins from: {}'.format(PLUGINDIR))
plugins.load_plugins(PLUGINDIR)
if not all(len(plugins.plugins[k]) > 0 for k in plugins.plugins):
    print(
        'Failed to load any plugins: {!r}'.format(plugins.plugins),
        file=sys.stderr)
    sys.exit(1)


class NewTest(unittest.TestCase):
    """ Tests for New. Ensures that plugins initialize and create content,
        or raise the proper errors.
    """

    def setUp(self):
        # Empty command line arg dict to build on.
        self.default_args = {
            'ARGS': [],
            'PLUGIN': None,
            'FILENAME': None,
            '-c': False,
            '--config': False,
            '-C': False,
            '--pluginconfig': False,
            '-d': False,
            '--dryrun': False,
            '-D': False,
            '--debug ': False,
            '-H': False,
            '--pluginhelp': False,
            '-h': False,
            '--help ': False,
            '-p': False,
            '--plugins ': False,
            '-x': False,
            '--executable': False,
            '-v': False,
            '--version ': False,
        }
        # Save a local reference to plugin classes.
        self.plugins = {k: v for k, v in plugins.plugins.items()}
        self.types = [p for p in self.plugins['types'].values()]
        self.post = [p for p in self.plugins['post'].values()]
        self.deferred = [p for p in self.plugins['deferred'].values()]
        self.default_plugin = plugins.get_plugin_default(_name='python')

    def iter_plugin_classes(self):
        """ Iterate through all loaded plugin classes. """
        for pluginset in self.plugins.values():
            yield from (p for p in pluginset.values())

    def get_argd(self, updatedict=None):
        """ Get an updated arg dict. """
        d = {k: v for k, v in self.default_args.items()}
        if updatedict is None:
            return d
        d.update(updatedict)
        return d

    def test_determine_plugin_byboth(self):
        """ Plugins can be determined by both name and file name. """
        argd = self.get_argd({'PLUGIN': 'text', 'FILENAME': 'test.txt'})
        cls = plugins.determine_plugin(argd)
        self.assertIsNot(
            cls,
            self.default_plugin,
            msg='\n'.join((
                'Failed to determine plugin by name and file name:',
                '  FILENAME: {a[FILENAME]!r}',
                '    PLUGIN: {a[PLUGIN]!r}'
            )).format(a=argd)
        )

    def test_determine_plugin_byfile(self):
        """ Plugins can be determined by file name. """
        argd = self.get_argd({'FILENAME': 'test.txt'})
        cls = plugins.determine_plugin(argd)
        self.assertIsNot(
            cls,
            self.default_plugin,
            msg='Failed to determine plugin by file name: {!r}'.format(
                argd['FILENAME']
            )
        )

    def test_determine_plugin_byname(self):
        """ Plugins can be determined by name. """
        argd = self.get_argd({'PLUGIN': 'text'})
        cls = plugins.determine_plugin(argd)
        self.assertIsNot(
            cls,
            self.default_plugin,
            msg='Failed to determine plugin by explicit name: {!r}'.format(
                argd['PLUGIN']
            )
        )

    def test_get_plugin_byext(self):
        """ Plugins can be loaded by file extension. """
        ext = 'test.txt'
        cls = plugins.get_plugin_byext(ext)
        self.assertIsNotNone(
            cls,
            msg='get_plugin_byext returned None for a known file extension!'
        )
        self.assertIsNot(
            cls,
            self.default_plugin,
            msg='Failed to load plugin by file extension: {!r}'.format(cls)
        )

    def test_get_plugin_byname(self):
        """ Plugins can be loaded by name. """
        name = 'text'
        cls = plugins.get_plugin_byname(name)

        self.assertIsNotNone(
            cls,
            msg='get_plugin_byname returned None for a known plugin!'
        )
        self.assertIsNot(
            cls,
            self.default_plugin,
            msg='Failed to load plugin by explicit name: {!r}'.format(cls)
        )

    def test_plugin_create(self):
        """ Filetype plugins should create. (unless allow_blank is set) """
        for cls in self.types:
            plugin = cls()
            # Notify plugin that this is just a test (disabled side-effects)
            plugin.dryrun = True
            try:
                content = plugin._create('no file', [])
            except plugins.SignalAction as sigaction:
                # Some plugins create through signals, to change content
                # or change the file name.
                self.assertTrue(
                    sigaction.content,
                    msg='Plugin signalled with no content!: {}'.format(
                        plugin.get_name()
                    )
                )
            else:
                # Content was supposed to be returned normally.
                if plugin.allow_blank:
                    self.assertIsNone(
                        content,
                        msg='Blank plugin created content: {}'.format(
                            plugin.get_name()
                        )
                    )
                else:
                    self.assertIsNotNone(
                        content,
                        msg='Plugin failed to create content: {}'.format(
                            plugin.get_name()
                        )
                    )

    def test_plugin_init(self):
        """ Plugins should initialize """

        for cls in self.iter_plugin_classes():
            self.assertTrue(
                isinstance(cls(), plugins.PluginBase),
                msg='Failed to initialize {ptype} plugin: {pname}'.format(
                    ptype=cls.__name__,
                    pname=cls.get_name())
            )

    def test_plugins_loaded(self):
        """ load_plugins should set plugins.plugins to non-empty values. """
        for key in ('types', 'post', 'deferred'):
            self.assertTrue(
                plugins.plugins.get(key, {}),
                msg='Global file {!r} plugins were not loaded!'.format(key)
            )

if __name__ == '__main__':
    print('{!r}'.format(plugins.plugins))
    sys.exit(unittest.main(argv=sys.argv))
