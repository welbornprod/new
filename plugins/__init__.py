""" Plugins package for New
    Includes the base plugin types (to be subclassed and overridden)
    and general plugin helper/loading functions.
    The raw plugins can be accessed with plugins.plugins.
"""
import inspect
import json
import os
import sys
from datetime import datetime
from enum import Enum
from importlib import import_module


SCRIPTDIR = os.path.abspath(sys.path[0])
DEBUG = False
config = {}
plugins = {'types': {}, 'post': {}, 'deferred': {}}


def conflicting_file(plugin, filearg, filename):
    """ Make sure this file name and plugin mixture isn't going to cause a
        show-stopping conflict with New.
        This only happens when creating .py files in New's directory, and only
        if they happen to have the same name as a plugin.
        Common mistake:
            When in config: {plugins : { default_plugin: 'python' }}
               And running: ./new bash
            ...creates bash.py that will be found in sys.path.
    """
    # The python plugin can create conflicting files when ran in New's dir.
    if plugin.get_name() != 'python':
        return False

    # Check for conflicting dir.
    rootdir = filearg.partition('/')[0]

    for plugintype in plugins:
        # If the filename arg matches a plugin module name we have a conflict.
        conflict = plugins[plugintype].get(filearg, None)
        if conflict:
            break
        elif rootdir:
            conflict = plugins[plugintype].get(rootdir, None)
            if conflict:
                break
    else:
        return False

    debug('WARNING: File name conflicts with a plugin name!')
    debug('         This will create a file named: {}'.format(filename))

    if os.getcwd() == SCRIPTDIR:
        print('\n'.join((
            '\nCreating this file here ({}) will override the {} plugin:',
            '{}')).format(SCRIPTDIR, conflict.get_name(), filename))
        print('\nPlease create it in another directory.\n')
        return True

    return False


def date():
    """ Returns a string formatted date for today. """
    return datetime.strftime(datetime.today(), '%m-%d-%Y')


def debug(*args, **kwargs):
    """ Print a message only if DEBUG is truthy. """
    if not (DEBUG and args):
        return None
    # Get filename, line number, and function name.
    frame = inspect.currentframe()
    frame = frame.f_back
    fname = os.path.split(frame.f_code.co_filename)[-1]
    lineno = frame.f_lineno
    func = frame.f_code.co_name
    # Patch args to stay compatible with print().
    pargs = list(args)
    lineinfo = '{}:{} {}(): '.format(fname, lineno, func).ljust(40)
    pargs[0] = ''.join((lineinfo, pargs[0]))
    print(*pargs, **kwargs)


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
        if pluginret == PluginReturn.fatal:
            return errors + 1
        errors += pluginret.value

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
        if pluginret == PluginReturn.fatal:
            return errors + 1
        errors += pluginret.value

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


