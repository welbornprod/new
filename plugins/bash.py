""" Bash plugin for New.
    -Christopher Welborn 12-25-14
"""
import os.path
from plugins import Plugin, date, default_version, fix_author

__version__ = '0.2.2'

template = """#!/bin/bash

# ...{description}
# {author}{date}
appname="{filename}"
appversion="{version}"
apppath="$(readlink -f "${{BASH_SOURCE[0]}}")"
appscript="${{apppath##*/}}"
appdir="${{apppath%/*}}"
"""

# Basic function template.
template_func = """
function XXXX {{

}}
"""

# Basic arg-parsing code.
template_args = """
function print_usage {{
    # Show usage reason if first arg is available.
    [[ -n "$1" ]] && echo -e "\\n$1\\n"

    echo "$appname v. $appversion

    Usage:
        $appscript -h | -v

    Options:
        -h,--help     : Show this message.
        -v,--version  : Show $appname version and exit.
    "
}}

if (( $# == 0 )); then
    print_usage "No arguments!"
    exit 1
fi

declare -a nonflags

for arg; do
    case "$arg" in
        "-h"|"--help" )
            print_usage ""
            exit 0
            ;;
        "-v"|"--version" )
            echo -e "$appname v. $appversion\\n"
            exit 0
            ;;
        -*)
            print_usage "Unknown flag argument: $arg"
            exit 1
            ;;
        *)
            nonflags=("${{nonflags[@]}}" "$arg")
    esac
done
"""


class BashPlugin(Plugin):

    """ A bash template with only the basics. """
    name = ('bash', 'sh')
    extensions = ('.sh', '.bash')
    version = __version__
    usage = """
    Usage:
        bash [-f | -a] [DESCRIPTION]

    Options:
        DESCRIPTION  : Description for the doc str, quoting is optional.
        -a,--args    : Include basic arg-parsing functions.
        -f,--func    : Include an empty function.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a basic bash source file. """

        sections = [template]
        if self.has_arg('^((-a)|(--args))$'):
            self.debug('Using args template...')
            self.pop_args(self.args, ('-a', '--args'))
            sections.append(template_args)
        if self.has_arg('^((-f)(--func))$'):
            self.debug('Using function template...')
            self.pop_args(self.args, ('-f', '--func'))
            sections.append(template_func)

        return '\n'.join(sections).format(
            author=fix_author(self.config.get('author', None)),
            date=date(),
            description=' '.join(self.args) if self.args else '',
            filename=os.path.splitext(os.path.split(filename)[-1])[0],
            version=self.config.get('default_version', default_version)
        )

    def pop_args(self, lst, args):
        """ Removes any occurrence of an argument from a list.
            Modifies the list that is passed in.
            Arguments:
                lst   : List to remove from.
                args  : List/Tuple of args to remove.
        """
        for a in args:
            while lst.count(a) > 0:
                lst.remove(a)

exports = (BashPlugin, )
