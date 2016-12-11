""" C plugin for New.
    Creates a new C file, and basic Makefile to go with it.
    -Christopher Welborn 2-20-15
"""
import os.path
from plugins import Plugin, date, fix_author, SignalAction

template = """/*  {filename}
    ...
    {author}{date}
*/

#include <{include}>
{namespace}
int main(int argc, char *argv[]) {{

    return 0;
}}
"""

template_lib = """/* {filename}
    ...
    {author}{date}
*/

"""

__version__ = '0.0.5'


class CPlugin(Plugin):
    name = ('c', 'cpp', 'c++', 'cc')
    extensions = ('.c', '.cpp', '.cc')
    cpp_extensions = ('.cpp', '.cc')
    version = __version__
    ignore_post = {'chmodx'}
    description = '\n'.join((
        'Creates a basic C or C++ file for small programs.',
        'If no Makefile exists, it will be created with basic targets.',
        'The Makefile is provided by the automakefile plugin.'
    ))

    docopt = True
    usage = """
    Usage:
        c [-l]

    Options:
        -l,--lib  : Treat as a library file, automakefile will not run.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a basic C file.
        """
        basename, ext = os.path.splitext(filename)
        if self.argd['--lib'] or (ext in CHeader.extensions):
            # Just do the CHeader thing.
            self.debug('Library file mode, no automakefile: {}'.format(
                filename
            ))
            # Remove .c,.cpp extensions.
            filename = basename
            while not filename.endswith(CHeaderPlugin.extensions):
                filename, ext = os.path.splitext(filename)
                if not ext:
                    # Add any missing CHeader extensions.
                    filename = '{}.h'.format(filename)
                    break
            self.debug('Switching to CHeader mode: {}'.format(filename))
            raise SignalAction(
                filename=filename,
                content=CHeaderPlugin().create(filename),
                ignore_post={'automakefile', 'chmodx'},
            )

        parentdir, basename = os.path.split(filename)

        fileext = os.path.splitext(filename)[-1].lower()
        if fileext in self.cpp_extensions:
            include = 'iostream'
            namespace = '\nusing std::cout;\nusing std::endl;\n'
        else:
            include = 'stdio.h'
            namespace = ''

        return template.format(
            filename=basename,
            author=fix_author(self.config.get('author', None)),
            date=date(),
            include=include,
            namespace=namespace
        )


class CHeaderPlugin(Plugin):
    name = ('header', 'cheader', 'cppheader', 'c++header')
    extensions = ('.h', '.hpp', '.h++')
    version = __version__
    ignore_post = {'chmodx', 'automakefile'}
    description = 'Creates a basic C or C++ header file.'
    usage = """
    Usage:
        header
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a basic C/C++ header file. """
        parentdir, basename = os.path.split(filename)

        return template_lib.format(
            filename=basename,
            author=fix_author(self.config.get('author', None)),
            date=date(),
        )


exports = (CPlugin, CHeaderPlugin)
