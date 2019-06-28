""" Python plugin for New.
    -Christopher Welborn 12-25-14
"""

import os

from plugins import (
    Plugin,
    SignalAction,
    SignalExit,
    date,
    default_version,
    fix_author
)

__version__ = '0.3.3'

# TODO: This plugin was basically just copied and adapted from the original
#       'newpython' script that inspired this project.
#       It is in need of some refactoring.


# Default imports to use if '--noimports' isn't given.
DEFAULT_IMPORTS = ['os', 'sys']

# if __name__ == '__main__' templates:
MAIN_DOCOPT = """
    try:
        mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    except InvalidArg as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\\nUser cancelled.\\n')
        mainret = 2
    except BrokenPipeError:
        print_err('\\nBroken pipe, input/output was interrupted.\\n')
        mainret = 3
    sys.exit(mainret)
"""

MAIN_COLR = MAIN_DOCOPT.replace('VERSIONSTR', 'VERSIONSTR, script=SCRIPT')

MAIN_NORMAL = """
    try:
        mainret = main(sys.argv[1:])
    except InvalidArg as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\\nUser cancelled.\\n')
        mainret = 2
    except BrokenPipeError:
        print_err('\\nBroken pipe, input/output was interrupted.\\n')
        mainret = 3
    sys.exit(mainret)
"""

PRINT_ERR_COLR = """
def print_err(*args, **kwargs):
    \"\"\" A wrapper for print() that uses stderr by default.
        Colorizes messages, unless a Colr itself is passed in.
    \"\"\"
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr

    # Use color if the file is a tty.
    if kwargs['file'].isatty():
        # Keep any Colr args passed, convert strs into Colrs.
        msg = kwargs.get('sep', ' ').join(
            str(a) if isinstance(a, C) else str(C(a, 'red'))
            for a in args
        )
    else:
        # The file is not a tty anyway, no escape codes.
        msg = kwargs.get('sep', ' ').join(
            str(a.stripped() if isinstance(a, C) else a)
            for a in args
        )

    print(msg, **kwargs)
""".strip()

PRINT_ERR_NORMAL = """
def print_err(*args, **kwargs):
    \"\"\" A wrapper for print() that uses stderr by default. \"\"\"
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(*args, **kwargs)
""".strip()

# Settings per template by name
# ..must at least contain {'base': 'template name', 'imports': []}
templates = {
    'blank': {
        'base': 'blank',
        'imports': []
    },
    'normal': {
        'base': 'main',
        'imports': DEFAULT_IMPORTS,
        'head': '',
        'mainsignature': 'main(args)',
        'maindoc': 'Main entry point, expects args from sys.',
        'mainif': MAIN_NORMAL,
        'print_err': PRINT_ERR_NORMAL,
    },
    'colr': {
        'base': 'main',
        'imports': DEFAULT_IMPORTS + [
            {
                'colr': (
                    'Colr as C',
                    'auto_disable as colr_auto_disable',
                    'docopt',
                )
            },
        ],
        'afterimports': 'colr_auto_disable()',
        'head': ('USAGESTR = """{versionstr}\n'
                 '    Usage:\n'
                 '        {script} [-h | -v]\n\n'
                 '    Options:\n'
                 '        -h,--help     : Show this help message.\n'
                 '        -v,--version  : Show version.\n'
                 '""".format(script=SCRIPT, versionstr=VERSIONSTR)\n'
                 ),
        'mainsignature': 'main(argd)',
        'maindoc': 'Main entry point, expects docopt arg dict as argd.',
        'mainif': MAIN_COLR,
        'print_err': PRINT_ERR_COLR,
    },
    'docopt': {
        'base': 'main',
        'imports': DEFAULT_IMPORTS + ['docopt.docopt'],
        'head': ('USAGESTR = """{versionstr}\n'
                 '    Usage:\n'
                 '        {script} [-h | -v]\n\n'
                 '    Options:\n'
                 '        -h,--help     : Show this help message.\n'
                 '        -v,--version  : Show version.\n'
                 '""".format(script=SCRIPT, versionstr=VERSIONSTR)\n'
                 ),
        'mainsignature': 'main(argd)',
        'maindoc': 'Main entry point, expects docopt arg dict as argd.',
        'mainif': MAIN_DOCOPT,
        'print_err': PRINT_ERR_NORMAL,
    },
    'setup': {
        'base': 'setup',
        'imports': [],
    },
    'unittest': {
        'base': 'test',
        'imports': ['sys', 'unittest'],
        'testsetup': '',

    },
}
# Aliases
templates['doc'] = templates['docopt']
templates['none'] = templates['blank']
templates['test'] = templates['unittest']

