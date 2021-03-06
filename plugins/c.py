""" C plugin for New.
    Creates a new C file, and basic Makefile to go with it.
    -Christopher Welborn 2-20-15
"""
import os.path
from plugins import Plugin, date, fix_author, SignalAction


__version__ = '0.3.4'

# Template for defining vars.
template_define = """
#ifndef {define}
    #define {define}
#endif
""".strip()

# Template for including headers.
template_include = """
#include {include}
""".strip()

# Template for all files with the filename, author, and date.
template_header = """/* {filename}
    ...
    {author}{date}
*/

"""

# Template for Doxygen-style docs.
template_header_doxygen = """/*! \\file {filename}
    ...
    \\author {author}
    \\date   {date}
*/

"""

# Template for header file content.
template_lib_body = """
#ifndef {header_def}
#pragma GCC diagnostic ignored "-Wunused-macros"
// Tell gcc to ignore clang pragmas, for linting.
#pragma GCC diagnostic ignored "-Wunknown-pragmas"
#pragma clang diagnostic ignored "-Wunused-macros"
#pragma clang diagnostic ignored "-Wempty-translation-unit"
#define {header_def}

// Warn for any other unused macros, for gcc and clang.
#pragma GCC diagnostic warning "-Wunused-macros"
#pragma clang diagnostic push
#pragma clang diagnostic warning "-Wunused-macros"



#pragma clang diagnostic pop // end warning -Wunused-macros
#endif // {header_def}
"""

# Template for C/C++ source files content.
template_body = """
{includes}
{defines}
{namespace}
int main(int argc, char** argv) {{
    (void)argc; // <- To silence linters when not using argc.
    (void)argv; // <- To silence linters when not using argv.

    return 0;
}}
""".strip()


c_defines = (
    '_GNU_SOURCE',
)

c_headers = (
    'stdbool.h',
    'stdio.h',
    'stdlib.h',
)

cpp_headers = (
    'iostream',
)


class CPlugin(Plugin):
    name = ('c', 'cpp', 'c++', 'cc')
    extensions = ('.c', '.cpp', '.cc', '.cxx')
    cpp_extensions = ('.cpp', '.cc', '.cxx')
    version = __version__
    ignore_post = {'chmodx'}
    description = '\n'.join((
        'Creates a basic C or C++ file for small programs.',
        'If no Makefile exists, it will be created with basic targets.',
        'The Makefile is provided by the automakefile plugin.'
    ))
    config_opts = {
        'author': 'Default author name for all files.',
        'doxygen': 'If truthy, use Doxygen-style comments, like --doxygen.',
    }
    docopt = True
    usage = """
    Usage:
        c [-D] [-l]
        c [-D] [-i include...] [-d define...]

    Options:
        -D,--doxygen            : Use doxygen-style comments.
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
        use_doxygen = (
            self.argd['--doxygen'] or self.config.get('doxygen', False)
        )
        template_head = (
            template_header_doxygen if use_doxygen else template_header
        )
        author = self.config.get('author', '')
        if not use_doxygen:
            author = fix_author(author)
        basename, ext = os.path.splitext(filename)
        base = os.path.split(filename)[-1]
        if base.startswith('test_'):
            self.debug('Switching to test file mode: {}'.format(filename))
            self.ignore_post.add('automakefile')
            return template_head.format(
                filename=base,
                author=author,
                date=date(),
            )
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
        template = ''.join((
            template_head,
            template_body
        ))

        return template.format(
            filename=basename,
            author=author,
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
    config_opts = {
        'author': 'Default author name for all files.',
        'doxygen': 'If truthy, use Doxygen-style comments, like --doxygen.',
    }
    docopt = True
    usage = """
    Usage:
        header [-D]

    Options:
        -D,--doxygen  : Use Doxygen-style comments.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a basic C/C++ header file. """
        parentdir, filepath = os.path.split(filename)
        filebase = os.path.splitext(filepath)[0]
        use_doxygen = (
            self.argd.get('--doxygen', False) or
            self.config.get('doxygen', False)
        )
        template_lib = ''.join((
            template_header_doxygen if use_doxygen else template_header,
            template_lib_body
        ))
        author = fix_author(self.config.get('author', None))
        if use_doxygen:
            author = author.lstrip('-')
        return template_lib.format(
            filename=filepath,
            author=author,
            date=date(),
            header_def='{}_H'.format(filebase.upper()),
        )


exports = (CPlugin, CHeaderPlugin)
