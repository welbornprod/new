""" Plugins package for New """
import os
from importlib import import_module
from .plugins import Plugin, PostPlugin


DEBUG = False


def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def get_plugin_byname(plugins, name, use_post=False):
    """ Retrieves a plugin module by name or alias.
        Returns the plugin on success, or None on failure.
    """
    name = name.lower()
    for plugin in plugins['types'].values():
        names = (pname.lower() for pname in plugin.name)
        if name in names:
            return plugin

    # Try post plugins also.
    if use_post:
        for plugin in plugins['post'].values():
            if name == plugin.name.lower():
                return plugin
    # The plugin wasn't found.
    return None


def is_py_file(path):
    """ Returns True if the given path looks like a python file name.
        Dunder names will return False (__init__.py is not included)
        The plugins module itself is skipped also.
    """
    return (
        path.endswith('.py') and
        (not path.startswith('__')) and
        (not path == 'plugins'))


def iter_py_files(path):
    """ Iterate over all python file names in the given path. """
    try:
        for path in [f for f in os.listdir(path) if is_py_file(f)]:
            yield path
    except EnvironmentError as exenv:
        debug('Error listing plugins: {}'.format(exenv))
    except Exception as ex:
        debug('Error iterating plugins: {}'.format(ex))


def list_plugins(plugins):
    """ Lists all plugins for the terminal. """
    if plugins['types']:
        indent = 20
        aliaslbl = 'aliases'.rjust(indent)
        extlbl = 'extensions'.rjust(indent)
        print('\nFound {} file-type plugins:'.format(len(plugins['types'])))
        for pname in sorted(plugins['types']):
            plugin = plugins['types'][pname]
            print('    {}:'.format(pname))
            if len(plugin.name) > 1:
                print('{}: {}'.format(aliaslbl, ', '.join(plugin.name)))
            print('{}: {}'.format(extlbl, ', '.join(plugin.extensions)))

    if plugins['post']:
        postlen = len(plugins['post'])
        print('\nFound {} post-processing plugins:'.format(postlen))
        for pname in sorted(plugins['post']):
            plugin = plugins['post'][pname]
            print('    {}:'.format(pname))
            print('        {}'.format(plugin.get_desc()))


def load_plugins(plugindir):
    """ Loads all available plugins from a path.
        Returns a dict of
            {'types': {module: Plugin}, 'post': {module: PostPlugin}}
    """
    debug('Loading plugins from: {}'.format(plugindir))
    plugins = {'types': {}, 'post': {}}
    for modname in (os.path.splitext(p)[0] for p in iter_py_files(plugindir)):
        try:
            module = import_module(modname)
            # Ensure that the module has a list of plugins to work with.
            if (not (hasattr(module, 'plugins')
                     and isinstance(module.plugins, (list, tuple)))):
                debug('{} ({}) is not a valid plugin!'.format(modname, module))
                continue

            for plugin in module.plugins:
                if isinstance(plugin, Plugin):
                    name = getattr(plugin, 'name', None)
                    if not name:
                        errmsg = 'Missing name for file-type plugin: {}.{}'
                        debug(errmsg.format(modname, plugin))
                        continue
                    if isinstance(name, str):
                        plugin.name = (name,)
                    elif isinstance(name, (list, tuple)):
                        try:
                            name = name[0]
                        except IndexError:
                            errmsg = 'Empty name for plugin in: {}'
                            debug(errmsg.format(modname))
                            continue
                    else:
                        debug('Bad type for name in: {}'.format(modname))
                        continue
                    plugins['types'][name] = plugin
                    statmsg = 'Plugin loaded: {}.{}'
                    debug(statmsg.format(modname, name))
                elif isinstance(plugin, PostPlugin):
                    name = getattr(plugin, 'name', None)
                    if not name:
                        errmsg = 'Missing name for post-plugin: {}.{}'
                        debug(errmsg.format(modname, plugin))
                        continue
                    plugins['post'][name] = plugin
                    statmsg = 'PostPlugin loaded: {}.{}'
                    debug(statmsg.format(modname, name))
        except ImportError as eximp:
            # Bad plugin, cannot be imported.
            debug('Plugin failed: {}\n{}'.format(modname, eximp))
        except Exception as ex:
            print('\nError loading plugin: {}\n{}'.format(modname, ex))
    return plugins
