""" NASM plugin for New.
    -Christopher Welborn 9-10-15
"""
import os
from plugins import Plugin, date, fix_author

template = """;
; {name}
; ...
; To compile:
;   nasm -felf64 {filename} && ld -o {outputfile} {objectfile}
; Then run the executable:
;   ./{outputfile}
;
; {author}{date}

section .data

section .bss

section .text
    global _start

_start:
    nop               ; possible breakpoint
    ; exit(0)
    mov rax, 60       ; system call 60 is exit
    xor rdi,rdi       ; exit code 0
    syscall           ; invoke exit call
    nop               ; possible breakpoint

"""

# Template for asm using the C library.
template_c = """;
; {name}
; ...
; To compile:
;   nasm -felf64 {filename} && gcc -o {outputfile} {objectfile}
; Then run the executable:
;   ./{outputfile}
;
; {author}{date}

section .data
    message: db "Hello, World", 0  ; Strings are terminated with 0 in C.

section .bss

section .text
    global main
    extern puts

main:
    nop                   ; possible breakpoint
    mov rdi, message      ; First integer/pointer argument in rdi.
    call puts             ; puts(message)
    ret                   ; Return from main back into C library wrapper.
    nop                   ; possible breakpoint
"""

# Template for asm with no main.
template_blank = """;
; {name}
; ...
; To compile:
;   nasm -felf64 {filename} && gcc -o {outputfile} {objectfile}
;
; {author}{date}

section .data

section .bss

section .text
    nop                   ; possible breakpoint

    nop                   ; possible breakpoint
"""


class AsmPlugin(Plugin):

    """ Creates a basic nasm source file. """

    name = ('asm', 'nasm', 'yasm')
    extensions = ('.asm', '.s', '.asmc')
    version = '0.0.6'
    ignore_post = {'chmodx'}
    config_opts = {'author': 'Default author name for all files.'}
    docopt = True
    usage = """
    Usage:
        asm [-b | -l] [-m] [MAKE_ARGS]

    Options:
        MAKE_ARGS   : A comma-separated list of arguments to forward to the
                      makefile post-processing plugin, with - or -- preceding
                      them.
        -b,--blank  : Blank asm file, no _start label.
        -l,--clib   : Use C library.
        -m,--multi  : Multiple source file mode.
                      The first file is created with or without -l,
                      and the following files are blank source files.
    """
    description = '\n'.join((
        'Creates a basic asm file, with or without C library usage.',
    ))

    def __init__(self):
        self.load_config()
        # Arguments forwarded to the makefile post-processing plugin.
        self.automakefile_args = []

    def create(self, filename):
        """ Creates a basic nasm file. """
        _, basename = os.path.split(filename)
        name, _ = os.path.splitext(basename)
        objfile = '{}.o'.format(name)
        if self.argd['--multi'] and self.created:
            tmplate = template_blank
        else:
            tmplate = self.get_template(filename)

        self.automakefile_args = self.parse_make_args()
        return tmplate.format(
            name=name,
            filename=basename,
            author=fix_author(self.config.get('author', None)),
            date=date(),
            objectfile=objfile,
            outputfile=name,
        )

    def get_template(self, filename):
        """ Return the template we are using, based on the filename or
            self.argd['--clib'].
        """
        if self.argd['--clib'] or filename.endswith('.asmc'):
            return template_c
        elif self.argd['--blank']:
            return template_blank
        return template

    def parse_make_args(self):
        """ Parse the MAKE_ARGS cmdline argument, and return a list of
            flag arguments.
        """
        if not self.argd['MAKE_ARGS']:
            return []
        rawargs = [s.strip() for s in self.argd['MAKE_ARGS'].split(',') if s]
        return [
            '{}{}'.format(
                '-' if len(s) == 1 else '--',
                s,
            )
            for s in rawargs
            if s
        ]


exports = (AsmPlugin, )
