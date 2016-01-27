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

__version__ = '0.2.1'

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
        print_err('\\nUser cancelled.\\n', file=sys.stderr)
        mainret = 2
    except BrokenPipeError:
        print_err(
            '\\nBroken pipe, input/output was interrupted.\\n',
            file=sys.stderr)
        mainret = 3
    sys.exit(mainret)
"""

MAIN_NORMAL = """
    try:
        mainret = main(sys.argv[1:])
    except InvalidArg as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\\nUser cancelled.\\n', file=sys.stderr)
        mainret = 2
    except BrokenPipeError:
        print_err(
            '\\nBroken pipe, input/output was interrupted.\\n',
            file=sys.stderr)
        mainret = 3
    sys.exit(mainret)
"""

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
        'maindoc': 'Main entry point, expects doctopt arg dict as argd.',
        'mainif': MAIN_DOCOPT
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


def print_err(*args, **kwargs):
    \"\"\" A wrapper for print() that uses stderr by default. \"\"\"
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(*args, **kwargs)


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

from distutils.core import setup
defaultdesc = '{desc}'
try:
    import pypandoc
except ImportError:
    print('Pypandoc not installed, using default description.')
    longdesc = defaultdesc
else:
    # Convert using pypandoc.
    try:
        longdesc = pypandoc.convert('README.md', 'rst')
    except EnvironmentError:
        # Fallback to README.txt (may be behind on updates.)
        try:
            with open('README.txt') as f:
                longdesc = f.read()
        except EnvironmentError:
            print('\\nREADME.md and README.txt failed!')
            longdesc = defaultdesc


setup(
    name='{pkgname}',
    version='{version}',
    author='{author}',
    author_email='{email}',
    packages=['{pkgname}'],
    url='http://pypi.python.org/pypi/{pkgname}/',
    license='LICENSE.txt',
    description=open('DESC.txt').read(),
    long_description=longdesc,
    keywords=('python module library 2 3 ...'),
    classifiers=[
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
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
    sys.exit(unittest.main(argv=sys.argv))
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
    usage = """
    Usage:
        python [template] [extra_imports...]
        python templates
        python setup [package_name] [version] [short_desc]

    Options:
        extra_imports   : Any extra modules to import. In the form of:
                          module1 module2.childmod1
        package_name    : A PyPi package name to create a setup.py for.
        short_desc      : One line description for a new PyPi package
                          setup.py.
                          This is only used if DESC.txt is not present during
                          installation of the package.
        template        : Which template to use.
                          Template ids are listed below.
        version         : Version number for a new PyPi package setup.py.

    Commands:
        t, templates    : List known template names.

    Templates:
        blank, none     : Only a shebang and the main doc str.
        docopt, doc     : A normal module including docopt boilerplate.
                          This is the default if not set in config.
        normal          : A normal, executable, script module with
                          boilerplate.
        setup           : Create a setup.py that uses distutils.
        unittest, test  : A unittest module.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a new python source file. Several templates are available.
        """
        if self.has_arg('^t(emplates)?$'):
            # Viewing template names.
            exitcode = self.print_templates()
            raise SignalExit(code=exitcode)

        templateid = (
            self.get_arg(0) or self.config.get('template', 'docopt')).lower()

        # Setup.py is completely different, these really need to be separated.
        if templateid == 'setup':
            return self.create_setup(filename, args=self.args[1:])

        extra_imports = self.args[1:]

        template_args = templates.get(templateid, None)
        if not template_args:
            msg = '\n'.join((
                'No template by that name: {}'.format(templateid),
                'Use \'t\' or \'templates\' to list known templates.'
            ))
            raise ValueError(msg)
        template_base = template_bases.get(template_args['base'], None)
        if not template_base:
            errmsg = 'Misconfigured template base: {}'
            raise ValueError(errmsg.format(templateid))

        imports = extra_imports + template_args['imports']
        scriptname = os.path.split(filename)[-1]
        shebangexe = self.config.get('shebangexe', '/usr/bin/env python3')
        version = self.config.get('default_version', default_version)

        # Regular template (none, unittest, docopt)...
        template_args.update({
            'author': fix_author(self.config.get('author', None)),
            'explanation': self.config.get('explanation', ''),
            'date': date(),
            'default_version': version,
            'imports': self.parse_importlist(imports),
            'scriptname': scriptname,
            'shebangexe': shebangexe,
        })

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
            template_args['scriptname'] = scriptname
            template_args['testtarget'] = testtarget
            # Render the template, action is needed because of a name change.
            if testaction:
                testaction.content = template_base.format(**template_args)
                raise testaction

        # Render a normal template and return the content.
        return template_base.format(**template_args)

    def create_setup(self, filename, args=None):
        """ Create a basic setup.py. """
        if args is None:
            args = []
        shebangexe = self.config.get('shebangexe', '/usr/bin/env python3')
        tmpargs = {
            'author': fix_author(self.config.get('author', None)),
            'date': date(),
            'desc': 'My default description.',
            'email': self.config.get('email', 'nobody@nowhere.com'),
            'pkgname': 'MyApp',
            'shebangexe': shebangexe,
            'version': self.config.get('default_version', default_version)
        }
        tmpargs['doc_author'] = '-{} '.format(tmpargs['author'])

        # Use supplied package name and version overrides.
        if args:
            tmpargs['pkgname'] = args[0]
        arglen = len(args)
        if arglen > 1:
            tmpargs['version'] = args[1]
        if arglen > 2:
            tmpargs['desc'] = args[2]

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
        """

        if '.' in modulename:
            parts = modulename.split('.')
            importfrom = parts[:-1]
            realimport = parts[-1]
            return 'from {} import {}'.format(
                '.'.join(importfrom),
                realimport)
        else:
            return 'import {}'.format(modulename)

    def parse_importlist(self, imports):
        """ Parses list of imports, returns finished string with newlines. """

        if not imports:
            return ''

        lines = [self.parse_importitem(imp) for imp in imports]
        # Remove any duplicates and sort the lines.
        return '\n'.join(sorted(set(lines)))

    def print_templates(self):
        """ Print known tempalte names. """
        if not templates:
            print('\nNo known templates.')
            return 1

        tmplen = len(templates)
        plural = 'template' if tmplen == 1 else 'templates'
        print('Found {} {}:'.format(tmplen, plural))
        print('\n    {}'.format('\n    '.join(sorted(templates))))
        return 0

exports = (PythonPlugin,)
