#!/usr/bin/env python3
""" Templates for the New plugin, `makefile`.
    -Christopher Welborn 11-17-17
"""
import os
from .. import (
    debug,
    fix_indent_tabs,
    FormatBlock,
)

# Default filename for the resulting makefile.
DEFAULT_MAKEFILE = 'makefile'


def format_cflags(flaglist, var='CFLAGS'):
    """ Format a list of C flags as a str.
        Insert \ line breaks so that the maximum line width is 80 chars.
    """
    # make doesn't mind spaces for continuation lines.
    indent = ' ' * len('{}='.format(var))
    # Add line breaks when splitting lines.
    append = ' \\'
    # Max line width is 80, but allow room for 'CFLAGS=' and ' \'.
    linewidth = 80 - len(indent) - len(append)
    return FormatBlock(' '.join(sorted(set(flaglist)))).format(
        prepend=indent,
        strip_first=True,
        append=append,
        strip_last=True,
        width=linewidth,
    ).rstrip('\\')


def format_vars(compilerinfo):
    """ Format a dict of {'VAR': value} into makefile variables.
    """
    return '\n'.join(
        '{}={}'.format(flag, compilerinfo[flag])
        for flag in sorted(compilerinfo)
    )


# I'm not very good with makefiles.
# {targets} and {cleantarget} are set by compiler type,
# and *then* the whole template is rendered.
# The fix_indent_tabs() is just for my sanity when dealing with tabs/spaces.
pre_template = fix_indent_tabs("""SHELL=bash
{{compilervars}}
{{flagvars}}{{libsline}}

binary={{binary}}
source={{filename}}

{targets}

.PHONY: clean, cleanmake, makeclean, targets
clean:
{cleantarget}

cleanmake makeclean:
    @make --no-print-directory clean && make --no-print-directory;

targets:
    -@printf "Make targets available:\\n\\
    all       : Build with no optimization or debug symbols.\\n\\
    clean     : Delete previous build files.\\n\\
    cleanmake : Run \\`make clean && make\\`\\n\\
    makeclean : Alias for \\`cleanmake\\`\\n\\
    debug     : Build the executable with debug symbols.\\n\\
    release   : Build the executable with optimization, and strip it.\\n\\
    ";
""")
# ####
# TODO: Add `ctags` target for c/c++ files (`ctags -R .`)
# ####

# Flags shared between C and C++.
csharedflags = [
    '-Wall',
    '-Wextra',
    '-Wfloat-equal',
    '-Winline',
    '-Wlogical-op',
    '-Wmissing-include-dirs',
    '-Wnull-dereference',
    '-Wpedantic',
    '-Wshadow',
    '-Wunused-macros',
]
# Flags for C only.
conlyflags = [
    '-std=c11',
    '-Wstrict-prototypes',
]
# Flags for CPP.
cpponlyflags = [
    '-std=c++14',
]

# Make targets for c/c++.
ctargets = fix_indent_tabs("""
all: {objects}
    $({compilervar}) -o $(binary) $({cflagsvar}) *.o $(LIBS)

debug: {cflagsvar}+=-g3 -DDEBUG
debug: all

release: {cflagsvar}+=-O3 -DNDEBUG
release: all
    @if strip $(binary); then\\
        printf "\\n%s was stripped.\\n" "$(binary)";\\
    else\\
        printf "\\nError stripping executable: %s\\n" "$(binary)" 1>&2;\\
    fi;

{objects}: $(source)
    $({compilervar}) -c $(source) $({cflagsvar}) $(LIBS)
""").strip()

# Clean target for C/C++.
ccleantarget = fix_indent_tabs("""
    -@if [[ -e $(binary) ]]; then\\
        if rm -f $(binary); then\\
            printf "Binaries cleaned.\\n";\\
        fi;\\
    else\\
        printf "Binaries already clean.\\n";\\
    fi;

    -@if ls *.o &>/dev/null; then\\
        if rm *.o; then\\
            printf "Objects cleaned.\\n";\\
        fi;\\
    else\\
        printf "Objects already clean.\\n";\\
    fi;
""").lstrip('\n')

# Make targets for rustc (until I find a better way)
rusttargets = fix_indent_tabs("""
all: $(source)
    $({compilervar}) $({cflagsvar}) -o $(binary) $(source)

debug: {cflagsvar}+=-g
debug: all

release: {cflagsvar}+=-O2
release: all
""").strip()

# Clean target for Rust/Cargo.
rustcleantarget = fix_indent_tabs("""
    -@if [[ -e $(binary) ]]; then\\
        if rm -f $(binary); then\\
            printf "Binaries cleaned.\\n";\\
        fi;\\
    else\\
        printf "Binaries already clean.\\n";\\
    fi;
""").lstrip('\n')