# TEMPLATE CONTENT ----------------------------------------------------------
# Blank template. Only the shebang and doc string.
template_blank = """#!{shebangexe}

\"\"\" {scriptname}
    ...{explanation}
    {author}{date}
\"\"\"
"""

# main template for generating py file.
template_main = """#!{shebangexe}
# -*- coding: utf-8 -*-

\"\"\" {scriptname}
    ...{explanation}
    {author}{date}
\"\"\"

{imports}

NAME = '{scriptname}'
VERSION = '{default_version}'
VERSIONSTR = '{{}} v. {{}}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

{head}

def {mainsignature}:
    \"\"\" {maindoc} \"\"\"
    return 0


{print_err}


class InvalidArg(ValueError):
    \"\"\" Raised when the user has used an invalid argument. \"\"\"
    def __init__(self, msg=None):
        self.msg = msg or ''

    def __str__(self):
        if self.msg:
            return 'Invalid argument, {{}}'.format(self.msg)
        return 'Invalid argument!'


if __name__ == '__main__':{mainif}
"""

# template for a basic distutils setup.py
template_setup = """#!{shebangexe}
# -*- coding: utf-8 -*-

\"\"\"
{pkgname} Setup

{doc_author}{date}
\"\"\"

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Try using the latest DESC.txt.
shortdesc = '{desc}'
try:
    with open('DESC.txt', 'r') as f:
        shortdesc = f.read()
except FileNotFoundError:
    pass

# Default README files to use for the longdesc, if pypandoc fails.
readmefiles = ('docs/README.txt', 'README.txt', 'docs/README.rst')
for readmefile in readmefiles:
    try:
        with open(readmefile, 'r') as f:
            longdesc = f.read()
        break
    except EnvironmentError:
        # File not found or failed to read.
        pass
else:
    # No readme file found.
    # If a README.md exists, and pypandoc is installed, generate a new readme.
    try:
        import pypandoc
    except ImportError:
        print('Pypandoc not installed, using default description.')
        longdesc = shortdesc
    else:
        # Convert using pypandoc.
        try:
            longdesc = pypandoc.convert('README.md', 'rst')
        except EnvironmentError:
            # No readme file, no fresh conversion.
            print('Pypandoc readme conversion failed, using default desc.')
            longdesc = shortdesc

setup(
    name='{pkgname}',
    version='{version}',
    author='{author}',
    author_email='{email}',
    packages=['{pkgname}'],
    url='http://pypi.python.org/pypi/{pkgname}/',
    description=shortdesc,
    long_description=longdesc,
    keywords=('python module library 2 3 ...'),
    classifiers=[
        # TODO: Review these classifiers, delete as needed!
        'License :: OSI Approved :: MIT License',
        # Or: GNU General Public License v3 or later (GPLv3+)
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3', # ' :: Only'
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    # TODO: List requirements, or delete these comments.
    # install_requires=[..],
)

"""

# template for generating a unit test module.
template_test = """#!{shebangexe}
# -*- coding: utf-8 -*-

\"\"\" {scriptname}
    Unit tests for {testtarget} v. {default_version}
    {explanation}
    {author}{date}
\"\"\"

{imports}


class TestCase(unittest.TestCase):
    {testsetup}
    def test_function(self):
        \"\"\" test for ... \"\"\"
        pass


if __name__ == '__main__':
    unittest.main(argv=sys.argv, verbosity=2)
"""

