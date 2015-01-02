""" Plugins package for New
    Includes the base plugin types (to be subclassed and overridden)
    and general plugin helper/loading functions.
    The raw plugins can be accessed with plugins.plugins.
"""
import json
import os
import sys
from importlib import import_module


SCRIPTDIR = os.path.abspath(sys.path[0])
DEBUG = False
plugins = {'types': {}, 'post': {}, 'deferred': {}}


def debug(*args, **kwargs):
    """ Print a message only if DEBUG is truthy. """
    if DEBUG:
        print(*args, **kwargs)


def debug_load_error(plugintype, modname, plugin, exmsg):
    """ Print a debug message about plugin load errors. """
    errmsg = 'Error loading {ptype} plugin {mod}.{plugin}: {ex}'
    debug(errmsg.format(
        ptype=plugintype,
        mod=modname,
        plugin=plugin,
        ex=exmsg))


def debug_missing(attr, plugintype, modname, plugin):
    """ Print a debug message about a plugin's missing attribute. """
    msg = 'Missing attribute \'{}\'!'.format(attr)
    debug_load_error(plugintype, modname, plugin, msg)


def do_post_plugins(fname):
    """ Handle all post-processing plugins.
        These plugins will be given the file name to work with.
        The plugin return values are not used.
        If the plugin raises pluginbase.SignalExit all processing will stop.
        Any other Exceptions are debug-printed, but processing continues.
        Returns: Number of errors encountered (can be used as an exit code)
    """
    errors = 0
    for plugin in plugins['post'].values():
        pluginret = try_post_plugin(plugin, fname)
        if pluginret == 2:
            # 2 means a SignalExit occurred.
            return errors + 1
        else:
            errors += pluginret

    # Cancel deferred plugins if there were errors.
    if errors:
        if errors == 1:
            pluralerrs = 'was 1 error'
        else:
            pluralerrs = 'were {} errors'.format(errors)
        debug('There {}.'.format(pluralerrs))
        if plugins['deferred']:
            deflen = len(plugins['deferred'])
            plural = 'plugin' if deflen == 1 else 'plugins'
            debug('Cancelling {} deferred post-{}.'.format(deflen, plural))
        return errors

    # Defferred plugins.
    for deferred in plugins['deferred'].values():
        pluginret = try_post_plugin(deferred, fname)
        if pluginret == 2:
            return errors + 1
        else:
            errors += pluginret
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
    # Normal Plugins (file-type)
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

    # Do PostPlugin and DeferredPostPlugin
    posttypes = (
        ('post', 'post-processing'),
        ('deferred', 'deferred post-processing')
    )
    for ptype, pname in posttypes:
        if plugins[ptype]:
            postlen = len(plugins[ptype])
            plural = 'plugin' if postlen == 1 else 'plugins'
            print('\nFound {} {} {}:'.format(postlen, pname, plural))
            for pname in sorted(plugins[ptype]):
                plugin = plugins[ptype][pname]
                print('    {}:'.format(pname))
                print('        {}'.format(plugin.get_desc()))


def load_config(filename):
    """ Load plugin config from a json file. """
    config = {}
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        debug('No config for plugins: {}'.format(filename))
    except EnvironmentError as exread:
        debug('Error reading config from: {}\n{}'.format(filename, exread))
    except ValueError as exjson:
        debug('Error loading json config: {}\n{}'.format(filename, exjson))
    except Exception as ex:
        debug('Error loading config: {}\n{}'.format(filename, ex))
    return config