# Make targets for nasm.
nasmtargets = fix_indent_tabs("""
all: {objects}
    $({linkervar}) -o $(binary) $({linkerflagsvar}) *.o

debug: {linkerflagsvar}+={linkerflags_debug}
debug: {cflagsvar}+={cflags_debug}
debug: all

release: {linkerflagsvar}+={linkerflags_release}
release: {cflagsvar}+={cflags_release}
release: all
    @if strip $(binary); then\\
        printf "\\n%s was stripped.\\n" "$(binary)";\\
    else\\
        printf "\\nError stripping executable: %s\\n" "$(binary)" 1>&2;\\
    fi;

{objects}: $(source)
    $({compilervar}) $({cflagsvar}) $(source)
""").strip()

# Template options based on compiler name.
coptions = {
    'nasm': {
        'compilervar': 'CC',
        'cflagsvar': 'CFLAGS',
        'cflags_debug': format_cflags(('-g', '-F stabs')),
        'cflags_release': format_cflags(('-Ox', )),
        'linkervar': 'LD',
        'linkerflagsvar': 'LDFLAGS',
        'linkerflags_debug': '',
        'linkerflags_release': format_cflags(
            ('--strip-all', ),
            var='LDFLAGS'
        ),
        'compilervars': format_vars({'CC': 'nasm', 'LD': 'ld'}),
        'flagvars': format_vars(
            {'LDFLAGS': '-O1', 'CFLAGS': '-felf64 -Wall'}
        ),
        'libsline': '',
        'targets': nasmtargets,
        'cleantarget': ccleantarget,
    },
    'nasm-c': {
        'compilervar': 'CC',
        'cflagsvar': 'CFLAGS',
        'cflags_debug': format_cflags(('-g', '-F stabs')),
        'cflags_release': format_cflags(('-Ox', )),
        'linkervar': 'LD',
        'linkerflagsvar': 'LDFLAGS',
        'linkerflags_debug': format_cflags(
            ('-g3', '-DDEBUG'),
            var='LDFLAGS'
        ),
        'linkerflags_release': format_cflags(
            ('-O3', '-DNDEBUG'),
            var='LDFLAGS'
        ),
        'compilervars': format_vars({'CC': 'nasm', 'LD': 'gcc'}),
        'flagvars': format_vars(
            {'LDFLAGS': '-Wall -static', 'CFLAGS': '-felf64 -Wall'}
        ),
        'libsline': '',
        'targets': nasmtargets,
        'cleantarget': ccleantarget,
    },
    'gcc': {
        'compilervar': 'CC',
        'cflagsvar': 'CFLAGS',
        'compilervars': format_vars({'CC': 'gcc'}),
        'flagvars': format_vars(
            {'CFLAGS': format_cflags(csharedflags + conlyflags)}
        ),
        'libsline': '\nLIBS=',
        'targets': ctargets,
        'cleantarget': ccleantarget,
    },
    'g++': {
        'compilervar': 'CXX',
        'cflagsvar': 'CXXFLAGS',
        'compilervars': format_vars({'CXX': 'g++'}),
        'flagvars': format_vars(
            {'CXXFLAGS': format_cflags(csharedflags + cpponlyflags)}
        ),
        'libsline': '\nLIBS=',
        'targets': ctargets,
        'cleantarget': ccleantarget,
    },
    'rustc': {
        'compilervar': 'RUSTC',
        'cflagsvar': 'RUSTFLAGS',
        'compilervars': format_vars({'RUSTC': 'rustc'}),
        'flagvars': format_vars(
            {'RUSTFLAGS': ''}
        ),
        'libsline': '\nLIBS=',
        'targets': rusttargets,
        'cleantarget': rustcleantarget,
    }
}


def template_render(filepath, makefile=None, argd=None):
    """ Render the makefile template for a given c source file name. """
    argd = {} if (argd is None) else argd
    parentdir, filename = os.path.split(filepath)
    fileext = os.path.splitext(filename)[-1]
    makefile = os.path.join(parentdir, makefile or DEFAULT_MAKEFILE)
    binary = os.path.splitext(filename)[0]
    objects = '{}.o'.format(binary)

    # Get compiler and make options by file extension (default to gcc).
    compiler = {
        '.asm': 'nasm',
        '.asmc': 'nasm-c',
        '.c': 'gcc',
        '.cpp': 'g++',
        '.rs': 'rustc',
        '.s': 'nasm',
    }.get('.asmc' if argd.get('--clib', False) else fileext, 'gcc')

    # Create the base template, retrieve compiler-specific settings.
    debug('Rendering makefile template for {}.'.format(compiler))
    compileropts = coptions[compiler]
    template = pre_template.format(
        targets=compileropts.pop('targets'),
        cleantarget=compileropts.pop('cleantarget')
    )

    # Create template args, update with compiler-based options.
    templateargs = {
        'compiler': compiler,
        'binary': binary,
        'filename': filename,
        'objects': objects
    }
    templateargs.update(coptions[compiler])

    # Format the template with compiler-specific settings.
    return makefile, template.format(**templateargs)
