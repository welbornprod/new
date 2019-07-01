""" Bash plugin for New.
    -Christopher Welborn 12-25-14
"""
import os.path
from plugins import Plugin, date, default_version, fix_author

__version__ = '0.3.3'

template = """#!/bin/bash

# {description}
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
function echo_err {{
    # Echo to stderr.
    echo -e "$@" 1>&2
}}

function fail {{
    # Print a message to stderr and exit with an error status code.
    echo_err "$@"
    exit 1
}}

function fail_usage {{
    # Print a usage failure message, and exit with an error status code.
    print_usage "$@"
    exit 1
}}

function print_usage {{
    # Show usage reason if first arg is available.
    [[ -n "$1" ]] && echo_err "\\n$1\\n"

    echo "$appname v. $appversion

    Usage:
        $appscript -h | -v

    Options:
        -h,--help     : Show this message.
        -v,--version  : Show $appname version and exit.
    "
}}

(( $# > 0 )) || fail_usage "No arguments!"

declare -a nonflags

for arg; do
    case "$arg" in
        "-h" | "--help")
            print_usage ""
            exit 0
            ;;
        "-v" | "--version")
            echo -e "$appname v. $appversion\\n"
            exit 0
            ;;
        -*)
            fail_usage "Unknown flag argument: $arg"
            ;;
        *)
            nonflags+=("$arg")
    esac
done
"""


class BashPlugin(Plugin):

    """ A bash template with only the basics. """
    name = ('bash', 'sh')
    extensions = ('.sh', '.bash')
    version = __version__
    config_opts = {'author': 'Default author name for all files.'}
    docopt = True
    usage = """
    Usage:
        bash [-f | -a] [DESCRIPTION...]
        bash -s [DESCRIPTION...]

    Options:
        DESCRIPTION  : Description for the doc str, quoting is optional.
                       Multiple args are joined with a space.
        -a,--args    : Include basic arg-parsing functions.
        -f,--func    : Include an empty function.
        -s,--simple  : Don't use -f or -a, even if set in config.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a basic bash source file. """
        sections = [template]
        if self.argd['--simple']:
            self.debug('Using simple template...')
        else:
            if self.argd['--args']:
                self.debug('Using args template...')
                sections.append(template_args)
            if self.argd['--func']:
                self.debug('Using function template...')
                sections.append(template_func)

        return '\n'.join(sections).format(
            author=fix_author(self.config.get('author', None)),
            date=date(),
            description=' '.join(self.argd['DESCRIPTION']) or '...',
            filename=os.path.splitext(os.path.split(filename)[-1])[0],
            version=self.config.get('default_version', default_version)
        )


exports = (BashPlugin, )
