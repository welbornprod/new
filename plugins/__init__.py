""" Plugins package for New """
import os
from importlib import import_module
from .pluginbase import Plugin, PostPlugin, SignalAction, SignalExit


DEBUG = False
plugins = {'types': {}, 'post': {}}


def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def do_post_plugins(fname):
    """ Handle all post-processing plugins.
        These plugins will be given the file name to work with.
        The plugin return values are not used.
        If the plugin raises pluginbase.SignalExit the processing will stop.
        Any other Exceptions are ignored.
        Returns: Number of errors encountered (can be used as an exit code)
    """
    errors = 0
    for plugin in (p for p in plugins['post'].values()):
        try:
            plugin.process(fname)
        except SignalExit as exstop:
            if exstop.reason:
                errmsg = '\nFatal error in post-processing plugin \'{}\':\n{}'
                print(errmsg.format(plugin.name, exstop.reason))
                print('Cancelling all post plugins.')
                return errors + 1
        except Exception as ex:
            errmsg = '\nError in post-processing plugin \'{}\':\n{}'
            print(errmsg.format(plugin.name, ex))
            errors += 1
    return errors


def get_plugin_byname(name, use_post=False):
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


def get_usage(indent=0):
    """ Get a usage and options from all plugins.
        Returns (usage_str, options_str).
    """
    usage, opts = [], []
    for plugin in plugins['types'].values():
        pluginusage = getattr(plugin, 'usage', None)
        if not pluginusage:
            continue
        elif not isinstance(pluginusage, dict):
            errmsg = 'Bad type for {} plugin usage: {}'
            debug(errmsg.format(plugin.get_name(), type(pluginusage)))
            continue
        pluginstrfmt = '{{script}} {} FILENAME [-d] [-D]'
        pluginstr = pluginstrfmt.format(plugin.get_name())
        for usageline in pluginusage.get('usage', []):
            usage.append(' '.join((pluginstr, usageline)))
        opts.extend(pluginusage.get('options', []))
    indention = ' ' * indent
    joiner = '\n{}'.format(indention)
    return (
        ''.join((indention, joiner.join(sorted(usage)))),
        ''.join((indention, joiner.join(sorted(opts)))))


def is_plugins_module(module):
    """ Returns True if the module appears to be a plugins module. """
    return (
        hasattr(module, 'plugins') and
        isinstance(module.plugins, (list, tuple)))


def is_py_file(path):
    """ Returns True if the given path looks like a python file name.
        Dunder names will return False (__init__.py is not included)
        The plugins module itself is skipped also.
    """
    return (
        path.endswith('.py') and
        (not path.startswith('__')) and
        (not path == 'pluginbase.py'))


def is_invalid_plugin(plugin):
    """ Determine whether a plugin has all the needed attributes.
        Returns a str (invalid reason) for invalid plugins.
        Returns None if it is a valid plugin.
    """
    if not hasattr(plugin, 'name'):
        return 'missing name attribute'

    if isinstance(plugin, Plugin):
        if not hasattr(plugin, 'extensions'):
            return 'missing extensions attribute'
        elif not hasattr(plugin, 'create'):
            return 'missing create function'
        return None
    elif isinstance(plugin, PostPlugin):
        if not hasattr(plugin, 'process'):
            return 'missing process function'
        return None

    return 'not a Plugin or PostPlugin'


def iter_py_files(path):
    """ Iterate over all python file names in the given path. """
    try:
        for path in [f for f in os.listdir(path) if is_py_file(f)]:
            yield path
    except EnvironmentError as exenv:
        debug('Error listing plugins: {}'.format(exenv))
    except Exception as ex:
        debug('Error iterating plugins: {}'.format(ex))


def list_plugins():
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
    global plugins
    debug('Loading plugins from: {}'.format(plugindir))
    tmp_plugins = {'types': {}, 'post': {}}
    errmsg = 'Error loading {ptype} plugin {mod}.{plugin}: {ex}'
    for modname in (os.path.splitext(p)[0] for p in iter_py_files(plugindir)):
        # debug('Importing: {}'.format(modname))
        try:
            module = import_module(modname)
            # Ensure that the module has a list of plugins to work with.
            if not is_plugins_module(module):
                debug('{} ({}) is not a valid plugin!'.format(modname, module))
                continue
            # debug('    {} ..imported.'.format(modname))
        except ImportError as eximp:
            # Bad plugin, cannot be imported.
            debug('Plugin failed: {}\n{}'.format(modname, eximp))
            continue
        try:
            for plugin in module.plugins:
                # debug('    checking {}'.format(plugin))
                invalidreason = is_invalid_plugin(plugin)
                if invalidreason:
                    errmsg = 'Not a valid plugin {}: {}'
                    debug(errmsg.format(plugin, invalidreason))
                    continue
                try:
                    name = plugin.get_name()
                except (TypeError, ValueError) as exname:
                    debug(errmsg.format(
                        ptype='a',
                        mod=modname,
                        plugin=plugin,
                        ex=exname))
                    continue

                if isinstance(plugin, Plugin):
                    if not name:
                        debug(errmsg.format(
                            ptype='file-type',
                            mod=modname,
                            plugin=plugin,
                            ex='Missing attribute \'name\'!'))
                        continue
                    tmp_plugins['types'][name] = plugin
                    statmsg = 'Plugin loaded: {}.{}'
                    debug(statmsg.format(modname, name))
                elif isinstance(plugin, PostPlugin):
                    if not name:
                        debug(errmsg.format(
                            ptype='post',
                            mod=modname,
                            plugin=plugin,
                            ex='Missing attribute \'name\'!'))
                        continue
                    tmp_plugins['post'][name] = plugin
                    statmsg = 'PostPlugin loaded: {}.{}'
                    debug(statmsg.format(modname, name))
                else:
                    debug('\nNon-plugin type!: {}'.format(type(plugin)))
        except Exception as ex:
            print('\nError loading plugin: {}\n{}'.format(modname, ex))
    # Set module-level copy of plugins.
    plugins = tmp_plugins


def plugin_help(plugin):
    """ Show help for a plugin if available. """
    if not hasattr(plugin, 'usage'):
        print('\nNo help available for {}.\n'.format(plugin.get_name()))
        return False

    print('\nHelp for {}:'.format(plugin.get_name()))
    print(plugin.usage)
    return True


def print_inplace(s):
    """ Overwrites the last printed line. """
    print('\033[2A\033[160D')
    print(s)