# To retrieve a raw template string by name/id.
template_bases = {
    'blank': template_blank,
    'main': template_main,
    'setup': template_setup,
    'test': template_test
}
# END TEMPLATE CONTENT ------------------------------------------------------


class PythonPlugin(Plugin):

    name = ('python', 'py')
    extensions = ('.py',)
    version = __version__

    docopt = True
    usage = """
    Usage:
        python [TEMPLATE] [IMPORTS...]
        python --templates
        python setup [NAME] [VERSION] [DESC]

    Options:
        IMPORTS          : Any extra modules to import. In the form of:
                           module1 module2.childmod1
        NAME             : A PyPi package name to create a setup.py for.
        DESC             : One line description for a new PyPi package
                           setup.py.
                           This is only used if DESC.txt is not present during
                           installation of the package.
        TEMPLATE         : Which template to use.
                           Template ids are listed below.
        VERSION          : Version number for a new PyPi package setup.py.

    Commands:
        -t, --templates  : List known template names.
        setup            : Create a setup.py that uses distutils, with a
                           custom app name, version, and description.

    Templates:
        blank, none      : Only a shebang and the main doc str.
        docopt, doc      : A normal module including docopt boilerplate.
                           This is the default if not set in config.
        normal           : A normal, executable, script module with
                           boilerplate.
        setup            : Create a setup.py that uses setuptools/distutils.
        unittest, test   : A unittest module.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a new python source file. Several templates are available.
        """
        if self.argd['--templates']:
            # Viewing template names.
            exitcode = self.print_templates()
            raise SignalExit(code=exitcode)

        templateid = (
            self.argd['TEMPLATE'] or
            self.config.get('template', 'docopt')
        ).lower()

        # Setup.py is completely different, these really need to be separated.
        if self.argd['TEMPLATE'] == 'setup':
            # Hack for ambiguos docopt usage string, use imports as args.
            return self.create_setup(filename, *self.argd['IMPORTS'])

        template_args = templates.get(templateid, None)
        if not template_args:
            msg = '\n'.join((
                'No template by that name: {}'.format(templateid),
                'Use \'-t\' or \'--templates\' to list known templates.'
            ))
            raise ValueError(msg)
        template_base = template_bases.get(template_args['base'], None)
        if not template_base:
            errmsg = 'Misconfigured template base: {}'
            raise ValueError(errmsg.format(templateid))
        imports = self.argd['IMPORTS'] + template_args['imports']
        scriptname = os.path.split(filename)[-1]
        shebangexe = self.config.get('shebangexe', '/usr/bin/env python3')
        version = self.config.get('default_version', default_version)

        use_template_args = {k: v for k, v in template_args.items()}
        # Regular template (none, unittest, docopt)...
        use_template_args.update({
            'author': fix_author(self.config.get('author', None)),
            'explanation': self.config.get('explanation', ''),
            'date': date(),
            'default_version': version,
            'imports': self.parse_importlist(imports),
            'scriptname': scriptname,
            'shebangexe': shebangexe,
        })
        after_imports = template_args.get('afterimports', None)
        if not isinstance(after_imports, str):
            after_imports = '\n'.join(after_imports)
        if after_imports:
            use_template_args['imports'] = '\n\n'.join((
                use_template_args['imports'],
                after_imports,
            ))

        testaction = None
        if templateid in {'unittest', 'test'}:
            # unittest is a special case.
            # It may need to change the file name
            if scriptname.startswith('test_'):
                testtarget = scriptname[5:]
            else:
                # Fix the filename to look more like a unittest.
                testtarget = scriptname
                path, name = os.path.split(filename)
                scriptname = 'test_{}'.format(name)
                filename = os.path.join(path, scriptname)
                # Create an action that will allow the filename change.
                testaction = SignalAction(
                    message='Switching to unittest file name format.',
                    filename=filename)
            # Fix the scriptname, add the testtarget args.
            use_template_args['scriptname'] = scriptname
            use_template_args['testtarget'] = testtarget
            # Render the template, action is needed because of a name change.
            if testaction:
                testaction.content = template_base.format(**use_template_args)
                raise testaction

        # Render a normal template and return the content.
        return template_base.format(**use_template_args)

    def create_setup(self, filename, *args):
        """ Create a basic setup.py. """

        name, ver, desc = self.parse_setup_args(*args)
        shebangexe = self.config.get('shebangexe', '/usr/bin/env python3')
        tmpargs = {
            'author': self.config.get('author', os.environ.get('USER', '?')),
            'date': date(),
            'desc': desc or 'My default description.',
            'email': self.config.get('email', 'nobody@nowhere.com'),
            'pkgname': name or 'MyApp',
            'shebangexe': shebangexe,
            'version': (
                ver or
                self.config.get('default_version', default_version)
            )
        }
        tmpargs['doc_author'] = fix_author(tmpargs['author'])

        # Render the template.
        content = template_setup.format(**tmpargs)

        # See if a SignalAction is needed.
        base, _ = os.path.split(filename)
        setupfile = os.path.join(base, 'setup.py')
        if filename == setupfile:
            return content

        raise SignalAction(
            message='Using required setup.py file name.',
            filename=setupfile,
            content=content
        )

    def parse_importitem(self, modulename):
        """ Returns proper import line based on import name.
            'mymodule' returns 'import mymodule'
            'my.module.myclass' returns 'from my.module import myclass'
            {"module": ("a", "b")} returns 'from module import (a, b,)'
        """
        if isinstance(modulename, dict):
            lines = []
            for k in sorted(modulename):
                lines.append('from {} import ('.format(k))
                for submodule in modulename[k]:
                    lines.append('    {},'.format(submodule))
                lines.append(')')
            return '\n'.join(lines)
        importfrom, _, realimport = modulename.rpartition('.')
        if importfrom:
            return 'from {} import {}'.format(importfrom, realimport)

        return 'import {}'.format(realimport)

    def parse_importlist(self, imports):
        """ Parses list of imports, returns finished string with newlines. """

        if not imports:
            return ''

        lines = [self.parse_importitem(imp) for imp in imports]
        # Remove any duplicates and sort the lines.
        presorted = sorted(set(lines))
        # Place the 'from' imports at the end.
        imps = []
        froms = []
        for line in presorted:
            if line.startswith('import'):
                imps.append(line)
            elif line.startswith('from'):
                froms.append(line)
            else:
                raise SignalExit('Invalid import: {!r}'.format(line), code=1)
        if froms:
            # Insert blank line between 'imports' and 'from X imports'
            froms.insert(0, '')
        return '\n'.join(imps + froms)

    def parse_setup_args(self, *args):
        """ Parse IMPORTS as NAME, VERSION, DESC arguments. """
        # Hack around ambiguous docopt usage string.
        arglen = len(args)
        if arglen > 3:
            raise SignalExit(
                'Incorrect arguments, expecting [NAME] [VERSION] [DESC].',
                code=1)
        name = ver = desc = None
        if arglen == 3:
            name, ver, desc = args
        elif arglen == 2:
            name, ver = args
        elif arglen == 1:
            name = args[0]

        return name, ver, desc

    def print_templates(self):
        """ Print known tempalte names. """
        if not templates:
            print('\nNo known templates.')
            return 1

        tmplen = len(templates)
        plural = 'template' if tmplen == 1 else 'templates'
        print('Found {} python {}:'.format(tmplen, plural))
        print('\n    {}'.format('\n    '.join(sorted(templates))))
        return 0

exports = (PythonPlugin, )  # noqa
