""" C plugin for New.
    Creates a new C file, and basic Makefile to go with it.
    -Christopher Welborn 2-20-15
"""
import os.path
from plugins import Plugin, date, debug
DATE = date()

template = """/*  {filename}
    ...
    {author} {date}
*/

#include <{include}>
{namespace}
int main(int argc, char *argv[]) {{

    return 0;
}}
"""

template_lib = """/* {filename}
    ...
    {author} {date}
*/

"""


class CPlugin(Plugin):

    def __init__(self):
        self.name = ('c', 'cpp', 'c++')
        self.extensions = ('.c', '.cpp')
        self.version = '0.0.3-1'
        self.ignore_post = {'chmodx'}
        self.description = '\n'.join((
            'Creates a basic C or C++ file for small programs.',
            'If no Makefile exists, it will be created with basic targets.',
            'The Makefile is provided by the automakefile plugin.'
        ))
        self.usage = """
    Usage:
        c [l]

    Options:
        l,lib  : Treat as a library file, automakefile will not run.
    """
        self.load_config()

    def create(self, filename):
        """ Creates a basic C file.
        """
        library = self.has_arg('l(ib)?')
        # Disable automakefile if asked.
        if library:
            debug('Library file mode, no automakefile.')
            self.ignore_post.add('automakefile')

        parentdir, basename = os.path.split(filename)
        author = self.config.get('author', '')

        fileext = os.path.splitext(filename)[-1]
        include = {'.c': 'stdio.h', '.cpp': 'iostream'}.get(fileext, 'stdio.h')
        if author:
            author = '-{}'.format(author)
        if fileext == '.cpp':
            namespace = '\nusing std::cout;\nusing std::endl;\n'
        else:
            namespace = ''
        return (template_lib if library else template).format(
            filename=basename,
            author=author,
            date=DATE,
            include=include,
            namespace=namespace)


exports = (CPlugin(),)