def load_plugin_config(plugin):
    """ Load config file for a plugin instance.
        Sets plugin.config to a dict on success.
    """
    if not getattr(plugin, 'config_file', None):
        configfile = 'new.{}.json'.format(plugin.get_name())
        plugin.config_file = os.path.join(SCRIPTDIR, configfile)

    config = {}
    try:
        with open(plugin.config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        msg = 'No config file for {}: {}'
        debug(msg.format(plugin.get_name(), plugin.config_file))
    except EnvironmentError as exread:
        errmsg = 'Unable to open {} config: {}\n{}'
        debug(errmsg.format(plugin.get_name(), plugin.config_file, exread))
    except ValueError as exjson:
        errmsg = 'Error loading json from: {}\n{}'
        debug(errmsg.format(plugin.config_file, exjson))
    except Exception as ex:
        errmsg = 'Error loading plugin config: {}\n{}'
        debug(errmsg.format(plugin.config_file, ex))

    plugin.config = config


def load_plugins(plugindir):
    """ Loads all available plugins from a path.
        Returns a dict of
            {'types': {module: Plugin}, 'post': {module: PostPlugin}}
    """
    global plugins, config
    # Load general plugin config.
    config = load_config(os.path.join(SCRIPTDIR, 'new.plugins.json'))

    debug('Loading plugins from: {}'.format(plugindir))
    tmp_plugins = {'types': {}, 'post': {}, 'deferred': {}}
    disabled_deferred = config.get('disabled_deferred', [])
    disabled_post = config.get('disabled_post', [])
    disabled_types = config.get('disabled_types', [])

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
                    debug_load_error('a', modname, plugin, exname)
                    continue
                else:
                    fullname = '{}.{}'.format(modname, name)

                if isinstance(plugin, Plugin):
                    if not name:
                        debug_missing('name', 'file-type', modname, plugin)
                        continue
                    # See if the plugin is disabled.
                    if name in disabled_types:
                        skipmsg = 'Skipping disabled type plugin: {}'
                        debug(skipmsg.format(fullname))
                        continue

                    tmp_plugins['types'][name] = plugin
                    debug('loaded: {} (Plugin)'.format(fullname))
                elif isinstance(plugin, DeferredPostPlugin):
                    if not name:
                        debug_missing('name', 'deferred', modname, plugin)
                        continue
                    if name in disabled_deferred:
                        skipmsg = 'Skipping disabled deferred-post plugin: {}'
                        debug(skipmsg.format(fullname))
                        continue
                    tmp_plugins['deferred'][name] = plugin
                    debug('loaded: {} (DeferredPostPlugin)'.format(fullname))
                elif isinstance(plugin, PostPlugin):
                    if not name:
                        debug_missing('name', 'post', modname, plugin)
                        continue
                    # See if the plugin is disabled.
                    if name in disabled_post:
                        skipmsg = 'Skipping disabled post plugin: {}'
                        debug(skipmsg.format(fullname))
                        continue

                    tmp_plugins['post'][name] = plugin
                    debug('loaded: {} (PostPlugin)'.format(fullname))
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


def try_post_plugin(plugin, fname):
    """ Try running a single post-plugin.
        Returns 0 on success, 1 on failure, 2 for SignalExit.
    """
    try:
        plugin.process(fname)
    except SignalExit as exstop:
        if exstop.reason:
            errmsg = '\nFatal error in post-processing plugin \'{}\':\n{}'
            print(errmsg.format(plugin.name, exstop.reason))
            print('Cancelling all post plugins.')
            return 2
    except Exception as ex:
        errmsg = '\nError in post-processing plugin \'{}\':\n{}'
        print(errmsg.format(plugin.name, ex))
        return 1
    # Success.
    return 0


class Plugin(object):

    """ Base for file-type plugins. """
    name = None
    extensions = None
    usage = None
    load_config = load_plugin_config

    def __init__(self, name=None, extensions=None):
        self._name = None
        self.name = name
        self.extensions = extensions
        # A docopt usage string for this plugin.
        self.usage = None

    def create(self, filename, args):
        """ (unimplemented plugin description)

            This should return a string that is ready to be written to a file.
            It may raise an exception to signal that something went wrong.

            Arguments:
                args      : A list of plugin-specific arguments.
                filename  : The file name that will be written.
                            Plugins do not write the file, but the file name
                            may be useful information. The python plugin
                            uses it to create the main doc str.
        """
        raise NotImplementedError('create() must be overridden!')

    def get_name(self):
        """ Get the proper name for this plugin (no aliases). """
        if not hasattr(self, '_name'):
            self._name = None
        if not hasattr(self, 'name'):
            raise ValueError('Plugin has an empty name!')

        if self._name:
            return self._name

        if isinstance(self.name, str):
            self._name = self.name
            self.name = (self._name,)
        elif isinstance(self.name, (list, tuple)):
            if not self.name:
                # Empty name list!
                raise ValueError('Plugin has an empty name!')
            self._name = self.name[0]
        else:
            raise TypeError('Plugin.name is the wrong type!')

        return self._name

    def get_usage(self):
        """ Safely retrieve a usage string for the plugin, if any exists.
            Returns self.usage on success, or None on failure.
        """
        return getattr(self, 'usage', None)


class PostPlugin(object):

    """ Base for post-processing plugins. """
    name = None
    description = None
    load_config = load_plugin_config

    def __init__(self, name=None):
        self.name = name

    def get_desc(self):
        """ Get the description for this plugin.
            It uses the first line in process.__doc__ if self.description is
            not set.
        """
        if self.description:
            return self.description

        docs = self.process.__doc__
        if docs:
            self.description = self.process.__doc__.split('\n')[0].strip()
        else:
            self.description = '(no description)'
        return self.description

    def get_name(self):
        """ Get the name for this plugin.
            Returns a str. (empty str on failure)
        """
        return self.name if self.name else ''

    def process(self, filename):
        """ (unimplented post-plugin description)

            This should accept an existing file name and do some processing.
            It may raise an exception to signal that something went wrong.
        """
        raise NotImplementedError('process() must be overridden!')


class DeferredPostPlugin(PostPlugin):

    """ A post plugin that is 'deferred', meaning that this plugin will only
        run if all the others succeeded without an exception.
    """
    pass


class SignalAction(Exception):

    """ An  exception to raise when the plugin.create() function is a success,
        but changes need to be made to the filename.
        It has attributes that hold information about the new file.
    """

    def __init__(self, *args, message=None, filename=None, content=None):
        Exception.__init__(self, *args)
        self.message = message
        self.filename = filename
        self.content = content
        arglen = len(args)
        if args:
            if not self.message:
                self.message = args[0]
            arglen = len(args)
            if arglen > 2:
                if not self.filename:
                    self.filename = args[1]
                if not self.content:
                    self.content = args[2]
            elif arglen > 1:
                if not self.filename:
                    self.filename = args[1]


class SignalExit(Exception):

    """ An exception to raise when a plugin wants to stop the rest of the
        plugins from running. In other words, stop and exit completely.
        The plugin may give a reason/message by initializing with a str as the
        first argument.
        Example:
            raise pluginbase.SignalExit('Program was not installed!')
    """

    def __init__(self, *args):
        self.reason = args[0] if args else None