def load_config(section=None):
    """ Load global config, or a specific section. """
    configfile = os.path.join(SCRIPTDIR, 'new.json')
    config = {}
    try:
        with open(configfile, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        debug('No config file: {}'.format(configfile))
    except EnvironmentError as exread:
        debug('Unable to read config file: {}\n{}'.format(configfile, exread))
    except ValueError as exjson:
        debug('Invalid JSON config: {}\n{}'.format(configfile, exjson))
    except Exception as ex:
        debug('Error loading config: {}\n{}'.format(configfile, ex))
    if section:
        sectionconfig = config.get(section, {})
        if not sectionconfig:
            debug('No config for: {}'.format(section))
        else:
            config = sectionconfig
            debug('Loaded {} config from: {}'.format(section, configfile))
    elif config:
        # Loading gobal config.
        debug('Loaded config from: {}'.format(configfile))
    return config


def load_plugin_config(plugin):
    """ Load config file for a plugin instance.
        Sets plugin.config to a dict on success.
    """
    if not getattr(plugin, 'config_file', None):
        configfile = 'new.json'
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
    pluginconfig = config.get(plugin.get_name(), {})
    if pluginconfig:
        loadmsg = 'Loaded {} config from: {}'
        debug(loadmsg.format(plugin.get_name(), plugin.config_file))
    else:
        errmsg = 'No config for {}: {}'
        debug(errmsg.format(plugin.get_name(), plugin.config_file))
    plugin.config = pluginconfig


def load_plugins(plugindir):
    """ Loads all available plugins from a path.
        Returns a dict of
            {'types': {module: Plugin}, 'post': {module: PostPlugin}}
    """
    global plugins, config
    # Load general plugin config.
    config = load_config('plugins')

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
                    elif name in tmp_plugins['types']:
                        debug('Conflicting Plugin: {}'.format(name))
                        continue
                    tmp_plugins['types'][name] = plugin
                    debug('Loaded: {} (Plugin)'.format(fullname))
                elif isinstance(plugin, DeferredPostPlugin):
                    if not name:
                        debug_missing('name', 'deferred', modname, plugin)
                        continue
                    if name in disabled_deferred:
                        skipmsg = 'Skipping disabled deferred-post plugin: {}'
                        debug(skipmsg.format(fullname))
                        continue
                    elif name in tmp_plugins['deferred']:
                        errmsg = 'Conflicting DeferredPostPlugin: {}'
                        debug(errmsg.format(name))
                        continue
                    tmp_plugins['deferred'][name] = plugin
                    debug('Loaded: {} (DeferredPostPlugin)'.format(fullname))
                elif isinstance(plugin, PostPlugin):
                    if not name:
                        debug_missing('name', 'post', modname, plugin)
                        continue
                    # See if the plugin is disabled.
                    if name in disabled_post:
                        skipmsg = 'Skipping disabled post plugin: {}'
                        debug(skipmsg.format(fullname))
                        continue
                    elif name in tmp_plugins['post']:
                        debug('Conflicting PostPlugin: {}'.format(name))
                        continue
                    tmp_plugins['post'][name] = plugin
                    debug('Loaded: {} (PostPlugin)'.format(fullname))
                else:
                    debug('\nNon-plugin type!: {}'.format(type(plugin)))
        except Exception as ex:
            print('\nError loading plugin: {}\n{}'.format(modname, ex))
    # Set module-level copy of plugins.
    plugins = tmp_plugins


def plugin_help(plugin):
    """ Show help for a plugin if available. """
    name = plugin.get_name()
    ver = getattr(plugin, 'version', '')
    if ver:
        name = '{} v. {}'.format(name, ver)

    usage = getattr(plugin, 'usage', '')
    if usage:
        print('\nHelp for {}:'.format(name))
        print(usage)
        return True

    # No real usage available, try getting a description instead.
    usage = plugin.get_desc()
    print('\nNo help available for {}.\n'.format(name))
    print(usage)
    return False


def print_inplace(s):
    """ Overwrites the last printed line. """
    print('\033[2A\033[160D')
    print(s)


def save_config(config, section=None):
    """ Save config to global config file. """
    configfile = os.path.join(SCRIPTDIR, 'new.json')
    if section:
        existing = load_config(section)
        existing[section] = config
        writeconfig = existing
    else:
        writeconfig = config

    try:
        with open(configfile, 'w') as f:
            json.dump(writeconfig, f, indent=4, sort_keys=True)
    except (TypeError, ValueError) as exjson:
        debug('Invalid JSON config error: {}'.format(exjson))
    except EnvironmentError as exwrite:
        debug('Unable to write config: {}\n{}'.format(configfile, exwrite))
    except Exception as ex:
        debug('Error writing config: {}\n{}'.format(configfile, ex))
    else:
        # Success.
        return True
    # Failure.
    return False


def try_post_plugin(plugin, filename):
    """ Try running plugin.process(filename).
        Returns one of:
            PluginReturn.success (0)
            PluginReturn.error (1)
            PluginReturn.fatal (2)
    """
    try:
        plugin.process(filename)
    except SignalExit as exstop:
        if exstop.reason:
            errmsg = '\nFatal error in post-processing plugin \'{}\':\n{}'
            print(errmsg.format(plugin.name, exstop.reason))
        else:
            errmsg = '\nFatal error in post-processing plugin: \'{}\''
            print(errmsg.format(plugin.name))
        print('\nCancelling all post plugins.')
        return PluginReturn.fatal
    except Exception as ex:
        errmsg = '\nError in post-processing plugin \'{}\':\n{}'
        print(errmsg.format(plugin.name, ex))
        return PluginReturn.error
    return PluginReturn.success


class Plugin(object):

    """ Base for file-type plugins. """
    name = None
    extensions = None
    description = None
    usage = None
    version = '0.0.1'
    load_config = load_plugin_config

    def __init__(self, name=None, extensions=None):
        self._name = None
        self.name = name
        self.extensions = extensions
        # A docopt usage string for this plugin.
        self.usage = None

    def create(self, filename, args=None):
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

    def get_desc(self):
        """ Get the description for this plugin.
            It uses the first line in create.__doc__ if self.description is
            not set. This is not the same as self.usage.
        """
        if self.description:
            return self.description

        docs = self.create.__doc__
        if docs:
            self.description = self.create.__doc__.split('\n')[0].strip()
        else:
            self.description = '(no description)'
        return self.description

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

    def print_status(self, msg):
        """ Print a status message including the plugin name and file name
            if available.
        """
        print('{}: {}'.format(self.get_name().ljust(15), msg))


class PostPlugin(object):

    """ Base for post-processing plugins. """
    name = None
    version = '0.0.1'
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

    def print_status(self, msg):
        """ Print a status message including the plugin name and file name
            if available.
        """
        print('{}: {}'.format(self.get_name().ljust(15), msg))

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


class PluginReturn(Enum):

    """ Return values for try_post_plugin().
        These provide readable names for the return values, but can be used
        as integers (or exit codes) with '.value'.
    """
    success = 0
    error = 1
    fatal = 2


class SignalAction(Exception):

    """ An  exception to raise when the plugin.create() function is a success,
        but changes need to be made to the filename.
        Arguments:
            message   : A message about the action. Printed with no formatting
                        when 'content' is set.
                        Defaults to: 'No message provided.' when 'content' is
                        not set.
            filename  : The new file name to use.
            content   : Content for the new file. If this is not set an error
                        message is printed along with 'message', and the
                        program exits.

        If you raise a SignalAction like a normal Exception:
            raise SignalAction(mystring)
        ...then SignalAction.message is set to mystring.

    """

    def __init__(self, *args, message=None, filename=None, content=None):
        Exception.__init__(self, *args)
        self.message = message
        self.filename = filename
        self.content = content
        arglen = len(args)
        if args:
            arglen = len(args)
            if (not self.content) and (arglen > 2):
                self.content = args[2]
            if (not self.filename) and (arglen > 1):
                self.filename = args[1]
            if not self.message:
                self.message = args[0]

        if (not self.content) and (not self.message):
            self.message = 'No message was provided.'


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
