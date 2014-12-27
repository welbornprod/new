"""
    Plugin bases for New.
    -Christopher Welborn 12-16-14
"""


class Plugin(object):

    """ Base for file-type plugins. """
    name = None
    extensions = None

    def __init__(self, name=None, extensions=None):
        self.name = name
        self.extensions = extensions

    def create(self):
        """ (unimplemented plugin)
            This should return a string that is ready to be written to a file.
            It may raise an exception to signal that something went wrong.
        """
        raise NotImplementedError('create_file() must be overridden!')


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

    def process(self, fname):
        """ (unimplented post-plugin)
            This should accept an existing file name and do some processing.
            It may raise an exception to signal that something went wrong.
        """
        raise NotImplementedError('process() must be overridden!')
