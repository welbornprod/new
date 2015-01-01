"""
    Plugin bases for New.
    -Christopher Welborn 12-16-14
"""


class Plugin(object):

    """ Base for file-type plugins. """

    def __init__(self, name=None, extensions=None):
        self._name = None
        self.name = name
        self.extensions = extensions
        # A docopt usage string for this plugin.
        self.usage = None

    def create(self, argd):
        """ (unimplemented plugin)
            This should return a string that is ready to be written to a file.
            It may raise an exception to signal that something went wrong.
            Arguments:
                argd  : A reference to the main docopt arg dict
        """
        raise NotImplementedError('create_file() must be overridden!')

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

    def process(self, fname):
        """ (unimplented post-plugin)
            This should accept an existing file name and do some processing.
            It may raise an exception to signal that something went wrong.
        """
        raise NotImplementedError('process() must be overridden!')


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
