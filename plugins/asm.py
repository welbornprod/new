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


class AsmPlugin(Plugin):

    """ Creates a basic nasm source file. """

    name = ('asm', 'nasm')
    extensions = ('.asm', '.s', '.asmc')
    version = '0.0.5'
    ignore_post = {'chmodx'}
    docopt = True
    usage = """
    Usage:
        asm [-l]

    Options:
        -l,--clib  : Use C library.
    """
    description = '\n'.join((
        'Creates a basic asm file, with or without C library usage.',
    ))

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a basic nasm file. """
        _, basename = os.path.split(filename)
        name, _ = os.path.splitext(basename)
        objfile = '{}.o'.format(name)
        return self.get_template(filename).format(
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
        return {
            True: template_c,
            False: template,
        }.get(filename.lower().endswith('.asmc') or self.argd['--clib'])


exports = (AsmPlugin, )
