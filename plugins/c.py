""" C plugin for New.
    Creates a new C file, and basic Makefile to go with it.
    -Christopher Welborn 2-20-15
"""
import os.path
from plugins import Plugin, date, fix_author, SignalAction

template_define = """
#ifndef {define}
    #define {define}
#endif
""".strip()

template_include = """
#include {include}
""".strip()

template_lib = """/* {filename}
    ...
    {author}{date}
*/

"""

template_body = """
{includes}
{defines}
{namespace}
int main(int argc, char *argv[]) {{

    return 0;
}}
""".strip()

# Headers and source files should use the same comment header.
template = ''.join((template_lib, template_body))

c_defines = (
    '_GNU_SOURCE',
)

c_headers = (
    'stdio.h',
)

cpp_headers = (
    'iostream',
)

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
        c [-i include...] [-d define...]

    Options:
        -d def,--define def     : Include a definition for the preprocessor.
                                  The format will be:
                                      #ifndef def
                                          #define def
                                      #endif
        -i name,--include name  : Include a header.
                                  The format will be:
                                      #include <name>.
        -l,--lib                : Treat as a library file, automakefile will
                                  not run.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a basic C file.
        """
        basename, ext = os.path.splitext(filename)
        if self.argd['--lib'] or (ext in CHeaderPlugin.extensions):
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
            includes = self.make_includes(
                self.argd['--include'],
                defaults=cpp_headers,
            )
            namespace = '\nusing std::cout;\nusing std::endl;\n'
        else:
            includes = self.make_includes(
                self.argd['--include'],
                defaults=c_headers,
            )
            namespace = ''

        return template.format(
            filename=basename,
            author=fix_author(self.config.get('author', None)),
            date=date(),
            defines=self.make_defines(self.argd['--define']),
            includes=includes,
            namespace=namespace
        ).replace('\n\n\n', '\n\n')

    def make_defines(self, definelst, defaults=None):
        """ Create #define lines, given a list of variables. """
        defstr = '\n'.join(
            template_define.format(define=s)
            for s in sorted(set((defaults or []) + definelst))
        )
        if defstr:
            return '\n{}'.format(defstr)
        return defstr

    def make_includes(self, includelst, defaults=None):
        """ Create #include lines, given a list of header names. """
        defaults = list(defaults) if defaults else []
        includes = sorted(set(defaults + includelst))
        lines = []
        for include in includes:
            if os.path.exists(include):
                fmt = '"{}"'
            else:
                fmt = '<{}>'
            lines.append(
                template_include.format(include=fmt.format(include))
            )
        return '\n'.join(lines)


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
