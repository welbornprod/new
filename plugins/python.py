""" Python plugin for New.
    -Christopher Welborn 12-25-14
"""

import os
import sys

from plugins import Plugin, SignalAction, date

SCRIPTDIR = os.path.abspath(sys.path[0])
DATE = date()

# Default imports to use if '--noimports' isn't given.
DEFAULT_IMPORTS = ['os', 'sys']
# Default versioning for all new scripts when config isn't set.
DEFAULT_VERSION = '0.0.1'

# Setting per template by name.(must at least contain 'base': 'template name' )
templates = {
    'blank': {
        'base': 'blank',
    },
    'normal': {
        'base': 'main',
        'imports': DEFAULT_IMPORTS,
        'head': '',
        'mainsignature': 'main(args)',
        'maindoc': 'Main entry point, expects args from sys.',
        'mainif': 'sys.exit(main(sys.argv[1:]))',
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
        'mainif': ('mainret = main(docopt(USAGESTR, version=VERSIONSTR))\n'
                   '    sys.exit(mainret)')
    },
    'unittest': {
        'base': 'test',
        'imports': ['unittest'],
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

if __name__ == '__main__':
    {mainif}
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
    'test': template_test
}
# END TEMPLATE CONTENT ------------------------------------------------------


class PythonPlugin(Plugin):

    def __init__(self):
        self.name = ('python', 'py')
        self.extensions = ('.py',)
        self.version = '0.0.1-1'
        self.load_config()
        self.usage = """
    Usage:
        python [template] [extra_imports...]

    Options:
        template       : Which template to use. Template ids are listed below.
        extra_imports  : Any extra modules to import. In the form of:
                         module1 module2.childmod1

    Templates:
        blank, none     : Only a shebang and the main doc str.
        docopt, doc     : A normal module including docopt boilerplate.
                          This is the default if not set in config.
        normal          : A normal, executable, script module with boilerplate.
        unittest, test  : A unittest module.
    """

    def create(self, filename, args):
        if args:
            templateid = args[0].lower()
        else:
            templateid = self.config.get('template', 'docopt')
        extra_imports = args[1:] if len(args) > 1 else []
        template_args = templates.get(templateid, None)
        if not template_args:
            raise ValueError('No template by that name: {}'.format(templateid))
        template_base = template_bases.get(template_args['base'], None)
        if not template_base:
            errmsg = 'Misconfigured template base: {}'
            raise ValueError(errmsg.format(templateid))

        author = self.config.get('author', '')
        imports = extra_imports + template_args['imports']
        scriptname = os.path.split(filename)[-1]
        shebangexe = self.config.get('shebangexe', '/usr/bin/env python3')
        version = self.config.get('version', DEFAULT_VERSION)
        template_args.update({
            'author': author,
            'explanation': self.config.get('explanation', ''),
            'date': ' {}'.format(DATE) if author else DATE,
            'default_version': version,
            'imports': self.parse_importlist(imports),
            'scriptname': scriptname,
            'shebangexe': shebangexe,
        })

        testaction = None
        if templateid in ('unittest', 'test'):
            # unittest is a special case.  It may need to change the file name.
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
            # Render the template, action is needed because of the name change.
            testaction.content = template_base.format(**template_args)
            raise testaction

        # Render a normal template and return the content.
        return template_base.format(**template_args)

    def parse_importitem(self, modulename):
        """ Returns proper import line based on import name.
            'mymodule' returns 'import mymodule'
            'my.module.myclass' returns 'from my.module import myclass'
        """

        if '.' in modulename:
            parts = modulename.split('.')
            importfrom = parts[:-1]
            realimport = parts[-1]
            return 'from {} import {}'.format('.'.join(importfrom), realimport)
        else:
            return 'import {}'.format(modulename)

    def parse_importlist(self, imports):
        """ Parses list of imports, returns finished string with newlines. """

        if not imports:
            return ''

        lines = [self.parse_importitem(imp) for imp in imports]
        # Remove any duplicates and sort the lines.
        return '\n'.join(sorted(set(lines)))

plugins = (PythonPlugin(),)
